"""
Resume Routes — file upload and in-memory text extraction.
The file is never stored; only extracted text is returned to the client.
"""
from flask import Blueprint, request, jsonify, current_app
from utils.firebase_helpers import get_user_from_request, require_auth
from services.resume_parser import extract_text

resume_bp = Blueprint("resume", __name__)


@resume_bp.route("/upload", methods=["POST"])
@require_auth
def upload_resume():
    uid, err = get_user_from_request(request)
    if err:
        return jsonify(err[0]), err[1]

    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded. Use field name 'resume'."}), 400

    file = request.files["resume"]
    if not file or file.filename == "":
        return jsonify({"error": "Empty file received."}), 400

    if not _allowed_file(file.filename, current_app.config):
        return jsonify({"error": "Invalid file type. Please upload a PDF or DOCX file."}), 400

    file_bytes = file.read()

    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 10 * 1024 * 1024)
    if len(file_bytes) > max_bytes:
        return jsonify({"error": f"File too large. Maximum size is {max_bytes // (1024 * 1024)}MB."}), 413

    text, extract_error = extract_text(file_bytes, file.filename)
    if extract_error:
        return jsonify({"error": extract_error}), 422

    return jsonify({
        "message": "Resume text extracted successfully.",
        "filename": file.filename,
        "text_length": len(text),
        "extracted_text": text,
    }), 200


def _allowed_file(filename, config):
    allowed = config.get("ALLOWED_EXTENSIONS", {"pdf", "docx"})
    return "." in filename and filename.rsplit(".", 1)[-1].lower() in allowed
