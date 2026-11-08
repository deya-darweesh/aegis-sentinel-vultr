# Base Quarantine Execution Image for Vultr Agent Rush Hackathon
# Enforces the 4 Containment Pillars:
# 1. Ephemeral & Minimal (Python 3.12 Alpine)
# 2. Non-root user: nobody:nogroup (UID 65534: GID 65534)
# 3. Read-only root compatibility (tmpfs scratchpad on /tmp)
# 4. Zero secret pollution

FROM python:3.12-alpine

# Install pytest for deterministic test suite execution
RUN pip install --no-cache-dir pytest

# Create dedicated isolated workspace owned by nobody
WORKDIR /workspace
RUN chown -R nobody:nogroup /workspace

# Set default unprivileged user
USER 65534:65534

# Default invocation runs python in unbuffered mode
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python3", "-c", "print('Quarantine runner ready')"]
