# ResumeAI — AI Resume Analyzer & Skill Improvement Platform

> AI-powered resume analysis, personalized skill improvement, job matching, and Resume Readiness Certificate — all in one platform.

---

## 🚀 Features

| Feature | Description |
|---|---|
| **AI Resume Analysis** | Deep analysis across 7 scoring categories |
| **ATS Compatibility Score** | Check if your resume passes ATS systems |
| **Skill Gap Detection** | Identify strong, weak, and missing skills |
| **Evidence-based Skill Levels** | Beginner / Intermediate / Advanced based on resume evidence |
| **Personalized Learning** | Curated free YouTube, docs, and practice resources |
| **Job Description Matching** | Compare resume vs job description with match score |
| **Progress Tracking** | Compare previous vs current analysis |
| **Learning Roadmap** | Week-by-week personalized improvement plan |
| **Resume Readiness Certificate** | Downloadable PDF certificate when thresholds are met |
| **Public Certificate Verification** | Verify certificates at `/verify/{cert_id}` |

---

## 🛠️ Tech Stack

**Backend:** Python 3.11+, Flask 3.x, Flask-CORS  
**AI:** Google Gemini API (`google-genai` SDK, `gemini-3.5-flash-lite` / `gemini-3.1-flash-lite` / `gemini-3.8-flash`) + OpenAI GPT-4o-mini support with structured analysis and dynamic fallback analyzer  
**Database:** Firebase Cloud Firestore  
**Storage:** Firebase Cloud Storage  
**Auth:** Firebase Authentication (Email/Password + Google OAuth)  
**PDF:** ReportLab (Certificate PDF generation)  
**Resume Parsing:** pdfplumber + PyMuPDF (fallback), python-docx  
**Frontend:** Vanilla ES6+ JavaScript, HTML5, CSS3 Custom Properties (Editorial Stationery Design System with Dark/Light modes), Chart.js  

---

## 📁 Project Structure

```
project/
│
├── app.py                     # Flask app factory
├── config.py                  # Configuration (env vars)
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
│
├── routes/
│   ├── auth_routes.py         # User profile CRUD
│   ├── resume_routes.py       # File upload + text extraction
│   ├── analysis_routes.py     # AI analysis, history, CRUD
│   ├── learning_routes.py     # Resources, roadmap, skill progress
│   ├── job_routes.py          # Job description matching
│   ├── certificate_routes.py  # Certificate generation + download
│   └── pages_routes.py        # HTML template serving
│
├── services/
│   ├── ai_service.py          # OpenAI API calls (never in frontend!)
│   ├── resume_parser.py       # PDF + DOCX text extraction
│   ├── scoring_service.py     # Score validation + normalization
│   ├── learning_service.py    # Curated resource database
│   └── certificate_service.py # PDF certificate generation (ReportLab)
│
├── templates/                 # Jinja2 HTML templates
│   ├── index.html             # Landing page
│   ├── login.html             # Login
│   ├── signup.html            # Signup
│   ├── forgot_password.html   # Password reset
│   ├── dashboard.html         # Main dashboard
│   ├── upload.html            # Resume upload + analysis trigger
│   ├── analysis.html          # Analysis results (5 tabs)
│   ├── skills.html            # Skill gap analysis
│   ├── learning.html          # Learning resources + roadmap
│   ├── job_match.html         # Job description matcher
│   ├── history.html           # Analysis history
│   ├── compare.html           # Analysis comparison
│   ├── profile.html           # User profile settings
│   ├── certificate.html       # Certificate generation
│   └── verify.html            # Public certificate verification
│
├── static/
│   ├── css/main.css           # Global design system (dark theme)
│   └── js/main.js             # Shared utilities + auth helpers
│
└── utils/
    └── firebase_helpers.py    # Firebase Admin SDK helpers
```

---

## ⚙️ Setup

### 1. Clone & Install

```bash
git clone <repo-url>
cd "Resume builder"
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Flask
FLASK_SECRET_KEY=your-random-secret-key

# Firebase Admin SDK (from service account JSON)
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com

# Firebase Frontend SDK (public — these are safe to expose)
FIREBASE_API_KEY=AIza...
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
```

### 3. Firebase Setup

#### Authentication
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a project
3. Enable **Authentication** → Sign-in Methods → Enable **Email/Password** and (optionally) **Google**

#### Firestore
1. Enable **Cloud Firestore** in your project
2. Start in **test mode** for development, then apply the security rules below
3. Create indexes as needed (Firestore will prompt you automatically on first query)

