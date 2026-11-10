import os
import json
import traceback
import firebase_admin
from firebase_admin import credentials
from flask import Flask
from flask_cors import CORS
from config import Config


def _resolve_credentials_path(app, raw_path):
    path = (raw_path or "./firebase-key.json").strip()
    if os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(app.root_path, path))


def init_firebase(app):
    if firebase_admin._apps:
        return

    bucket = app.config.get("FIREBASE_STORAGE_BUCKET") or ""

    cred_json = (app.config.get("FIREBASE_CREDENTIALS_JSON") or os.getenv("FIREBASE_CREDENTIALS_JSON") or "").strip()
    if cred_json:
        try:
            data = json.loads(cred_json)
            cred = credentials.Certificate(data)
            options = {}
            if bucket:
                options["storageBucket"] = bucket
            firebase_admin.initialize_app(cred, options)
            print("[INFO] Firebase Admin initialized using FIREBASE_CREDENTIALS_JSON")
            return
        except Exception as e:
            print("[ERROR] FIREBASE_CREDENTIALS_JSON failed:", e)
            traceback.print_exc()

    key_path = _resolve_credentials_path(
        app,
        app.config.get("FIREBASE_CREDENTIALS") or os.getenv("FIREBASE_CREDENTIALS") or "./firebase-key.json",
    )
    if os.path.exists(key_path):
        try:
            cred = credentials.Certificate(key_path)
            options = {}
            if bucket:
                options["storageBucket"] = bucket
            firebase_admin.initialize_app(cred, options)
            print("[INFO] Firebase Admin initialized using FIREBASE_CREDENTIALS file")
            return
        except Exception as e:
            print("[ERROR] Failed to load Firebase credentials file:", e)
            traceback.print_exc()
    else:
        print("[ERROR] Firebase credentials file not found. Set FIREBASE_CREDENTIALS or FIREBASE_CREDENTIALS_JSON.")

    cred_dict = {
        "type": "service_account",
        "project_id": app.config.get("FIREBASE_PROJECT_ID", ""),
        "private_key_id": app.config.get("FIREBASE_PRIVATE_KEY_ID", ""),
        "private_key": app.config.get("FIREBASE_PRIVATE_KEY", ""),
        "client_email": app.config.get("FIREBASE_CLIENT_EMAIL", ""),
        "client_id": app.config.get("FIREBASE_CLIENT_ID", ""),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
    if cred_dict["project_id"] and cred_dict["client_email"] and cred_dict["private_key"]:
        try:
            cred = credentials.Certificate(cred_dict)
            options = {}
            if bucket:
                options["storageBucket"] = bucket
            firebase_admin.initialize_app(cred, options)
            print("[INFO] Firebase Admin initialized using env service-account fields")
            return
        except Exception as e:
            print("[ERROR] Env service-account fields failed:", e)
            traceback.print_exc()
    else:
        print("[ERROR] Firebase Admin is not initialized. Auth API calls will return 401.")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app)

    init_firebase(app)

    from routes.auth_routes import auth_bp
    from routes.resume_routes import resume_bp
    from routes.analysis_routes import analysis_bp
    from routes.learning_routes import learning_bp
    from routes.job_routes import job_bp
    from routes.certificate_routes import certificate_bp
    from routes.pages_routes import pages_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(resume_bp, url_prefix="/api/resume")
    app.register_blueprint(analysis_bp, url_prefix="/api/analysis")
    app.register_blueprint(learning_bp, url_prefix="/api/learning")
    app.register_blueprint(job_bp, url_prefix="/api/job")
    app.register_blueprint(certificate_bp, url_prefix="/api/certificate")

    @app.route("/health")
    def health():
        return {"status": "ok", "service": "ResumeAI"}, 200

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
