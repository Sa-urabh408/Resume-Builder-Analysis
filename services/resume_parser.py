"""
Resume Parser Service — extracts text from PDF and DOCX files.
"""
import io
import re


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber (fallback to PyMuPDF)."""
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if text.strip():
            return clean_text(text)
    except Exception as e:
        print(f"[pdfplumber error] {e}")

    # Fallback: pypdf
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        if text.strip():
            return clean_text(text)
    except Exception as e:
        print(f"[pypdf error] {e}")

    # Fallback: PyMuPDF if installed
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        if text.strip():
            return clean_text(text)
    except Exception as e:
        pass

    return ""


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from DOCX bytes using python-docx."""
    try:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        # Also extract from tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        paragraphs.append(cell.text.strip())
        return clean_text("\n".join(paragraphs))
    except Exception as e:
        print(f"[DOCX error] {e}")
        return ""


def extract_text(file_bytes: bytes, filename: str) -> tuple[str, str | None]:
    """
    Main entry point for text extraction.
    Returns (text, error_message).
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "pdf":
        text = extract_text_from_pdf(file_bytes)
    elif ext == "docx":
        text = extract_text_from_docx(file_bytes)
    else:
        return "", f"Unsupported file type: .{ext}. Please upload a PDF or DOCX file."

    if not text or len(text.strip()) < 50:
        return "", "Could not extract meaningful text from the file. Ensure the resume is not scanned/image-based."

    return text, None


def clean_text(text: str) -> str:
    """Basic text normalization."""
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()
