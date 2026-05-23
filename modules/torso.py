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
            mesh, divisionsU=0, divisionsV=0,
            pointsWire=4, pointsShaded=1, polygonObject=1,
        )
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def _block(name: str, w: float, h: float, d: float,
           pos: tuple, rot: tuple = (0, 0, 0),
           mat: str = "rm_white_armor_mat",
           bevel: float = 0.025,
           hard: bool = True) -> str:
    node = mc.polyCube(w=w, h=h, d=d, sx=2, sy=2, sz=1, name=name)[0]
    mc.move(pos[0], pos[1], pos[2], node, absolute=True)
    mc.rotate(rot[0], rot[1], rot[2], node)
    assign_material(node, mat)
    try:
        if bevel > 0:
            mc.polyBevel(node, offset=bevel, segments=1, chamfer=0, ch=0)
        mc.polySoftEdge(node, angle=0 if hard else 45, ch=0)
    except Exception:
        pass
    if mc.objExists(node):
        mc.delete(node, ch=True)
    return node


def _keel(name: str, r: float, h: float, pos: tuple,
          mat: str = "rm_white_armor_mat") -> str:
    node = mc.polyCone(r=r, h=h, sa=4, name=name)[0]
    mc.move(pos[0], pos[1], pos[2], node, absolute=True)
    mc.rotate(180, 45, 0, node)
    mc.scale(0.70, 1.0, 0.38, node)
    assign_material(node, mat)
    try:
        mc.polySoftEdge(node, angle=0, ch=0)
    except Exception:
        pass
    if mc.objExists(node):
        mc.delete(node, ch=True)
    return node


def _build_main_torso(aggr: float, torso_h: float, style: str) -> str:
    """Cuerpo cúbico ancho arriba; caras de abajo escaladas pequeñas."""
    if style == "heavy":
        w = 2.10 + aggr * 0.22
        h = torso_h * 0.76
        d = 1.34 + aggr * 0.12
        bottom_scale = 0.86
        top_scale = 1.18 + aggr * 0.10
        bottom_face = 0.46 + aggr * 0.06
        bevel = 0.075 + aggr * 0.015
    elif style == "slim":
        w = 1.36 + aggr * 0.08
        h = torso_h * 0.98
        d = 0.96 + aggr * 0.04
        bottom_scale = 0.50
        top_scale = 0.96 + aggr * 0.06
        bottom_face = 0.26 + aggr * 0.04
        bevel = 0.070 + aggr * 0.015
    elif style == "compact":
        w = 1.58 + aggr * 0.12
        h = torso_h * 0.66
        d = 1.08 + aggr * 0.04
        bottom_scale = 0.70
        top_scale = 1.02 + aggr * 0.06
        bottom_face = 0.42 + aggr * 0.04
        bevel = 0.085 + aggr * 0.018
    else:
        w = 1.82 + aggr * 0.12
        h = torso_h * 0.82
        d = 1.18 + aggr * 0.06
        bottom_scale = 0.72
        top_scale = 1.10 + aggr * 0.08
        bottom_face = 0.34 + aggr * 0.06
        bevel = 0.09 + aggr * 0.02

    body = mc.polyCube(
        w=w, h=h, d=d,
        sx=5, sy=6, sz=5,
        name="rm_torso_body_#",
    )[0]
    mc.move(0, torso_h * 0.08, 0.02, body, relative=True)

    bb = mc.exactWorldBoundingBox(body)
    _taper_y(body, bb[1], bb[4], bottom_scale, top_scale)
    _scale_bottom_faces(body, y_band=0.16, face_scale=bottom_face)
    _bulge_front(body, 0.10 + aggr * 0.05)
    _round_block(body, bevel)
    assign_material(body, "rm_white_armor_mat")

    return _finish(body)


