"""
Certificate Routes — generation, download, and public verification.
"""
from flask import Blueprint, request, jsonify, send_file, current_app
from utils.firebase_helpers import get_db, get_user_from_request
from services.certificate_service import generate_certificate_pdf, generate_certificate_id
from datetime import datetime
import io

certificate_bp = Blueprint("certificate", __name__)


@certificate_bp.route("/check-eligibility", methods=["GET"])
def check_eligibility():
    """Check if user meets readiness criteria for a certificate."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"eligible": False, "reason": "Database not configured"}), 200

    # Get latest analysis strictly from evaluations collection
    if not db:
        return jsonify({"eligible": False, "reason": "Database not configured"}), 200

    try:
        req_analysis_id = request.args.get("analysis_id") or request.args.get("eval_id")
        if req_analysis_id:
            doc = db.collection("users").document(uid).collection("evaluations").document(req_analysis_id).get()
            docs = [doc] if doc and doc.exists else []
        else:
            docs = list(
                db.collection("users").document(uid).collection("evaluations")
                .stream()
            )
    except Exception as e:
        print(f"[ERROR] Certificate check eligibility query failed: {e}")
        return jsonify({"eligible": False, "reason": "Failed to load evaluation from database."}), 500

    if not docs:
        return jsonify({"eligible": False, "reason": "No resume evaluation found. Please evaluate your resume first."}), 200

    all_evals = [d.to_dict() for d in docs if (d.exists if hasattr(d, 'exists') else True)]
    if not all_evals:
        return jsonify({"eligible": False, "reason": "No resume evaluation found. Please evaluate your resume first."}), 200

    # Pick the best evaluation by overallScore
    latest = max(all_evals, key=lambda x: (x.get("overallScore", 0), x.get("atsScore", 0)))
    overall = latest.get("overallScore", 0)
    ats = latest.get("atsScore", 0)
    readiness = latest.get("readinessScore", 0)

    # Realistic thresholds — lowered so AI-scored resumes can actually qualify
    threshold = current_app.config.get("CERTIFICATE_READINESS_THRESHOLD", 70)
    ats_threshold = current_app.config.get("ATS_READINESS_THRESHOLD", 70)

    if overall >= threshold and ats >= ats_threshold:
        return jsonify({
            "eligible": True,
            "overallScore": overall,
            "resumeScore": overall,   # alias for JS compat
            "atsScore": ats,
            "readinessScore": readiness,
            "analysisId": latest.get("evalId", ""),
            "threshold": threshold,
            "atsThreshold": ats_threshold,
        }), 200
    else:
        missing = []
        if overall < threshold:
            missing.append(f"Overall score must be ≥{threshold} (current: {overall})")
        if ats < ats_threshold:
            missing.append(f"ATS score must be ≥{ats_threshold} (current: {ats})")
        return jsonify({
            "eligible": False,
            "reason": " | ".join(missing),
            "overallScore": overall,
            "resumeScore": overall,   # alias for JS compat
            "atsScore": ats,
            "threshold": threshold,
            "atsThreshold": ats_threshold,
        }), 200


@certificate_bp.route("/generate", methods=["POST"])
def generate_certificate():
    """Generate and store a certificate."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    # Query evaluations — use best evaluation or requested evaluation
    try:
        body = request.get_json(silent=True) or {}
        req_eval_id = body.get("evalId") or body.get("analysis_id") or request.args.get("analysis_id")
        if req_eval_id:
            doc = db.collection("users").document(uid).collection("evaluations").document(req_eval_id).get()
            docs = [doc] if doc and doc.exists else []
        else:
            docs = list(
                db.collection("users").document(uid).collection("evaluations")
                .stream()
            )
    except Exception as e:
        print(f"[ERROR] Generate cert query failed: {e}")
        return jsonify({"error": "Failed to load evaluation."}), 500

    if not docs:
        return jsonify({"error": "No resume evaluation found."}), 400

    all_evals = [d.to_dict() for d in docs if (d.exists if hasattr(d, 'exists') else True)]
    if not all_evals:
        return jsonify({"error": "No resume evaluation found."}), 400

    latest = max(all_evals, key=lambda x: (x.get("overallScore", 0), x.get("atsScore", 0)))
    overall = latest.get("overallScore", 0)
    ats = latest.get("atsScore", 0)

    # Realistic thresholds — lowered so AI-scored resumes can actually qualify
    threshold = current_app.config.get("CERTIFICATE_READINESS_THRESHOLD", 70)
    ats_threshold = current_app.config.get("ATS_READINESS_THRESHOLD", 70)

    if overall < threshold or ats < ats_threshold:
        return jsonify({"error": f"Resume does not yet meet readiness criteria (need ≥{threshold} overall, ≥{ats_threshold} ATS). Current: {overall}/{ats}."}), 403

    # Get user name
    user_doc = db.collection("users").document(uid).get()
    name = user_doc.to_dict().get("fullName", "User") if user_doc.exists else "User"

    # Generate certificate
    cert_id = generate_certificate_id()
    issue_date = datetime.utcnow().strftime("%B %d, %Y")
    base_url = request.host_url.rstrip("/")

    now = datetime.utcnow().isoformat()

    # Store metadata
    cert_doc = {
        "certificateId": cert_id,
        "uid": uid,
        "userName": name,
        "overallScore": overall,
        "atsScore": ats,
        "analysisId": latest.get("analysisId", ""),
        "issuedAt": now,
        "verificationStatus": "valid",
    }
    db.collection("certificates").document(cert_id).set(cert_doc)
    # Also store in user sub-collection
    db.collection("users").document(uid).collection("certificates").document(cert_id).set(cert_doc)

    return jsonify({
        "certificateId": cert_id,
        "certificate": {
            "certificateId": cert_id,
            "userName": name,
            "overallScore": overall,
            "atsScore": ats,
            "issuedAt": now,
            "issueDate": issue_date,
            "verifyUrl": f"{base_url}/verify/{cert_id}",
        },
        "name": name,
        "overallScore": overall,
        "atsScore": ats,
        "issuedAt": now,
        "issueDate": issue_date,
        "verifyUrl": f"{base_url}/verify/{cert_id}",
    }), 200


@certificate_bp.route("/download/<cert_id>", methods=["GET"])
def download_certificate(cert_id):
    """Generate and stream PDF certificate."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    cert_doc = db.collection("certificates").document(cert_id).get()
    if not cert_doc.exists:
        return jsonify({"error": "Certificate not found"}), 404

    cert_data = cert_doc.to_dict()
    if cert_data.get("uid") != uid:
        return jsonify({"error": "Unauthorized"}), 403

    issue_date = datetime.fromisoformat(cert_data.get("issuedAt", datetime.utcnow().isoformat())).strftime("%B %d, %Y")
    base_url = request.host_url.rstrip("/")

    pdf_bytes = generate_certificate_pdf(
        name=cert_data.get("userName", "User"),
        readiness_score=cert_data.get("overallScore", 0),
        ats_score=cert_data.get("atsScore", 0),
        certificate_id=cert_id,
        issue_date=issue_date,
        base_url=base_url,
    )

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"ResumeAI_Certificate_{cert_id}.pdf",
    )


@certificate_bp.route("/my-certificates", methods=["GET"])
def my_certificates():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    docs = db.collection("users").document(uid).collection("certificates").stream()
    certs = [doc.to_dict() for doc in docs]
    return jsonify({"certificates": certs}), 200
