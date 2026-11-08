"""Audit Event Data Transfer Object.

Carries typed, sequential SHA-256 hash-chained telemetry records across use case and API boundaries (AGENTS.md Rule 15).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AuditEventDTO:
    """Typed DTO representing a persisted hash-chained audit event."""

    event_id: str
    timestamp: str
    task_slug: str
    event_type: str
    container_id: Optional[str]
    payload: dict
    prev_hash: str
    event_hash: str
