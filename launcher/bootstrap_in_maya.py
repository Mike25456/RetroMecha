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
    prefixes = (
        "modules.",
        "terrain.",
        "core.",
        "ui.",
        "layers.",
        "utils.",
        "launcher.",
    )
    for name in list(sys.modules):
        if name.startswith(prefixes) or name == "main":
            del sys.modules[name]


def run_plugin() -> None:
    _reload_project_modules()
    import main as retromecha_main
    retromecha_main.start(reload_modules=True)


run_plugin()
