import subprocess
import time
import sys
import os
import urllib.request

def wait_for_url(url, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(1)
    return False

def main():
    print("==================================================")
    print("STARTING CLINICCARE LIVE FULL E2E TEST RUNNER")
    print("==================================================")
    
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    
    # 1. Start Backend
    print("\n[1/4] Starting FastAPI backend on port 8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # 2. Start Frontend
    print("[2/4] Starting Vite frontend on port 5173...")
    frontend_proc = subprocess.Popen(
        "npm run dev -- --host 127.0.0.1 --port 5173",
        cwd=frontend_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for backend
        print("Waiting for backend /health...")
        if not wait_for_url("http://127.0.0.1:8000/health", 25):
            print("ERROR: Backend failed to become healthy in time.")
            sys.exit(1)
        print("Backend is healthy!")

        # Wait for frontend
        print("Waiting for frontend :5173...")
        if not wait_for_url("http://127.0.0.1:5173", 25):
            print("ERROR: Frontend failed to respond in time.")
            sys.exit(1)
        print("Frontend is up!")

        # 3. Execute Browser Flow
        print("\n[3/4] Executing Playwright Browser Verification...")
        browser_test = subprocess.run(
            [sys.executable, os.path.join(root_dir, "verify_browser_flow.py")],
            cwd=root_dir,
            capture_output=True,
            text=True,
        )
        print(browser_test.stdout)
        if browser_test.stderr:
            print("STDERR:", browser_test.stderr)

        if browser_test.returncode != 0:
            print("Browser test failed!")
            sys.exit(1)

        print("\n[4/4] ALL LIVE E2E CHECKS PASSED SUCCESSFULLY!")

    finally:
        print("\nShutting down server processes...")
        backend_proc.terminate()
        frontend_proc.terminate()
        try:
            backend_proc.wait(timeout=3)
            frontend_proc.wait(timeout=3)
        except Exception:
            backend_proc.kill()
            frontend_proc.kill()

        # Force kill any dangling nodes or uvicorns on Windows
        subprocess.run("taskkill /F /IM uvicorn.exe /T", shell=True, capture_output=True)
        print("Servers stopped cleanly.")

if __name__ == "__main__":
    main()
