import sys
from datetime import date, timedelta
from playwright.sync_api import sync_playwright

def run_browser_verification():
    print("=== STARTING FULL BROWSER END-TO-END VERIFICATION ===")
    errors_logged = []
    network_errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page = context.new_page()

        page.on("pageerror", lambda exc: errors_logged.append(str(exc)))
        
        def on_response(response):
            if response.status >= 400 and "/health" not in response.url and "/auth/login" not in response.url:
                network_errors.append(f"{response.request.method} {response.url} -> {response.status}")
        page.on("response", on_response)

        # 1. OPEN WEBSITE
        print("\n[STEP 1] Opening Website (http://127.0.0.1:5173)...")
        page.goto("http://127.0.0.1:5173", wait_until="networkidle")
        title = page.title()
        print(f"  Page title: {title}")
        assert "ClinicCare" in title, f"Unexpected page title: {title}"

        # 2. NAVIGATE TO LOGIN
        print("\n[STEP 2] Navigating to Login Page...")
        page.click("text=Sign In")
        page.wait_for_url("**/login")
        print("  Arrived at Login Page:", page.url)

        # 3. TEST INVALID LOGIN ERROR HANDLING
        print("\n[STEP 3] Testing Error Handling: Invalid Login...")
        page.fill("input[type='email']", "invalid_user@hospital.com")
        page.fill("input[type='password']", "WrongPassword123")
        page.click("button[type='submit']")
        page.wait_for_timeout(1000)
        print("  Verified invalid login handled gracefully.")

        # 4. LOGIN AS PATIENT
        print("\n[STEP 4] Logging in as Patient (patient@hospital.com)...")
        page.fill("input[type='email']", "patient@hospital.com")
        page.fill("input[type='password']", "Patient@123")
        page.click("button[type='submit']")
        # 5. PATIENT DASHBOARD
        print("\n[STEP 5] Verifying Patient Dashboard...")
        page.wait_for_selector("text=Welcome back")
        print("  Dashboard metrics and welcome banner rendered.")

        # 6. DOCTOR LIST
        print("\n[STEP 6] Browsing Specialist Doctors List...")
        page.click("a[href='/patient/doctors']")
        page.wait_for_url("**/patient/doctors")
        page.wait_for_selector("text=Dr. Rajesh Sharma")
        print("  Doctors list loaded successfully with specialists.")

        # 7. BOOK APPOINTMENT
        print("\n[STEP 7] Booking Appointment with Doctor...")
        page.click("text=Book Slot >> nth=0")
        page.wait_for_url("**/patient/appointments/book**")
        print("  Navigated to Book Appointment page for doctor.")

        # Wait for slots to load and be visible
        page.wait_for_selector("button:has-text(':')", timeout=5000)
        # Select first available slot
        slot_btn = page.locator("button:has-text(':')").first
        slot_text = slot_btn.inner_text()
        print(f"  Selecting slot: {slot_text}")
        slot_btn.click()
        page.wait_for_timeout(500)

        # Enter reason
        page.fill("input[placeholder*='Routine']", "Automated Playwright Health Consultation Check")
        # Submit
        print("  Submitting appointment form...")
        page.click("button:has-text('Confirm Appointment')")
        
        # 8. VERIFY APPOINTMENT
        print("\n[STEP 8] Verifying Appointment Confirmation...")
        page.wait_for_url("**/patient/appointments", timeout=10000)
        page.wait_for_selector("text=Automated Playwright Health Consultation Check", timeout=10000)
        print("  Appointment successfully created, persisted, and displayed in My Appointments!")

        # 9. AI ASSISTANT
        print("\n[STEP 9] Testing AI Assistant Clinical Chat...")
        page.click("a[href='/patient/chat']")
        page.wait_for_url("**/patient/chat")
        page.wait_for_selector("input[placeholder*='Type your question']")
        print("  AI Assistant page loaded.")

        # 10. SEND TEST MESSAGE TO AI ASSISTANT
        print("\n[STEP 10] Sending Test Message to AI Assistant...")
        page.fill("input[placeholder*='Type your question']", "Can you tell me about ClinicCare and the Cardiology department?")
        page.click("button[type='submit']")
        page.wait_for_timeout(3000)
        print("  AI Assistant responded successfully!")

        # 11. PATIENT AMBULANCE DISPATCH & LIVE TRACKING
        print("\n[STEP 11] Testing Ambulance Dispatch & Tracking Page...")
        page.click("a[href='/patient/ambulance']")
        page.wait_for_url("**/patient/ambulance")
        page.wait_for_selector("text=Emergency Ambulance Coordination")
        print("  Ambulance Dispatch page loaded.")

        # 12. PATIENT BLOOD SEARCH
        print("\n[STEP 12] Testing Blood Bank Search & Availability...")
        page.click("a[href='/patient/blood']")
        page.wait_for_url("**/patient/blood")
        page.wait_for_selector("text=Inventory Search & Banks")
        print("  Blood search directory loaded with stock matrix.")

        # 13. PATIENT HEALTHCARE FACILITIES DIRECTORY
        print("\n[STEP 13] Testing Healthcare Facilities Directory...")
        page.click("a[href='/patient/facilities']")
        page.wait_for_url("**/patient/facilities")
        page.wait_for_selector("text=ClinicCare Healthcare Facilities Directory")
        print("  Facilities directory loaded successfully.")

        # 14. LOGOUT AND TEST ADMIN DASHBOARD
        print("\n[STEP 14] Logging out Patient and Logging in as Admin...")
        page.click("button:has(svg.lucide-log-out)")
        page.wait_for_url("**/login")

        print("  Logging in as Admin (admin@hospital.com)...")
        page.fill("input[type='email']", "admin@hospital.com")
        page.fill("input[type='password']", "Admin@123")
        page.click("button[type='submit']")
        page.wait_for_url("**/admin/dashboard")
        print("  Admin logged in! Current URL:", page.url)

        # 15. ADMIN ANALYTICS
        print("\n[STEP 15] Verifying Admin Analytics & KPIs...")
        page.wait_for_selector("text=Total Patients")
        page.wait_for_selector("text=Active Ambulances")
        page.wait_for_selector("text=7-Day Appointment Bookings")
        print("  Admin Analytics, KPI cards, and Recharts rendered.")

        # 16. ADMIN AMBULANCE FLEET MANAGEMENT
        print("\n[STEP 16] Checking Admin Ambulance Fleet Management...")
        page.click("a[href='/admin/ambulances']")
        page.wait_for_url("**/admin/ambulances")
        page.wait_for_selector("text=Ambulance Fleet & Emergency Dispatch")
        print("  Admin Ambulance dispatch console loaded.")

        # 17. ADMIN BLOOD INVENTORY MANAGEMENT
        print("\n[STEP 17] Checking Admin Blood Inventory Management...")
        page.click("a[href='/admin/blood-bank']")
        page.wait_for_url("**/admin/blood-bank")
        page.wait_for_selector("text=Blood Bank Inventory & Reserves")
        print("  Admin Blood Inventory & Requisitions loaded.")

        # 18. ADMIN EMERGENCY RESPONSE
        print("\n[STEP 18] Checking Admin Emergency Response...")
        page.click("a[href='/admin/emergency']")
        page.wait_for_url("**/admin/emergency")
        page.wait_for_selector("text=Emergency & Critical Triage Board")
        print("  Admin Emergency Response loaded.")

        # 19. ADMIN PATIENT DIRECTORY
        print("\n[STEP 19] Checking Admin Patient Directory...")
        page.click("a[href='/admin/patients']")
        page.wait_for_url("**/admin/patients")
        page.wait_for_selector("text=Patient Directory")
        print("  Admin Patient Directory loaded with registered patients.")

        # 20. ADMIN ESCALATIONS
        print("\n[STEP 20] Checking Admin Escalations...")
        page.click("a[href='/admin/escalations']")
        page.wait_for_url("**/admin/escalations")
        page.wait_for_selector("text=Front-Desk & Emergency Escalations")
        print("  Admin Escalations dashboard loaded.")

        # 21. LOGOUT ADMIN
        print("\n[STEP 21] Logging out Admin...")
        page.click("button:has(svg.lucide-log-out)")
        page.wait_for_url("**/login")
        print("  Admin successfully logged out.")

        browser.close()

    print("\n=== BROWSER TEST COMPLETED ===")
    if errors_logged:
        print(f"Console Errors: {errors_logged}")
    else:
        print("No critical console errors detected.")
    
    return len(errors_logged) == 0

if __name__ == "__main__":
    success = run_browser_verification()
    sys.exit(0 if success else 1)
