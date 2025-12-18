import os
import subprocess
import time


def wait_for_app_via_docker_network(target_url: str, network: str = "zap-network", timeout: int = 180):
    print(f"\n⏳ Waiting for app (via Docker network '{network}') at {target_url} ...")
    start = time.time()

    while time.time() - start < timeout:
        cmd = (
            f'docker run --rm --network {network} curlimages/curl:8.5.0 '
            f'curl -s -o /dev/null -w "%{{http_code}}" "{target_url}/"'
        )
        try:
            code = subprocess.check_output(cmd, shell=True, text=True).strip()
            if code and code != "000":
                print(f"✅ App responded with HTTP {code}")
                return
        except subprocess.CalledProcessError:
            pass
        time.sleep(3)

    print("\n❌ Timed out waiting for app. Showing logs:\n")
    os.system("docker ps -a || true")
    os.system("docker logs test-app || true")
    raise TimeoutError(f"App did not respond at {target_url} within {timeout} seconds")


def run(cmd: str, name: str):
    print(f"\n🚀 Running: {name}")
    print("=" * 60)
    print(cmd)
    print("-" * 60)

    proc = subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="ignore",
    )

    for line in proc.stdout:
        print(line, end="")

    proc.wait()
    if proc.returncode != 0:
        print(f"\n❌ {name} finished with errors (exit code {proc.returncode})")
    else:
        print(f"\n✅ {name} completed successfully")


# =============================
# Config
# =============================
REPO_DIR = os.environ.get("REPO_DIR", os.getcwd())
REPORTS_DIR = os.path.join(os.getcwd(), "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

TARGET_URL = os.environ.get("TARGET_URL", "http://test-app:8000").strip()
NETWORK_NAME = os.environ.get("DOCKER_NETWORK", "zap-network").strip()

# For ZAP baseline script
ZAP_WRK = os.path.join(REPORTS_DIR, "zap-wrk")
os.makedirs(ZAP_WRK, exist_ok=True)

wait_for_app_via_docker_network(TARGET_URL, network=NETWORK_NAME, timeout=180)

# =============================
# Semgrep
# =============================
run(
    f'docker run --rm '
    f'-v "{REPO_DIR}:/src" '
    f'-v "{REPORTS_DIR}:/reports" '
    f'semgrep/semgrep semgrep --config=auto /src --json -o /reports/semgrep_report.json',
    "Semgrep (SAST) Scan"
)

# =============================
# OWASP ZAP (mount /zap/wrk)
# =============================
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/zap/reports" '
    f'-v "{ZAP_WRK}:/zap/wrk" '
    f'--network {NETWORK_NAME} '
    f'zaproxy/zap-stable zap-baseline.py '
    f'-t "{TARGET_URL}" '
    f'-r /zap/reports/zap_report.html '
    f'-T 120',
    "OWASP ZAP (DAST) Scan"
)

# =============================
# Nuclei (DO NOT mount reports to /root)
# =============================
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/out" '
    f'--network {NETWORK_NAME} '
    f'projectdiscovery/nuclei '
    f'-u "{TARGET_URL}" '
    f'-severity low,medium,high,critical '
    f'-o /out/nuclei_report.txt',
    "Nuclei Scan"
)

print("\n🎉 ALL SECURITY SCANS COMPLETED")
print("📂 Reports generated in the 'reports/' folder")


