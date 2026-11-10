"""
Analysis Routes — AI analysis, storage, retrieval.
"""
import uuid
import io
from flask import Blueprint, request, jsonify, send_file
from utils.firebase_helpers import get_db, get_user_from_request
from services.ai_service import analyze_resume, enhance_resume_content
from services.scoring_service import validate_and_normalize_scores, get_score_breakdown
from services.learning_service import get_resources_for_skill, get_youtube_video_for_skill
from services.certificate_service import generate_resume_audit_pdf
from datetime import datetime

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/analyze", methods=["POST"])
def analyze():
    """
    Analyze a resume. Expects JSON:
    { "extracted_text": "...", "storage_path": "...", "filename": "...",
      "career_goal": "...", "experience_level": "..." }
    """
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    data = request.get_json(silent=True) or {}
    resume_text = data.get("extracted_text", "").strip()

    if not resume_text or len(resume_text) < 50:
        return jsonify({"error": "Resume text is empty or too short to analyze."}), 400

    career_goal = data.get("career_goal", "")
    experience_level = data.get("experience_level", "")

    try:
        analysis = analyze_resume(resume_text, career_goal, experience_level)
    except ValueError as e:
        return jsonify({"error": f"AI analysis failed: {str(e)}"}), 502
    except Exception as e:
        print(f"[Analysis Error] {e}")
        return jsonify({"error": "AI service temporarily unavailable. Please try again."}), 503

    # Validate and normalize scores
    analysis = validate_and_normalize_scores(analysis)

    # Enrich learning recommendations with curated resources & guaranteed YouTube tutorials
    for rec in analysis.get("learning_recommendations", []):
        skill = rec.get("skill", "")
        level = rec.get("current_level", "Beginner")
        rec["curated_resources"] = get_resources_for_skill(skill, level)
        rec["youtube_video"] = get_youtube_video_for_skill(skill, level)

    # Generate 1-Click AI Enhanced & Rewritten Resume Draft
    try:
        enhanced_version = enhance_resume_content(resume_text, career_goal, analysis)
        analysis["enhanced_resume"] = enhanced_version
    except Exception as enh_err:
        print(f"[Warning] Enhanced resume generation non-fatal error: {enh_err}")
        analysis["enhanced_resume"] = None

    # Add score breakdown
    analysis["score_breakdown"] = get_score_breakdown(analysis)

    # Save to Firestore (evaluations collection)
    eval_id = str(uuid.uuid4())
    db = get_db()
    if not db:
        print("[ERROR] Database connection unavailable during analysis save.")
        return jsonify({"error": "Database service unavailable. Analysis could not be saved."}), 503

    now_iso = datetime.utcnow().isoformat()
    eval_doc = {
        "evalId": eval_id,
        "uid": uid,
        "filename": data.get("filename", "resume.pdf"),
        "extractedText": resume_text,
        "overallScore": analysis.get("overall_score", 0),
        "atsScore": analysis.get("ats_score", 0),
        "readinessScore": analysis.get("readiness_score", 0),
        "readinessStatus": analysis.get("readiness_status", "Improving"),
        "scores": analysis.get("category_scores", {}),
        "categoryScores": analysis.get("category_scores", {}),
        "skills": {
            "strong": analysis.get("strong_skills", []),
            "improve": analysis.get("skills_to_improve", []),
            "missing": analysis.get("missing_skills", [])
        },
        "strongSkills": analysis.get("strong_skills", []),
        "skillsToImprove": analysis.get("skills_to_improve", []),
        "missingSkills": analysis.get("missing_skills", []),
        "roadmap": analysis.get("learning_recommendations", []),
        "learningRecommendations": analysis.get("learning_recommendations", []),
        "suggestions": analysis.get("suggestions", []),
        "targetRole": career_goal,
        "careerGoal": career_goal,
        "experienceLevel": experience_level,
        "enhancedResume": analysis.get("enhanced_resume"),
        "fullAnalysis": analysis,
        "createdAt": now_iso
    }

    try:
        # Write ONLY to users/{uid}/evaluations collection
        user_ref = db.collection("users").document(uid)
        user_ref.collection("evaluations").document(eval_id).set(eval_doc)
        print(f"[SUCCESS] Saved evaluation {eval_id} to users/{uid}/evaluations")
    except Exception as e:
        print(f"[ERROR] Firestore write failed for user {uid}: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to save evaluation to database: {str(e)}"}), 500

    analysis["eval_id"] = eval_id
    analysis["evalId"] = eval_id
    analysis["analysis_id"] = eval_id
    return jsonify(analysis), 200


