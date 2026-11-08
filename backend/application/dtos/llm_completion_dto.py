"""LLM Completion Data Transfer Object.

Carries typed language model response and usage data across infrastructure and application layers (AGENTS.md Rule 15).
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class LLMTokenUsageDTO:
    """Token consumption metrics for cost and budget enforcement."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass(frozen=True)
class LLMCompletionDTO:
    """Typed completion payload returned by LLM gateways."""

    role: str
    content: Optional[str]
    tool_calls: Optional[List[dict]]
    usage: LLMTokenUsageDTO