def _build_layered_torso(aggr: float, torso_h: float, style: str) -> str:
    """High-quality torso shell made from separated armor plates."""
    if style == "heavy":
        cfg = {
            "spine": (0.66, torso_h * 0.92, 0.76),
            "upper": (0.78 + aggr * 0.08, torso_h * 0.48, 0.24),
            "lower": (0.55 + aggr * 0.05, torso_h * 0.32, 0.20),
            "x": 0.44,
            "upper_y": torso_h * 0.18,
            "lower_y": -torso_h * 0.28,
            "z": 0.42,
            "rot": 7.0,
            "keel": (0.24, torso_h * 0.42, -torso_h * 0.55),
        }
    elif style == "slim":
        cfg = {
            "spine": (0.36, torso_h * 1.05, 0.58),
            "upper": (0.44 + aggr * 0.04, torso_h * 0.56, 0.18),
            "lower": (0.30 + aggr * 0.03, torso_h * 0.44, 0.16),
            "x": 0.28,
            "upper_y": torso_h * 0.22,
            "lower_y": -torso_h * 0.32,
            "z": 0.36,
            "rot": 4.0,
            "keel": (0.15, torso_h * 0.55, -torso_h * 0.62),
        }
    elif style == "compact":
        cfg = {
            "spine": (0.58, torso_h * 0.72, 0.66),
            "upper": (0.62 + aggr * 0.05, torso_h * 0.34, 0.22),
            "lower": (0.48 + aggr * 0.04, torso_h * 0.28, 0.18),
            "x": 0.34,
            "upper_y": torso_h * 0.10,
            "lower_y": -torso_h * 0.22,
            "z": 0.39,
            "rot": 5.0,
            "keel": (0.18, torso_h * 0.26, -torso_h * 0.44),
        }
    else:
        cfg = {
            "spine": (0.50, torso_h * 0.88, 0.66),
            "upper": (0.58 + aggr * 0.05, torso_h * 0.46, 0.22),
            "lower": (0.40 + aggr * 0.04, torso_h * 0.34, 0.18),
            "x": 0.36,
            "upper_y": torso_h * 0.18,
            "lower_y": -torso_h * 0.30,
            "z": 0.40,
            "rot": 6.0,
            "keel": (0.20, torso_h * 0.38, -torso_h * 0.54),
        }

    grp = mc.group(empty=True, name="rm_torso_body_#")
    parts = []

    spine_w, spine_h, spine_d = cfg["spine"]
    parts.append(_block("rm_torso_inner_spine_#", spine_w, spine_h, spine_d,
                        (0, -torso_h * 0.02, 0.02),
                        mat="rm_graphite_mat", bevel=0.035, hard=True))
    parts.append(_block("rm_torso_front_channel_#", spine_w * 0.48,
                        spine_h * 0.74, 0.08,
                        (0, -torso_h * 0.02, cfg["z"] + 0.04),
                        mat="rm_graphite_mat", bevel=0.014, hard=True))

    upper_w, upper_h, upper_d = cfg["upper"]
    lower_w, lower_h, lower_d = cfg["lower"]
    rear_z = -(spine_d * 0.50) - 0.08
    parts.append(_block("rm_torso_back_spine_#", spine_w * 0.58,
                        spine_h * 0.62, 0.16,
                        (0, -torso_h * 0.04, rear_z),
                        mat="rm_graphite_mat", bevel=0.018, hard=True))
    parts.append(_block("rm_torso_back_armor_#", spine_w * 0.88,
                        spine_h * 0.30, 0.18,
                        (0, cfg["upper_y"] + upper_h * 0.04, rear_z - 0.06),
                        mat="rm_white_armor_mat", bevel=0.030, hard=True))
    parts.append(_block("rm_torso_back_lower_#", spine_w * 0.62,
                        spine_h * 0.24, 0.15,
                        (0, cfg["lower_y"] - lower_h * 0.05, rear_z - 0.04),
                        mat="rm_white_armor_mat", bevel=0.026, hard=True))

    for side in (-1.0, 1.0):
        parts.append(_block("rm_torso_chest_plate_#", upper_w, upper_h, upper_d,
                            (side * cfg["x"], cfg["upper_y"], cfg["z"]),
                            rot=(0, 0, -cfg["rot"] * side),
                            mat="rm_white_armor_mat", bevel=0.035, hard=True))
        parts.append(_block("rm_torso_abdomen_plate_#", lower_w, lower_h, lower_d,
                            (side * cfg["x"] * 0.62,
                             cfg["lower_y"], cfg["z"] + 0.01),
                            rot=(0, 0, cfg["rot"] * 0.55 * side),
                            mat="rm_white_armor_mat", bevel=0.030, hard=True))
        parts.append(_block("rm_torso_side_armor_#", 0.18, spine_h * 0.44, 0.42,
                            (side * (cfg["x"] + upper_w * 0.48),
                             cfg["upper_y"] - upper_h * 0.12, 0.08),
                            rot=(0, 8 * side, -cfg["rot"] * 0.45 * side),
                            mat="rm_white_armor_mat", bevel=0.026, hard=True))
        parts.append(_block("rm_torso_side_dark_joint_#", 0.10, spine_h * 0.54, 0.28,
                            (side * (cfg["x"] + upper_w * 0.34),
                             cfg["upper_y"] - upper_h * 0.20, -0.10),
                            rot=(0, 6 * side, 0),
                            mat="rm_graphite_mat", bevel=0.014, hard=True))

    keel_r, keel_h, keel_y = cfg["keel"]
    parts.append(_keel("rm_torso_lower_keel_#", keel_r, keel_h,
                       (0, keel_y, cfg["z"] - 0.02)))

    if style == "heavy":
        for side in (-1.0, 1.0):
            parts.append(_block("rm_torso_heavy_outer_#", 0.20, spine_h * 0.64, 0.18,
                                (side * (cfg["x"] + upper_w * 0.58),
                                 cfg["upper_y"] - 0.05, cfg["z"] - 0.02),
                                rot=(0, 0, -4 * side),
                                mat="rm_graphite_mat", bevel=0.018, hard=True))
    elif style == "slim":
        parts.append(_block("rm_torso_slim_center_#", 0.12, spine_h * 0.80, 0.06,
                            (0, -torso_h * 0.02, cfg["z"] + 0.09),
                            mat="rm_cyan_glow_mat", bevel=0.006, hard=True))
    elif style == "compact":
        parts.append(_block("rm_torso_compact_brow_#", spine_w * 1.25, 0.14, 0.16,
                            (0, cfg["upper_y"] + upper_h * 0.48, cfg["z"] + 0.02),
                            mat="rm_graphite_mat", bevel=0.018, hard=True))

    mc.parent(parts, grp)
    return grp


