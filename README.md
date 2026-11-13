# ResumeAI — AI Resume Analyzer & Career Readiness Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Framework-Flask%203.x-green?logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/AI-Google%20Gemini%20API-orange?logo=google&logoColor=white" alt="Google Gemini">
  <img src="https://img.shields.io/badge/Database-Firebase%20Firestore-yellow?logo=firebase&logoColor=white" alt="Firebase">
  <img src="https://img.shields.io/badge/Auth-Firebase%20Authentication-red?logo=firebase&logoColor=white" alt="Firebase Auth">
  <img src="https://img.shields.io/badge/PDF%20Engine-ReportLab-lightgrey" alt="ReportLab">
  <img src="https://img.shields.io/badge/License-MIT-purple" alt="License">
</p>

> **ResumeAI** is an end-to-end career intelligence and resume evaluation platform powered by **Google Gemini AI**. It parses PDFs/DOCX resumes, assesses ATS compatibility, detects evidence-based skill gaps, matches resumes against job descriptions, provides personalized learning roadmaps, and generates verifiable PDF readiness certificates.

---

## 🌟 Key Features

| Feature | Description |
|---|---|
| 🤖 **Deep AI Resume Analysis** | Multi-category scoring (ATS, Technical Skills, Projects, Experience, Education, Grammar) powered by Google Gemini 3.x models. |
| 📊 **ATS Compatibility Check** | Evaluates document structure, keyword density, section headers, and formatting to maximize ATS parsing pass rates. |
| 🎯 **Evidence-based Skill Gap Detection** | Categorizes extracted skills into Strong, Needs Improvement, and Missing with proficiency levels (Beginner, Intermediate, Advanced). |
| 💼 **Job Description Matching** | Compares resume text with specific target job descriptions, highlights missing keywords, and calculates match percentages. |
| 📚 **Personalized Learning Roadmaps** | Generates tailored week-by-week learning plans with curated, verified free resources (YouTube, official documentation, practice labs). |
| 🔄 **Multi-Evaluation History & Compare** | Tracks progress across revisions with visual side-by-side diffs and delta badges for category scores. |
| 🏅 **Verifiable Readiness Certificate** | Generates dynamic, cryptographic PDF certificates via ReportLab for resumes meeting readiness thresholds (≥70/100). |
| 🔗 **Public Verification & LinkedIn Integration** | Public verification portal (`/verify/<cert_id>`) with one-click "Add to LinkedIn Profile" deeplink integration. |
| 🎨 **Editorial Stationery UI** | Refined warm paper aesthetic, fluid responsive layouts, dark & light theme modes, and accessible typography. |

---

## 🛠️ Architecture & Tech Stack

```
[ Frontend: Vanilla ES6+ / HTML5 / CSS3 / Chart.js ]
                        │
                        ▼ (HTTP REST / Bearer Token)
[ Backend: Flask 3.x Application Factory ]
      │               │                  │
      ▼               ▼                  ▼
[ Google Gemini AI ]  [ Firebase Auth ]  [ Cloud Firestore & Storage ]
(3.5-flash-lite /     (Token Verify)     (User Profiles, Evaluations,
 3.1-flash-lite /                         Job Matches, Certificates)
 dynamic analyzer)
```

* **Backend Engine:** Python 3.11+, Flask 3.x, Werkzeug, Flask-CORS
* **Generative AI:** Google Gemini API (`google-genai` SDK) with automatic model fallback cascade (`gemini-3.5-flash-lite` → `gemini-3.1-flash-lite` → `gemini-3.8-flash`) + dynamic analyzer
* **Database & Storage:** Firebase Cloud Firestore (structured documents) & Firebase Storage
* **Authentication:** Firebase Client SDK (Email/Password & Google OAuth) + Firebase Admin SDK (Server-side JWT verification)
* **Document Parsing:** `pdfplumber`, `PyMuPDF` (`fitz`), and `python-docx`
* **PDF Generation:** `ReportLab` engine with dynamic cryptographic QR / verification links
* **Frontend:** Vanilla JavaScript (Modular ES6 modules), CSS3 custom properties, responsive grid layout

---

## 📁 Repository Structure

