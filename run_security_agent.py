import os
import subprocess
import socket
import time
from urllib.parse import urlparse


def wait_for_app(host: str, port: int, timeout: int = 120):
    print(f"\n⏳ Waiting for app at {host}:{port} to be ready...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("✅ App is ready!")
                return
        except OSError:
            time.sleep(2)

    raise TimeoutError(f"❌ App did not start on {host}:{port} within {timeout} seconds")


# =============================
# Configuration
# =============================
REPO_DIR = os.environ.get("REPO_DIR", os.getcwd())
REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Always read TARGET_URL from env (workflow will set it to http://test-app:8000)
TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:8000").strip()
parsed = urlparse(TARGET_URL)
TARGET_HOST = parsed.hostname or "localhost"
TARGET_PORT = parsed.port or (443 if parsed.scheme == "https" else 80)

# Wait until the app is reachable (IMPORTANT: this must match TARGET_URL host/port)
wait_for_app(host=TARGET_HOST, port=TARGET_PORT, timeout=120)


def run(cmd: str, name: str):
    print(f"\n🚀 Running: {name}")
    print("=" * 60)
    print(cmd)
    print("-" * 60)

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="ignore",
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()
    if process.returncode != 0:
        print(f"\n❌ {name} finished with errors (exit code {process.returncode})")
        # Do NOT raise — keep running the other tools and still upload artifacts
    else:
        print(f"\n✅ {name} completed successfully")


# =============================
# SEMGREP – Static Code Analysis
# =============================
run(
    f'docker run --rm '
    f'-v "{REPO_DIR}:/src" '
    f'-v "{REPORTS_DIR}:/reports" '
    f'semgrep/semgrep semgrep --config=auto /src --json -o /reports/semgrep_report.json',
    "Semgrep (SAST) Scan",
)

# =============================
# OWASP ZAP – Dynamic App Scan
# =============================
# Run on the same docker network as the app and target http://test-app:8000
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/zap/reports" '
    f'--network zap-network '
    f'zaproxy/zap-stable zap-baseline.py '
    f'-t "{TARGET_URL}" '
    f'-r /zap/reports/zap_report.html '
    f'-T 120',
    "OWASP ZAP (DAST) Scan",
)

# =============================
# NUCLEI – Vulnerability Scan
# =============================
# Also run on the same docker network so it can reach test-app
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/root" '
    f'--network zap-network '
    f'projectdiscovery/nuclei -u "{TARGET_URL}" '
    f'-severity low,medium,high,critical -o /root/nuclei_report.txt',
    "Nuclei Scan",
)

print("\n🎉 ALL SECURITY SCANS COMPLETED")
print("📂 Reports should be in the 'reports/' folder")