def _build_waist(aggr: float, torso_h: float) -> str:
    r = 0.20 + aggr * 0.05
    h = torso_h * 0.12
    waist = mc.polyCylinder(r=r, h=h, sa=4, name="rm_torso_waist_#")[0]
    mc.move(0, -torso_h * 0.42, 0, waist, relative=True)
    assign_material(waist, "rm_graphite_mat")
    return _finish(waist)


def _build_reactor(aggr: float, body: str, style: str) -> str:
    grp = mc.group(empty=True, name="rm_torso_reactor_#")
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = bb[1] + (bb[4] - bb[1]) * 0.64
    cz = bb[5] - 0.02
    s = 1.0 + aggr * 0.18

    if style == "column":
        frame = mc.polyCube(w=0.28 * s, h=0.78 * s, d=0.075 * s,
                            name="rm_reactor_column_frame_#")[0]
        glow = mc.polyCube(w=0.09 * s, h=0.64 * s, d=0.040 * s,
                           name="rm_reactor_column_glow_#")[0]
        cap_top = mc.polyCube(w=0.34 * s, h=0.08 * s, d=0.09 * s,
                              name="rm_reactor_column_cap_top_#")[0]
        cap_bot = mc.polyCube(w=0.34 * s, h=0.08 * s, d=0.09 * s,
                              name="rm_reactor_column_cap_bot_#")[0]
        mc.move(0, 0.35 * s, 0.02 * s, cap_top, relative=True)
        mc.move(0, -0.35 * s, 0.02 * s, cap_bot, relative=True)
        assign_material(frame, "rm_graphite_mat")
        assign_material(cap_top, "rm_graphite_mat")
        assign_material(cap_bot, "rm_graphite_mat")
        assign_material(glow, "rm_cyan_glow_mat")
        for part in (frame, glow, cap_top, cap_bot):
            try:
                mc.polyBevel(part, offset=0.010 * s, segments=1, chamfer=0, ch=0)
                mc.polySoftEdge(part, angle=0, ch=0)
            except Exception:
                pass
            if mc.objExists(part):
                mc.delete(part, ch=True)
        mc.parent(frame, glow, cap_top, cap_bot, grp)
        mc.move(cx, cy - 0.05 * s, cz + 0.01 * s, grp, absolute=True)
        return grp

    if style == "orb":
        shell = mc.polyTorus(r=0.34 * s, sr=0.050 * s, sa=24, sh=8,
                             name="rm_reactor_orb_ring_#")[0]
        mc.rotate(90, 0, 0, shell)
        core = mc.polySphere(r=0.17 * s, sa=14, sh=8,
                             name="rm_reactor_orb_core_#")[0]
        mc.scale(1.0, 1.0, 0.45, core)
        halo = mc.polyTorus(r=0.24 * s, sr=0.016 * s, sa=24, sh=4,
                            name="rm_reactor_orb_halo_#")[0]
        mc.rotate(90, 35, 0, halo)
        assign_material(shell, "rm_graphite_mat")
        assign_material(core, "rm_cyan_glow_mat")
        assign_material(halo, "rm_cyan_glow_mat")
        mc.parent(shell, core, halo, grp)
        mc.move(cx, cy, cz, grp, absolute=True)
        return grp

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


