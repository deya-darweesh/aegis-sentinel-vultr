"""Application DTO for Cryptographic Receipt Verification.

Carries verified mathematical assertions across use case boundaries.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ReceiptVerificationResult:
    """Result of an Ed25519 digital signature and canonical hash verification."""

    is_valid: bool
    message: str
    receipt_id: Optional[str] = None
    digest_sha256: Optional[str] = None
