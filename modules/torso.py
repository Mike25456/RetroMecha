"""
RetroMecha — modules/torso.py
Torso cúbico redondeado; caras inferiores escaladas pequeñas (cintura/punta roma).
Reactor llamativo en el pecho.
"""

import math

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from utils.maya_materials import assign_material


def _bbox_center(mesh: str) -> tuple:
    bb = mc.exactWorldBoundingBox(mesh)
    return (
        (bb[0] + bb[3]) * 0.5,
        (bb[1] + bb[4]) * 0.5,
        (bb[2] + bb[5]) * 0.5,
    )


def _taper_y(mesh: str, y_min: float, y_max: float,
             scale_bottom: float, scale_top: float) -> None:
    cx, _, cz = _bbox_center(mesh)
    span = y_max - y_min or 1.0
    for v in mc.ls(f"{mesh}.vtx[*]", flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = max(0.0, min(1.0, (pos[1] - y_min) / span))
        s = scale_bottom + (scale_top - scale_bottom) * t
        mc.move(cx + (pos[0] - cx) * s, pos[1], cz + (pos[2] - cz) * s, v, ws=True)


def _scale_bottom_faces(mesh: str, y_band: float = 0.14, face_scale: float = 0.38) -> None:
    """
    Equivalente a escalar las caras de abajo en Maya:
    encoge el anillo inferior del mesh hacia el centro en XZ.
    """
    bb = mc.exactWorldBoundingBox(mesh)
    y_cut = bb[1] + (bb[4] - bb[1]) * y_band
    cx, cz = (bb[0] + bb[3]) * 0.5, (bb[2] + bb[5]) * 0.5

    bottom_verts = set()
    n_faces = mc.polyEvaluate(mesh, face=True) or 0
    for i in range(n_faces):
        face = f"{mesh}.f[{i}]"
        verts = mc.polyListComponentConversion(face, fromFace=True, toVertex=True)
        verts = mc.ls(verts, flatten=True) or []
        if not verts:
            continue
        ys = [mc.pointPosition(v, w=True)[1] for v in verts]
        if sum(ys) / len(ys) <= y_cut:
            bottom_verts.update(verts)

    for v in bottom_verts:
        pos = mc.pointPosition(v, w=True)
        mc.move(
            cx + (pos[0] - cx) * face_scale,
            pos[1],
            cz + (pos[2] - cz) * face_scale,
            v, ws=True,
        )


def _bulge_front(mesh: str, amount: float) -> None:
    _, _, cz = _bbox_center(mesh)
    for v in mc.ls(f"{mesh}.vtx[*]", flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        if pos[2] > cz:
            t = min(1.0, (pos[2] - cz) / 0.5)
            mc.move(pos[0], pos[1], pos[2] + amount * t, v, ws=True)


def _round_block(mesh: str, bevel: float) -> None:
    try:
        mc.polyBevel(mesh, offset=bevel, segments=2, chamfer=0, ch=0)
    except Exception:
        pass
    try:
        mc.polySoftEdge(mesh, angle=180, ch=0)
    except Exception:
        pass


def _finish(mesh: str) -> str:
    try:
        mc.displaySmoothness(
            mesh, divisionsU=3, divisionsV=3,
            pointsWire=16, pointsShaded=4, polygonObject=3,
        )
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def _build_main_torso(aggr: float, torso_h: float) -> str:
    """Cuerpo cúbico ancho arriba; caras de abajo escaladas pequeñas."""
    w = 1.82 + aggr * 0.12
    h = torso_h * 0.82
    d = 1.18 + aggr * 0.06

    body = mc.polyCube(
        w=w, h=h, d=d,
        sx=5, sy=6, sz=5,
        name="rm_torso_body_#",
    )[0]
    mc.move(0, torso_h * 0.08, 0.02, body, relative=True)

    bb = mc.exactWorldBoundingBox(body)
    _taper_y(body, bb[1], bb[4], 0.72, 1.10 + aggr * 0.08)
    _scale_bottom_faces(body, y_band=0.16, face_scale=0.34 + aggr * 0.06)
    _bulge_front(body, 0.10 + aggr * 0.05)
    _round_block(body, 0.09 + aggr * 0.02)
    assign_material(body, "rm_white_armor_mat")

    return _finish(body)


def _build_waist(aggr: float, torso_h: float) -> str:
    r = 0.20 + aggr * 0.05
    h = torso_h * 0.12
    waist = mc.polyCylinder(r=r, h=h, sa=8, name="rm_torso_waist_#")[0]
    mc.move(0, -torso_h * 0.42, 0, waist, relative=True)
    assign_material(waist, "rm_graphite_mat")
    return _finish(waist)


def _build_reactor(aggr: float, body: str) -> str:
    grp = mc.group(empty=True, name="rm_torso_reactor_#")
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = bb[1] + (bb[4] - bb[1]) * 0.64
    cz = bb[5] - 0.02
    s = 1.0 + aggr * 0.18

    outer = mc.polyTorus(
        r=0.40 * s, sr=0.045 * s, sa=18, sh=8, name="rm_reactor_outer_#",
    )[0]
    mc.rotate(90, 0, 0, outer)

    inner = mc.polyTorus(
        r=0.28 * s, sr=0.030 * s, sa=14, sh=6, name="rm_reactor_inner_#",
    )[0]
    mc.rotate(90, 45, 0, inner)

    core = mc.polyCube(w=0.16 * s, h=0.16 * s, d=0.16 * s, name="rm_reactor_core_#")[0]
    mc.rotate(45, 45, 0, core)
    mc.scale(1.0, 2.0, 1.0, core)

    spikes = []
    spike_r = 0.34 * s
    for i in range(4):
        sp = mc.polyCone(r=0.07 * s, h=0.14 * s, sa=4, name=f"rm_reactor_spike_{i}_#")[0]
        ang = math.radians(i * 90 + 45)
        mc.move(
            spike_r * math.cos(ang), spike_r * 0.12 * math.sin(ang), 0.06 * s,
            sp, relative=True,
        )
        mc.rotate(90, math.degrees(ang) + 90, 0, sp, relative=True)
        spikes.append(sp)

    mc.parent(outer, inner, core, *spikes, grp)
    assign_material(outer, "rm_graphite_mat")
    assign_material(inner, "rm_cyan_glow_mat")
    assign_material(core, "rm_cyan_glow_mat")
    for sp in spikes:
        assign_material(sp, "rm_graphite_mat")
    mc.move(cx, cy, cz, grp, absolute=True)
    return grp


def _build_chest_strip(aggr: float, body: str) -> str:
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = bb[1] + (bb[4] - bb[1]) * 0.34
    cz = bb[5] + 0.015
    strip = mc.polyCube(w=0.09 + aggr * 0.03, h=0.58, d=0.035,
                        name="rm_torso_cyan_strip_#")[0]
    mc.move(cx, cy, cz, strip, absolute=True)
    assign_material(strip, "rm_cyan_glow_mat")
    try:
        mc.polyBevel(strip, offset=0.012, segments=1, chamfer=0, ch=0)
        mc.polySoftEdge(strip, angle=0, ch=0)
    except Exception:
        pass
    if mc.objExists(strip):
        mc.delete(strip, ch=True)
    return strip


def _build_shoulder_pads(aggr: float, torso_h: float, sep: float) -> tuple:
    """Layered shoulder pods: dark mechanical root plus angled white armor."""
    pad_w = 0.42 + aggr * 0.18
    pad_h = 0.34 + aggr * 0.10
    pad_d = 0.92 + aggr * 0.10
    y = torso_h * 0.30
    spread = 1.06 + sep * 0.20

    pads = []
    for side, label in ((-1.0, "l"), (1.0, "r")):
        grp = mc.group(empty=True, name=f"rm_torso_shoulder_{label}_#")

        socket = mc.polyCylinder(r=0.22 + aggr * 0.04, h=0.28, sa=10,
                                 name=f"rm_torso_shoulder_socket_{label}_#")[0]
        mc.rotate(90, 0, 0, socket)
        mc.move(side * (spread - 0.08), y - 0.02, 0.02, socket, relative=True)
        assign_material(socket, "rm_graphite_mat")
        _finish(socket)

        armor = mc.polyCube(w=pad_w, h=pad_h, d=pad_d,
                            sx=2, sy=1, sz=2,
                            name=f"rm_torso_pad_{label}_#")[0]
        mc.move(side * spread, y + 0.08, -0.06, armor, relative=True)
        mc.rotate(0, 0, -8 * side, armor)
        mc.scale(1.0, 0.86, 1.08, armor)
        assign_material(armor, "rm_white_armor_mat")
        _round_block(armor, 0.035)
        _finish(armor)

        trim = mc.polyCube(w=0.08, h=pad_h * 0.72, d=pad_d * 0.72,
                           name=f"rm_torso_pad_trim_{label}_#")[0]
        mc.move(side * (spread + pad_w * 0.44), y + 0.03, -0.02,
                trim, relative=True)
        mc.rotate(0, 0, -8 * side, trim)
        assign_material(trim, "rm_graphite_mat")
        _finish(trim)

        mc.parent(socket, armor, trim, grp)
        pads.append(grp)

    return tuple(pads)


@register('TORSO')
class TorsoModule(BaseModule):
    MODULE_NAME = 'TORSO'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_torso_DEBUG'

        grp = mc.group(empty=True, name='rm_torso_#')

        aggr = self._get('aggressiveness', 0.5)
        h_sc = self._get('height_scale', 1.0)
        sep = self._get('separation', 0.35)
        torso_h = 2.0 * h_sc

        body = _build_main_torso(aggr, torso_h)
        waist = _build_waist(aggr, torso_h)
        reactor = _build_reactor(aggr, body)
        chest_strip = _build_chest_strip(aggr, body)
        pad_l, pad_r = _build_shoulder_pads(aggr, torso_h, sep)

        stub = mc.polyCylinder(r=0.12 + aggr * 0.03, h=0.20, sa=8,
                               name="rm_torso_stub_#")[0]
        mc.move(0, -(torso_h * 0.52), 0, stub, relative=True)
        assign_material(stub, "rm_graphite_mat")

        mc.parent(body, waist, reactor, chest_strip, pad_l, pad_r, stub, grp)
        return self._finalize_group(grp, position, rotation, scale)
