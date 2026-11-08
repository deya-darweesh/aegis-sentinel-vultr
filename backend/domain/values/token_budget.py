"""Token Budget Value Object.

Enforces strict cost controls and credit preservation ($200 Vultr Credits).
Guarantees that development and test loops never drain inference credits.
"""

from dataclasses import dataclass


class TokenBudgetExceededError(Exception):
    """Raised when an inference call or mission exceeds credit safety thresholds."""

    pass


@dataclass(frozen=True)
class TokenBudget:
    """Enforces per-call and cumulative token ceilings to protect the $200 credit pool."""

    max_tokens_per_call: int = 512
    max_tokens_per_mission: int = 2048
    max_calls_per_mission: int = 5
    estimated_cost_per_1k_tokens_usd: float = 0.0008  # Vultr Serverless Inference average

    def __post_init__(self):
        # Strict cost-preservation invariants:
        # Never allow a single call to request unbounded tokens in development
        if self.max_tokens_per_call > 1024:
            raise TokenBudgetExceededError(
                f"Per-call token ceiling of {self.max_tokens_per_call} exceeds development safety limit (max 1024)."
            )
        if self.max_calls_per_mission > 10:
            raise TokenBudgetExceededError(
                f"Mission call limit of {self.max_calls_per_mission} violates credit runaway protection (max 10)."
            )

    def validate_request(self, requested_max_tokens: int) -> int:
        """Returns safe clamped token count."""
        return min(requested_max_tokens, self.max_tokens_per_call)

    def estimate_mission_cost_usd(self, tokens_used: int) -> float:
        """Calculates estimated cost against Vultr credits."""
        return round((tokens_used / 1000.0) * self.estimated_cost_per_1k_tokens_usd, 6)

    @classmethod
    def development_safe(cls) -> "TokenBudget":
        """Conservative preset prioritizing credit conservation."""
        return cls(
            max_tokens_per_call=512,
            max_tokens_per_mission=2048,
            max_calls_per_mission=5,
        )

    @classmethod
    def live_evaluation(cls) -> "TokenBudget":
        """Production preset for official judge evaluations."""
        return cls(
            max_tokens_per_call=1024,
            max_tokens_per_mission=4096,
            max_calls_per_mission=8,
        )
