"""Audit Ledger Port Protocol.

Defines the interface for append-only SHA-256 hash-chained telemetry and receipt persistence.
"""

from typing import List, Optional, Protocol

from application.dtos.audit_event_dto import AuditEventDTO
from application.dtos.execution_receipt_dto import ExecutionReceiptDTO
from domain.values.execution_receipt import ExecutionReceipt


class IAuditLedger(Protocol):
    """Protocol for immutable cryptographic event logging and receipt storage."""

    def append_event(
        self,
        event_id: str,
        task_slug: str,
        event_type: str,
        payload: dict,
        container_id: Optional[str] = None,
    ) -> str:
        """Appends an event to the hash chain and returns the updated chain hash."""
        ...

    def get_latest_chain_hash(self) -> str:
        """Returns the current head SHA-256 hash."""
        ...

    def persist_receipt(self, receipt: ExecutionReceipt) -> None:
        """Persists the signed containment receipt."""
        ...

    def get_receipt(self, receipt_id: str) -> Optional[ExecutionReceiptDTO]:
        """Retrieves a persisted receipt by ID."""
        ...

    def list_recent_events(self, limit: int = 50) -> List[AuditEventDTO]:
        """Lists recent audit events with hash-chain continuity."""
        ...
