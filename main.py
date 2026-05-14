"""
RetroMecha — main.py
Punto de entrada. Correr este archivo desde el bridge de VS Code → Maya.

Orden de ejecución:
  1. Agrega la carpeta del proyecto al sys.path (por si el bridge no lo hace)
  2. Importa todos los módulos para que se auto-registren en el Registry
  3. Lanza la UI

Para recargar durante desarrollo (hot-reload desde VS Code):
  exec(open('ruta/a/RetroMecha/main.py').read())
"""

import sys
import os

# ── Asegurar que el proyecto esté en el path ──────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ── Importar módulos para activar el @register() ─────────────────────────────
#    Agregar una línea aquí por cada módulo nuevo que se cree en modules/
import modules.head       # noqa: F401  → registra 'HEAD'
import modules.torso      # noqa: F401  → registra 'TORSO'
import modules.arm        # noqa: F401  → registra 'ARM'
import modules.wing       # noqa: F401  → registra 'WING'

# ── Verificar registro ────────────────────────────────────────────────────────
from core.module_registry import all_registered
_registered = all_registered()
print(f'[RetroMecha] Módulos registrados: {list(_registered.keys())}')

# ── Abrir UI ──────────────────────────────────────────────────────────────────
from ui.main_window import build_ui
build_ui()