def _build_style_details(style: str, aggr: float, body: str) -> list:
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = (bb[1] + bb[4]) * 0.5
    cz = bb[5] + 0.02
    half_w = (bb[3] - bb[0]) * 0.5
    parts = []

    if style == "heavy":
        for side in (-1.0, 1.0):
            slab = mc.polyCube(w=0.22 + aggr * 0.04,
                               h=(bb[4] - bb[1]) * 0.56,
                               d=0.18,
                               name="rm_torso_heavy_slab_#")[0]
            mc.move(cx + side * half_w * 0.66, cy - 0.05, cz,
                    slab, absolute=True)
            assign_material(slab, "rm_graphite_mat")
            _finish(slab)
            parts.append(slab)

    elif style == "slim":
        for side in (-1.0, 1.0):
            fin = mc.polyCone(r=0.08 + aggr * 0.02, h=0.58, sa=4,
                              name="rm_torso_slim_fin_#")[0]
            mc.move(cx + side * half_w * 0.52, bb[4] - 0.18, cz - 0.02,
                    fin, absolute=True)
            mc.rotate(0, 0, -14 * side, fin)
            mc.scale(0.65, 1.0, 0.22, fin)
            assign_material(fin, "rm_white_armor_mat")
            _finish(fin)
            parts.append(fin)

    elif style == "compact":
        collar = mc.polyCube(w=(bb[3] - bb[0]) * 0.72, h=0.16, d=0.18,
                             name="rm_torso_compact_collar_#")[0]
        mc.move(cx, bb[4] - 0.08, cz, collar, absolute=True)
        assign_material(collar, "rm_graphite_mat")
        _finish(collar)
        parts.append(collar)

    return parts


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

        socket = mc.polyCylinder(r=0.22 + aggr * 0.04, h=0.28, sa=4,
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
        torso_style = self._get('torso_style', 'core')
        nucleus_style = self._get('nucleus_style', 'ring')
        torso_h = 2.0 * h_sc

        body = _build_layered_torso(aggr, torso_h, torso_style)
        waist = _build_waist(aggr, torso_h)
        reactor = _build_reactor(aggr, body, nucleus_style)
        chest_strip = _build_chest_strip(aggr, body)
        style_parts = _build_style_details(torso_style, aggr, body)
        pad_l, pad_r = _build_shoulder_pads(aggr, torso_h, sep)

        stub = mc.polyCylinder(r=0.12 + aggr * 0.03, h=0.20, sa=4,
                               name="rm_torso_stub_#")[0]
        mc.move(0, -(torso_h * 0.52), 0, stub, relative=True)
        assign_material(stub, "rm_graphite_mat")

        mc.parent(body, waist, reactor, chest_strip, *style_parts,
                  pad_l, pad_r, stub, grp)
        return self._finalize_group(grp, position, rotation, scale)
