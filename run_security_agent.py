import os
import subprocess
import socket
import time

# =============================
# Wait for app to start
# =============================
def wait_for_app(host="localhost", port=8000, timeout=60):
    print(f"\n⏳ Waiting for app at {host}:{port} to be ready...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("✅ App is ready!")
                return
        except OSError:
            time.sleep(2)
    raise TimeoutError(f"App did not start on {host}:{port} within {timeout} seconds")

# Use environment variable if set (useful for GitHub Actions)
TARGET_HOST = os.environ.get("TARGET_HOST", "localhost")
TARGET_PORT = int(os.environ.get("TARGET_PORT", 8000))
TARGET_URL = os.environ.get("TARGET_URL", f"http://{TARGET_HOST}:{TARGET_PORT}")

wait_for_app(host=TARGET_HOST, port=TARGET_PORT, timeout=60)

# =============================
# Configuration
# =============================
REPO_DIR = os.environ.get("REPO_DIR", os.getcwd())
REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# =============================
# Helper function
# =============================
def run(cmd, name="Command"):
    print(f"\n🚀 Running: {name}")
    print("=" * 60)
    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="ignore"
    )
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        print(f"\n❌ {name} finished with errors (exit code {process.returncode})")
    else:
        print(f"\n✅ {name} completed successfully")

# =============================
# SEMGREP – Static Code Analysis
# =============================
run(
    f'docker run --rm -v "{REPO_DIR}:/src" -v "{REPORTS_DIR}:/reports" '
    f'semgrep/semgrep semgrep --config=auto /src --json -o /reports/semgrep_report.json',
    "Semgrep (SAST) Scan"
)

# =============================
# OWASP ZAP – Dynamic App Scan
# =============================
run(
    f'docker run --rm -v "{REPORTS_DIR}:/zap/wrk" '
    f'zaproxy/zap-stable zap-baseline.py '
    f'-t {TARGET_URL} '
    f'-r /zap/wrk/zap_report.html -T 120',
    "OWASP ZAP (DAST) Scan"
)

# =============================
# NUCLEI – Vulnerability Scan
# =============================
run(
    f'docker run --rm -v "{REPORTS_DIR}:/root" '
    f'projectdiscovery/nuclei -u {TARGET_URL} '
    f'-severity low,medium,high,critical -o /root/nuclei_report.txt',
    "Nuclei Scan"
)

print("\n🎉 ALL SECURITY SCANS COMPLETED SUCCESSFULLY")
print("📂 Reports generated in the 'reports/' folder")


