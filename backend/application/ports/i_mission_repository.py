"""Mission Repository Port Protocol.

Defines persistence interface for missions, exploits, patches, and receipts.
"""

from typing import List, Optional, Protocol


class IMissionRepository(Protocol):
    """Protocol for persisting and querying mission state."""

    async def save_mission(
        self,
        mission_id: str,
        task_slug: str,
        status: str,
        tokens_used: int,
    ) -> None:
        """Persists or updates high-level mission metadata."""
        ...

    async def save_exploit(
        self,
        mission_id: str,
        exploit_id: str,
        round_number: int,
        attack_vector: str,
        code_payload: str,
        exit_code: int,
        intercepted: bool,
    ) -> None:
        """Persists an adversarial exploit execution record."""
        ...

    async def save_patch(
        self,
        mission_id: str,
        patch_id: str,
        round_number: int,
        diff_content: str,
        ast_safe: bool,
        all_passed: bool,
    ) -> None:
        """Persists a synthesized patch verification record."""
        ...

    async def save_receipt(
        self,
        mission_id: str,
        digest_sha256: str,
        ed25519_sig: str,
        public_key: str,
        runtime_engine: str,
        duration_ms: float,
        memory_peak_mb: float,
    ) -> None:
        """Persists the final cryptographic immunity receipt."""
        ...

    async def save_audit_event(
        self,
        mission_id: str,
        event_type: str,
        event_hash: str,
        prev_hash: str,
        payload: dict,
    ) -> None:
        """Persists an individual hash-chained audit event."""
        ...

    async def get_mission(self, mission_id: str) -> Optional[dict]:
        """Retrieves a mission and its related entities."""
        ...

    async def list_recent_missions(self, limit: int = 20) -> List[dict]:
        """Retrieves a list of recent mission summaries."""
        ...
