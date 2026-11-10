"""
Learning Routes — learning resources filter + roadmap.
"""
from flask import Blueprint, request, jsonify
from utils.firebase_helpers import get_db, get_user_from_request
from services.learning_service import get_resources_for_skill, get_all_curated_skills
from datetime import datetime

learning_bp = Blueprint("learning", __name__)


@learning_bp.route("/resources", methods=["GET"])
def get_resources():
    """
    GET /api/learning/resources?skill=python&level=Beginner&free_only=true
    """
    skill = request.args.get("skill", "").strip()
    level = request.args.get("level", "Beginner").strip()
    free_only = request.args.get("free_only", "true").lower() == "true"

    if not skill:
        return jsonify({"error": "skill parameter is required"}), 400

    resources = get_resources_for_skill(skill, level, free_only)
    return jsonify({"skill": skill, "level": level, "resources": resources}), 200


@learning_bp.route("/skills", methods=["GET"])
def get_supported_skills():
    """Return list of skills with curated resources."""
    return jsonify({"skills": get_all_curated_skills()}), 200


@learning_bp.route("/roadmap", methods=["GET"])
def get_roadmap():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    docs = db.collection("users").document(uid).collection("roadmap").stream()
    tasks = [doc.to_dict() for doc in docs]
    tasks.sort(key=lambda x: x.get("week", 0))
    return jsonify({"tasks": tasks}), 200


@learning_bp.route("/roadmap", methods=["POST"])
def save_roadmap():
    """Save AI-generated roadmap tasks to Firestore."""
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    data = request.get_json(silent=True) or {}
    tasks = data.get("tasks", [])
    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    batch = db.batch()
    for task in tasks:
        task_id = task.get("id", str(datetime.utcnow().timestamp()).replace(".", ""))
        ref = db.collection("users").document(uid).collection("roadmap").document(task_id)
        task["uid"] = uid
        task.setdefault("completed", False)
        task.setdefault("createdAt", datetime.utcnow().isoformat())
        batch.set(ref, task, merge=True)
    batch.commit()

    return jsonify({"message": f"Saved {len(tasks)} roadmap tasks."}), 200


@learning_bp.route("/roadmap/<task_id>/complete", methods=["PATCH"])
def complete_task(task_id):
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    ref = db.collection("users").document(uid).collection("roadmap").document(task_id)
    ref.update({"completed": True, "completedAt": datetime.utcnow().isoformat()})
    return jsonify({"message": "Task marked complete"}), 200


@learning_bp.route("/skill-progress", methods=["GET"])
def get_skill_progress():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    db = get_db()
    if not db:
        return jsonify({"error": "Database not configured"}), 503

    docs = db.collection("users").document(uid).collection("skill_progress").stream()
    skills = [doc.to_dict() for doc in docs]
    return jsonify({"skills": skills}), 200
