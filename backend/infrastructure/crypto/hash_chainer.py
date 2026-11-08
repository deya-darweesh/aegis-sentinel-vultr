"""Merkle and Hash-Chaining Utility.

Computes immutable cryptographic linkage between sequential audit events.
"""

import hashlib
import json


class HashChainer:
    """Computes incremental SHA-256 hash chains."""

    GENESIS_HASH = "0" * 64

    @staticmethod
    def canonical_json(payload: dict) -> str:
        """RFC 8785 canonical JSON formatting."""
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @classmethod
    def compute_next_hash(cls, prev_hash: str, timestamp: float, event_type: str, payload: dict) -> str:
        hasher = hashlib.sha256()
        hasher.update(prev_hash.encode("ascii"))
        hasher.update(str(timestamp).encode("ascii"))
        hasher.update(event_type.encode("ascii"))
        hasher.update(cls.canonical_json(payload).encode("utf-8"))
        return hasher.hexdigest()
