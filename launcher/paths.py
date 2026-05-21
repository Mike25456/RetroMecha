"""Rutas del proyecto RetroMecha."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LAUNCHER_DIR = PROJECT_ROOT / "launcher"
BOOTSTRAP_PY = LAUNCHER_DIR / "bootstrap_in_maya.py"
LOCAL_CONFIG = PROJECT_ROOT / "retromecha.local.json"
