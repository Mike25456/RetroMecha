"""RetroMecha - modules/wing.py
Fan of primitive armor blades inspired by angelic mecha silhouettes.
"""

from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@dataclass(frozen=True)
class WingTune:
    """Multiplicadores desde la UI (config avanzada de alas)."""
    width: float = 1.0
    length: float = 1.0
    detail: float = 1.0
    spread: float = 1.0

    @classmethod
    def from_params(cls, getter) -> 'WingTune':
        return cls(
            width=float(getter('wing_width_mul', 1.0)),
            length=float(getter('wing_length_mul', 1.0)),
            detail=float(getter('wing_detail_mul', 1.0)),
            spread=float(getter('wing_spread_mul', 1.0)),
        )


def _finish(mesh: str, bevel: float = 0.025, hard: bool = False) -> str:
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


def _make_blade(index: int, side: float, length: float, width: float,
                angle: float, y: float, z: float) -> str:
    blade = mc.polyCone(r=width, h=length, sa=4, name=f"rm_wing_blade_{index}_#")[0]
    mc.scale(0.92, 1.0, 0.18, blade)
    mc.rotate(0, 0, angle * side, blade)
    mc.move(side * length * 0.42, y + length * 0.50, z, blade, relative=True)
    return _finish(blade, 0.022, hard=True)


def _make_blade_edge(index: int, side: float, length: float, angle: float,
                     y: float, z: float, d_mul: float = 1.0) -> str:
    edge = mc.polyCube(w=0.070 * d_mul, h=length * 0.70, d=0.070 * d_mul,
                       name=f"rm_wing_edge_{index}_#")[0]
    mc.rotate(0, 0, angle * side, edge)
    mc.move(side * length * 0.43, y + length * 0.50, z + 0.045,
            edge, relative=True)
    return _finish(edge, 0.006, hard=True)


def _make_compact_plate(index: int, side: float, length: float, width: float,
                        angle: float, y: float, z: float) -> str:
    plate = mc.polyCube(w=width, h=length, d=0.12,
                        sx=2, sy=2, sz=1,
                        name=f"rm_wing_compact_plate_{index}_#")[0]
    mc.rotate(0, 0, angle * side, plate)
    mc.move(side * length * 0.24, y + length * 0.24, z, plate, relative=True)
    return _finish(plate, 0.035, hard=True)


def _make_fan_plate(index: int, side: float, length: float, width: float,
                    angle: float, y: float, z: float, d_mul: float = 1.0) -> str:
    grp = mc.group(empty=True, name=f"rm_wing_fan_plate_{index}_#")

    body = mc.polyCube(w=width, h=length * 0.74, d=0.13,
                       sx=2, sy=3, sz=1,
                       name=f"rm_wing_fan_body_{index}_#")[0]
    mc.move(0, length * 0.16, 0, body, relative=True)
    _finish(body, 0.040, hard=True)

    tip = mc.polyCone(r=width * 0.36, h=length * 0.24, sa=4,
                      name=f"rm_wing_fan_tip_{index}_#")[0]
    mc.move(0, length * 0.64, 0, tip, relative=True)
    mc.scale(0.90, 1.0, 0.34, tip)
    _finish(tip, 0.0, hard=True)

    rib = mc.polyCube(w=0.060 * d_mul, h=length * 0.62, d=0.060 * d_mul,
                      name=f"rm_wing_fan_rib_{index}_#")[0]
    mc.move(side * width * 0.30, length * 0.20, 0.045, rib, relative=True)
    _finish(rib, 0.006, hard=True)

    mc.parent(body, tip, rib, grp)
    mc.rotate(0, 0, angle * side, grp)
    mc.move(side * length * 0.34, y + length * 0.34, z, grp, relative=True)
    return grp


def _make_thruster(index: int, side: float, scale: float,
                   x: float, y: float, z: float,
                   d_mul: float = 1.0) -> str:
    thruster = mc.polyCylinder(r=0.13 * scale * d_mul, h=0.24 * scale * d_mul,
                               sa=10, name=f"rm_wing_thruster_{index}_#")[0]
    mc.rotate(90, 0, 0, thruster)
    mc.move(side * x * scale, y * scale, z * scale, thruster, relative=True)
    return _finish(thruster, 0.0)