```
resume-builder/
│
├── app.py                      # Flask application factory & blueprint registration
├── config.py                   # Centralized configuration & environment loader
├── requirements.txt            # Python dependencies
├── .env.example                # Safe environment variable template (no secrets)
├── firebase-key.example.json   # Safe Firebase service account template (no secrets)
├── firestore.rules             # Cloud Firestore security rules
├── storage.rules               # Cloud Storage security rules
├── .gitattributes              # Linguist configuration (identifies repo as Python)
│
├── routes/                     # Modular Flask Blueprints
│   ├── auth_routes.py          # User profile synchronization & account deletion
│   ├── resume_routes.py        # File upload validation & text extraction
│   ├── analysis_routes.py      # Gemini AI analysis, score calculation & evaluation history
│   ├── learning_routes.py      # Curated resources, roadmaps & skill progress
│   ├── job_routes.py           # Job description matching & gap analysis
│   ├── certificate_routes.py   # Certificate eligibility check, generation & PDF streaming
│   └── pages_routes.py         # Template routing & frontend configuration injection
│
├── services/                   # Business Logic & Core Services
│   ├── ai_service.py           # Gemini API integrations, prompts, structured output & fallbacks
│   ├── resume_parser.py        # Resilient multi-engine PDF and DOCX extraction
│   ├── scoring_service.py      # Mathematical validation & score normalization
│   ├── learning_service.py     # Resource catalog & dynamic roadmap generator
│   └── certificate_service.py  # ReportLab vector PDF certificate builder
│
├── templates/                  # Jinja2 HTML Templates
│   ├── index.html              # Landing page
│   ├── login.html              # Sign-in portal
│   ├── signup.html             # User registration
│   ├── forgot_password.html    # Password reset flow
│   ├── dashboard.html          # Overview dashboard & score visualizations
│   ├── upload.html             # 4-stage animated resume upload & parser
│   ├── analysis.html           # Full evaluation report (5 tabs + A4 print format)
│   ├── skills.html             # Skill gaps, categories & proficiency breakdown
│   ├── learning.html           # Interactive learning plan & video modal player
│   ├── job_match.html          # JD matcher with quick-fill sample roles
│   ├── history.html            # Evaluation timeline & individual PDF downloads
│   ├── compare.html            # Side-by-side revision comparator
│   ├── profile.html            # Profile management & account settings
│   ├── certificate.html        # Readiness certificate issuance & LinkedIn button
│   ├── verify.html             # Public certificate validation portal
│   └── partials/               # Reusable components (sidebar, topbar, firebase_boot)
│
├── static/
│   ├── css/main.css            # Complete design system (Dark & Light themes)
│   └── js/
│       ├── main.js             # Shared utilities, auth listeners & API wrapper
│       └── firebase-init.js    # Modular Firebase Client SDK initialization
│
└── utils/
    └── firebase_helpers.py     # Firebase Admin SDK helpers & token verifier
```

---

## ⚙️ Quick Start & Installation

### 1. Prerequisites
* Python 3.11 or higher
* A free [Google AI Studio API Key](https://aistudio.google.com/)
* A [Firebase Project](https://console.firebase.google.com/) with Authentication & Firestore enabled

### 2. Clone the Repository
```bash
git clone https://github.com/Sa-urabh408/Resume-Builder-Analysis.git
cd Resume-Builder-Analysis
```

### 3. Create Virtual Environment & Install Dependencies
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the template file to `.env`:
```bash
cp .env.example .env
```

Open `.env` in your editor and configure your credentials:
```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash-lite

# Flask App Configuration
FLASK_SECRET_KEY=your_generated_random_secret_key
FLASK_ENV=development
FLASK_DEBUG=True

# Firebase Admin Service Account (JSON file path)
FIREBASE_CREDENTIALS=firebase-key.json

# Firebase Web Client Configuration (Safe to expose to frontend)
FIREBASE_API_KEY=your_firebase_web_api_key
FIREBASE_AUTH_DOMAIN=your-project-id.firebaseapp.com
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project-id.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id

# Platform Readiness Thresholds (Default: 70/100)
CERTIFICATE_READINESS_THRESHOLD=70
ATS_READINESS_THRESHOLD=70
```

> 🔒 **Security Notice:** Never commit `.env` or `firebase-key.json` to public repositories. Both are included in `.gitignore` by default.

### 5. Launch the Application
```bash
python app.py
```
Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 🔒 Security Architecture

* **Server-Side AI Proxy:** Gemini API keys are maintained exclusively on the backend server; frontend clients never interface directly with AI APIs.
* **Token Verification:** Every API endpoint validates Firebase JWT tokens server-side via `Authorization: Bearer <token>`.
* **Tenant Isolation:** Firestore documents are scoped under `users/{uid}/...` ensuring users can only read and write their own evaluations.
* **Safe Public Verification:** Public certificate verification at `/verify/<cert_id>` only displays holder name, certificate ID, issue date, and readiness score. No emails, phone numbers, or uploaded resume files are exposed.
* **Sanitized File Uploads:** Uploaded documents are restricted by MIME type (`pdf`, `docx`), size limit (`10MB`), and stored with randomized UUID filenames.

---

## 📈 Evaluation & Readiness Methodology

The platform calculates readiness across 7 core dimensions:

$$\text{Readiness Score} = (\text{Overall Score} \times 0.6) + (\text{ATS Score} \times 0.4)$$

| Category | Weight | Focus Areas |
|---|---|---|
| **ATS Compatibility** | 20% | Keyword parsing, clean structure, standard fonts, absence of complex tables/graphics |
| **Technical Skills** | 20% | Relevant modern stack, clarity of skill proficiencies, hard skills |
| **Projects & Experience** | 20% | Quantifiable impact (STAR method), metric-driven accomplishments |
| **Education & Credentials** | 10% | Degree, relevant coursework, academic background |
| **Achievements & Certs** | 10% | Competitions, verified certifications, leadership signals |
| **Resume Layout** | 10% | Visual hierarchy, spacing, clear section headers |
| **Readability & Grammar** | 10% | Action verbs, concise phrasing, spelling accuracy |

---

## 🧪 Testing

Run the automated test suite:
```bash
python -m unittest tests/test_suite.py
```

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<p align="center">
  Developed with ❤️ as an AI-powered Career Platform.
</p>
