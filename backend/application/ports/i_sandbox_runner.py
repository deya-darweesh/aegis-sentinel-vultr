"""Sandbox Runner Port Protocol.

Defines the interface for quarantined script execution.
"""

from dataclasses import dataclass
from typing import Awaitable, Callable, Optional, Protocol

from domain.values.containment_policy import ContainmentPolicy
from domain.values.security_violation import SecurityViolation


@dataclass(frozen=True)
class ExecutionOutput:
    """Immutable execution outcome from the sandbox runner."""

    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    peak_memory_mb: float
    container_id: str
    runtime_used: str
    violation: Optional[SecurityViolation] = None


class ISandboxRunner(Protocol):
    """Protocol for executing code in a hardened quarantine container."""

    def detect_runtime(self) -> str:
        """Returns the active container execution runtime (e.g. 'runsc' or 'runc')."""
        ...

    def is_docker_available(self) -> bool:
        """Checks if container virtualization daemon is accessible."""
        ...

    async def run_quarantined_script(
        self,
        script_code: str,
        policy: ContainmentPolicy,
        session_id: str,
        on_stdout_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
        on_stderr_chunk: Optional[Callable[[str], Awaitable[None]]] = None,
    ) -> ExecutionOutput: ...
