"""
Certificate Service — generates PDF Resume Readiness Certificates.
"""
import uuid
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


# Color palette
NAVY = HexColor("#0F172A")
BLUE = HexColor("#3B82F6")
PURPLE = HexColor("#7C3AED")
GOLD = HexColor("#F59E0B")
LIGHT_BLUE = HexColor("#DBEAFE")
GRAY = HexColor("#6B7280")
WHITE = white
BLACK = black


def generate_certificate_id() -> str:
    """Generate a unique certificate ID like RA-2026-XXXXXX."""
    year = datetime.utcnow().strftime("%Y")
    unique_part = uuid.uuid4().hex[:6].upper()
    return f"RA-{year}-{unique_part}"


def generate_certificate_pdf(
    name: str,
    readiness_score: int,
    ats_score: int,
    certificate_id: str,
    issue_date: str,
    base_url: str = "https://resumeai.app",
) -> bytes:
    """
    Generate a professional PDF certificate and return as bytes.
    """
    buffer = io.BytesIO()
    page_size = landscape(A4)
    width, height = page_size
    c = canvas.Canvas(buffer, pagesize=page_size)

    # --- Background ---
    c.setFillColor(NAVY)
    c.rect(0, 0, width, height, fill=True, stroke=False)

    # --- Decorative border frame ---
    border_margin = 1.5 * cm
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.rect(border_margin, border_margin,
           width - 2 * border_margin, height - 2 * border_margin,
           fill=False, stroke=True)

    inner_margin = 2.0 * cm
    c.setStrokeColor(BLUE)
    c.setLineWidth(1)
    c.rect(inner_margin, inner_margin,
           width - 2 * inner_margin, height - 2 * inner_margin,
           fill=False, stroke=True)

    # --- Top accent bar ---
    c.setFillColor(BLUE)
    c.rect(0, height - 1.8 * cm, width, 1.8 * cm, fill=True, stroke=False)

    # --- Bottom accent bar ---
    c.setFillColor(PURPLE)
    c.rect(0, 0, width, 1.8 * cm, fill=True, stroke=False)

    # --- Header ---
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 4.5 * cm, "ResumeAI")

    c.setFont("Helvetica", 11)
    c.setFillColor(GOLD)
    c.drawCentredString(width / 2, height - 5.5 * cm, "AI-POWERED CAREER READINESS PLATFORM")

    # --- Divider ---
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(5 * cm, height - 6.3 * cm, width - 5 * cm, height - 6.3 * cm)

    # --- Certificate title ---
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, height - 7.8 * cm, "CERTIFICATE OF RESUME READINESS")

    # --- Body text ---
    c.setFont("Helvetica", 12)
    c.setFillColor(LIGHT_BLUE)
    c.drawCentredString(width / 2, height - 9.3 * cm, "This certifies that")

    # --- Name ---
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 10.8 * cm, name)

    # --- Description ---
    c.setFillColor(WHITE)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 12.0 * cm,
                        "has successfully completed the Resume Readiness assessment on ResumeAI")
    c.drawCentredString(width / 2, height - 12.6 * cm,
                        "and demonstrated career-ready resume quality.")

    # --- Score boxes ---
    box_y = height - 15.5 * cm
    box_w = 7 * cm
    box_h = 2.8 * cm

    # Readiness Score box
    left_x = width / 2 - box_w - 1 * cm
    c.setFillColor(HexColor("#1E293B"))
    c.roundRect(left_x, box_y, box_w, box_h, 0.3 * cm, fill=True, stroke=False)
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(left_x + box_w / 2, box_y + 1.7 * cm, f"{readiness_score}/100")
    c.setFillColor(LIGHT_BLUE)
    c.setFont("Helvetica", 9)
    c.drawCentredString(left_x + box_w / 2, box_y + 0.6 * cm, "Resume Readiness Score")

    # ATS Score box
    right_x = width / 2 + 1 * cm
    c.setFillColor(HexColor("#1E293B"))
    c.roundRect(right_x, box_y, box_w, box_h, 0.3 * cm, fill=True, stroke=False)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(right_x + box_w / 2, box_y + 1.7 * cm, f"{ats_score}/100")
    c.setFillColor(LIGHT_BLUE)
    c.setFont("Helvetica", 9)
    c.drawCentredString(right_x + box_w / 2, box_y + 0.6 * cm, "ATS Compatibility Score")

    # --- Divider 2 ---
    c.setStrokeColor(GRAY)
    c.setLineWidth(0.5)
    c.line(5 * cm, height - 17.2 * cm, width - 5 * cm, height - 17.2 * cm)

    # --- Footer details ---
    footer_y = height - 18.2 * cm
    c.setFont("Helvetica", 9)
    c.setFillColor(GRAY)
    c.drawString(4 * cm, footer_y, f"Certificate ID: {certificate_id}")
    c.drawString(4 * cm, footer_y - 0.5 * cm, f"Issue Date: {issue_date}")
    c.drawRightString(width - 4 * cm, footer_y,
                      f"Verify at: {base_url}/verify/{certificate_id}")
    c.drawRightString(width - 4 * cm, footer_y - 0.5 * cm,
                      "This is a platform assessment certificate, not an industry accreditation.")

    c.save()
    buffer.seek(0)
    return buffer.read()


