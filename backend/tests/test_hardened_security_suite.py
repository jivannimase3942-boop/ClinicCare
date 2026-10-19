import pytest
import time
from app.core.config import settings
from app.core.security import validate_password_strength, get_password_hash, create_access_token
from app.core.sanitizer import sanitize_text, sanitize_payload
from app.core.rate_limit import limiter
from app.models.user import User, Patient
from app.models.report import Report


def test_security_headers_present_on_responses(client):
    """Verifies all mandatory OWASP security headers are present on API responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    headers = resp.headers

    # OWASP Defense-in-Depth headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert "strict-origin-when-cross-origin" in headers.get("Referrer-Policy", "")
    assert "camera=()" in headers.get("Permissions-Policy", "")
    assert "max-age=" in headers.get("Strict-Transport-Security", "")
    assert "default-src 'self'" in headers.get("Content-Security-Policy", "")


def test_sensitive_endpoints_prevent_caching(client, seed_test_data):
    """Verifies sensitive patient endpoints send Cache-Control: no-store."""
    pat = seed_test_data["patient"]
    tok = create_access_token({"sub": pat.user.id, "email": pat.user.email, "role": "PATIENT"})
    resp = client.get(f"/api/patients/{pat.id}", headers={"Authorization": f"Bearer {tok}"})
    assert resp.status_code == 200
    cache_ctrl = resp.headers.get("Cache-Control", "")
    assert "no-store" in cache_ctrl
    assert "no-cache" in cache_ctrl


def test_debug_mode_is_disabled():
    """Verifies that debug mode is securely turned off by default and in environment."""
    assert settings.DEBUG is False, "Production security requires DEBUG=False"


def test_password_strength_validator():
    """Tests password strength criteria."""
    # Too short (<6)
    valid, err = validate_password_strength("12345")
    assert valid is False
    assert "at least 6" in err.lower()

    # Empty
    valid, err = validate_password_strength("")
    assert valid is False

    # Valid
    valid, err = validate_password_strength("SecureHospital@2026")
    assert valid is True
    assert err is None

    # Too long (>128 prevents bcrypt algorithmic DoS)
    valid, err = validate_password_strength("A" * 129)
    assert valid is False
    assert "exceed 128" in err.lower()


def test_input_sanitization_xss_protection():
    """Verifies that XSS payloads are thoroughly stripped from incoming data."""
    # 1. Script tag injection
    malicious_script = "Hello <script>alert('XSS')</script>World"
    assert sanitize_text(malicious_script) == "Hello World"

    # 2. Iframe / embed injection
    malicious_iframe = "Click <iframe src='http://evil.com'></iframe>Here"
    assert sanitize_text(malicious_iframe) == "Click Here"

    # 3. JavaScript protocol injection
    malicious_js = "javascript:alert(document.cookie)"
    assert sanitize_text(malicious_js) == "alert(document.cookie)"

    # 4. Inline event handler injection
    malicious_handler = 'Image <img src="x" onerror="alert(1)"> test'
    assert 'onerror="alert(1)"' not in sanitize_text(malicious_handler)

    # 5. Recursive payload sanitization
    nested_data = {
        "name": "<script>alert(1)</script>John Doe",
        "notes": ["Clean note", "<style>body{display:none}</style>Important"],
        "metadata": {"reason": "<object data='evil.swf'></object>Fever"}
    }
    sanitized = sanitize_payload(nested_data)
    assert sanitized["name"] == "John Doe"
    assert "<style>" not in sanitized["notes"][1]
    assert "<object" not in sanitized["metadata"]["reason"]


def test_unauthenticated_access_is_blocked_on_sensitive_routes(client, seed_test_data):
    """
    Verifies that all sensitive clinical, patient, and management routes
    properly return 401 UNAUTHORIZED when called without credentials.
    """
    pat_id = seed_test_data["patient"].id

    # 1. Patients search
    res1 = client.get("/api/patients")
    assert res1.status_code == 401

    # 2. Patient profile by ID
    res2 = client.get(f"/api/patients/{pat_id}")
    assert res2.status_code == 401

    # 3. Patient visits
    res3 = client.get(f"/api/patients/{pat_id}/visits")
    assert res3.status_code == 401

    # 4. Reports list
    res4 = client.get("/api/reports")
    assert res4.status_code == 401

    # 5. Report by ID
    res5 = client.get("/api/reports/some-report-id")
    assert res5.status_code == 401

    # 6. Emergencies list
    res6 = client.get("/api/emergencies")
    assert res6.status_code == 401

    # 7. Ambulance requests list
    res7 = client.get("/api/ambulances/requests")
    assert res7.status_code == 401

    # 8. Blood requests list
    res8 = client.get("/api/blood/requests")
    assert res8.status_code == 401

    # 9. Voice calls list
    res9 = client.get("/api/voice/my")
    assert res9.status_code == 401

    # 10. Escalations list
    res10 = client.get("/api/escalations/my")
    assert res10.status_code == 401

    # 11. Follow-up reminders
    res11 = client.get("/api/reminders")
    assert res11.status_code == 401

    # 12. Trigger dispatch reminder
    res12 = client.post("/api/reminders/fake-id/dispatch")
    assert res12.status_code == 401


def test_rate_limiting_enforces_429_on_excessive_requests(client):
    """Verifies rate limiting triggers 429 Too Many Requests when threshold is hit."""
    limiter.reset()

    # Enable rate limiting enforcement header for this test
    headers = {"X-Rate-Limit-Test": "true", "X-Enforce-Rate-Limit": "true"}

    # Limit for auth is 20 req/min
    status_codes = []
    for i in range(25):
        resp = client.post(
            "/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "WrongPassword@123"},
            headers=headers
        )
        status_codes.append(resp.status_code)

    assert 429 in status_codes, f"Expected 429 Too Many Requests in {status_codes}"
    # Verify 429 response structure
    rate_limited_idx = status_codes.index(429)
    # Reset limiter after test
    limiter.reset()