#### Firestore Security Rules
```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can only access their own data
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
      
      match /analyses/{analysisId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      match /roadmap/{taskId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      match /skill_progress/{skillId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      match /job_matches/{matchId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
      match /certificates/{certId} {
        allow read, write: if request.auth != null && request.auth.uid == userId;
      }
    }
    
    // Public certificate verification (read-only, no private data)
    match /certificates/{certId} {
      allow read: if true;  // Public
      allow write: if false; // Only backend (Admin SDK) can write
    }
  }
}
```

#### Firebase Storage
1. Enable **Cloud Storage** in your project
2. Apply these rules:
```
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /resumes/{userId}/{allPaths=**} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
  }
}
```

#### Firebase Admin SDK (Service Account)
1. Go to **Project Settings** → **Service Accounts**
2. Click **Generate New Private Key** → downloads a JSON file
3. Copy values from the JSON into your `.env` file

#### Firebase Frontend SDK
1. Go to **Project Settings** → **General** → **Your apps**
2. Register a Web app
3. Copy the config values into your `.env` file

### 4. OpenAI Setup
1. Get an API key from [platform.openai.com](https://platform.openai.com)
2. The app uses **`gpt-4o-mini`** by default (configurable in `config.py`)
3. Set `OPENAI_API_KEY` in your `.env`

### 5. Run Locally

```bash
python app.py
```

App runs at **http://localhost:5000**

---

## 🗄️ Firestore Data Structure

```
users/{uid}
  - fullName, email, degree, branch, college
  - experienceLevel, careerGoal, targetRole
  - createdAt, updatedAt

users/{uid}/analyses/{analysisId}
  - overallScore, atsScore, readinessScore, readinessStatus
  - categoryScores, skills, strongSkills, skillsToImprove, missingSkills
  - suggestions, learningRecommendations, fullAnalysis
  - filename, storagePath, fileUrl, createdAt

users/{uid}/roadmap/{taskId}
  - week, skill, topics, projectIdea, completed, completedAt

users/{uid}/job_matches/{matchId}
  - matchScore, matchedSkills, missingSkills, summary, jobDescription

users/{uid}/certificates/{certId}
  - certificateId, overallScore, atsScore, issuedAt, verificationStatus

certificates/{certId}       ← public collection for verification
  - certificateId, userName, overallScore, atsScore, issuedAt, verificationStatus
```

---

## 📈 Scoring System

| Category | Max Score |
|---|---|
| ATS Compatibility | 20 |
| Skills | 20 |
| Projects & Experience | 20 |
| Education | 10 |
| Achievements | 10 |
| Resume Structure | 10 |
| Readability & Grammar | 10 |
| **Total** | **100** |

**Readiness Score** = `(overall_score × 0.6) + (ats_score × 0.4)`

**Certificate Eligibility:**
- Overall Score ≥ 90
- ATS Score ≥ 90
(Thresholds configurable via `CERTIFICATE_READINESS_THRESHOLD` and `ATS_READINESS_THRESHOLD` env vars)

---

## 🔒 Security

- ✅ OpenAI API key is **never** exposed to the frontend
- ✅ All AI calls go through the Flask backend
- ✅ Firebase Admin SDK authenticates all API routes
- ✅ Firebase ID token verified server-side via `Authorization: Bearer <token>` header
- ✅ Users can only access their own Firestore data (enforced by both backend UID check and Firestore rules)
- ✅ Certificate verification page exposes only: name, scores, date, cert ID — no email, phone, or resume
- ✅ Uploaded resumes stored at `resumes/{uid}/{uuid}.{ext}` — user-scoped paths

---

## 📚 Adding Learning Resources

Edit `services/learning_service.py` → `CURATED_RESOURCES` dict:

```python
"your_skill": {
    "Beginner": [
        {
            "title": "Resource Title",
            "platform": "YouTube",
            "url": "https://...",
            "type": "youtube",  # youtube | documentation | course | practice
            "free": True,
        }
    ],
    "Intermediate": [...],
}
```

Only add **verified**, working URLs.

---

## 🎓 Certificate System

When a user's latest analysis meets the thresholds (default 90/90):

1. User clicks **Generate Certificate** on `/certificate`
2. Backend verifies scores, generates a unique `RA-YYYY-XXXXXX` certificate ID
3. Certificate metadata stored in both `certificates/{certId}` (public) and `users/{uid}/certificates/{certId}`
4. User downloads PDF via `/api/certificate/download/{certId}`
5. Anyone can verify at `/verify/{certId}` — shows only: name, scores, date, status

> ⚠️ This is a **platform assessment certificate** — not an industry certification, government certificate, or professional qualification.

---

## 🚀 Production Deployment

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

Set `FLASK_DEBUG=False` in production `.env`.

---

## 📝 License

MIT — See LICENSE file.

---

*ResumeAI is an independent AI-powered career tool. It is not affiliated with any government body, university, or industry accreditor.*
