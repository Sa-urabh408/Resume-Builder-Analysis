"""
Auth Routes — user profile creation and retrieval (Firestore side).
Firebase Auth itself is handled client-side with Firebase JS SDK.
"""
from flask import Blueprint, request, jsonify, current_app
from utils.firebase_helpers import get_db, get_user_from_request
from datetime import datetime

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/profile", methods=["GET"])
def get_profile():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    doc = db.collection("users").document(uid).get()
    if doc.exists:
        return jsonify(doc.to_dict()), 200
    return jsonify({"error": "Profile not found"}), 404


@auth_bp.route("/profile", methods=["POST"])
def create_profile():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    data = request.get_json(silent=True) or {}
    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    now = datetime.utcnow().isoformat()
    user_ref = db.collection("users").document(uid)
    existing = user_ref.get()
    profile = {
        "uid": uid,
        "fullName": data.get("fullName", ""),
        "email": data.get("email", ""),
        "profileImage": data.get("profileImage", ""),
        "education": data.get("education", ""),
        "degree": data.get("degree", ""),
        "branch": data.get("branch", ""),
        "college": data.get("college", ""),
        "experienceLevel": data.get("experienceLevel", ""),
        "careerGoal": data.get("careerGoal", ""),
        "targetRole": data.get("targetRole", ""),
        "updatedAt": now,
    }
    if not existing.exists:
        profile["createdAt"] = now
    elif "createdAt" not in (existing.to_dict() or {}):
        profile["createdAt"] = now

    user_ref.set(profile, merge=True)
    return jsonify({"message": "Profile created", "profile": profile}), 200


@auth_bp.route("/profile", methods=["PUT"])
def update_profile():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    data = request.get_json(silent=True) or {}
    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    allowed_fields = ["fullName", "education", "degree", "branch", "college",
                      "experienceLevel", "careerGoal", "targetRole", "profileImage"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    update_data["updatedAt"] = datetime.utcnow().isoformat()

    db.collection("users").document(uid).set(update_data, merge=True)
    return jsonify({"message": "Profile updated"}), 200


@auth_bp.route("/profile", methods=["DELETE"])
def delete_user_data():
    """Delete all data associated with the user (evaluations, roadmap, job_matches, user doc)."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    try:
        user_ref = db.collection("users").document(uid)

        # Helper to delete subcollection
        for subcoll in ["evaluations", "roadmap", "job_matches", "skill_progress", "certificates", "learning"]:
            docs = user_ref.collection(subcoll).stream()
            for doc in docs:
                doc.reference.delete()

        # Delete user doc itself
        user_ref.delete()
        print(f"[SUCCESS] Deleted all data for user {uid}")
        return jsonify({"message": "All user data deleted successfully."}), 200
    except Exception as e:
        print(f"[ERROR] Failed to delete user data for {uid}: {e}")
        return jsonify({"error": f"Failed to delete user data: {str(e)}"}), 500
