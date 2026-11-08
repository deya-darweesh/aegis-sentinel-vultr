"""Domain Entities: Core business objects with unique identity."""

from .code_patch import CodePatch
from .sandbox_session import SandboxSession, SessionState
from .test_suite import TestResult, TestSuite

__all__ = [
    "CodePatch",
    "TestSuite",
    "TestResult",
    "SandboxSession",
    "SessionState",
]
