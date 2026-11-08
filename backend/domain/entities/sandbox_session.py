"""Sandbox Session Entity.

Represents an ephemeral quarantined execution environment and its state transitions.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from domain.values.containment_policy import ContainmentPolicy
from domain.values.security_violation import SecurityViolation


class SessionState(str, Enum):
    PROVISIONING = "PROVISIONING"
    READY = "READY"
    EXECUTING = "EXECUTING"
    CONTAINED = "CONTAINED"
    TERMINATED = "TERMINATED"
    FAILED = "FAILED"


@dataclass
class SandboxSession:
    """An isolated task-bound sandbox container instance."""

    session_id: str
    container_name: str
    policy: ContainmentPolicy
    runtime: str = "runsc"  # Defaults to gVisor
    state: SessionState = SessionState.PROVISIONING
    created_at: float = field(default_factory=time.time)
    terminated_at: Optional[float] = None
    exit_code: Optional[int] = None
    peak_memory_mb: float = 0.0
    violations: List[SecurityViolation] = field(default_factory=list)

    @property
    def is_active(self) -> bool:
        return self.state in (SessionState.READY, SessionState.EXECUTING)

    @property
    def lifetime_seconds(self) -> float:
        end = self.terminated_at or time.time()
        return round(end - self.created_at, 2)

    def transition_to(self, new_state: SessionState):
        """Enforces legal state transitions."""
        legal_transitions = {
            SessionState.PROVISIONING: [SessionState.READY, SessionState.FAILED],
            SessionState.READY: [SessionState.EXECUTING, SessionState.TERMINATED],
            SessionState.EXECUTING: [SessionState.READY, SessionState.CONTAINED, SessionState.TERMINATED, SessionState.FAILED],
            SessionState.CONTAINED: [SessionState.TERMINATED],
            SessionState.TERMINATED: [],
            SessionState.FAILED: [SessionState.TERMINATED],
        }
        if new_state not in legal_transitions.get(self.state, []):
            raise ValueError(f"Illegal state transition from {self.state} to {new_state}")
        self.state = new_state
        if new_state == SessionState.TERMINATED:
            self.terminated_at = time.time()

    def record_violation(self, violation: SecurityViolation):
        self.violations.append(violation)
        self.transition_to(SessionState.CONTAINED)
