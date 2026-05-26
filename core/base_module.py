"""
RetroMecha — core/base_module.py
Clase abstracta base para todos los módulos de geometría.

CONTRATO PARA GENERACIÓN DE CÓDIGO (AI/OpenCode):
Cualquier módulo nuevo DEBE heredar de BaseModule e implementar:
  - MODULE_NAME: str   (identificador único en el Registry)
  - generate(position, scale, rotation) -> str  (nombre del grupo Maya creado)

El método generate() es el único punto de entrada que el MechaBuilder conoce.
No agregar lógica de ensamblaje aquí — solo creación de geometría local.
"""

from abc import ABC, abstractmethod

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


class BaseModule(ABC):
    """
    Clase base para todos los módulos de RetroMecha.

    Cada módulo representa una pieza del mecha (cabeza, torso, brazo, etc.)
    y es responsable únicamente de crear su propia geometría en Maya.
    El posicionamiento global lo maneja MechaBuilder.

    Parámetros que llegan desde la UI (via self.params):

        height_scale     float  0.5–2.0   — escala vertical global
        symmetry         bool              — si True, ambos lados son idénticos
        _side_seed       int | None        — semilla para variación local (asimetría)
    """

    MODULE_NAME: str = ""  # Sobreescribir en cada subclase

    def __init__(self, params: dict = None):
        self.params = params or {}

    @abstractmethod
    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:
        """
        Crea la geometría del módulo en Maya.

        Args:
            position: (x, y, z) en espacio de mundo — MechaBuilder lo define
            scale:    escala uniforme del módulo
            rotation: (rx, ry, rz) en grados

        Returns:
            Nombre del grupo raíz creado en Maya (str)
        """
        pass

    def _finalize_group(self, group: str,
                        position: tuple,
                        rotation: tuple,
                        scale: float) -> str:
        """
        Aplica transformaciones finales al grupo creado.
        Llamar al final de cada generate().
        """
        if not MAYA_AVAILABLE:
            return group
        mc.move(position[0], position[1], position[2], group)
        mc.rotate(rotation[0], rotation[1], rotation[2], group)
        mc.scale(scale, scale, scale, group)
        return group

    def _get(self, key: str, default=None):
        """Acceso seguro a params con fallback."""
        return self.params.get(key, default)
