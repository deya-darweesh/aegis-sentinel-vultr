"""Execution Receipt Data Transfer Object.

Carries typed, tamper-proof containment receipt data across use case and API boundaries (AGENTS.md Rule 15).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExecutionReceiptDTO:
    """Verifiable proof-carrying receipt of an execution or containment event."""

    receipt_id: str
    timestamp: str
    task_slug: str
    status: str
    exit_code: int
    duration_ms: float
    memory_peak_mb: float
    runtime_engine: str
    container_id: str
    digest_sha256: str
    ed25519_signature: Optional[str] = None
    public_key: Optional[str] = None
    violation: Optional[str] = None

    def to_dict(self) -> dict:
        """Converts the typed receipt to a concrete dictionary representation."""
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "task_slug": self.task_slug,
            "status": self.status,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "memory_peak_mb": self.memory_peak_mb,
            "runtime_engine": self.runtime_engine,
            "container_id": self.container_id,
            "digest_sha256": self.digest_sha256,
            "ed25519_signature": self.ed25519_signature,
            "public_key": self.public_key,
            "violation": self.violation,
        }
