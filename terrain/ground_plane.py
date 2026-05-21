"""
RetroMecha — terrain/ground_plane.py  v4
Plano de suelo 150u de lado.
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
        gs = 150.0
        surface = mc.polyCube(w=gs, h=0.10, d=gs, sx=8, sz=8,
                              name='rm_ground_surface_#')[0]
        border = mc.polyCube(w=gs+1.0, h=0.06, d=gs+1.0,
                             name='rm_ground_border_#')[0]
        mc.move(0, -0.08, 0, border, relative=True)
        mc.parent(surface, border, grp)
        return self._finalize_group(grp, position, rotation, scale)