"""
RetroMecha — terrain/ground_plane.py
Plano de suelo. Siempre presente, no es símbolo del L-System.
Delimita el piso de la escena.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('GROUND_PLANE')
class GroundPlaneModule(BaseModule):
    """
    Plano horizontal grande que delimita el suelo de la escena.
    Se crea antes de cualquier otro elemento del terreno.
    """
    MODULE_NAME = 'GROUND_PLANE'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_ground_DEBUG'

        grp = mc.group(empty=True, name='rm_ground_#')

        sep = self._get('separation', 0.35)

        # Tamaño proporcional al mecha (3-5x)
        ground_size = max(8.0, sep * 25.0)

        ground = mc.polyCube(
            w=ground_size, h=0.08, d=ground_size,
            sx=2, sz=2,
            name='rm_ground_surface_#'
        )[0]

        # Borde sutil (labio exterior)
        border = mc.polyCube(
            w=ground_size + 0.3, h=0.04, d=ground_size + 0.3,
            name='rm_ground_border_#'
        )[0]
        mc.move(0, -0.06, 0, border, relative=True)

        mc.parent(ground, border, grp)

        return self._finalize_group(grp, position, rotation, scale)
