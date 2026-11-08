"""Application Data Transfer Objects (DTOs) for Sandboxed Task Execution.

Carries typed data across use case and presentation boundaries (AGENTS.md Rule 15).
"""

from dataclasses import dataclass
from typing import Optional

from application.dtos.execution_receipt_dto import ExecutionReceiptDTO
from domain.values.containment_policy import ContainmentPolicy


@dataclass(frozen=True)
class TaskExecutionRequest:
    """Request DTO to initiate a quarantined execution task."""

    task_slug: str
    code_content: str
    target_file: str = "main.py"
    policy: Optional[ContainmentPolicy] = None


@dataclass(frozen=True)
class TaskExecutionResult:
    """Result DTO returned upon task execution completion."""

    mission_id: str
    status: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    receipt: ExecutionReceiptDTO
    is_success: bool
    violation: Optional[str] = None
