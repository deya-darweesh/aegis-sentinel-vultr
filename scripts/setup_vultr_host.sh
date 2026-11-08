#!/usr/bin/env bash
# ==============================================================================
# Vultr Cloud Compute (VX1) 1-Click Host Provisioning Script
# Vultr: Agent Rush Hackathon 2026 (Co-located with KubeCon NA)
# Installs Docker, gVisor (runsc), Caddy, registers sandbox image, and starts stack.
# ==============================================================================

set -euo pipefail

echo "======================================================================"
echo "  PROVISIONING VULTR CLOUD COMPUTE HOST (BLAST RADIUS ZERO FOUNDATION) "
echo "======================================================================"

# 1. Update OS Packages
export DEBIAN_FRONTEND=noninteractive
apt-get update && apt-get upgrade -y
apt-get install -y curl wget git jq ca-certificates gnupg lsb-release

# 2. Install Docker CE
if ! command -v docker &> /dev/null; then
    echo "--> Installing Docker CE..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" > /etc/apt/sources.list.d/docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# 3. Install gVisor (runsc) for kernel-level sandbox isolation
if ! command -v runsc &> /dev/null; then
    echo "--> Installing gVisor (runsc)..."
    ARCH=$(uname -m)
    URL="https://storage.googleapis.com/gvisor/releases/release/latest/${ARCH}"
    wget "${URL}/runsc" -O /usr/local/bin/runsc
    wget "${URL}/runsc.sha512" -O /usr/local/bin/runsc.sha512
    cd /usr/local/bin && sha512sum -c runsc.sha512 && rm runsc.sha512
    chmod a+rx /usr/local/bin/runsc

    # Register runsc in Docker daemon
    echo "--> Registering gVisor runtime in /etc/docker/daemon.json..."
    mkdir -p /etc/docker
    cat <<EOF > /etc/docker/daemon.json
{
  "runtimes": {
    "runsc": {
      "path": "/usr/local/bin/runsc",
      "runtimeArgs": [
        "--ignore-cgroups=false",
        "--network=none"
      ]
    }
  }
}
EOF
    systemctl restart docker
    echo "--> gVisor (runsc) registered and active!"
fi

# 4. Prepare Directories and Data Persistence
cd "$(dirname "$0")/.."
mkdir -p data
touch data/audit_log.jsonl

# 5. Build Base Runner Image
echo "--> Building base sandbox quarantine runner image (vultr-agent-runner)..."
docker build -t vultr-agent-runner:latest sandboxes/base-runner/

# 6. Launch Production Modular Monolith
echo "--> Starting Containment Monolith & Caddy Auto-SSL Reverse Proxy..."
docker compose up -d --build

echo "======================================================================"
echo "  DEPLOYMENT COMPLETE! HOST STATUS:"
echo "  - Backend Port:   8000"
echo "  - Public HTTPS:   443 (Managed by Caddy)"
echo "  - gVisor Engine:  $(runsc --version | head -n 1)"
echo "  - Mock Mode:      ACTIVE ($0.00 credit burn during testing)"
echo "======================================================================"
