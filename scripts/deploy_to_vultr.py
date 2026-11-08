"""AegisSentinel Vultr Server Deployment Automator.

Securely packages the production stack, transfers it via SFTP,
configures Docker and isolation kernels, and brings up AegisSentinel.
"""

import os
import tarfile
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
import paramiko
import requests

load_dotenv()

VULTR_HOST = os.getenv("VULTR_HOST", "64.177.59.95")
VULTR_USER = os.getenv("VULTR_USER", "root")
VULTR_PASS = os.getenv("VULTR_PASS")
INFERENCE_API_KEY = os.getenv("INFERENCE_API_KEY", "")

ROOT_DIR = Path(__file__).resolve().parent.parent


def create_release_archive() -> Path:
    """Create a minimal, clean tarball of production artifacts."""
    tar_path = Path(tempfile.gettempdir()) / "aegis_sentinel_release.tar.gz"
    if tar_path.exists():
        tar_path.unlink()

    included_paths = [
        "backend",
        "sandboxes",
        "docker-compose.yml",
        "Caddyfile",
        "scripts/setup_vultr_host.sh",
    ]

    with tarfile.open(tar_path, "w:gz") as tar:
        for rel_path in included_paths:
            src = ROOT_DIR / rel_path
            if src.exists():
                tar.add(src, arcname=rel_path)

    print(f"[+] Release archive created at: {tar_path} ({tar_path.stat().st_size / 1024:.1f} KB)")
    return tar_path


def run_ssh_cmd(ssh: paramiko.SSHClient, cmd: str, timeout: int = 300) -> str:
    """Run command on remote host and stream output."""
    print(f"\n[REMOTE EXEC] {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode("utf-8", errors="replace")
    err = stderr.read().decode("utf-8", errors="replace")

    if exit_status != 0:
        print(f"[!] Command failed (code {exit_status}):\nSTDOUT: {out}\nSTDERR: {err}")
        raise RuntimeError(f"Command failed: {cmd}\nExit Code: {exit_status}\n{err}")

    if out.strip():
        print(f"[OUT] {out.strip()[:500]}...")
    return out


def deploy():
    if not VULTR_PASS:
        raise ValueError("VULTR_PASS not found in environment variables.")

    print(f"[*] Connecting to Vultr Cloud Compute server ({VULTR_USER}@{VULTR_HOST})...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(VULTR_HOST, port=22, username=VULTR_USER, password=VULTR_PASS, timeout=30)
    print("[+] SSH connection established successfully.")

    # 1. System Inspection & Package Updates
    run_ssh_cmd(ssh, "uname -a")

    # 2. Check Docker installation or install
    print("[*] Verifying Docker and Docker Compose...")
    docker_check = ssh.exec_command("docker --version")[1].read().decode()
    if "Docker version" not in docker_check:
        print("[*] Docker not found. Installing Docker CE on Ubuntu...")
        run_ssh_cmd(ssh, "apt-get update -y && apt-get install -y curl ufw")
        run_ssh_cmd(ssh, "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh")
        run_ssh_cmd(ssh, "apt-get install -y docker-compose-plugin")
    else:
        print(f"[+] Found {docker_check.strip()}")

    # 3. Upload Release Archive
    tar_path = create_release_archive()
    remote_tar = "/tmp/aegis_sentinel_release.tar.gz"

    print(f"[*] Uploading release archive via SFTP to {remote_tar}...")
    sftp = ssh.open_sftp()
    sftp.put(str(tar_path), remote_tar)
    sftp.close()
    print("[+] Archive upload completed.")

    # 4. Extract into /opt/aegis-sentinel
    run_ssh_cmd(ssh, "mkdir -p /opt/aegis-sentinel && tar -xzf /tmp/aegis_sentinel_release.tar.gz -C /opt/aegis-sentinel")

    # 5. Create remote production .env
    remote_env = f"""# AegisSentinel Production Configuration - Vultr Cloud Compute
INFERENCE_API_KEY={INFERENCE_API_KEY}
VULTR_BASE_URL=https://api.vultrinference.com/v1
VULTR_MODEL=kimi-k2-instruct
VULTR_CODE_MODEL=deepseek-v4.1-flash-1017
MOCK_MODE=false
SANDBOX_IMAGE=python:3.11-slim
PREFER_GVISOR=false
WORKSPACE_DIR=./data/workspaces
LOG_DIR=./data/audit
KEY_PATH=./data/secrets/ed25519.key
HOST=0.0.0.0
PORT=8000
"""
    print("[*] Writing production .env on remote server...")
    sftp = ssh.open_sftp()
    with sftp.file("/opt/aegis-sentinel/.env", "w") as f:
        f.write(remote_env)
    sftp.close()

    # 6. Ensure data directories exist
    run_ssh_cmd(ssh, "mkdir -p /opt/aegis-sentinel/data/audit /opt/aegis-sentinel/data/secrets /opt/aegis-sentinel/data/workspaces")

    # 7. Pull base runner image
    print("[*] Pulling base runner image python:3.11-slim...")
    run_ssh_cmd(ssh, "docker pull python:3.11-slim")

    # 8. Start Stack with Docker Compose
    print("[*] Building and starting container stack with Docker Compose...")
    run_ssh_cmd(ssh, "cd /opt/aegis-sentinel && docker compose down || true")
    run_ssh_cmd(ssh, "cd /opt/aegis-sentinel && docker compose up -d --build")

    # 9. Verify Container Status
    time.sleep(5)
    run_ssh_cmd(ssh, "cd /opt/aegis-sentinel && docker compose ps")
    run_ssh_cmd(ssh, "cd /opt/aegis-sentinel && docker compose logs backend --tail=30")

    ssh.close()
    print("\n[+] Remote deployment finished successfully!")

    # 10. Live HTTP Health Verification
    print(f"[*] Testing live endpoint at http://{VULTR_HOST}/health...")
    for attempt in range(1, 6):
        try:
            resp = requests.get(f"http://{VULTR_HOST}/health", timeout=5)
            if resp.status_code == 200:
                print(f"[+] Health check PASSED: {resp.json()}")
                break
        except Exception as e:
            print(f"[-] Attempt {attempt}/5: Health check waiting ({e}). Retrying in 3s...")
            time.sleep(3)


if __name__ == "__main__":
    deploy()
