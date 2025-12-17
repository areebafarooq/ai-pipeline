import subprocess
import os

BASE = os.getcwd()
REPORTS_DIR = os.path.join(BASE, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

TARGET_URL = os.environ.get("TARGET_URL", "http://localhost:8000")
REPO_DIR = os.environ.get("REPO_DIR", os.path.join(BASE, "repo"))

def run(cmd, name="Command"):
    print(f"\nRunning: {name}\n{'='*40}")
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding="utf-8", errors="ignore")
    for line in process.stdout:
        print(line, end="")
    process.wait()
    if process.returncode != 0:
        print(f"\n❌ {name} finished with errors (exit code {process.returncode})")
    else:
        print(f"\n✅ {name} completed successfully")

# Semgrep
run(f'docker run --rm -v "{REPO_DIR}:/src" -v "{REPORTS_DIR}:/reports" semgrep/semgrep semgrep --config=auto /src --json -o /reports/semgrep_report.txt', "Semgrep Scan")

# OWASP ZAP
run(f'docker run --rm -v "{REPORTS_DIR}:/zap/wrk" zaproxy/zap-stable zap-baseline.py -t {TARGET_URL} -r /zap/wrk/zap_report.html', "OWASP ZAP Scan")

# Nuclei
run(f'docker run --rm -v "{REPORTS_DIR}:/root" projectdiscovery/nuclei -u {TARGET_URL} -o /root/nuclei_report.txt', "Nuclei Scan")

print("\n🎉 ALL SECURITY SCANS COMPLETED")
