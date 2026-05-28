"""Detecta si Maya está en ejecución (Windows)."""

from __future__ import annotations

import subprocess


def is_maya_running() -> bool:
    """True si hay al menos un proceso maya.exe activo."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq maya.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW
            if hasattr(subprocess, "CREATE_NO_WINDOW")
            else 0,
        )
        out = (result.stdout or "").lower()
        return "maya.exe" in out and "no tasks" not in out
    except (OSError, subprocess.TimeoutExpired):
        return False
