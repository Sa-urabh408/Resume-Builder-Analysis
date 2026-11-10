"""
Scoring service — validates and normalizes AI scores, enforces weight caps.
"""
from flask import current_app

SCORING_WEIGHTS = {
    "ats_compatibility": 20,
    "skills": 20,
    "projects_experience": 20,
    "education": 10,
    "achievements": 10,
    "structure": 10,
    "readability": 10,
}


def clamp(value, min_val=0, max_val=100):
    return max(min_val, min(max_val, int(value or 0)))


def validate_and_normalize_scores(analysis: dict) -> dict:
    """
    Ensures all scores are within valid ranges and re-calculates
    the overall score from category scores for transparency.
    """
    try:
        from flask import has_app_context, current_app
        weights = current_app.config.get("SCORING_WEIGHTS", SCORING_WEIGHTS) if has_app_context() else SCORING_WEIGHTS
    except Exception:
        weights = SCORING_WEIGHTS
    category_scores = analysis.get("category_scores", {})

    # Clamp each category to its max weight
    normalized = {}
    computed_total = 0
    for key, max_weight in weights.items():
        raw = category_scores.get(key, 0)
        if isinstance(raw, dict):
            raw = raw.get("score", 0)
        clamped = clamp(raw, 0, max_weight)
        normalized[key] = clamped
        computed_total += clamped

    analysis["category_scores"] = normalized
    # Use computed total (more transparent than raw AI value)
    analysis["overall_score"] = clamp(computed_total, 0, 100)

    # Clamp ATS score
    analysis["ats_score"] = clamp(analysis.get("ats_score", 0), 0, 100)

    # Compute readiness score
    overall = analysis["overall_score"]
    ats = analysis["ats_score"]
    readiness = round((overall * 0.6 + ats * 0.4))
    analysis["readiness_score"] = clamp(readiness, 0, 100)

    # Readiness status
    if readiness >= 90:
        analysis["readiness_status"] = "Resume Ready"
    elif readiness >= 75:
        analysis["readiness_status"] = "Nearly Ready"
    elif readiness >= 50:
        analysis["readiness_status"] = "Improving"
    else:
        analysis["readiness_status"] = "Needs Improvement"

    return analysis


def get_score_breakdown(analysis: dict) -> list[dict]:
    """Returns a list of score breakdown items for UI display."""
    weights = SCORING_WEIGHTS
    scores = analysis.get("category_scores", {})
    feedback = analysis.get("category_feedback", {})

    labels = {
        "ats_compatibility": "ATS Compatibility",
        "skills": "Skills",
        "projects_experience": "Projects & Experience",
        "education": "Education",
        "achievements": "Achievements",
        "structure": "Resume Structure",
        "readability": "Readability & Grammar",
    }

    breakdown = []
    for key, max_weight in weights.items():
        breakdown.append({
            "key": key,
            "label": labels.get(key, key.replace("_", " ").title()),
            "score": scores.get(key, 0),
            "max": max_weight,
            "percentage": round((scores.get(key, 0) / max_weight) * 100) if max_weight else 0,
            "feedback": feedback.get(key, ""),
        })
    return breakdown