def generate_resume_audit_pdf(
    analysis_data: dict,
    candidate_name: str = "Candidate",
    base_url: str = "https://resumeai.app"
) -> bytes:
    """
    Generate an in-depth, professional multi-section Resume Audit Report PDF.
    """
    buffer = io.BytesIO()
    width, height = A4  # Portrait A4 (595.27 x 841.89 pt)
    c = canvas.Canvas(buffer, pagesize=A4)

    # Theme colors
    PRIMARY = HexColor("#1F4D3A")  # Forest Green
    DARK = HexColor("#0F172A")     # Slate Navy
    ACCENT = HexColor("#D97706")   # Amber / Gold
    MUTED = HexColor("#475569")    # Slate Muted
    LIGHT_BG = HexColor("#F8FAFC") # Soft Card
    BORDER = HexColor("#E2E8F0")

    # Header top strip
    c.setFillColor(PRIMARY)
    c.rect(0, height - 1.2 * cm, width, 1.2 * cm, fill=True, stroke=False)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(1.5 * cm, height - 0.8 * cm, "RESUMEAI AUDIT ENGINE • OFFICIAL EVALUATION DOSSIER")
    c.drawRightString(width - 1.5 * cm, height - 0.8 * cm, datetime.utcnow().strftime("%B %d, %Y"))

    # Title block
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 22)
    c.drawString(1.5 * cm, height - 2.5 * cm, "Resume Audit & Readiness Report")

    filename = analysis_data.get("filename", "resume.pdf")
    target_role = analysis_data.get("targetRole") or analysis_data.get("careerGoal") or "Software Engineering / Tech"
    c.setFont("Helvetica", 10)
    c.setFillColor(MUTED)
    c.drawString(1.5 * cm, height - 3.2 * cm, f"Candidate: {candidate_name}   |   Document: {filename}   |   Target Role: {target_role}")

    # Divider line
    c.setStrokeColor(BORDER)
    c.setLineWidth(1)
    c.line(1.5 * cm, height - 3.6 * cm, width - 1.5 * cm, height - 3.6 * cm)

    # Score Cards Strip (Overall, ATS, Readiness)
    card_y = height - 6.2 * cm
    card_h = 2.2 * cm
    card_w = (width - 3 * cm - 1 * cm) / 3

    overall_score = analysis_data.get("overallScore", analysis_data.get("overall_score", 0))
    ats_score = analysis_data.get("atsScore", analysis_data.get("ats_score", 0))
    readiness_status = analysis_data.get("readinessStatus", analysis_data.get("readiness_status", "Improving"))

    scores_meta = [
        ("OVERALL SCORE", f"{overall_score}/100", PRIMARY),
        ("ATS PARSE RATING", f"{ats_score}%", HexColor("#2563EB")),
        ("READINESS BENCHMARK", str(readiness_status), ACCENT)
    ]

    for i, (title, val, clr) in enumerate(scores_meta):
        cx = 1.5 * cm + i * (card_w + 0.5 * cm)
        c.setFillColor(LIGHT_BG)
        c.setStrokeColor(BORDER)
        c.roundRect(cx, card_y, card_w, card_h, 4, fill=True, stroke=True)

        c.setFillColor(MUTED)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(cx + 12, card_y + card_h - 18, title)

        c.setFillColor(clr)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(cx + 12, card_y + 14, val)

    # Section 1: Rubric Breakdown
    y = card_y - 1.0 * cm
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, y, "1. Comprehensive Rubric Scoring")
    y -= 0.6 * cm

    cat_scores = analysis_data.get("scores") or analysis_data.get("categoryScores") or analysis_data.get("category_scores") or {}
    cat_items = [
        ("ATS Compatibility", cat_scores.get("ats_compatibility", 0), 20),
        ("Skills & Competencies", cat_scores.get("skills", 0), 20),
        ("Projects & Experience Depth", cat_scores.get("projects_experience", 0), 20),
        ("Education & Credentials", cat_scores.get("education", 0), 10),
        ("Measurable Achievements", cat_scores.get("achievements", 0), 10),
        ("Structure & Formatting", cat_scores.get("structure", 0), 10),
        ("Clarity & Professional Tone", cat_scores.get("readability", 0), 10),
    ]

    # Render rubric table
    for name, sc, mx in cat_items:
        c.setFont("Helvetica", 9)
        c.setFillColor(DARK)
        c.drawString(1.8 * cm, y, name)

        # Bar background
        bar_x = 9.0 * cm
        bar_w = 6.0 * cm
        c.setFillColor(HexColor("#E2E8F0"))
        c.roundRect(bar_x, y - 2, bar_w, 6, 2, fill=True, stroke=False)

        # Bar fill
        pct = min(1.0, max(0.0, sc / mx if mx else 0))
        c.setFillColor(PRIMARY)
        if pct > 0:
            c.roundRect(bar_x, y - 2, bar_w * pct, 6, 2, fill=True, stroke=False)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(DARK)
        c.drawRightString(width - 1.8 * cm, y, f"{sc} / {mx}")
        y -= 0.55 * cm

    # Section 2: Skills Identified
    y -= 0.5 * cm
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, y, "2. Skills Assessment & Gap Analysis")
    y -= 0.6 * cm

    strong_skills = analysis_data.get("strongSkills") or analysis_data.get("skills", {}).get("strong") or []
    improve_skills = analysis_data.get("skillsToImprove") or analysis_data.get("skills", {}).get("improve") or []
    missing_skills = analysis_data.get("missingSkills") or analysis_data.get("skills", {}).get("missing") or []

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#16A34A"))
    c.drawString(1.8 * cm, y, "Strong Proficiencies: ")
    c.setFont("Helvetica", 9)
    c.setFillColor(DARK)
    strong_str = ", ".join(strong_skills[:8]) if strong_skills else "Solid general foundational skills identified."
    c.drawString(5.5 * cm, y, strong_str[:70])
    y -= 0.5 * cm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#D97706"))
    c.drawString(1.8 * cm, y, "Needs Improvement: ")
    c.setFont("Helvetica", 9)
    c.setFillColor(DARK)
    improve_str = ", ".join(improve_skills[:8]) if improve_skills else "Add measurable metrics to past responsibilities."
    c.drawString(5.5 * cm, y, improve_str[:70])
    y -= 0.5 * cm

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor("#DC2626"))
    c.drawString(1.8 * cm, y, "High-Value Missing Skills: ")
    c.setFont("Helvetica", 9)
    c.setFillColor(DARK)
    missing_str = ", ".join(missing_skills[:8]) if missing_skills else "No critical skill omissions detected."
    c.drawString(5.5 * cm, y, missing_str[:70])
    y -= 0.8 * cm

    # Section 3: Strategic Recommendations
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, y, "3. Key AI Recommendations to Boost Score")
    y -= 0.6 * cm

    suggestions = analysis_data.get("suggestions", []) or [
        "Quantify project achievements with metrics, percentages, or scale numbers.",
        "Include industry-standard keywords aligned to your target job profile.",
        "Ensure standard chronological section headings (Experience, Education, Skills)."
    ]

    for s in suggestions[:4]:
        c.setFillColor(PRIMARY)
        c.circle(1.9 * cm, y + 3, 2, fill=True, stroke=False)
        c.setFont("Helvetica", 9)
        c.setFillColor(DARK)
        c.drawString(2.3 * cm, y, str(s)[:85])
        y -= 0.5 * cm

    # Section 4: Recommended YouTube Tutorials for Skill Gaps
    y -= 0.4 * cm
    c.setFillColor(DARK)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(1.5 * cm, y, "4. Curated Video Learning Plan (Free on YouTube)")
    y -= 0.6 * cm

    recs = analysis_data.get("roadmap") or analysis_data.get("learningRecommendations") or []
    for r in recs[:3]:
        skill = r.get("skill", "Core Competency")
        yt = r.get("youtube_video") or {}
        yt_title = yt.get("title", f"{skill} Practical Crash Course")
        yt_channel = yt.get("channel", "Top Tech Creator")

        c.setFillColor(LIGHT_BG)
        c.setStrokeColor(BORDER)
        c.roundRect(1.8 * cm, y - 0.4 * cm, width - 3.6 * cm, 1.1 * cm, 3, fill=True, stroke=True)

        c.setFillColor(HexColor("#E50914"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2.1 * cm, y + 0.3 * cm, f"[VIDEO] {skill}")

        c.setFillColor(DARK)
        c.setFont("Helvetica", 8.5)
        c.drawString(2.1 * cm, y - 0.1 * cm, f"{yt_title[:55]} | Channel: {yt_channel}")

        y -= 1.35 * cm

    # Footer
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.8)
    c.line(1.5 * cm, 1.5 * cm, width - 1.5 * cm, 1.5 * cm)

    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    c.drawString(1.5 * cm, 1.0 * cm, "Generated by ResumeAI Evaluator • Confidential Candidate Assessment")
    c.drawRightString(width - 1.5 * cm, 1.0 * cm, f"Report ID: {analysis_data.get('evalId', 'N/A')[:18]}")

    c.save()
    buffer.seek(0)
    return buffer.read()

