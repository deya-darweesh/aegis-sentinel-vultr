"""Security Violation Value Object.

Classifies and formats containment failures, breach attempts, and resource kills.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ViolationType(str, Enum):
    FILESYSTEM_WRITE_BLOCKED = "FILESYSTEM_WRITE_BLOCKED"
    NETWORK_EGRESS_BLOCKED = "NETWORK_EGRESS_BLOCKED"
    SECRET_EXFILTRATION_PROBE = "SECRET_EXFILTRATION_PROBE"
    MEMORY_OOM_KILLED = "MEMORY_OOM_KILLED"
    PID_FORK_BOMB_EXHAUSTED = "PID_FORK_BOMB_EXHAUSTED"
    WALL_CLOCK_TIMEOUT = "WALL_CLOCK_TIMEOUT"
    FORBIDDEN_AST_IMPORT = "FORBIDDEN_AST_IMPORT"
    PATH_JAIL_TRAVERSAL = "PATH_JAIL_TRAVERSAL"
    PRIVILEGE_ESCALATION_ATTEMPT = "PRIVILEGE_ESCALATION_ATTEMPT"
    UNKNOWN_ANOMALY = "UNKNOWN_ANOMALY"


@dataclass(frozen=True)
class SecurityViolation:
    """Immutable record of an intercepted security or containment event."""

    violation_type: ViolationType
    raw_message: str
    target_resource: Optional[str] = None
    exit_code: int = 1
    absorbed_safely: bool = True

    @property
    def human_readable_summary(self) -> str:
        descriptions = {
            ViolationType.FILESYSTEM_WRITE_BLOCKED: "Unauthorized disk write intercepted by read-only rootfs.",
            ViolationType.NETWORK_EGRESS_BLOCKED: "Outbound socket creation neutralized by network air-gap.",
            ViolationType.SECRET_EXFILTRATION_PROBE: "Process scanned environment; zero host secrets were revealed.",
            ViolationType.MEMORY_OOM_KILLED: "Memory allocation exceeded quota; container terminated by OOM killer.",
            ViolationType.PID_FORK_BOMB_EXHAUSTED: "Process spawn loop neutralized by cgroups PID limit.",
            ViolationType.WALL_CLOCK_TIMEOUT: "Infinite loop terminated by async execution timer.",
            ViolationType.FORBIDDEN_AST_IMPORT: "Static code analysis blocked dangerous module import before execution.",
            ViolationType.PATH_JAIL_TRAVERSAL: "Attempted symlink or path traversal outside workspace boundary.",
            ViolationType.PRIVILEGE_ESCALATION_ATTEMPT: "Setuid/privilege escalation blocked by no-new-privileges.",
            ViolationType.UNKNOWN_ANOMALY: "Anomalous execution pattern intercepted by safety monitor.",
        }
        return descriptions.get(self.violation_type, self.raw_message)
