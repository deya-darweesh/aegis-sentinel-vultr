"""Containment Policy Value Object.

Enforces the 4 Mandatory Containment Pillars:
1. Process Isolation (dropped caps, non-root uid, read-only root)
2. Secret Hygiene (zero host environment leakage)
3. Resource Limits (RAM ceiling, CPU throttle, PID limit, wall-clock timeout)
4. Lifecycle Discipline (ephemeral tmpfs, unprivileged user)
"""

from dataclasses import dataclass
from typing import Tuple


class SecurityViolationError(Exception):
    """Raised when a containment policy violates blast-radius domain invariants."""

    pass


@dataclass(frozen=True)
class ContainmentPolicy:
    """Immutable security and resource boundary specification."""

    memory_limit_mb: int = 256
    cpu_limit: float = 0.5
    pids_limit: int = 64
    timeout_seconds: int = 15
    network_enabled: bool = False
    read_only_root: bool = True
    drop_all_capabilities: bool = True
    no_new_privileges: bool = True
    user_uid: int = 65534  # nobody
    user_gid: int = 65534  # nogroup
    tmpfs_mount: str = "/tmp:rw,noexec,nosuid,size=64m"
    allowed_syscall_filter: Tuple[str, ...] = ("default",)
    is_chaos_probe: bool = False

    def __post_init__(self):
        # Invariant 1: Memory cap strictly bounded between 32MB and 512MB
        if not (32 <= self.memory_limit_mb <= 512):
            raise SecurityViolationError(f"Memory limit {self.memory_limit_mb}MB violates domain policy (must be 32-512MB).")

        # Invariant 2: CPU quota cannot exceed 1.0 core on shared compute
        if not (0.1 <= self.cpu_limit <= 1.0):
            raise SecurityViolationError(f"CPU limit {self.cpu_limit} violates domain policy (must be 0.1-1.0 cores).")

        # Invariant 3: PIDs limit strictly bounded to stop fork-bombs
        if not (8 <= self.pids_limit <= 128):
            raise SecurityViolationError(f"PIDs limit {self.pids_limit} violates fork-bomb defense policy (must be 8-128).")

        # Invariant 4: Wall-clock timeout strictly capped at 30 seconds
        if not (1 <= self.timeout_seconds <= 30):
            raise SecurityViolationError(f"Timeout {self.timeout_seconds}s violates domain policy (must be 1-30s).")

        # Invariant 5: Root filesystem MUST be read-only in code execution mode
        if not self.read_only_root:
            raise SecurityViolationError("Root filesystem must be mounted read-only.")

        # Invariant 6: Must drop all Linux capabilities
        if not self.drop_all_capabilities:
            raise SecurityViolationError("All Linux capabilities must be dropped (--cap-drop=ALL).")

        # Invariant 7: Deny privilege escalation
        if not self.no_new_privileges:
            raise SecurityViolationError("Privilege escalation must be denied (no-new-privileges).")

        # Invariant 8: Non-root execution strictly required
        if self.user_uid == 0 or self.user_gid == 0:
            raise SecurityViolationError(f"Container execution as root (UID {self.user_uid}) is strictly prohibited.")

    @classmethod
    def strict_airgap(cls) -> "ContainmentPolicy":
        """Pre-configured standard policy for Pattern A (air-gapped code sandbox)."""
        return cls(
            memory_limit_mb=256,
            cpu_limit=0.5,
            pids_limit=64,
            timeout_seconds=15,
            network_enabled=False,
            read_only_root=True,
            drop_all_capabilities=True,
            no_new_privileges=True,
            user_uid=65534,
            user_gid=65534,
        )

    @classmethod
    def chaos_stress_test(cls) -> "ContainmentPolicy":
        """Strict policy specifically calibrated for the mandatory Chaos Test."""
        return cls(
            memory_limit_mb=128,
            cpu_limit=0.25,
            pids_limit=32,
            timeout_seconds=10,
            network_enabled=False,
            read_only_root=True,
            drop_all_capabilities=True,
            no_new_privileges=True,
            user_uid=65534,
            user_gid=65534,
            is_chaos_probe=True,
        )
