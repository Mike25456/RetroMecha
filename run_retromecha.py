#!/usr/bin/env python3
"""
RetroMecha — Lanzador desde el proyecto (sin bridge de VS Code).

Uso:
  python run_retromecha.py
  Doble clic en "Run RetroMecha.bat"

Comportamiento:
  • Maya cerrado  → abre Maya y carga el plugin
  • Maya abierto  → envía el plugin a la sesión actual (Windows: maya -script)
"""

from __future__ import annotations

import sys

# Asegurar imports del paquete launcher
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from launcher.maya_runner import run_retromecha  # noqa: E402


def main() -> int:
    print("=" * 50)
    print("  RetroMecha — Lanzador")
    print("=" * 50)
    return run_retromecha()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
