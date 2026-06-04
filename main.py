"""
RetroMecha — main.py
Punto de entrada del plugin (se ejecuta dentro de Maya).

Forma recomendada de arrancar (desde el proyecto, sin bridge):
  python run_retromecha.py
  o doble clic en Run RetroMecha.bat

Orden de ejecución:
  1. Agrega la carpeta del proyecto al sys.path
  2. Importa todos los módulos para que se auto-registren en el Registry
  3. Lanza la UI
"""

import sys
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)


def _import_modules() -> None:
    """Importa módulos para activar el @register() en el Registry."""
    import modules.head       # noqa: F401  → registra 'HEAD'
    import modules.torso      # noqa: F401  → registra 'TORSO'
    import modules.arm        # noqa: F401  → registra 'ARM'  (paquete)
    import modules.wing       # noqa: F401  → registra 'WING' (paquete)

    import terrain.monument    # noqa: F401  → registra 'MONUMENT'
    import terrain.platform    # noqa: F401  → registra 'PLATFORM'
    import terrain.fragment    # noqa: F401  → registra 'FRAGMENT'
    import terrain.debris      # noqa: F401  → registra 'DEBRIS'
    import terrain.tower       # noqa: F401  → registra 'TOWER'
    import terrain.skyline     # noqa: F401  → registra 'SKYLINE'
    import terrain.ground_plane  # noqa: F401  → registra 'GROUND_PLANE'

    import animations.flight      # noqa: F401  → registra 'flight'
    import animations.idle        # noqa: F401  → registra 'idle'
    import animations.spin        # noqa: F401  → registra 'spin'
    import animations.charge      # noqa: F401  → registra 'charge'

    import materials.presets      # noqa: F401  → expone list_presets / apply_preset
    import materials.materializer  # noqa: F401 → expone materialize_mecha / materialize_terrain


def start(*, reload_modules: bool = False) -> None:
    """Inicializa el plugin y abre la UI una sola vez por sesión."""
    if reload_modules:
        _import_modules()
        from core.module_registry import all_registered
        print(f'[RetroMecha] Módulos registrados: {list(all_registered().keys())}')
    elif not getattr(start, '_ready', False):
        _import_modules()
        from core.module_registry import all_registered
        print(f'[RetroMecha] Módulos registrados: {list(all_registered().keys())}')
        start._ready = True  # type: ignore[attr-defined]

    from ui.main_window import build_ui
    build_ui(recreate=reload_modules)


if __name__ == '__main__':
    start(reload_modules=True)
