"""Code Patch Entity.

Represents code under verification, its AST safety classification, and SHA-256 fingerprint.
"""

import hashlib
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class CodePatch:
    """An autonomous code artifact submitted for verification and quarantine testing."""

    patch_id: str
    target_file: str
    code_content: str
    language: str = "python"
    author_agent: str = "synthesizer"  # e.g., kimi-k2-instruct
    ast_safe: bool = False
    ast_warnings: List[str] = field(default_factory=list)

    @property
    def sha256_hash(self) -> str:
        """Computes unambiguous SHA-256 hash of the normalized code."""
        normalized = self.code_content.strip().encode("utf-8")
        return hashlib.sha256(normalized).hexdigest()

    @property
    def line_count(self) -> int:
        return len(self.code_content.splitlines())

    def mark_ast_validated(self, is_safe: bool, warnings: Optional[List[str]] = None) -> None:
        self.ast_safe = is_safe
        if warnings:
            self.ast_warnings.extend(warnings)
