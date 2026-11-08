"""Combat Duel DTOs for AegisSentinel Maker-Breaker Duels."""

from dataclasses import dataclass, field
from typing import List, Optional

from application.dtos.execution_receipt_dto import ExecutionReceiptDTO


@dataclass(frozen=True)
class CombatDuelRequest:
    """Input DTO for initiating an autonomous security duel."""

    task_slug: str
    scenario_preset: str = "SUPPLY_CHAIN_BACKDOOR"  # SUPPLY_CHAIN_BACKDOOR | FORK_MEMORY_EXHAUSTION | FINANCIAL_INVARIANT_TAMPER | CUSTOM
    target_code: Optional[str] = None
    max_rounds: int = 3


@dataclass(frozen=True)
class CombatRoundResultDTO:
    """DTO representing one adversarial round outcome."""

    round_number: int
    stage: str  # RED_ATTACK | BLUE_PATCH | RETALIATION_VERIFIED
    agent_name: str
    code_snippet: str
    exit_code: int
    intercepted: bool
    interception_reason: Optional[str]
    stdout: str
    stderr: str
    duration_ms: float


@dataclass(frozen=True)
class CombatDuelResultDTO:
    """Output DTO summarizing the completed combat match."""

    mission_id: str
    task_slug: str
    status: str
    rounds: List[CombatRoundResultDTO] = field(default_factory=list)
    immunity_achieved: bool = False
    receipt: Optional[ExecutionReceiptDTO] = None
    summary: str = ""
