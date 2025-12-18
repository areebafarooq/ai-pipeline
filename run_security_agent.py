import os
import subprocess

# =============================
# Configuration
# =============================
REPO_DIR = os.environ.get("REPO_DIR", os.getcwd())
REPORTS_DIR = os.path.join(os.getcwd(), "reports")

# ZAP + Nuclei need a RUNNING app
TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:8000")

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
    f'docker run --rm '
    f'-v "{REPO_DIR}:/src" '
    f'-v "{REPORTS_DIR}:/reports" '
    f'semgrep/semgrep '
    f'semgrep --config=auto /src --json '
    f'-o /reports/semgrep_report.json',
    "Semgrep (SAST) Scan"
)

# =============================
# OWASP ZAP – Dynamic App Scan
# =============================
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/zap/wrk" '
    f'zaproxy/zap-stable '
    f'zap-baseline.py '
    f'-t {TARGET_URL} '
    f'-r /zap/wrk/zap_report.html',
    "OWASP ZAP (DAST) Scan"
)

# =============================
# NUCLEI – Vulnerability Scan
# =============================
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/root" '
    f'projectdiscovery/nuclei '
    f'-u {TARGET_URL} '
    f'-severity low,medium,high,critical '
    f'-o /root/nuclei_report.txt',
    "Nuclei Scan"
)

print("\n🎉 ALL SECURITY SCANS COMPLETED SUCCESSFULLY")
print("📂 Reports generated in the 'reports/' folder")
