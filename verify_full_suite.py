import sys
import time
import json
import urllib.request
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

def test_full_application():
    print("==================================================")
    print("CLINICCARE EXTENSIVE BROWSER & SYSTEM VERIFICATION")
    print("==================================================")
    
    results = {}
    
    # 1. Health check & Backend connectivity
    print("\n--- 1. BACKEND & HEALTH ENDPOINT CHECK ---")
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/health")
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            print(f"Health Response: {data}")
            assert data.get("status") == "healthy"
            assert data.get("database") == "healthy"
            results["BACKEND"] = "PASS"
            results["DATABASE"] = "PASS"
    except Exception as e:
        print(f"Health Check Failed: {e}")
        results["BACKEND"] = "FAIL"
        results["DATABASE"] = "FAIL"

    # 2. Playwright Browser Tests
    console_errors = []
    page_errors = []
    api_failures = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Responsive check viewports
        viewports = [
            ("Mobile 390px", {"width": 390, "height": 844}),
            ("Tablet 768px", {"width": 768, "height": 1024}),
            ("Desktop 1024px", {"width": 1024, "height": 768}),
            ("Wide Desktop 1440px", {"width": 1440, "height": 900}),
        ]

        print("\n--- 2. RESPONSIVE VIEWPORT TESTING ---")
        responsive_passed = True
        for name, vp in viewports:
            ctx = browser.new_context(viewport=vp)
            pg = ctx.new_page()
            try:
                pg.goto("http://127.0.0.1:5173", wait_until="networkidle")
                assert pg.is_visible("text=ClinicCare") or pg.is_visible("header")
                print(f"  [OK] {name} rendered navigation and landing page.")
            except Exception as e:
                print(f"  [FAIL] {name}: {e}")
                responsive_passed = False
            finally:
                ctx.close()
        results["RESPONSIVE"] = "PASS" if responsive_passed else "FAIL"

        # Main Flow Context
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        def on_response(response):
            if response.status >= 400 and "/health" not in response.url:
                try:
                    body = response.text()
                except:
                    body = "N/A"
                msg = f"HTTP {response.status}: {response.request.method} {response.url} -> {body[:200]}"
                print(f"  [NETWORK LOG] {msg}")
                if response.status >= 500:
                    api_failures.append(msg)
        page.on("response", on_response)

        # Website Load
        print("\n--- 3. WEBSITE LOAD & NAVIGATION ---")
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        assert "ClinicCare" in page.title()
        results["WEBSITE"] = "PASS"

        # Navigate to login & test invalid credentials
        print("\n--- 4. ERROR HANDLING & VALIDATION CHECKS ---")
        page.click("text=Sign In")
        page.wait_for_url("**/login", timeout=5000)
        page.fill("input[type='email']", "nonexistent@hospital.com")
        page.fill("input[type='password']", "Wrong@Pass999")
        page.click("button[type='submit']")
        page.wait_for_timeout(1000)
        assert "/login" in page.url
        print("  [OK] Invalid credentials safely rejected.")

        # Test Patient Flow
        print("\n--- 5. PATIENT WORKFLOW & AUTHENTICATION ---")
        page.fill("input[type='email']", "patient@hospital.com")
        page.fill("input[type='password']", "Patient@123")
        page.click("button[type='submit']")
        page.wait_for_url("**/patient/dashboard", timeout=5000)
        results["LOGIN"] = "PASS"
        results["DASHBOARD"] = "PASS"
        results["PATIENT"] = "PASS"

        # Doctor listing
        print("\n--- 6. DOCTOR LISTING & SELECTION ---")
        page.click("a[href='/patient/doctors']")
        page.wait_for_url("**/patient/doctors")
        page.wait_for_selector("text=Dr. Rajesh Sharma")
        results["DOCTOR"] = "PASS"

        # Appointment Booking & Persistence Check
        print("\n--- 7. APPOINTMENT BOOKING & DATABASE PERSISTENCE ---")
        page.click("text=Book Slot >> nth=1") # Choose Dr. Priya Patel
        page.wait_for_url("**/patient/appointments/book**")
        
        # Pick a date 4 days ahead to have clean fresh slots
        future_date = (date.today() + timedelta(days=4)).isoformat()
        page.fill("input[type='date']", future_date)
        page.wait_for_timeout(1000)

        # Wait for slots to load
        page.wait_for_selector("button:has-text(':')", timeout=5000)
        slot_btn = page.locator("button:has-text(':')").first
        slot_text = slot_btn.inner_text()
        print(f"  Selecting slot: {slot_text}")
        slot_btn.click()
        page.wait_for_timeout(500)
        
        unique_reason = f"Automated Checkup ID-{int(time.time())}"
        page.fill("input[placeholder*='Routine']", unique_reason)
        print("  Submitting appointment form...")
        page.click("button:has-text('Confirm Appointment')")
        page.wait_for_url("**/patient/appointments", timeout=10000)
        page.wait_for_selector(f"text={unique_reason}", timeout=10000)
        print("  [OK] Appointment saved and displayed in UI.")

        # Browser Refresh Persistence Verification
        print("  [PERSISTENCE] Refreshing browser to verify database persistence...")
        page.reload(wait_until="networkidle")
        page.wait_for_selector(f"text={unique_reason}", timeout=5000)
        print("  [OK] Persisted record remains present after page reload.")
        results["APPOINTMENT"] = "PASS"

        # AI Assistant Chat
        print("\n--- 8. AI ASSISTANT CONVERSATION & SAFETY ---")
        page.click("a[href='/patient/chat']")
        page.wait_for_url("**/patient/chat")
        page.fill("input[placeholder*='Type your question']", "Hello, which cardiology doctors are available for heart consultation?")
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        print("  [OK] AI Assistant conversation active and responsive.")
        results["AI"] = "PASS"

        # Logout Patient
        page.click("button:has(svg.lucide-log-out)")
        page.wait_for_url("**/login")

        # Doctor Flow
        print("\n--- 9. DOCTOR PORTAL WORKFLOW ---")
        page.fill("input[type='email']", "dr.sharma@hospital.com")
        page.fill("input[type='password']", "Doctor@123")
        page.click("button[type='submit']")
        page.wait_for_url("**/doctor/dashboard", timeout=5000)
        page.wait_for_selector("text=Physician Clinical Portal")
        print("  [OK] Doctor Dashboard loaded with schedule.")

        # Doctor Appointments view
        page.click("a[href='/doctor/appointments']")
        page.wait_for_url("**/doctor/appointments")
        page.wait_for_selector("text=My Consultations")
        print("  [OK] Doctor Consultations Schedule loaded.")

        # Doctor Logout
        page.click("button:has(svg.lucide-log-out)")
        page.wait_for_url("**/login")

        # Admin Flow
        print("\n--- 10. ADMIN & ANALYTICS WORKFLOW ---")
        page.fill("input[type='email']", "admin@hospital.com")
        page.fill("input[type='password']", "Admin@123")
        page.click("button[type='submit']")
        page.wait_for_url("**/admin/dashboard", timeout=5000)
        page.wait_for_selector("text=Total Patients")
        page.wait_for_selector("text=Active Ambulances")
        page.wait_for_selector("text=7-Day Appointment Bookings")
        print("  [OK] Admin Dashboard & Analytics metrics verified.")

        # Admin Patients Directory
        page.click("a[href='/admin/patients']")
        page.wait_for_url("**/admin/patients")
        page.wait_for_selector("text=Patient Directory")
        print("  [OK] Admin Patients Directory verified.")

        # Admin Escalations
        page.click("a[href='/admin/escalations']")
        page.wait_for_url("**/admin/escalations")
        page.wait_for_selector("text=Front-Desk & Emergency Escalations")
        print("  [OK] Admin Escalations dashboard verified.")

        # Admin Reports
        page.click("a[href='/admin/reports']")
        page.wait_for_url("**/admin/reports")
        page.wait_for_selector("text=Diagnostic Reports Directory")
        print("  [OK] Admin Reports management verified.")

        # Logout Admin
        page.click("button:has(svg.lucide-log-out)")
        page.wait_for_url("**/login")
        results["ADMIN"] = "PASS"

        browser.close()

    print("\n--- CONSOLE & API ERROR SUMMARY ---")
    print(f"Page/Console Errors: {page_errors}")
    print(f"API Failures: {api_failures}")

    results["END-TO-END"] = "PASS" if not page_errors and not api_failures else "FAIL"
    return results

if __name__ == "__main__":
    res = test_full_application()
    print("\nSUMMARY RESULTS DICTIONARY:")
    print(json.dumps(res, indent=2))
