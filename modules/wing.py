"""RetroMecha - modules/wing.py
Fan of primitive armor blades inspired by angelic mecha silhouettes.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from utils.maya_materials import assign_material


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
    assign_material(blade, "rm_white_armor_mat")
    return _finish(blade, 0.022, hard=True)


def _make_blade_edge(index: int, side: float, length: float, angle: float,
                     y: float, z: float) -> str:
    edge = mc.polyCube(w=0.070, h=length * 0.70, d=0.070,
                       name=f"rm_wing_edge_{index}_#")[0]
    mc.rotate(0, 0, angle * side, edge)
    mc.move(side * length * 0.43, y + length * 0.50, z + 0.045,
            edge, relative=True)
    assign_material(edge, "rm_graphite_mat")
    return _finish(edge, 0.006, hard=True)


def _build_root(side: float, scale: float, aggr: float) -> str:
    grp = mc.group(empty=True, name="rm_wing_root_#")

    hub = mc.polyCylinder(r=0.28 * scale, h=0.28 * scale, sa=14,
                          name="rm_wing_hub_#")[0]
    mc.rotate(90, 0, 0, hub)
    assign_material(hub, "rm_graphite_mat")
    _finish(hub, 0.0)

    glow = mc.polyTorus(r=0.25 * scale, sr=0.016 * scale, sa=24, sh=4,
                        name="rm_wing_hub_glow_#")[0]
    mc.rotate(90, 0, 0, glow)
    assign_material(glow, "rm_cyan_glow_mat")
    _finish(glow, 0.0)

    armor = mc.polyCube(w=0.34 * scale, h=0.52 * scale, d=0.22 * scale,
                        name="rm_wing_root_armor_#")[0]
    mc.move(side * 0.13 * scale, -0.06 * scale, -0.08 * scale, armor,
            relative=True)
    mc.rotate(0, 0, -18 * side, armor)
    assign_material(armor, "rm_graphite_mat")
    _finish(armor, 0.03, hard=True)

    spikes = []
    for i, off in enumerate((-0.16, 0.02, 0.20)):
        spike = mc.polyCone(r=0.055 * scale, h=(0.28 + aggr * 0.18) * scale,
                            sa=4, name=f"rm_wing_root_spike_{i}_#")[0]
        mc.rotate(90, 0, 20 * side, spike)
        mc.move(-side * 0.08 * scale, off * scale, -0.18 * scale,
                spike, relative=True)
        assign_material(spike, "rm_graphite_mat")
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

        aggr = self._get('aggressiveness', 0.5)
        decay = self._get('decay', 0.85)
        side = -1.0 if position[0] < 0 else 1.0
        s = decay * (1.0 + aggr * 0.25)

        root = _build_root(side, s, aggr)

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
            length *= s
            width *= s
            y *= s
            z *= s
            blades.append(_make_blade(idx, side, length, width, angle, y, z))
            edges.append(_make_blade_edge(idx, side, length, angle, y, z))

        mc.parent(root, *blades, *edges, grp)
        return self._finalize_group(grp, position, rotation, scale)