@analysis_bp.route("/history", methods=["GET"])
def get_history():
    """Return all evaluations for the current user (latest first)."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    try:
        docs = list(
            db.collection("users").document(uid).collection("evaluations")
            .order_by("createdAt", direction="DESCENDING")
            .limit(50)
            .stream()
        )
    except Exception as e:
        print(f"[ERROR] Firestore history query failed for user {uid}: {e}")
        return jsonify({"error": "Failed to load evaluation history."}), 500

    items = []
    for doc in docs:
        d = doc.to_dict()
        created_at = d.get("createdAt", "")
        if hasattr(created_at, "isoformat"):
            created_at = created_at.isoformat()

        items.append({
            "evalId": d.get("evalId", getattr(doc, "id", "")),
            "filename": d.get("filename", "resume.pdf"),
            "overallScore": d.get("overallScore", 0),
            "atsScore": d.get("atsScore", 0),
            "readinessScore": d.get("readinessScore", 0),
            "readinessStatus": d.get("readinessStatus", "Improving"),
            "createdAt": str(created_at),
            "careerGoal": d.get("careerGoal", d.get("targetRole", "")),
            "targetRole": d.get("targetRole", d.get("careerGoal", "")),
            "analysisId": d.get("evalId", getattr(doc, "id", "")),
        })
    return jsonify({"evaluations": items, "analyses": items}), 200


@analysis_bp.route("/<analysis_id>", methods=["GET"])
def get_analysis(analysis_id):
    """Return full evaluation by ID."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    try:
        doc = db.collection("users").document(uid).collection("evaluations").document(analysis_id).get()
    except Exception as e:
        print(f"[ERROR] Firestore get_analysis error for {analysis_id}: {e}")
        return jsonify({"error": "Failed to fetch evaluation from database."}), 500

    if not doc or not doc.exists:
        return jsonify({"error": "Evaluation not found"}), 404

    data = doc.to_dict()
    if hasattr(data.get("createdAt"), "isoformat"):
        data["createdAt"] = data["createdAt"].isoformat()

    return jsonify(data), 200


@analysis_bp.route("/<analysis_id>", methods=["DELETE"])
def delete_analysis(analysis_id):
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    try:
        db.collection("users").document(uid).collection("evaluations").document(analysis_id).delete()
        print(f"[SUCCESS] Deleted evaluation {analysis_id} for user {uid}")
    except Exception as e:
        print(f"[ERROR] Firestore delete_analysis error: {e}")
        return jsonify({"error": "Failed to delete evaluation."}), 500

    return jsonify({"message": "Evaluation deleted successfully"}), 200


@analysis_bp.route("/<analysis_id>/report-pdf", methods=["GET"])
def download_analysis_report(analysis_id):
    """Generate and stream a comprehensive PDF audit report for an evaluation."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    try:
        doc = db.collection("users").document(uid).collection("evaluations").document(analysis_id).get()
    except Exception as e:
        print(f"[ERROR] Firestore get_analysis error for PDF {analysis_id}: {e}")
        return jsonify({"error": "Failed to fetch evaluation from database."}), 500

    if not doc or not doc.exists:
        return jsonify({"error": "Evaluation not found"}), 404

    data = doc.to_dict()
    user_doc = db.collection("users").document(uid).get()
    user_name = user_doc.to_dict().get("fullName", "Candidate") if user_doc.exists else "Candidate"

    try:
        pdf_bytes = generate_resume_audit_pdf(data, candidate_name=user_name, base_url=request.host_url.rstrip("/"))
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"ResumeAI_Audit_Report_{analysis_id[:8]}.pdf",
        )
    except Exception as pdf_err:
        print(f"[PDF Gen Error] {pdf_err}")
        return jsonify({"error": f"Failed to generate report PDF: {str(pdf_err)}"}), 500

