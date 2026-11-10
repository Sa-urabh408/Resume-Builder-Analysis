"""
Pages Routes — serves all HTML template pages.
"""
from flask import Blueprint, render_template, current_app

pages_bp = Blueprint("pages", __name__)


def firebase_config():
    """Return Firebase frontend config dict for injection into templates."""
    return {
        "apiKey": current_app.config.get("FIREBASE_API_KEY", ""),
        "authDomain": current_app.config.get("FIREBASE_AUTH_DOMAIN", ""),
        "projectId": current_app.config.get("FIREBASE_PROJECT_ID", ""),
        "storageBucket": current_app.config.get("FIREBASE_STORAGE_BUCKET", ""),
        "messagingSenderId": current_app.config.get("FIREBASE_MESSAGING_SENDER_ID", ""),
        "appId": current_app.config.get("FIREBASE_APP_ID", ""),
    }


@pages_bp.route("/")
def index():
    return render_template("index.html", firebase=firebase_config())


@pages_bp.route("/login")
def login():
    return render_template("login.html", firebase=firebase_config())


@pages_bp.route("/signup")
def signup():
    return render_template("signup.html", firebase=firebase_config())


@pages_bp.route("/forgot-password")
def forgot_password():
    return render_template("forgot_password.html", firebase=firebase_config())


@pages_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", firebase=firebase_config())


@pages_bp.route("/upload")
def upload():
    return render_template("upload.html", firebase=firebase_config())


@pages_bp.route("/analysis")
def analysis():
    return render_template("analysis.html", firebase=firebase_config())


@pages_bp.route("/skills")
def skills():
    return render_template("skills.html", firebase=firebase_config())


@pages_bp.route("/learning")
def learning():
    return render_template("learning.html", firebase=firebase_config())


@pages_bp.route("/job-match")
def job_match():
    return render_template("job_match.html", firebase=firebase_config())


@pages_bp.route("/history")
def history():
    return render_template("history.html", firebase=firebase_config())


@pages_bp.route("/compare")
def compare():
    return render_template("compare.html", firebase=firebase_config())


@pages_bp.route("/profile")
def profile():
    return render_template("profile.html", firebase=firebase_config())


@pages_bp.route("/certificate")
def certificate():
    return render_template("certificate.html", firebase=firebase_config())


@pages_bp.route("/verify/<cert_id>")
def verify(cert_id):
    """Public certificate verification — no auth required."""
    from utils.firebase_helpers import get_db
    cert_data = None
    db = get_db()
    if db:
        try:
            doc = db.collection("certificates").document(cert_id).get()
            if doc and doc.exists:
                d = doc.to_dict()
                cert_data = {
                    "certificateId": d.get("certificateId", cert_id),
                    "userName": d.get("userName", ""),
                    "overallScore": d.get("overallScore", 0),
                    "atsScore": d.get("atsScore", 0),
                    "issuedAt": d.get("issuedAt", ""),
                    "verificationStatus": d.get("verificationStatus", "valid"),
                }
        except Exception as e:
            print(f"[Verify Error] {e}")

    return render_template("verify.html", cert_id=cert_id, cert_data=cert_data)
