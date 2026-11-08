"""AST Blast Radius Guard Domain Service.

Deterministic Python Abstract Syntax Tree (AST) analyzer.
Intercepts dangerous imports, syscalls, and privilege escalation vectors
BEFORE code reaches the sandbox container.
"""

import ast
from dataclasses import dataclass, field
from typing import List, Set


@dataclass
class ASTScanResult:
    is_safe: bool
    violations: List[str] = field(default_factory=list)
    imported_modules: Set[str] = field(default_factory=set)
    has_dangerous_calls: bool = False


class ASTBlastRadiusGuard:
    """Statically verifies that agent-generated code respects blast radius limits."""

    FORBIDDEN_MODULES: Set[str] = {
        "ctypes",
        "pty",
        "socket",
        "subprocess",
        "posix",
        "multiprocessing",
        "winreg",
        "pickle",
        "shelve",
    }

    FORBIDDEN_CALLS: Set[str] = {
        "eval",
        "exec",
        "compile",
        "__import__",
        "fork",
        "kill",
        "system",
        "popen",
    }

    def inspect_code(self, source_code: str) -> ASTScanResult:
        """Parses Python source and returns safety classification."""
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            return ASTScanResult(
                is_safe=False,
                violations=[f"SYNTAX_ERROR: Code cannot be parsed: {e.msg} at line {e.lineno}"],
            )

        violations: List[str] = []
        imported_modules: Set[str] = set()
        has_dangerous_calls = False

        for node in ast.walk(tree):
            # 1. Inspect import statements (import foo)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_pkg = alias.name.split(".")[0]
                    imported_modules.add(root_pkg)
                    if root_pkg in self.FORBIDDEN_MODULES:
                        violations.append(f"FORBIDDEN_IMPORT: Import of dangerous module '{root_pkg}' is blocked at line {node.lineno}.")

            # 2. Inspect from-import statements (from foo import bar)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_pkg = node.module.split(".")[0]
                    imported_modules.add(root_pkg)
                    if root_pkg in self.FORBIDDEN_MODULES:
                        violations.append(
                            f"FORBIDDEN_IMPORT: From-import of dangerous module '{root_pkg}' is blocked at line {node.lineno}."
                        )

            # 3. Inspect dangerous function calls (eval, exec, os.system, os.fork)
            elif isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in self.FORBIDDEN_CALLS:
                    has_dangerous_calls = True
                    violations.append(f"FORBIDDEN_CALL: Execution of dangerous function '{func_name}' is blocked at line {node.lineno}.")

        is_safe = len(violations) == 0
        return ASTScanResult(
            is_safe=is_safe,
            violations=violations,
            imported_modules=imported_modules,
            has_dangerous_calls=has_dangerous_calls,
        )
