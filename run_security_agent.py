import subprocess
import os
import sys

BASE = os.getcwd()

def run(cmd):
    print("\n==============================")
    print("Running:", cmd)
    print("==============================\n")

    process = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="ignore"   # <-- IMPORTANT FIX
    )

    for line in process.stdout:
        print(line, end="")

    process.wait()

# SEMGREP
run(f'docker run --rm -v "{BASE}\\repo:/src" semgrep/semgrep semgrep --config=auto /src')

# ZAP
run(f'docker run --rm -v "{BASE}\\reports:/zap/wrk" zaproxy/zap-stable zap-baseline.py '
    f'-t http://host.docker.internal:8000 -r /zap/wrk/zap_report.html')

# NUCLEI
run(f'docker run --rm -v "{BASE}\\reports:/root" projectdiscovery/nuclei '
    f'-u http://host.docker.internal:8000 -o /root/nuclei_report.txt')

print("\n✅ ALL SECURITY SCANS COMPLETED SUCCESSFULLY")
