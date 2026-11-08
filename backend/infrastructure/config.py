"""Application and Infrastructure Configuration.

Enforces cost controls and credit preservation ($200 Vultr Credits) by defaulting
to MOCK_MODE=True for local development.
"""

import os
from pathlib import Path

from pydantic import BaseModel


class Settings(BaseModel):
    # Vultr Serverless Inference settings
    INFERENCE_API_KEY: str = os.getenv("INFERENCE_API_KEY", os.getenv("VULTR_INFERENCE_API_KEY", ""))
    VULTR_BASE_URL: str = os.getenv("VULTR_BASE_URL", "https://api.vultrinference.com/v1")
    DEFAULT_MODEL: str = os.getenv("VULTR_MODEL", "kimi-k2-instruct")
    CODE_MODEL: str = os.getenv("VULTR_CODE_MODEL", "deepseek-v4.1-flash-1017")

    # CRITICAL: Default to MOCK_MODE=True to preserve $200 credits during development
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")

    # Sandbox execution settings
    SANDBOX_BASE_IMAGE: str = os.getenv("SANDBOX_IMAGE", "vultr-sandbox-runner:latest")
    PREFER_GVISOR: bool = os.getenv("PREFER_GVISOR", "true").lower() in ("true", "1", "yes")
    WORKSPACE_DIR: Path = Path(os.getenv("WORKSPACE_DIR", "./data/workspaces")).resolve()

    # Telemetry and Security persistence
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", "./data/audit")).resolve()
    KEY_PATH: Path = Path(os.getenv("KEY_PATH", "./data/secrets/ed25519.key")).resolve()
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{Path('./data/audit/aegis_sentinel.db').resolve().as_posix()}",
    )

    # Host settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))


settings = Settings()

# Ensure directories exist
settings.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
settings.KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
