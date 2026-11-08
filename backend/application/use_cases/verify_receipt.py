"""Verify Receipt Use Case.

Allows auditors, reviewers, and judges to mathematically verify containment receipts.
Enforces Rule 4 (UseCase with execute) and Rule 15 (typed Result DTO).
"""

from typing import Optional

from application.dtos.execution_receipt_dto import ExecutionReceiptDTO
from application.dtos.receipt_verification_dto import ReceiptVerificationResult
from infrastructure.crypto.receipt_signer import ReceiptSigner


class VerifyReceiptUseCase:
    """Verifies that an ExecutionReceipt was authentically signed by the host."""

    def __init__(self, signer: ReceiptSigner):
        self.signer = signer

    def _verify(self, receipt: ExecutionReceiptDTO) -> ReceiptVerificationResult:
        digest = receipt.digest_sha256
        signature = receipt.ed25519_signature
        public_key = receipt.public_key or self.signer.public_key_hex
        receipt_id = receipt.receipt_id

        if not digest or not signature:
            return ReceiptVerificationResult(
                is_valid=False,
                message="Missing SHA-256 digest or Ed25519 signature.",
                receipt_id=receipt_id,
                digest_sha256=digest,
            )

        is_valid = self.signer.verify_signature(
            digest_sha256=digest,
            signature_hex=signature,
            public_key_hex=public_key,
        )

        return ReceiptVerificationResult(
            is_valid=is_valid,
            message=(
                f"Receipt is cryptographically authentic (Signed with Ed25519: {signature[:16]}...)."
                if is_valid
                else "Signature verification failed. The receipt has been modified or forged."
            ),
            receipt_id=receipt_id,
            digest_sha256=digest,
        )

    async def execute(self, receipt: ExecutionReceiptDTO) -> ReceiptVerificationResult:
        """Executes cryptographic signature verification against a canonical receipt."""
        return self._verify(receipt)

    def verify_sync(self, receipt: ExecutionReceiptDTO) -> ReceiptVerificationResult:
        """Synchronous verification helper for offline audit utilities."""
        return self._verify(receipt)
