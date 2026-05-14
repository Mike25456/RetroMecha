"""
RetroMecha — core/module_registry.py
Registry de módulos con auto-registro por decorador.

CÓMO AGREGAR UN MÓDULO NUEVO (sin tocar este archivo):
  1. Crea modules/mi_modulo.py
  2. Hereda de BaseModule
  3. Pon @register('MI_MODULO') sobre la clase
  4. Importa el archivo en main.py

El MechaBuilder descubrirá el módulo automáticamente.
"""

_REGISTRY: dict = {}


def register(name: str):
    """
    Decorador para registrar un módulo en el Registry global.

    Uso:
        @register('HEAD')
        class HeadModule(BaseModule):
            ...
    """
    def decorator(cls):
        if name in _REGISTRY:
            print(f'[RetroMecha][Registry] ADVERTENCIA: '
                  f'"{name}" ya registrado — sobreescribiendo con {cls.__name__}')
        _REGISTRY[name] = cls
        return cls
    return decorator


def get(name: str):
    """Retorna la clase del módulo o None si no existe."""
    mod = _REGISTRY.get(name)
    if mod is None:
        print(f'[RetroMecha][Registry] Módulo "{name}" no encontrado. '
              f'Registrados: {list(_REGISTRY.keys())}')
    return mod


def all_registered() -> dict:
    """Retorna copia del registry completo."""
    return dict(_REGISTRY)


def is_registered(name: str) -> bool:
    return name in _REGISTRY
