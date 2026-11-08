"""Secret Scrubber Domain Service.

Enforces Pillar 2: Secret Hygiene.
Detects, strips, and blocks sensitive tokens (Vultr API keys, passwords, bearer tokens)
from ever being passed into the sandbox environment or logged unmasked.
"""

import re
from typing import List, Set, Tuple


class SecretScrubber:
    """Scans and scrubs sensitive credentials from text payloads and environments."""

    SECRET_PATTERNS = [
        re.compile(r"vultr[_-]?inference[_-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,})['\"]?", re.IGNORECASE),
        re.compile(r"api[_-]?key\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?", re.IGNORECASE),
        re.compile(r"sk-[A-Za-z0-9]{20,}", re.IGNORECASE),
        re.compile(r"ghp_[A-Za-z0-9]{36}", re.IGNORECASE),
        re.compile(r"Bearer\s+([A-Za-z0-9_\-\.]{20,})", re.IGNORECASE),
        re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", re.IGNORECASE),
    ]

    SENSITIVE_ENV_KEYS: Set[str] = {
        "VULTR_INFERENCE_API_KEY",
        "INFERENCE_API_KEY",
        "OPENAI_API_KEY",
        "AWS_SECRET_ACCESS_KEY",
        "GITHUB_TOKEN",
        "DATABASE_URL",
        "POSTGRES_PASSWORD",
        "SECRET_KEY",
    }

    def detect_secrets(self, text: str) -> List[str]:
        """Returns detected secret snippets or key names."""
        found = []
        for pattern in self.SECRET_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                found.append(f"Secret matched pattern: {pattern.pattern[:30]}...")
        return found

    def sanitize_text(self, text: str) -> str:
        """Replaces detected credentials with redaction markers."""
        sanitized = text
        for pattern in self.SECRET_PATTERNS:
            sanitized = pattern.sub("[REDACTED_BY_SECRET_HYGIENE_PILLAR]", sanitized)
        return sanitized

    def filter_environment(self, env_dict: dict) -> dict:
        """Strips all sensitive environment variables from container injection payloads."""
        sanitized_env = {}
        for k, v in env_dict.items():
            upper_k = k.upper()
            if upper_k in self.SENSITIVE_ENV_KEYS or "KEY" in upper_k or "SECRET" in upper_k or "TOKEN" in upper_k or "PASS" in upper_k:
                # Do NOT pass to container!
                continue
            sanitized_env[k] = v
        return sanitized_env
