"""RetroMecha - modules/arm.py
Floating segmented arm module with different variations (standard, heavy, blade, cannon).
"""

from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@dataclass(frozen=True)
class ArmTune:
    """Multiplicadores desde la UI (config avanzada de brazos)."""
    width: float = 1.0
    length: float = 1.0
    detail: float = 1.0
    hand: float = 1.0

    @classmethod
    def from_params(cls, getter) -> 'ArmTune':
        return cls(
            width=float(getter('arm_width_mul', 1.0)),
            length=float(getter('arm_length_mul', 1.0)),
            detail=float(getter('arm_detail_mul', 1.0)),
            hand=float(getter('arm_hand_mul', 1.0)),
        )


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
        aggr = 0.5
        arm_style = self._get('arm_style', 'standard')
        side = -1.0 if position[0] < 0 else 1.0
        tune = ArmTune.from_params(self._get)
        w = tune.width
        l = tune.length
        d_mul = tune.detail
        hm = tune.hand

        side_seed = self._get('_side_seed')
        if side_seed is not None:
            import random as _rnd
            rng = _rnd.Random(side_seed + (1 if side > 0 else 0))
            w *= 1.0 + (rng.random() - 0.5) * 0.30
            l *= 1.0 + (rng.random() - 0.5) * 0.30
            hm *= 1.0 + (rng.random() - 0.5) * 0.20
            d_mul *= 1.0 + (rng.random() - 0.5) * 0.20

        parts = []

        if arm_style == 'heavy':
            upper = _armor_block('rm_arm_upper_#', 0.58 * w, 1.0 * l, 0.48 * w, 0.08)
            mc.rotate(0, 0, -5 * side, upper)

            upper_core = mc.polyCylinder(r=0.22 * w, h=0.34 * l, sa=12, name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core)
            mc.move(0, 0.60 * l, 0, upper_core, relative=True)
            _finish(upper_core, 0.0)

            shoulder_glow = mc.polyTorus(r=0.25 * w, sr=0.015 * d_mul, sa=24, sh=4, name='rm_arm_shoulder_glow_#')[0]
            mc.rotate(90, 0, 0, shoulder_glow)
            mc.move(0, 0.60 * l, 0, shoulder_glow, relative=True)
            _finish(shoulder_glow, 0.0)

            elbow = mc.polyCube(w=0.35 * w, h=0.35 * l, d=0.35 * w, name='rm_arm_elbow_#')[0]
            mc.move(0, -0.55 * l, 0, elbow, relative=True)
            _finish(elbow, 0.03)

            fore_h = 0.95 * l
            forearm = _armor_block('rm_arm_forearm_#', 0.52 * w, fore_h, 0.45 * w, -1.15 * l)
            mc.rotate(0, 0, 4 * side, forearm)

            tip_h = 0.4 * hm
            tip = mc.polyCube(w=0.45 * hm, h=tip_h, d=0.35 * hm, name='rm_arm_tip_#')[0]
            mc.move(0, -1.15 * l - fore_h * 0.5 - tip_h * 0.5, 0, tip, relative=True)

            parts.extend([upper, upper_core, shoulder_glow, elbow, forearm, tip])

        elif arm_style == 'blade':
            upper = _armor_block('rm_arm_upper_#', 0.32 * w, 0.85 * l, 0.30 * w, 0.08)
            mc.rotate(0, 0, -8 * side, upper)

            upper_core = mc.polyCylinder(r=0.14 * w, h=0.22 * l, sa=12, name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core) 
            mc.move(0, 0.50 * l, 0, upper_core, relative=True)
            _finish(upper_core, 0.0)

            shoulder_glow = mc.polyTorus(r=0.17 * w, sr=0.01 * d_mul, sa=24, sh=4, name='rm_arm_shoulder_glow_#')[0]
            mc.rotate(90, 0, 0, shoulder_glow)
            mc.move(0, 0.50 * l, 0, shoulder_glow, relative=True)
            _finish(shoulder_glow, 0.0)

            elbow = mc.polySphere(r=0.14 * w, sa=8, sh=6, name='rm_arm_elbow_#')[0]
            mc.move(0, -0.45 * l, 0, elbow, relative=True)
            _finish(elbow, 0.0)

            fore_h = 1.1 * l
            forearm = _armor_block('rm_arm_forearm_#', 0.28 * w, fore_h, 0.25 * w, -1.1 * l)
            mc.rotate(0, 0, 10 * side, forearm)

            tip_h = (0.8 + aggr * 0.6) * hm
            tip = mc.polyCone(r=0.12 * hm, h=tip_h, sa=3, name='rm_arm_tip_#')[0]
            mc.move(0, -1.1 * l - fore_h * 0.5 - tip_h * 0.5, 0, tip, relative=True)
            mc.rotate(180, 90 if side > 0 else -90, 0, tip)
            _finish(tip, 0.0, hard=True)

            accent = mc.polyCube(w=0.03 * d_mul, h=0.7 * d_mul, d=0.04 * d_mul, name='rm_arm_cyan_strip_#')[0]
            mc.move(0, -1.1 * l - fore_h * 0.5 - tip_h - 0.02, 0, accent, relative=True)

            parts.extend([upper, upper_core, shoulder_glow, elbow, forearm, tip, accent])

        elif arm_style == 'cannon':
            upper = _armor_block('rm_arm_upper_#', 0.40 * w, 0.88 * l, 0.45 * w, 0.08)
            mc.rotate(0, 0, -3 * side, upper)

            upper_core = mc.polyCylinder(r=0.18 * w, h=0.30 * l, sa=12, name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core)
            mc.move(0, 0.60 * l, 0, upper_core, relative=True)
            _finish(upper_core, 0.0)

            elbow = mc.polyCylinder(r=0.16 * w, h=0.32 * l, sa=12, name='rm_arm_elbow_#')[0]
            mc.rotate(90, 0, 0, elbow)
            mc.move(0, -0.45 * l, 0, elbow, relative=True)
            _finish(elbow, 0.0)

            fore_h = 0.9 * l
            forearm = mc.polyCylinder(r=0.22 * w, h=fore_h, sa=12, name='rm_arm_forearm_#')[0]
            mc.move(0, -1.0 * l, 0, forearm, relative=True)
            _finish(forearm, 0.02)

            tip_h = 0.35 * hm
            tip = mc.polyCylinder(r=0.18 * hm, h=tip_h, sa=12, name='rm_arm_tip_#')[0]
            mc.move(0, -1.0 * l - fore_h * 0.5 - tip_h * 0.5, 0, tip, relative=True)
            _finish(tip, 0.02, hard=True)

            cannon_core = mc.polyCylinder(r=0.12 * w, h=0.36 * d_mul, sa=12, name='rm_arm_cannon_core_#')[0]
            mc.move(0, -1.0 * l - fore_h * 0.5 - tip_h - 0.01, 0, cannon_core, relative=True)
            _finish(cannon_core, 0.0, hard=True)

            parts.extend([upper, upper_core, elbow, forearm, tip, cannon_core])

        else: # standard
            upper = _armor_block('rm_arm_upper_#', 0.42 * w, 0.92 * l, 0.38 * w, 0.08)
            mc.rotate(0, 0, -5 * side, upper)

            upper_core = mc.polyCylinder(r=0.16 * w, h=0.28 * l, sa=12,
                                         name='rm_arm_shoulder_core_#')[0]
            mc.rotate(90, 0, 0, upper_core)
            mc.move(0, 0.60 * l, 0, upper_core, relative=True)
            _finish(upper_core, 0.0)

            shoulder_glow = mc.polyTorus(r=0.19 * w, sr=0.012 * d_mul, sa=24, sh=4,
                                         name='rm_arm_shoulder_glow_#')[0]
            mc.rotate(90, 0, 0, shoulder_glow)
            mc.move(0, 0.60 * l, 0, shoulder_glow, relative=True)
            _finish(shoulder_glow, 0.0)

            elbow = mc.polySphere(r=0.18 * w, sa=8, sh=6, name='rm_arm_elbow_#')[0]
            mc.move(0, -0.52 * l, 0, elbow, relative=True)
            _finish(elbow, 0.0)

            elbow_glow = mc.polyTorus(r=0.20 * w, sr=0.012 * d_mul, sa=24, sh=4,
                                      name='rm_arm_elbow_glow_#')[0]
            mc.move(0, -0.52 * l, 0, elbow_glow, relative=True)
            _finish(elbow_glow, 0.0)

            fore_h = 0.82 * l
            forearm = _armor_block('rm_arm_forearm_#', 0.36 * w,
                                   fore_h, 0.34 * w, -1.05 * l)
            mc.rotate(0, 0, 7 * side, forearm)

            tip_h = (0.34 + aggr * 0.42) * hm
            tip = mc.polyCone(r=0.16 * hm, h=tip_h, sa=4,
                              name='rm_arm_tip_#')[0]
            mc.move(0, -1.05 * l - fore_h * 0.5 - tip_h * 0.5, 0, tip, relative=True)
            mc.rotate(180, 45, 0, tip)
            _finish(tip, 0.0, hard=True)

            accent = mc.polyCube(w=0.045 * d_mul, h=0.46 * d_mul, d=0.035 * d_mul,
                                 name='rm_arm_cyan_strip_#')[0]
            mc.move(0, -1.05 * l, 0.20, accent, relative=True)
            _finish(accent, 0.006, hard=True)

            parts.extend([upper, upper_core, shoulder_glow, elbow, elbow_glow, forearm, tip, accent])

        mc.parent(parts, grp)
        return self._finalize_group(grp, position, rotation, scale)
