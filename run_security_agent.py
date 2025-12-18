import os
import subprocess
import time


def wait_for_app_via_docker_network(
    target_url: str,
    network: str = "zap-network",
    timeout: int = 180,
):
    """
    Wait for the app to become reachable by running curl INSIDE a container attached
    to the same Docker network as the app (so hostnames like 'test-app' resolve).
    """
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
        # Don't raise; still generate/upload whatever reports we have.
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

# Wait until app is reachable (from within Docker network)
wait_for_app_via_docker_network(TARGET_URL, network=NETWORK_NAME, timeout=180)

# =============================
# Semgrep (SAST)
# =============================
run(
    f'docker run --rm '
    f'-v "{REPO_DIR}:/src" '
    f'-v "{REPORTS_DIR}:/reports" '
    f'semgrep/semgrep semgrep --config=auto /src --json -o /reports/semgrep_report.json',
    "Semgrep (SAST) Scan",
)

# =============================
# OWASP ZAP (DAST) - FINAL FIX
# =============================
# Fixes:
# - Run as root to avoid permission denied on mounted volume.
# - Mount reports/ directly to /zap/wrk because baseline automation writes there.
# - Report written inside /zap/wrk -> appears in reports/ on runner.
# - -I prevents failing due to WARNs, but report is still generated.
run(
    f'docker run --rm '
    f'--user 0 '
    f'-v "{REPORTS_DIR}:/zap/wrk" '
    f'--network {NETWORK_NAME} '
    f'zaproxy/zap-stable zap-baseline.py '
    f'-t "{TARGET_URL}" '
    f'-I '
    f'-r zap_report.html '
    f'-T 120',
    "OWASP ZAP (DAST) Scan",
)

# =============================
# Nuclei - FINAL FIX
# =============================
# Fix:
# - Do NOT mount reports/ to /root (prevents nuclei-templates in reports => EACCES on upload).
# - Mount to /out and only write the output file.
run(
    f'docker run --rm '
    f'-v "{REPORTS_DIR}:/out" '
    f'--network {NETWORK_NAME} '
    f'projectdiscovery/nuclei '
    f'-u "{TARGET_URL}" '
    f'-severity low,medium,high,critical '
    f'-o /out/nuclei_report.txt',
    "Nuclei Scan",
)

print("\n🎉 ALL SECURITY SCANS COMPLETED")
print("📂 Reports generated in the 'reports/' folder")