def _build_root(side: float, scale: float, aggr: float,
                d_mul: float = 1.0) -> str:
    grp = mc.group(empty=True, name="rm_wing_root_#")

    hub = mc.polyCylinder(r=0.28 * scale, h=0.28 * scale, sa=14,
                          name="rm_wing_hub_#")[0]
    mc.rotate(90, 0, 0, hub)
    _finish(hub, 0.0)

    glow = mc.polyTorus(r=0.25 * scale, sr=0.016 * scale * d_mul,
                        sa=24, sh=4, name="rm_wing_hub_glow_#")[0]
    mc.rotate(90, 0, 0, glow)
    _finish(glow, 0.0)

    armor = mc.polyCube(w=0.34 * scale, h=0.52 * scale, d=0.22 * scale,
                        name="rm_wing_root_armor_#")[0]
    mc.move(side * 0.13 * scale, -0.06 * scale, -0.08 * scale, armor,
            relative=True)
    mc.rotate(0, 0, -18 * side, armor)
    _finish(armor, 0.03, hard=True)

    spikes = []
    for i, off in enumerate((-0.16, 0.02, 0.20)):
        spike = mc.polyCone(r=0.055 * scale * d_mul,
                            h=(0.28 + aggr * 0.54) * scale * d_mul,
                            sa=4, name=f"rm_wing_root_spike_{i}_#")[0]
        mc.rotate(90, 0, 20 * side, spike)
        mc.move(-side * 0.08 * scale, off * scale, -0.18 * scale,
                spike, relative=True)
        _finish(spike, 0.0, hard=True)
        spikes.append(spike)

    mc.parent(hub, glow, armor, *spikes, grp)
    return grp


@register('WING')
class WingModule(BaseModule):
    MODULE_NAME = 'WING'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_wing_DEBUG'

        grp = mc.group(empty=True, name='rm_wing_#')

        aggr = 0.5
        style = self._get('wing_style', 'needle')
        side = -1.0 if position[0] < 0 else 1.0
        tune = WingTune.from_params(self._get)
        w_mul = tune.width
        l_mul = tune.length
        d_mul = tune.detail
        s_mul = tune.spread
        s = 1.0 + aggr * 0.75

        side_seed = self._get('_side_seed')
        if side_seed is not None:
            import random as _rnd
            rng = _rnd.Random(side_seed + (1 if side > 0 else 0))
            w_mul *= 1.0 + (rng.random() - 0.5) * 0.30
            l_mul *= 1.0 + (rng.random() - 0.5) * 0.30
            d_mul *= 1.0 + (rng.random() - 0.5) * 0.20
            s_mul *= 1.0 + (rng.random() - 0.5) * 0.20

        root = _build_root(side, s, aggr, d_mul)

        if style == 'compact':
            specs = [
                (0, 1.52, 0.46, 18, -0.10, -0.03),
                (1, 1.22, 0.38, 7, -0.20, 0.02),
                (2, 1.05, 0.32, -7, -0.30, -0.02),
            ]
        elif style == 'fan':
            specs = [
                (0, 2.55, 0.74, 34, -0.24, -0.08),
                (1, 2.35, 0.68, 24, -0.22, -0.04),
                (2, 2.15, 0.61, 14, -0.19, 0.00),
                (3, 1.95, 0.54, 5, -0.15, 0.02),
                (4, 1.82, 0.50, -5, -0.10, -0.02),
                (5, 2.05, 0.55, -15, -0.05, -0.07),
            ]
        else:
            specs = [
                (0, 3.16, 0.42, 25, -0.36, -0.06),
                (1, 2.78, 0.38, 17, -0.30, -0.02),
                (2, 2.42, 0.34, 9, -0.24, 0.02),
                (3, 2.12, 0.31, 2, -0.18, 0.00),
                (4, 2.36, 0.33, -6, -0.12, -0.04),
            ]
        blades = []
        edges = []
        for idx, length, width, angle, y, z in specs:
            length *= s * l_mul
            width *= s * w_mul
            y *= s * l_mul
            z *= s
            angle *= s_mul
            if style == 'compact':
                blades.append(_make_compact_plate(idx, side, length, width,
                                                  angle, y, z))
            elif style == 'fan':
                blades.append(_make_fan_plate(idx, side, length, width,
                                              angle, y, z, d_mul))
            else:
                blades.append(_make_blade(idx, side, length, width, angle, y, z))
                edges.append(_make_blade_edge(idx, side, length, angle, y, z, d_mul))

        if style == 'compact':
            edges.extend([
                _make_thruster(0, side, s, 0.28, -0.08, -0.22, d_mul),
                _make_thruster(1, side, s, 0.46, 0.18, -0.20, d_mul),
            ])

        mc.parent(root, *blades, *edges, grp)
        return self._finalize_group(grp, position, rotation, scale)
