"""FastAPI Modular Monolith Entrypoint.

Vultr: Agent Rush Hackathon 2026 - Containment & Verification Foundation.
Designed for 1-click deployment on Vultr Cloud Compute (VX1).
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from api.router import ledger, router, runner, signer
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from infrastructure.config import settings
from infrastructure.persistence.database import init_db
from infrastructure.telemetry.structured_logger import configure_logger

logger = configure_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle hook for startup verification and shutdown."""
    await init_db()
    logger.info("AEGISSENTINEL: AUTONOMOUS CYBER ARENA & IMMUNITY ENGINE (VULTR) INITIALIZED")
    logger.info(
        "AegisSentinel system status",
        extra={
            "mock_mode": settings.MOCK_MODE,
            "runtime_engine": runner._detect_runtime(),
            "docker_available": runner.is_docker_available(),
            "database": settings.DATABASE_URL.split("://")[0],
            "signer_public_key": signer.public_key_hex[:24] + "...",
            "audit_ledger_initial_hash": ledger.get_latest_chain_hash()[:24] + "...",
        },
    )
    yield
    logger.info("Shutting down AegisSentinel Foundation...")


app = FastAPI(
    title="Vultr Agent Rush - Blast Radius Zero Foundation",
    description="Theme-agnostic containment, verification, and cryptographic audit engine.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local dashboards, judges' browsers, and remote test harnesses
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount presentation routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
def index_dashboard():
    """High-fidelity Cyber Arena Mission Control Dashboard for Judges and Operators."""
    template_candidates = [
        Path(__file__).parent / "templates" / "index.html",
        Path("/app/templates/index.html"),
        Path("/app/backend/templates/index.html"),
        Path("backend/templates/index.html"),
        Path("templates/index.html"),
    ]
    template_path = next((p for p in template_candidates if p.exists()), None)
    if not template_path:
        return HTMLResponse("<h1>AegisSentinel Template Not Found</h1>", status_code=500)

    html_content = template_path.read_text(encoding="utf-8")

    # Inject dynamic environment tokens into placeholders
    html_content = (
        html_content.replace("{{ RUNTIME_ENGINE }}", runner._detect_runtime())
        .replace("{{ DEFAULT_MODEL }}", settings.DEFAULT_MODEL)
        .replace("{{ LATEST_HASH }}", ledger.get_latest_chain_hash())
        .replace("{{ PUBLIC_KEY }}", signer.public_key_hex)
        .replace("{{ MOCK_MODE }}", str(settings.MOCK_MODE).lower())
    )
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
