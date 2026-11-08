"""SecOps Copilot Application DTOs.

ENG-STD-001 & AGENTS.md Rule 15: Typed frozen dataclass crossing use case boundaries.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SecOpsCopilotRequest:
    """Carries operator intent, conversational prompt, and optional code across use case boundary."""

    message: str
    code_snippet: Optional[str] = None
    session_id: Optional[str] = None


@dataclass(frozen=True)
class SecOpsCopilotResult:
    """Structured SecOps analysis, threat assessment, and cryptographic attestation."""

    reply: str
    mission_id: str
    scenario: str
    status: str
    cvss_score: str
    red_findings: str
    blue_patch: str
    pdf_report_url: str
    voice_alert_url: str
    duration_ms: float
    memory_peak_mb: float
    digest_sha256: str
    ed25519_signature: str
