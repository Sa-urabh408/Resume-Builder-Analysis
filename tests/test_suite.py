"""
ResumeAI — Strict Test Suite
Tests real auth protection (401 on missing/invalid token), valid token mock,
endpoint validation, score normalization, and public routes.
"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent dir to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


class TestHealthEndpoint(unittest.TestCase):
    """Test the /health endpoint."""

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_health_returns_200(self):
        """GET /health should return 200 with status ok."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "ResumeAI")


class TestStrictAuthProtection(unittest.TestCase):
    """Test that API endpoints strictly reject requests without valid Firebase tokens."""

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_profile_missing_token_returns_401(self):
        """GET /api/auth/profile without Authorization header must return 401."""
        resp = self.client.get("/api/auth/profile")
        self.assertEqual(resp.status_code, 401)
        data = resp.get_json()
        self.assertIn("error", data)

    def test_profile_invalid_token_returns_401(self):
        """GET /api/auth/profile with invalid token must return 401."""
        headers = {"Authorization": "Bearer invalid_fake_token_xyz"}
        resp = self.client.get("/api/auth/profile", headers=headers)
        self.assertEqual(resp.status_code, 401)

    def test_analyze_missing_token_returns_401(self):
        """POST /api/analysis/analyze without token must return 401."""
        payload = {"extracted_text": "A" * 100}
        resp = self.client.post("/api/analysis/analyze", json=payload)
        self.assertEqual(resp.status_code, 401)

    def test_history_missing_token_returns_401(self):
        """GET /api/analysis/history without token must return 401."""
        resp = self.client.get("/api/analysis/history")
        self.assertEqual(resp.status_code, 401)

    @patch('utils.firebase_helpers.verify_token')
    def test_valid_token_accepted(self, mock_verify):
        """With valid token mock, endpoint accepts request."""
        mock_verify.return_value = {"uid": "user_123_abc", "email": "test@example.com"}
        headers = {"Authorization": "Bearer valid_real_id_token"}
        
        # Test analyze validation with valid token
        payload = {"extracted_text": "Short"}
        resp = self.client.post("/api/analysis/analyze", json=payload, headers=headers)
        # Should pass auth and reach validation (400 for short text)
        self.assertEqual(resp.status_code, 400)


class TestAnalyzeValidation(unittest.TestCase):
    """Test analyze endpoint input validation."""

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('utils.firebase_helpers.verify_token')
    def test_analyze_rejects_short_text(self, mock_verify):
        """POST /api/analysis/analyze with short text returns 400."""
        mock_verify.return_value = {"uid": "user_123_abc", "email": "test@example.com"}
        headers = {"Authorization": "Bearer valid_id_token"}
        payload = {"extracted_text": "Short", "career_goal": "Python Developer"}
        resp = self.client.post("/api/analysis/analyze", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertIn("error", data)

    @patch('utils.firebase_helpers.verify_token')
    def test_analyze_rejects_empty_text(self, mock_verify):
        """POST /api/analysis/analyze with empty text returns 400."""
        mock_verify.return_value = {"uid": "user_123_abc", "email": "test@example.com"}
        headers = {"Authorization": "Bearer valid_id_token"}
        payload = {"extracted_text": "", "career_goal": "Python Developer"}
        resp = self.client.post("/api/analysis/analyze", json=payload, headers=headers)
        self.assertEqual(resp.status_code, 400)


class TestScoreValidation(unittest.TestCase):
    """Test score normalization and validation logic."""

    def test_scores_clamped_0_to_100(self):
        """Scores must be clamped between 0 and 100."""
        from services.scoring_service import validate_and_normalize_scores

        analysis = {
            "overall_score": 150,
            "ats_score": -10,
            "category_scores": {
                "ats_compatibility": 25,  # Max is 20
                "skills": 30,             # Max is 20
            }
        }
        result = validate_and_normalize_scores(analysis)
        self.assertTrue(0 <= result.get("overall_score", 0) <= 100)
        self.assertTrue(0 <= result.get("ats_score", 0) <= 100)
        self.assertTrue(result["category_scores"]["ats_compatibility"] <= 20)
        self.assertTrue(result["category_scores"]["skills"] <= 20)

    def test_dict_category_scores_normalized(self):
        """Category scores provided as dicts with 'score' key are normalized properly."""
        from services.scoring_service import validate_and_normalize_scores

        analysis = {
            "category_scores": {
                "ats_compatibility": {"score": 18, "max": 20},
                "skills": {"score": 19, "max": 20}
            }
        }
        result = validate_and_normalize_scores(analysis)
        self.assertEqual(result["category_scores"]["ats_compatibility"], 18)
        self.assertEqual(result["category_scores"]["skills"], 19)


class TestPublicRoutes(unittest.TestCase):
    """Test public pages load without requiring auth."""

    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_landing_page(self):
        """GET / should return 200."""
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)

    def test_login_page(self):
        """GET /login should return 200."""
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)

    def test_signup_page(self):
        """GET /signup should return 200."""
        resp = self.client.get("/signup")
        self.assertEqual(resp.status_code, 200)

    def test_verify_certificate_page(self):
        """GET /verify/<cert_id> should return 200."""
        resp = self.client.get("/verify/sample-cert-id-123")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
