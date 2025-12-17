import subprocess
import os

# ----------------------------
# CI/CD-friendly Security Agent
# ----------------------------

BASE = os.getcwd()
REPORTS_DIR = os.path.join(BASE, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Target URLs (set via environment variables or default)
TARGET_URL = os.environ.get("TARGET_URL", "http://app:8000")  # <-- use container hostname in CI
REPO_DIR = os.environ.get("REPO_DIR", os.path.join(BASE, "repo"))

def run(cmd, name="Command"):
    print("\n==============================")
    print(f"Running: {name}")
    print("==============================\n")
    
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

# ----------------------------
# 1️⃣ Run Semgrep
# ----------------------------
run(
    f'docker run --rm -v "{REPO_DIR}:/src" -v "{REPORTS_DIR}:/reports" '
    f'semgrep/semgrep semgrep --config=auto /src --json -o /reports/semgrep_report.txt',
    "Semgrep Scan"
)

# ----------------------------
# 2️⃣ Run OWASP ZAP Baseline Scan
# ----------------------------
run(
    f'docker run --rm --network host -v "{REPORTS_DIR}:/zap/wrk" '
    f'zaproxy/zap-stable zap-baseline.py -t {TARGET_URL} -r /zap/wrk/zap_report.html',
    "OWASP ZAP Scan"
)

# ----------------------------
# 3️⃣ Run Nuclei Scan
# ----------------------------
run(
    f'docker run --rm -v "{REPORTS_DIR}:/reports" projectdiscovery/nuclei -u {TARGET_URL} -o /reports/nuclei_report.txt',
    "Nuclei Scan"
)

print("\n🎉 ALL SECURITY SCANS COMPLETED")
