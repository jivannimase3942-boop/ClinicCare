import urllib.request
import urllib.error
import json
import ssl
import time

ctx = ssl.create_default_context()
BACKEND = "https://cliniccare-backend-48g6.onrender.com"
FRONTEND = "https://cliniccare-g3c6.onrender.com"

def req(url, method="GET", data=None, headers=None, timeout=25):
    h = {"User-Agent": "ClinicCare-Verification/1.0"}
    if headers:
        h.update(headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        h["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, headers=h, method=method)
    return urllib.request.urlopen(request, context=ctx, timeout=timeout)

def run():
    print("=" * 60)
    print("CLINICCARE PRODUCTION VERIFICATION SUITE")
    print(f"Backend: {BACKEND}")
    print(f"Frontend: {FRONTEND}")
    print("=" * 60)

    # 1. Health & Root checks
    for path in ["/", "/api", "/health", "/api/health"]:
        url = f"{BACKEND}{path}"
        try:
            res = req(url)
            print(f"[PASS] {path} -> {res.getcode()} (length: {len(res.read())})")
        except urllib.error.HTTPError as e:
            print(f"[FAIL/PENDING DEPLOY] {path} -> HTTP {e.code}: {e.read().decode('utf-8')[:80]}")
        except Exception as e:
            print(f"[FAIL] {path} -> {e}")

    # 2. CORS OPTIONS preflight
    print("\n--- Testing CORS Preflight ---")
    cors_req = urllib.request.Request(
        f"{BACKEND}/api/auth/login",
        headers={
            "Origin": FRONTEND,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization"
        },
        method="OPTIONS"
    )
    try:
        res = urllib.request.urlopen(cors_req, context=ctx, timeout=15)
        allow_origin = res.getheader("Access-Control-Allow-Origin")
        allow_creds = res.getheader("Access-Control-Allow-Credentials")
        print(f"[PASS] OPTIONS /api/auth/login -> {res.getcode()}")
        print(f"       Allow-Origin: {allow_origin}, Allow-Credentials: {allow_creds}")
    except Exception as e:
        print(f"[FAIL] CORS preflight failed: {e}")

    # 3. Authentication for all demo users
    print("\n--- Testing All Demo Role Logins ---")
    demo_creds = [
        ("Patient", "patient@hospital.com", "Patient@123", "PATIENT"),
        ("Doctor", "dr.sharma@hospital.com", "Doctor@123", "DOCTOR"),
        ("Doctor (alt)", "doctor@hospital.com", "Doctor@123", "DOCTOR"),
        ("Admin", "admin@hospital.com", "Admin@123", "ADMIN"),
        ("Front Desk", "frontdesk@hospital.com", "FrontDesk@123", "FRONT_DESK"),
    ]

    tokens = {}
    for role_name, email, password, expected_role in demo_creds:
        try:
            res = req(f"{BACKEND}/api/auth/login", method="POST", data={"email": email, "password": password})
            body = json.loads(res.read().decode("utf-8"))
            user = body.get("data", {}).get("user", {})
            tok = body.get("data", {}).get("access_token")
            actual_role = user.get("role")
            assert actual_role == expected_role, f"Expected role {expected_role} but got {actual_role}"
            assert tok, "Missing access_token"
            tokens[role_name] = tok
            print(f"[PASS] {role_name} ({email}) -> 200 OK, Role: {actual_role}")
        except urllib.error.HTTPError as e:
            print(f"[FAIL/PENDING DEPLOY] {role_name} ({email}) -> HTTP {e.code}: {e.read().decode('utf-8')[:80]}")
        except Exception as e:
            print(f"[FAIL] {role_name} ({email}) -> {e}")

    # 4. Invalid Login
    print("\n--- Testing Invalid Login ---")
    try:
        req(f"{BACKEND}/api/auth/login", method="POST", data={"email": "patient@hospital.com", "password": "WrongPassword999"})
        print("[FAIL] Invalid login was unexpectedly accepted!")
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"[PASS] Invalid login rejected with HTTP 401: {e.read().decode('utf-8')[:80]}")
        else:
            print(f"[INFO] Invalid login returned HTTP {e.code}")
    except Exception as e:
        print(f"[ERROR] {e}")

    # 5. Protected Endpoints
    print("\n--- Testing Protected Endpoints ---")
    if "Patient" in tokens:
        p_hdr = {"Authorization": f"Bearer {tokens['Patient']}"}
        try:
            res = req(f"{BACKEND}/api/appointments/my", headers=p_hdr)
            print(f"[PASS] Patient appointments: HTTP {res.getcode()}")
        except Exception as e:
            print(f"[FAIL] Patient appointments: {e}")

    if "Doctor" in tokens:
        d_hdr = {"Authorization": f"Bearer {tokens['Doctor']}"}
        try:
            res = req(f"{BACKEND}/api/doctor/appointments", headers=d_hdr)
            print(f"[PASS] Doctor appointments: HTTP {res.getcode()}")
        except Exception as e:
            print(f"[FAIL] Doctor appointments: {e}")

    if "Admin" in tokens:
        a_hdr = {"Authorization": f"Bearer {tokens['Admin']}"}
        try:
            res = req(f"{BACKEND}/api/admin/stats", headers=a_hdr)
            data = json.loads(res.read().decode("utf-8")).get("data", {})
            print(f"[PASS] Admin stats: HTTP {res.getcode()}, Metrics: {list(data.get('metrics', {}).keys())}")
        except Exception as e:
            print(f"[FAIL] Admin stats: {e}")

    # 6. AI Chat
    print("\n--- Testing AI Chat Endpoint ---")
    try:
        t0 = time.time()
        res = req(f"{BACKEND}/api/ai/chat", method="POST", data={"message": "What are your OPD timings?"})
        elapsed = time.time() - t0
        data = json.loads(res.read().decode("utf-8"))
        reply = data.get("data", {}).get("reply") or data.get("data", {}).get("response") or ""
        print(f"[PASS] AI Chat: HTTP {res.getcode()} in {elapsed:.2f}s")
        print(f"       Reply preview: {reply[:80].strip()}...")
    except Exception as e:
        print(f"[FAIL] AI Chat: {e}")

    # 7. Frontend bundle and SPA routing
    print("\n--- Testing Frontend and SPA Routing ---")
    try:
        res = req(f"{FRONTEND}/")
        html = res.read().decode("utf-8")
        import re
        js_files = re.findall(r'src=["\']([^"\']+\.js)["\']', html)
        print(f"[PASS] Frontend / -> HTTP {res.getcode()}, Active JS: {js_files}")
    except Exception as e:
        print(f"[FAIL] Frontend / -> {e}")

    for spa_path in ["/login", "/register", "/patient/dashboard"]:
        try:
            res = req(f"{FRONTEND}{spa_path}")
            print(f"[PASS] Frontend {spa_path} direct navigation -> HTTP {res.getcode()}")
        except urllib.error.HTTPError as e:
            print(f"[NOTE] Frontend {spa_path} -> HTTP {e.code} (Render SPA rewrite rule may be pending in dashboard)")
        except Exception as e:
            print(f"[ERROR] Frontend {spa_path} -> {e}")

    print("\n" + "=" * 60)
    print("VERIFICATION RUN COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    run()
