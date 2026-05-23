"""RetroMecha - modules/arm.py
Floating segmented arm module with different variations (standard, heavy, blade, cannon).
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
        arm_style = self._get('arm_style', 'standard')
        side = -1.0 if position[0] < 0 else 1.0

        parts = []

        if arm_style == 'heavy':
            upper = _armor_block('rm_arm_upper_#', 0.58, 1.0, 0.48, 0.08)
            mc.rotate(0, 0, -5 * side, upper)

            upper_core = mc.polyCylinder(r=0.22, h=0.34, sa=12, name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core)
            mc.move(0, 0.60, 0, upper_core, relative=True)
            assign_material(upper_core, "rm_graphite_mat")
            _finish(upper_core, 0.0)

            shoulder_glow = mc.polyTorus(r=0.25, sr=0.015, sa=24, sh=4, name='rm_arm_shoulder_glow_#')[0]
            mc.rotate(90, 0, 0, shoulder_glow)
            mc.move(0, 0.60, 0, shoulder_glow, relative=True)
            assign_material(shoulder_glow, "rm_cyan_glow_mat")
            _finish(shoulder_glow, 0.0)

            elbow = mc.polyCube(w=0.35, h=0.35, d=0.35, name='rm_arm_elbow_#')[0]
            mc.move(0, -0.55, 0, elbow, relative=True)
            assign_material(elbow, "rm_graphite_mat")
            _finish(elbow, 0.03)

            fore_h = 0.95 * decay
            forearm = _armor_block('rm_arm_forearm_#', 0.52 * decay, fore_h, 0.45 * decay, -1.15)
            mc.rotate(0, 0, 4 * side, forearm)

            tip = mc.polyCube(w=0.45 * decay, h=0.4, d=0.35 * decay, name='rm_arm_tip_#')[0]
            mc.move(0, -1.75, 0, tip, relative=True)
            assign_material(tip, "rm_graphite_mat")
            _finish(tip, 0.04, hard=True)

            parts.extend([upper, upper_core, shoulder_glow, elbow, forearm, tip])

        elif arm_style == 'blade':
            upper = _armor_block('rm_arm_upper_#', 0.32, 0.85, 0.30, 0.08)
            mc.rotate(0, 0, -8 * side, upper)

            upper_core = mc.polyCylinder(r=0.14, h=0.22, sa=12, name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core) 
            mc.move(0, 0.50, 0, upper_core, relative=True)
            assign_material(upper_core, "rm_graphite_mat")
            _finish(upper_core, 0.0)

            shoulder_glow = mc.polyTorus(r=0.17, sr=0.01, sa=24, sh=4, name='rm_arm_shoulder_glow_#')[0]
            mc.rotate(90, 0, 0, shoulder_glow)
            mc.move(0, 0.50, 0, shoulder_glow, relative=True)
            assign_material(shoulder_glow, "rm_cyan_glow_mat")
            _finish(shoulder_glow, 0.0)

            elbow = mc.polySphere(r=0.14, sa=8, sh=6, name='rm_arm_elbow_#')[0]
            mc.move(0, -0.45, 0, elbow, relative=True)
            assign_material(elbow, "rm_graphite_mat")
            _finish(elbow, 0.0)

            fore_h = 1.1 * decay
            forearm = _armor_block('rm_arm_forearm_#', 0.28 * decay, fore_h, 0.25 * decay, -1.1)
            mc.rotate(0, 0, 10 * side, forearm)

            tip = mc.polyCone(r=0.12 * decay, h=0.8 + aggr * 0.2, sa=3, name='rm_arm_tip_#')[0]
            mc.move(0, -2.1, 0, tip, relative=True)
            mc.rotate(180, 90 if side > 0 else -90, 0, tip)
            assign_material(tip, "rm_white_armor_mat")
            _finish(tip, 0.0, hard=True)

            accent = mc.polyCube(w=0.03, h=0.7, d=0.04, name='rm_arm_cyan_strip_#')[0]
            mc.move(0, -1.9, 0, accent, relative=True)
            assign_material(accent, "rm_cyan_glow_mat")
            _finish(accent, 0.006, hard=True)

            parts.extend([upper, upper_core, shoulder_glow, elbow, forearm, tip, accent])

        elif arm_style == 'cannon':
            upper = _armor_block('rm_arm_upper_#', 0.40, 0.88, 0.45, 0.08)
            mc.rotate(0, 0, -3 * side, upper)

            upper_core = mc.polyCylinder(r=0.18, h=0.30, sa=12, name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core)
            mc.move(0, 0.60, 0, upper_core, relative=True)
            assign_material(upper_core, "rm_graphite_mat")
            _finish(upper_core, 0.0)

            elbow = mc.polyCylinder(r=0.16, h=0.32, sa=12, name='rm_arm_elbow_#')[0]
            mc.rotate(90, 0, 0, elbow)
            mc.move(0, -0.45, 0, elbow, relative=True)
            assign_material(elbow, "rm_graphite_mat")
            _finish(elbow, 0.0)

            fore_h = 0.9 * decay
            forearm = mc.polyCylinder(r=0.22 * decay, h=fore_h, sa=12, name='rm_arm_forearm_#')[0]
            mc.move(0, -1.0, 0, forearm, relative=True)
            assign_material(forearm, "rm_white_armor_mat")
            _finish(forearm, 0.02)

            tip = mc.polyCylinder(r=0.18 * decay, h=0.35, sa=12, name='rm_arm_tip_#')[0]
            mc.move(0, -1.55, 0, tip, relative=True)
            assign_material(tip, "rm_graphite_mat")
            _finish(tip, 0.02, hard=True)

            cannon_core = mc.polyCylinder(r=0.12 * decay, h=0.36, sa=12, name='rm_arm_cannon_core_#')[0]
            mc.move(0, -1.56, 0, cannon_core, relative=True)
            assign_material(cannon_core, "rm_cyan_glow_mat")
            _finish(cannon_core, 0.0, hard=True)

            parts.extend([upper, upper_core, elbow, forearm, tip, cannon_core])

        else: # standard
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

            parts.extend([upper, upper_core, shoulder_glow, elbow, elbow_glow, forearm, tip, accent])

        mc.parent(parts, grp)
        return self._finalize_group(grp, position, rotation, scale)
