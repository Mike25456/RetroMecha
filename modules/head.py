"""RetroMecha - modules/head.py
Helmet-like floating head built from simple primitives.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from utils.maya_materials import assign_material


def _finish(mesh: str, bevel: float = 0.03, hard: bool = False) -> str:
    if bevel > 0:
        try:
            mc.polyBevel(mesh, offset=bevel, segments=1, chamfer=0, ch=0)
        except Exception:
            pass
    try:
        mc.polySoftEdge(mesh, angle=0 if hard else 55, ch=0)
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def _make_fin(name: str, side: float, aggr: float) -> str:
    fin = mc.polyCone(r=0.11, h=0.72 + aggr * 0.28, sa=4, name=name)[0]
    mc.rotate(0, 0, -18 * side, fin)
    mc.scale(0.55, 1.0, 0.18, fin)
    mc.move(side * 0.52, 0.54, -0.02, fin, relative=True)
    assign_material(fin, "rm_white_armor_mat")
    return _finish(fin, 0.0, hard=True)


@register('HEAD')
class HeadModule(BaseModule):
    MODULE_NAME = 'HEAD'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_head_DEBUG'

        grp = mc.group(empty=True, name='rm_head_#')
        aggr = self._get('aggressiveness', 0.5)

        main = mc.polyCube(w=0.86, h=0.74, d=0.74, sx=2, sy=2, sz=2,
                           name='rm_head_main_#')[0]
        mc.scale(1.0, 1.12, 0.88, main)
        assign_material(main, "rm_white_armor_mat")
        _finish(main, 0.08)

        brow = mc.polyCube(w=0.70, h=0.16, d=0.10, name='rm_head_brow_#')[0]
        mc.move(0, 0.14, 0.39, brow, relative=True)
        mc.rotate(-8, 0, 0, brow)
        assign_material(brow, "rm_graphite_mat")
        _finish(brow, 0.025, hard=True)

        jaw = mc.polyCube(w=0.42, h=0.30, d=0.16, name='rm_head_jaw_#')[0]
        mc.move(0, -0.30, 0.39, jaw, relative=True)
        mc.scale(0.72, 1.0, 1.0, jaw)
        assign_material(jaw, "rm_graphite_mat")
        _finish(jaw, 0.025, hard=True)

        visor_l = mc.polyCube(w=0.32, h=0.055, d=0.035, name='rm_head_visor_l_#')[0]
        mc.move(-0.17, 0.04, 0.46, visor_l, relative=True)
        mc.rotate(0, 0, -16, visor_l)
        assign_material(visor_l, "rm_cyan_glow_mat")
        _finish(visor_l, 0.01, hard=True)

        visor_r = mc.polyCube(w=0.32, h=0.055, d=0.035, name='rm_head_visor_r_#')[0]
        mc.move(0.17, 0.04, 0.46, visor_r, relative=True)
        mc.rotate(0, 0, 16, visor_r)
        assign_material(visor_r, "rm_cyan_glow_mat")
        _finish(visor_r, 0.01, hard=True)

        ear_h = 0.42 + aggr * 0.18
        ear_l = mc.polyCube(w=0.16, h=ear_h, d=0.28, name='rm_head_ear_l_#')[0]
        mc.move(-0.50, 0.08, 0, ear_l, relative=True)
        assign_material(ear_l, "rm_graphite_mat")
        _finish(ear_l, 0.025, hard=True)

        ear_r = mc.polyCube(w=0.16, h=ear_h, d=0.28, name='rm_head_ear_r_#')[0]
        mc.move(0.50, 0.08, 0, ear_r, relative=True)
        assign_material(ear_r, "rm_graphite_mat")
        _finish(ear_r, 0.025, hard=True)

        fin_l = _make_fin('rm_head_fin_l_#', -1.0, aggr)
        fin_r = _make_fin('rm_head_fin_r_#', 1.0, aggr)

        neck_glow = mc.polyTorus(r=0.22, sr=0.012, sa=24, sh=4,
                                 name='rm_head_neck_glow_#')[0]
        mc.move(0, -0.52, 0, neck_glow, relative=True)
        assign_material(neck_glow, "rm_cyan_glow_mat")
        _finish(neck_glow, 0.0)

        mc.parent(main, brow, jaw, visor_l, visor_r,
                  ear_l, ear_r, fin_l, fin_r, neck_glow, grp)

        return self._finalize_group(grp, position, rotation, scale)
