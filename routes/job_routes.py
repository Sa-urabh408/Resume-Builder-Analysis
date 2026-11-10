"""
Job Description Matching Routes.
"""
import uuid
from flask import Blueprint, request, jsonify
from utils.firebase_helpers import get_db, get_user_from_request
from services.ai_service import match_job_description
from datetime import datetime

job_bp = Blueprint("job", __name__)


@job_bp.route("/match", methods=["POST"])
def job_match():
    """
    Match resume text against a job description.
    Expects JSON: { "extracted_text": "...", "job_description": "...", "analysis_id": "..." }
    """
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    data = request.get_json(silent=True) or {}
    resume_text = data.get("extracted_text", "").strip()
    job_desc = data.get("job_description", "").strip()

    if not resume_text:
        eval_id = data.get("evalId") or data.get("analysis_id") or data.get("id")
        db = get_db()
        if db:
            try:
                doc = None
                if eval_id:
                    doc = db.collection("users").document(uid).collection("evaluations").document(eval_id).get()
                if not doc or not doc.exists:
                    docs = list(db.collection("users").document(uid).collection("evaluations").order_by("createdAt", direction="DESCENDING").limit(1).stream())
                    if docs:
                        doc = docs[0]
                if doc and doc.exists:
                    edata = doc.to_dict()
                    resume_text = edata.get("extractedText") or edata.get("extracted_text") or edata.get("enhancedResume") or ""
                    if not resume_text and edata.get("fullAnalysis"):
                        fa = edata.get("fullAnalysis", {})
                        skills = ", ".join(fa.get("strong_skills", []) + fa.get("skills_to_improve", []))
                        resume_text = f"Candidate: {fa.get('candidate_name', 'Applicant')}\nTarget Role: {edata.get('targetRole', '')}\nSkills: {skills}\nSummary: {fa.get('executive_summary', '')}"
            except Exception as e:
                print(f"[Warning] Failed to fetch fallback resume text from Firestore: {e}")

    if not resume_text:
        return jsonify({"error": "No resume text found. Please upload or analyze your resume first."}), 400
    if not job_desc or len(job_desc) < 50:
        return jsonify({"error": "Please provide a valid job description (minimum 50 characters)."}), 400

    try:
        result = match_job_description(resume_text, job_desc)
    except ValueError as e:
        return jsonify({"error": f"AI matching failed: {str(e)}"}), 502
    except Exception as e:
        print(f"[Job Match Error] {e}")
        return jsonify({"error": "AI service temporarily unavailable."}), 503

    # Save to Firestore
    match_id = str(uuid.uuid4())
    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503
    try:
        match_doc = {
            "matchId": match_id,
            "uid": uid,
            "evalId": data.get("evalId", data.get("analysis_id", "")),
            "jobDescription": job_desc[:2000],
            "matchScore": result.get("match_score", 0),
            "matchedSkills": result.get("matched_skills", []),
            "missingSkills": result.get("missing_skills", []),
            "matchedKeywords": result.get("matched_keywords", []),
            "missingKeywords": result.get("missing_keywords", []),
            "recommendedAdditions": result.get("recommended_additions", []),
            "resumeChanges": result.get("resume_changes", []),
            "tailoredBullets": result.get("tailored_bullets", []),
            "summary": result.get("summary", ""),
            "fullResult": result,
            "createdAt": datetime.utcnow().isoformat(),
        }
        db.collection("users").document(uid).collection("job_matches").document(match_id).set(match_doc)
    except Exception as e:
        print(f"[ERROR] Firestore job match write failed for user {uid}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to save job match: {str(e)}"}), 500

    result["match_id"] = match_id
    return jsonify(result), 200


@job_bp.route("/history", methods=["GET"])
def job_match_history():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    docs = (
        db.collection("users").document(uid).collection("job_matches")
        .order_by("createdAt", direction="DESCENDING")
        .limit(10)
        .stream()
    )
    matches = []
    for doc in docs:
        d = doc.to_dict()
        matches.append({
            "matchId": d.get("matchId", doc.id),
            "matchScore": d.get("matchScore", 0),
            "jobDescriptionPreview": d.get("jobDescription", "")[:100],
            "createdAt": d.get("createdAt", ""),
        })
    return jsonify({"matches": matches}), 200
