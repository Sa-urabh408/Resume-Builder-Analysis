import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_FILE_SIZE_MB", 10)) * 1024 * 1024

    # AI Providers (OpenAI or Gemini)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4o-mini"
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

    # Firebase Admin
    FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_PRIVATE_KEY_ID = os.getenv("FIREBASE_PRIVATE_KEY_ID", "")
    FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
    FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    FIREBASE_CLIENT_ID = os.getenv("FIREBASE_CLIENT_ID", "")
    FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    # Firebase Frontend SDK (injected into templates)
    FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
    FIREBASE_AUTH_DOMAIN = os.getenv("FIREBASE_AUTH_DOMAIN", "")
    FIREBASE_DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL", "")
    FIREBASE_MESSAGING_SENDER_ID = os.getenv("FIREBASE_MESSAGING_SENDER_ID", "")
    FIREBASE_APP_ID = os.getenv("FIREBASE_APP_ID", "")
    FIREBASE_CREDENTIALS = os.getenv("FIREBASE_CREDENTIALS", "./firebase-key.json")
    FIREBASE_CREDENTIALS_JSON = os.getenv("FIREBASE_CREDENTIALS_JSON", "")

    # Resume Readiness Criteria
    CERTIFICATE_READINESS_THRESHOLD = int(os.getenv("CERTIFICATE_READINESS_THRESHOLD", 70))
    ATS_READINESS_THRESHOLD = int(os.getenv("ATS_READINESS_THRESHOLD", 70))

    # Scoring Weights (must sum to 100)
    SCORING_WEIGHTS = {
        "ats_compatibility": 20,
        "skills": 20,
        "projects_experience": 20,
        "education": 10,
        "achievements": 10,
        "structure": 10,
        "readability": 10,
    }

    # Allowed file types
    ALLOWED_EXTENSIONS = {"pdf", "docx"}

    @staticmethod
    def allowed_file(filename):
        return "." in filename and \
               filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
