"""
RetroMecha — terrain/ground_plane.py  v2
Plano de suelo fijo, grande, con subdivisiones y borde.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('GROUND_PLANE')
class GroundPlaneModule(BaseModule):
    MODULE_NAME = 'GROUND_PLANE'

    def generate(self, position=(0,0,0), scale=1.0, rotation=(0,0,0)) -> str:
        if mc is None:
            return 'rm_ground_DEBUG'

        grp = mc.group(empty=True, name='rm_ground_#')

        # Tamaño fijo amplio — scale del terrain_builder ya es 1.0 para el suelo,
        # el tamaño se controla aquí directamente.
        gs = 60.0   # 60 unidades de lado — cubre toda la escena holgadamente

        surface = mc.polyCube(w=gs, h=0.10, d=gs,
                              sx=4, sz=4,
                              name='rm_ground_surface_#')[0]

        border = mc.polyCube(w=gs + 0.5, h=0.06, d=gs + 0.5,
                             name='rm_ground_border_#')[0]
        mc.move(0, -0.08, 0, border, relative=True)

        mc.parent(surface, border, grp)
        return self._finalize_group(grp, position, rotation, scale)
