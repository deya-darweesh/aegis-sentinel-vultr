"""Ed25519 Cryptographic Receipt Signer.

Provides digital signatures for ExecutionReceipts and verifies integrity.
"""

from pathlib import Path
from typing import Optional

from infrastructure.config import settings
from nacl.encoding import HexEncoder
from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey


class ReceiptSigner:
    """Manages the host Ed25519 private/public keypair."""

    def __init__(self, key_path: Optional[Path] = None):
        self.key_path = key_path or settings.KEY_PATH
        self.signing_key = self._load_or_generate_key()
        self.verify_key = self.signing_key.verify_key

    def _load_or_generate_key(self) -> SigningKey:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            seed = self.key_path.read_bytes()
            return SigningKey(seed)

        # Generate fresh seed
        new_key = SigningKey.generate()
        self.key_path.write_bytes(new_key.encode())
        return new_key

    @property
    def public_key_hex(self) -> str:
        return self.verify_key.encode(encoder=HexEncoder).decode("ascii")

    def sign_digest(self, digest_sha256: str) -> str:
        """Signs a canonical SHA-256 hash using Ed25519 and returns 128-char hex."""
        signed = self.signing_key.sign(digest_sha256.encode("ascii"))
        return HexEncoder.encode(signed.signature).decode("ascii")

    def verify_signature(self, digest_sha256: str, signature_hex: str, public_key_hex: Optional[str] = None) -> bool:
        """Verifies an Ed25519 signature against a digest."""
        try:
            vk = VerifyKey(public_key_hex.encode("ascii"), encoder=HexEncoder) if public_key_hex else self.verify_key
            sig_bytes = HexEncoder.decode(signature_hex.encode("ascii"))
            vk.verify(digest_sha256.encode("ascii"), sig_bytes)
            return True
        except BadSignatureError:
            return False
        except Exception:
            return False
