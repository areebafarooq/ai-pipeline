import subprocess
import os

# ----------------------------
# CI/CD-friendly Security Agent
# ----------------------------

# Base directory for reports
BASE = os.getcwd()
REPORTS_DIR = os.path.join(BASE, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# Target URLs (set via environment variables or default to example)
TARGET_URL = os.environ.get("TARGET_URL", "http://host.docker.internal:8000")
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
        errors="ignore"  # avoids UnicodeDecodeError
    )
    
    for line in process.stdout:
        print(line, end="")
    
    process.wait()
    if process.returncode != 0:
        print(f"\n❌ {name} finished with errors (exit code {process.returncode})")
    else:
        print(f"\n✅ {name} completed successfully")

# ----------------------------
# 1 Run Semgrep
# ----------------------------
run(
    f'docker run --rm -v "{REPO_DIR}:/src" semgrep/semgrep semgrep --config=auto /src > "{REPORTS_DIR}/semgrep_report.txt"',
    "Semgrep Scan"
)

# ----------------------------
# 2️ Run OWASP ZAP Baseline Scan
# ----------------------------
run(
    f'docker run --rm -v "{REPORTS_DIR}:/zap/wrk" zaproxy/zap-stable zap-baseline.py -t {TARGET_URL} -r /zap/wrk/zap_report.html',
    "OWASP ZAP Scan"
)

# ----------------------------
# 3️ Run Nuclei Scan
# ----------------------------
run(
    f'docker run --rm -v "{REPORTS_DIR}:/root" projectdiscovery/nuclei -u {TARGET_URL} -o /root/nuclei_report.txt',
    "Nuclei Scan"
)

print("\n🎉 ALL SECURITY SCANS COMPLETED")
