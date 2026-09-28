import sys
import os
import urllib.request
import urllib.error
import json
import ssl
import time

ctx = ssl.create_default_context()
BACKEND = "https://cliniccare-backend-48g6.onrender.com"
FRONTEND = "https://cliniccare-g3c6.onrender.com"

failed_checks = []

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", "replace").decode("ascii"))

def req(url, method="GET", data=None, headers=None, timeout=30):
    h = {"User-Agent": "ClinicCare-Production-Verification/1.0"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=h, method=method)
    return urllib.request.urlopen(request, context=ctx, timeout=timeout)

def test_check(name, func):
    try:
        func()
        safe_print(f"[PASS] {name}")
    except Exception as e:
        safe_print(f"[FAIL] {name}: {e}")
        failed_checks.append((name, str(e)))

def run():
    safe_print("=" * 65)
    safe_print("CLINICCARE COMPREHENSIVE PRODUCTION VERIFICATION SUITE")
    safe_print(f"Backend: {BACKEND}")
    safe_print(f"Frontend: {FRONTEND}")
    safe_print("=" * 65)

    # 0. Warm up cold backend if needed
    safe_print("\n--- 0. Checking Backend Availability (Warm-up) ---")
    warmed = False
    for attempt in range(1, 7):
        try:
            res = req(f"{BACKEND}/health", timeout=15)
            if res.getcode() == 200:
                safe_print(f"[PASS] Backend is awake and responsive (attempt {attempt})")
                warmed = True
                break
        except Exception as e:
            safe_print(f"[WAIT] Backend warming up (attempt {attempt}/6)... ({e})")
            time.sleep(5)
    if not warmed:
        safe_print("[WARNING] Backend may still be starting up, proceeding with suite...")

    # 1. Root & Health
    safe_print("\n--- 1. Testing Root & Health Check Endpoints ---")
    for path in ["/", "/api", "/health", "/api/health"]:
        def _check_endpoint(p=path):
            res = req(f"{BACKEND}{p}")
            assert res.getcode() == 200, f"Expected 200, got {res.getcode()}"
            body = json.loads(res.read().decode("utf-8"))
            assert body.get("success") is True or body.get("status") in ["healthy", "online"], f"Unexpected payload: {body}"
        test_check(f"Endpoint {path}", _check_endpoint)

    # 2. CORS Preflight
    safe_print("\n--- 2. Testing Production CORS Headers ---")
    def _check_cors():
        cors_req = urllib.request.Request(
            f"{BACKEND}/api/auth/login",
            headers={
                "Origin": FRONTEND,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            },
            method="OPTIONS"
        )
        res = urllib.request.urlopen(cors_req, context=ctx, timeout=15)
        assert res.getcode() == 200, f"Expected 200 on OPTIONS, got {res.getcode()}"
        allow_origin = res.getheader("Access-Control-Allow-Origin")
        allow_creds = res.getheader("Access-Control-Allow-Credentials")
        assert allow_origin == FRONTEND, f"Expected {FRONTEND}, got {allow_origin}"
        assert allow_creds.lower() == "true", f"Expected credentials true, got {allow_creds}"
    test_check("CORS Preflight on /api/auth/login", _check_cors)

    # 3. Authentication for All Demo Roles
    safe_print("\n--- 3. Testing Authentication For All 5 Demo Accounts ---")
    demo_creds = [
        ("Patient", "patient@hospital.com", "Patient@123", "PATIENT"),
        ("Doctor", "dr.sharma@hospital.com", "Doctor@123", "DOCTOR"),
        ("Doctor (alt)", "doctor@hospital.com", "Doctor@123", "DOCTOR"),
        ("Admin", "admin@hospital.com", "Admin@123", "ADMIN"),
        ("Front Desk", "frontdesk@hospital.com", "FrontDesk@123", "FRONT_DESK"),
    ]

    tokens = {}
    for role_name, email, password, expected_role in demo_creds:
        def _login(r=role_name, em=email, pw=password, exp=expected_role):
            res = req(f"{BACKEND}/api/auth/login", method="POST", data={"email": em, "password": pw})
            assert res.getcode() == 200, f"HTTP {res.getcode()}"
            body = json.loads(res.read().decode("utf-8"))
            tok = body.get("data", {}).get("access_token")
            user = body.get("data", {}).get("user", {})
            assert tok, "Missing token"
            assert user.get("role") == exp, f"Expected {exp}, got {user.get('role')}"
            tokens[r] = tok
        test_check(f"Login {role_name} ({email})", _login)

    # 4. Invalid Login Handling
    safe_print("\n--- 4. Testing Invalid Login Rejection ---")
    def _invalid_login():
        try:
            req(f"{BACKEND}/api/auth/login", method="POST", data={"email": "patient@hospital.com", "password": "WrongPassword!999"})
            raise AssertionError("Invalid password was unexpectedly accepted!")
        except urllib.error.HTTPError as e:
            assert e.code == 401, f"Expected 401, got {e.code}"
    test_check("Invalid credentials rejection (401)", _invalid_login)

    # 4b. Registration OTP Flow
    safe_print("\n--- 4b. Testing Email OTP Registration Flow ---")
    def _test_otp_flow():
        t_email = f"test_verify_{int(time.time())}@hospital.com"
        res = req(f"{BACKEND}/api/auth/register/send-otp", method="POST", data={"email": t_email, "full_name": "OTP Test User"})
        assert res.getcode() == 200, f"Expected 200 on send-otp, got {res.getcode()}"
        body = json.loads(res.read().decode("utf-8"))
        assert body.get("success") is True, f"Failed send-otp payload: {body}"

        # Test invalid OTP rejection
        try:
            req(f"{BACKEND}/api/auth/register/verify-otp", method="POST", data={"email": t_email, "otp": "000000"})
            raise AssertionError("Invalid OTP unexpectedly accepted!")
        except urllib.error.HTTPError as e:
            assert e.code == 400, f"Expected 400 on invalid OTP, got {e.code}"
    test_check("Email OTP registration endpoint & invalid OTP rejection", _test_otp_flow)

    # 5. Protected Endpoints
    safe_print("\n--- 5. Testing Protected Endpoints With JWT ---")
    if "Patient" in tokens:
        def _patient_endpoints():
            hdr = {"Authorization": f"Bearer {tokens['Patient']}"}
            res = req(f"{BACKEND}/api/appointments/my", headers=hdr)
            assert res.getcode() == 200
            res2 = req(f"{BACKEND}/api/reports/my", headers=hdr)
            assert res2.getcode() == 200
        test_check("Patient Protected Endpoints (/appointments/my, /reports/my)", _patient_endpoints)

    if "Doctor" in tokens:
        def _doctor_endpoints():
            hdr = {"Authorization": f"Bearer {tokens['Doctor']}"}
            res = req(f"{BACKEND}/api/doctor/appointments", headers=hdr)
            assert res.getcode() == 200
        test_check("Doctor Protected Endpoints (/doctor/appointments)", _doctor_endpoints)

    if "Admin" in tokens:
        def _admin_endpoints():
            hdr = {"Authorization": f"Bearer {tokens['Admin']}"}
            res = req(f"{BACKEND}/api/admin/stats", headers=hdr)
            assert res.getcode() == 200
            data = json.loads(res.read().decode("utf-8")).get("data", {})
            assert "metrics" in data, "Metrics missing from admin stats"
            res2 = req(f"{BACKEND}/api/admin/patients", headers=hdr)
            assert res2.getcode() == 200
            res3 = req(f"{BACKEND}/api/admin/errors", headers=hdr)
            assert res3.getcode() == 200
        test_check("Admin Protected Endpoints (/admin/stats, /admin/patients, /admin/errors)", _admin_endpoints)

    # 5b. Role Isolation & Privacy
    safe_print("\n--- 5b. Testing Strict Role-Based Access Control (RBAC) & Privacy ---")
    if "Patient" in tokens:
        def _patient_rbac_blocks():
            hdr = {"Authorization": f"Bearer {tokens['Patient']}"}
            # Patient cannot access Admin stats
            try:
                req(f"{BACKEND}/api/admin/stats", headers=hdr)
                raise AssertionError("Patient unexpectedly accessed /admin/stats")
            except urllib.error.HTTPError as e:
                assert e.code == 403, f"Expected 403, got {e.code}"
            # Patient cannot access Doctor appointments
            try:
                req(f"{BACKEND}/api/doctor/appointments", headers=hdr)
                raise AssertionError("Patient unexpectedly accessed /doctor/appointments")
            except urllib.error.HTTPError as e:
                assert e.code == 403, f"Expected 403, got {e.code}"
            # Patient cannot browse patient directory
            try:
                req(f"{BACKEND}/api/patients", headers=hdr)
                raise AssertionError("Patient unexpectedly accessed /patients")
            except urllib.error.HTTPError as e:
                assert e.code == 403, f"Expected 403, got {e.code}"
        test_check("Patient Role Isolation (Cannot access /admin/stats, /doctor/appointments, /patients)", _patient_rbac_blocks)

    if "Front Desk" in tokens:
        def _frontdesk_rbac_blocks():
            hdr = {"Authorization": f"Bearer {tokens['Front Desk']}"}
            # Front desk cannot access admin system errors
            try:
                req(f"{BACKEND}/api/admin/errors", headers=hdr)
                raise AssertionError("Front desk unexpectedly accessed /admin/errors")
            except urllib.error.HTTPError as e:
                assert e.code == 403, f"Expected 403, got {e.code}"
        test_check("Front Desk Role Isolation (Cannot access /admin/errors)", _frontdesk_rbac_blocks)

    # 6. AI Assistant Endpoints & Scenarios
    safe_print("\n--- 6. Testing AI Assistant Chat Scenarios ---")
    ai_scenarios = [
        ("Doctors Inquiry", "Who are the available doctors?"),
        ("Medication Query", "Tell me about cetirizine"),
        ("Cardiology Information", "What does the Cardiology department offer?"),
        ("Facilities Search", "Where is the main hospital located?"),
        ("Emergency Guardrail", "I have sudden severe chest pain and cannot breathe"),
        ("Long Message", "Hello, " + "can you help me " * 30 + "book an appointment?"),
    ]

    for title, prompt in ai_scenarios:
        def _test_ai(p=prompt, is_emerg=("Emergency" in title)):
            t0 = time.time()
            res = req(f"{BACKEND}/api/ai/chat", method="POST", data={"message": p})
            elapsed = time.time() - t0
            assert res.getcode() == 200, f"HTTP {res.getcode()}"
            body = json.loads(res.read().decode("utf-8"))
            reply = body.get("data", {}).get("reply") or body.get("data", {}).get("response") or ""
            assert len(reply) > 5, "Empty reply received from AI"
            if is_emerg:
                assert body.get("data", {}).get("is_emergency") is True or "emergency" in reply.lower() or "911" in reply, "Emergency guardrail not triggered"
            safe_print(f"       [{title}] Latency: {elapsed:.2f}s | Reply snippet: {reply[:60].replace(chr(10), ' ')}...")
        test_check(f"AI Chat: {title}", _test_ai)

    # 7. Frontend Bundle & API Resolution
    safe_print("\n--- 7. Testing Frontend Bundle & API Resolution ---")
    def _test_bundle():
        res = req(f"{FRONTEND}/")
        assert res.getcode() == 200
        html = res.read().decode("utf-8")
        import re
        js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
        assert len(js_files) > 0, "No JS bundle found in index.html"
        active_bundle_url = f"{FRONTEND}{js_files[0]}" if js_files[0].startswith("/") else f"{FRONTEND}/{js_files[0]}"
        js_code = urllib.request.urlopen(active_bundle_url, context=ctx, timeout=15).read().decode("utf-8")
        assert "cliniccare-backend-48g6" in js_code, "Deployed bundle missing production backend reference"
        assert "/api" in js_code, "Deployed bundle missing /api reference"
        safe_print(f"       Active JS bundle: {js_files[0]} verified.")
    test_check("Production Frontend Bundle Content", _test_bundle)

    # Summary
    safe_print("\n" + "=" * 65)
    if failed_checks:
        safe_print(f"VERIFICATION FAILED: {len(failed_checks)} failure(s) detected:")
        for name, err in failed_checks:
            safe_print(f"  - {name}: {err}")
        safe_print("=" * 65)
        sys.exit(1)
    else:
        safe_print("ALL PRODUCTION CHECKS PASSED (100% HEALTHY)")
        safe_print("=" * 65)
        sys.exit(0)

if __name__ == "__main__":
    run()
