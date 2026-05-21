"""RetroMecha - modules/arm.py
Floating segmented arm module with white armor plates and cyan joints.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from utils.maya_materials import assign_material


def _finish(mesh: str, bevel: float = 0.035, hard: bool = False) -> str:
    if bevel > 0:
        try:
            mc.polyBevel(mesh, offset=bevel, segments=1, chamfer=0, ch=0)
        except Exception:
            pass
    try:
        mc.polySoftEdge(mesh, angle=0 if hard else 45, ch=0)
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def _armor_block(name: str, w: float, h: float, d: float, y: float) -> str:
    block = mc.polyCube(w=w, h=h, d=d, sx=2, sy=3, sz=1, name=name)[0]
    mc.move(0, y, 0, block, relative=True)
    assign_material(block, "rm_white_armor_mat")
    return _finish(block, 0.055)


@register('ARM')
class ArmModule(BaseModule):
    MODULE_NAME = 'ARM'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_arm_DEBUG'

        grp = mc.group(empty=True, name='rm_arm_#')
        decay = self._get('decay', 0.85)
        aggr = self._get('aggressiveness', 0.5)
        side = -1.0 if position[0] < 0 else 1.0

        upper = _armor_block('rm_arm_upper_#', 0.42, 0.92, 0.38, 0.08)
        mc.rotate(0, 0, -5 * side, upper)

        upper_core = mc.polyCylinder(r=0.16, h=0.28, sa=12,
                                     name='rm_arm_shoulder_core_#')[0]
        mc.rotate(90, 0, 0, upper_core)
        mc.move(0, 0.60, 0, upper_core, relative=True)
        assign_material(upper_core, "rm_graphite_mat")
        _finish(upper_core, 0.0)

        shoulder_glow = mc.polyTorus(r=0.19, sr=0.012, sa=24, sh=4,
                                     name='rm_arm_shoulder_glow_#')[0]
        mc.rotate(90, 0, 0, shoulder_glow)
        mc.move(0, 0.60, 0, shoulder_glow, relative=True)
        assign_material(shoulder_glow, "rm_cyan_glow_mat")
        _finish(shoulder_glow, 0.0)

        elbow = mc.polySphere(r=0.18, sa=8, sh=6, name='rm_arm_elbow_#')[0]
        mc.move(0, -0.52, 0, elbow, relative=True)
        assign_material(elbow, "rm_graphite_mat")
        _finish(elbow, 0.0)

        elbow_glow = mc.polyTorus(r=0.20, sr=0.012, sa=24, sh=4,
                                  name='rm_arm_elbow_glow_#')[0]
        mc.move(0, -0.52, 0, elbow_glow, relative=True)
        assign_material(elbow_glow, "rm_cyan_glow_mat")
        _finish(elbow_glow, 0.0)

        fore_h = 0.82 * decay
        forearm = _armor_block('rm_arm_forearm_#', 0.36 * decay,
                               fore_h, 0.34 * decay, -1.05)
        mc.rotate(0, 0, 7 * side, forearm)

        tip = mc.polyCone(r=0.16 * decay, h=0.34 + aggr * 0.14, sa=4,
                          name='rm_arm_tip_#')[0]
        mc.move(0, -1.62, 0, tip, relative=True)
        mc.rotate(180, 45, 0, tip)
        assign_material(tip, "rm_graphite_mat")
        _finish(tip, 0.0, hard=True)

        accent = mc.polyCube(w=0.045, h=0.46, d=0.035,
                             name='rm_arm_cyan_strip_#')[0]
        mc.move(0, -1.05, 0.20 * decay, accent, relative=True)
        assign_material(accent, "rm_cyan_glow_mat")
        _finish(accent, 0.006, hard=True)

        mc.parent(upper, upper_core, shoulder_glow, elbow, elbow_glow,
                  forearm, tip, accent, grp)
        return self._finalize_group(grp, position, rotation, scale)
