"""
Código ejecutado DENTRO de Maya (GUI).
Lo invoca el launcher externo vía MEL/python o commandPort.
"""

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _reload_project_modules() -> None:
    """Quita módulos cacheados para que un relanzamiento recargue cambios."""
    prefixes = ("modules.", "terrain.", "core.", "ui.", "layers.", "launcher.")
    for name in list(sys.modules):
        if name.startswith(prefixes) or name == "main":
            del sys.modules[name]


def run_plugin() -> None:
    _reload_project_modules()

    import runpy

    runpy.run_path(os.path.join(_ROOT, "main.py"), run_name="__main__")


run_plugin()
