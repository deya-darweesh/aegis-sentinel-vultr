"""Path Jail Guard.

Validates that any file input or generated output strictly resides within the sandbox root.
Prevents symlink escapes and directory traversal.
"""

import os
from pathlib import Path


class PathJailViolation(Exception):
    """Raised when a path escapes the designated workspace jail."""

    pass


class PathJail:
    """Enforces directory containment on host workspace mounts."""

    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_safe_path(self, target_path: Path) -> Path:
        target = Path(target_path)

        # Symlink escape check before resolution follows target
        if target.is_symlink():
            raw_link = os.readlink(target)
            link_target = Path(raw_link)
            if not link_target.is_absolute():
                link_target = (target.parent / link_target).resolve()
            else:
                link_target = link_target.resolve()
            try:
                link_target.relative_to(self.base_dir)
            except ValueError:
                raise PathJailViolation(f"Symlink Traversal Blocked: Symlink '{target}' targets outside jail -> '{link_target}'.")

        resolved = target.resolve()

        # Boundary check
        try:
            resolved.relative_to(self.base_dir)
        except ValueError:
            raise PathJailViolation(f"Path Traversal Blocked: '{target_path}' escapes sandbox jail '{self.base_dir}'.")

        return resolved
