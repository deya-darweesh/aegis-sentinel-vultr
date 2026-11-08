"""Execution Receipt Value Object.

Represents an immutable, cryptographically verifiable containment receipt.
Contains SHA-256 fingerprints of inputs, patch, assertions, and execution telemetry.
"""

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SecurityStatus(str, Enum):
    MATHEMATICALLY_VERIFIED = "MATHEMATICALLY_VERIFIED"
    CONTAINMENT_TRIGGERED = "CONTAINMENT_TRIGGERED"
    ASSERTION_FAILED = "ASSERTION_FAILED"
    POLICY_REJECTED = "POLICY_REJECTED"


@dataclass(frozen=True)
class ExecutionReceipt:
    """Verifiable proof-carrying receipt of an execution or containment event."""

    receipt_id: str
    timestamp: str
    task_slug: str
    status: SecurityStatus
    exit_code: int
    duration_ms: float
    memory_peak_mb: float
    runtime_engine: str
    container_id: str
    input_sha256: str
    patch_sha256: str
    audit_chain_hash: str
    ed25519_signature: Optional[str] = None
    violation: Optional[str] = None

    def compute_canonical_digest(self) -> str:
        """Produces RFC 8785 deterministic JSON representation and returns SHA-256."""
        payload = {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "task_slug": self.task_slug,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "memory_peak_mb": self.memory_peak_mb,
            "runtime_engine": self.runtime_engine,
            "container_id": self.container_id,
            "input_sha256": self.input_sha256,
            "patch_sha256": self.patch_sha256,
            "audit_chain_hash": self.audit_chain_hash,
            "violation": self.violation,
        }
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()

    def with_signature(self, signature: str) -> "ExecutionReceipt":
        """Returns a new immutable ExecutionReceipt instance carrying the Ed25519 signature."""
        import dataclasses

        return dataclasses.replace(self, ed25519_signature=signature)

    def to_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "task_slug": self.task_slug,
            "status": self.status.value,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "memory_peak_mb": self.memory_peak_mb,
            "runtime_engine": self.runtime_engine,
            "container_id": self.container_id,
            "digest_sha256": self.compute_canonical_digest(),
            "ed25519_signature": self.ed25519_signature,
            "violation": self.violation,
        }
