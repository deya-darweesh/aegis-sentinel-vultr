"""Audit Report Generator Port Protocol.

ENG-STD-001 & AGENTS.md Rule 3: One Protocol per file with I prefix.
"""

from typing import Optional, Protocol


class IAuditReportGenerator(Protocol):
    """Port defining the cryptographic PDF audit report generation capability."""

    def generate_report_bytes(
        self,
        mission_id: str,
        task_slug: str,
        status: str,
        runtime_engine: str,
        public_key: str,
        signature_hex: str,
        chain_hash: str,
        duration_ms: float,
        memory_mb: float,
        attack_vector: str,
        red_code: Optional[str] = None,
        blue_code: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> bytes:
        """Assembles a print-ready cryptographic audit report and returns raw PDF bytes."""
        ...
