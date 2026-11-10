"""
Firebase helper utilities for the ResumeAI application.
Handles strict Firebase Admin Auth verification and Firestore client access.
"""
import firebase_admin
from firebase_admin import firestore, auth, storage
from flask import current_app, request, jsonify
from functools import wraps
import traceback


def get_db():
    """Return Firestore client."""
    if firebase_admin._apps:
        return firestore.client()
    return None


def get_storage_bucket():
    """Return the Firebase Storage bucket if Firebase is initialized."""
    if firebase_admin._apps:
        try:
            return storage.bucket()
        except Exception as e:
            print(f"[STORAGE ERROR] {e}")
    return None


def verify_token(id_token: str):
    """
    Verify a Firebase ID token using Firebase Admin SDK.
    Returns decoded token dictionary or None on failure.
    Logs token verification, uid, name, and full exception.
    """
    if not id_token:
        print("[AUTH ERROR] Token is missing or empty")
        return None

    if not firebase_admin._apps:
        print("[AUTH ERROR] Firebase Admin SDK is not initialized")
        return None

    try:
        decoded = auth.verify_id_token(id_token)
        uid = decoded.get("uid")
        name = decoded.get("name") or decoded.get("email") or "User"
        print(f"[AUTH SUCCESS] Token verified successfully | UID: {uid} | Name: {name}")
        return decoded
    except Exception as e:
        print(f"[AUTH ERROR] firebase_admin.auth.verify_id_token failed: {e}")
        traceback.print_exc()
        return None


def get_user_from_request(req):
    """
    Extract and verify user from Authorization header.
    Returns (uid, error_response_tuple | None)
    """
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        print(f"[AUTH ERROR] Missing or malformed Authorization header: '{auth_header}'")
        return None, ({"error": "Missing or malformed Authorization header. Please sign in."}, 401)

    token = auth_header.split("Bearer ", 1)[1].strip()
    decoded = verify_token(token)
    if not decoded or "uid" not in decoded:
        return None, ({"error": "Invalid or expired session token. Please sign in again."}, 401)

    return decoded["uid"], None


def require_auth(f):
    """Decorator to enforce strict Firebase authentication on API endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        uid, err = get_user_from_request(request)
        if err:
            return jsonify(err[0]), err[1]
        return f(*args, **kwargs)
    return decorated_function
