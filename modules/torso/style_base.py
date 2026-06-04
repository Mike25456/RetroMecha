"""
RetroMecha — modules/torso/style_base.py
Estilos existentes: core, heavy, slim, compact.
Contiene cuerpo laminado + reactor (ring/column/orb) + waist + shoulders.
"""
import math
from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from modules.torso._shared import (
    taper_y, scale_bottom_faces, bulge_front, round_block,
    finish, finish_bevel, block, keel, bbox_center,
)
from utils.maya_materials import assign_material


@dataclass(frozen=True)
class TorsoTune:
    width: float = 1.0
    depth: float = 1.0
    detail: float = 1.0
    shoulder: float = 1.0

    @classmethod
    def from_params(cls, getter) -> 'TorsoTune':
        return cls(
            width=float(getter('torso_width_mul', 1.0)),
            depth=float(getter('torso_depth_mul', 1.0)),
            detail=float(getter('torso_detail_mul', 1.0)),
            shoulder=float(getter('torso_shoulder_mul', 1.0)),
        )


@dataclass(frozen=True)
class NucleusTune:
    size: float = 1.0
    glow: float = 1.0

    @classmethod
    def from_params(cls, getter) -> 'NucleusTune':
        return cls(
            size=float(getter('nucleus_size_mul', 1.0)),
            glow=float(getter('nucleus_glow_mul', 1.0)),
        )


def _build_main_torso(aggr: float, torso_h: float, style: str) -> str:
    """Cuerpo cúbico ancho arriba; caras de abajo escaladas pequeñas."""
    if style == "heavy":
        w = 2.10 + aggr * 0.66
        h = torso_h * 0.76
        d = 1.34 + aggr * 0.36
        bottom_scale = 0.86
        top_scale = 1.18 + aggr * 0.30
        bottom_face = 0.46 + aggr * 0.18
        bevel = 0.075 + aggr * 0.045
    elif style == "slim":
        w = 1.36 + aggr * 0.24
        h = torso_h * 0.98
        d = 0.96 + aggr * 0.12
        bottom_scale = 0.50
        top_scale = 0.96 + aggr * 0.18
        bottom_face = 0.26 + aggr * 0.12
        bevel = 0.070 + aggr * 0.045
    elif style == "compact":
        w = 1.58 + aggr * 0.36
        h = torso_h * 0.66
        d = 1.08 + aggr * 0.12
        bottom_scale = 0.70
        top_scale = 1.02 + aggr * 0.18
        bottom_face = 0.42 + aggr * 0.12
        bevel = 0.085 + aggr * 0.054
    else:
        w = 1.82 + aggr * 0.36
        h = torso_h * 0.82
        d = 1.18 + aggr * 0.18
        bottom_scale = 0.72
        top_scale = 1.10 + aggr * 0.24
        bottom_face = 0.34 + aggr * 0.18
        bevel = 0.09 + aggr * 0.06

    body = mc.polyCube(w=w, h=h, d=d, sx=5, sy=6, sz=5,
                       name="rm_torso_body_#")[0]
    mc.move(0, torso_h * 0.08, 0.02, body, relative=True)

    bb = mc.exactWorldBoundingBox(body)
    taper_y(body, bb[1], bb[4], bottom_scale, top_scale)
    scale_bottom_faces(body, y_band=0.16, face_scale=bottom_face)
    bulge_front(body, 0.10 + aggr * 0.15)
    round_block(body, bevel)
    return finish(body)


def _build_layered_torso(aggr: float, torso_h: float, style: str,
                         tune: TorsoTune | None = None) -> str:
    """High-quality torso shell made from separated armor plates."""
    if tune is None:
        tune = TorsoTune()
    wm = tune.width
    dm = tune.depth
    if style == "heavy":
        cfg = {
            "spine": (0.66 * wm, torso_h * 0.92, 0.76 * dm),
            "upper": ((0.78 + aggr * 0.24) * wm, torso_h * 0.48, 0.24 * dm),
            "lower": ((0.55 + aggr * 0.15) * wm, torso_h * 0.32, 0.20 * dm),
            "x": 0.44 * wm,
            "upper_y": torso_h * 0.18,
            "lower_y": -torso_h * 0.28,
            "z": 0.42 * dm,
            "rot": 7.0,
            "keel": (0.24 * wm, torso_h * 0.42, -torso_h * 0.55),
        }
    elif style == "slim":
        cfg = {
            "spine": (0.36 * wm, torso_h * 1.05, 0.58 * dm),
            "upper": ((0.44 + aggr * 0.12) * wm, torso_h * 0.56, 0.18 * dm),
            "lower": ((0.30 + aggr * 0.09) * wm, torso_h * 0.44, 0.16 * dm),
            "x": 0.28 * wm,
            "upper_y": torso_h * 0.22,
            "lower_y": -torso_h * 0.32,
            "z": 0.36 * dm,
            "rot": 4.0,
            "keel": (0.15 * wm, torso_h * 0.55, -torso_h * 0.62),
        }
    elif style == "compact":
        cfg = {
            "spine": (0.58 * wm, torso_h * 0.72, 0.66 * dm),
            "upper": ((0.62 + aggr * 0.15) * wm, torso_h * 0.34, 0.22 * dm),
            "lower": ((0.48 + aggr * 0.12) * wm, torso_h * 0.28, 0.18 * dm),
            "x": 0.34 * wm,
            "upper_y": torso_h * 0.10,
            "lower_y": -torso_h * 0.22,
            "z": 0.39 * dm,
            "rot": 5.0,
            "keel": (0.18 * wm, torso_h * 0.26, -torso_h * 0.44),
        }
    else:
        cfg = {
            "spine": (0.50 * wm, torso_h * 0.88, 0.66 * dm),
            "upper": ((0.58 + aggr * 0.15) * wm, torso_h * 0.46, 0.22 * dm),
            "lower": ((0.40 + aggr * 0.12) * wm, torso_h * 0.34, 0.18 * dm),
            "x": 0.36 * wm,
            "upper_y": torso_h * 0.18,
            "lower_y": -torso_h * 0.30,
            "z": 0.40 * dm,
            "rot": 6.0,
            "keel": (0.20 * wm, torso_h * 0.38, -torso_h * 0.54),
        }

    grp = mc.group(empty=True, name="rm_torso_body_#")
    parts = []
    b_mul = tune.detail

    spine_w, spine_h, spine_d = cfg["spine"]
    parts.append(block("rm_torso_inner_spine_#", spine_w, spine_h, spine_d,
                        (0, -torso_h * 0.02, 0.02),
                        bevel=b_mul * 0.035, hard=True))
    parts.append(block("rm_torso_front_channel_#", spine_w * 0.48,
                        spine_h * 0.74, 0.08,
                        (0, -torso_h * 0.02, cfg["z"] + 0.04),
                        bevel=b_mul * 0.014, hard=True))

    upper_w, upper_h, upper_d = cfg["upper"]
    lower_w, lower_h, lower_d = cfg["lower"]
    rear_z = -(spine_d * 0.50) - 0.08
    parts.append(block("rm_torso_back_spine_#", spine_w * 0.58,
                        spine_h * 0.62, 0.16,
                        (0, -torso_h * 0.04, rear_z),
                        bevel=b_mul * 0.018, hard=True))
    parts.append(block("rm_torso_back_armor_#", spine_w * 0.88,
                        spine_h * 0.30, 0.18,
                        (0, cfg["upper_y"] + upper_h * 0.04, rear_z - 0.06),
                        bevel=b_mul * 0.030, hard=True))
    parts.append(block("rm_torso_back_lower_#", spine_w * 0.62,
                        spine_h * 0.24, 0.15,
                        (0, cfg["lower_y"] - lower_h * 0.05, rear_z - 0.04),
                        bevel=b_mul * 0.026, hard=True))

    for side in (-1.0, 1.0):
        parts.append(block("rm_torso_chest_plate_#", upper_w, upper_h, upper_d,
                            (side * cfg["x"], cfg["upper_y"], cfg["z"]),
                            rot=(0, 0, -cfg["rot"] * side),
                            bevel=b_mul * 0.035, hard=True))
        parts.append(block("rm_torso_abdomen_plate_#", lower_w, lower_h, lower_d,
                            (side * cfg["x"] * 0.62, cfg["lower_y"], cfg["z"] + 0.01),
                            rot=(0, 0, cfg["rot"] * 0.55 * side),
                            bevel=b_mul * 0.030, hard=True))
        parts.append(block("rm_torso_side_armor_#", 0.18, spine_h * 0.44, 0.42,
                            (side * (cfg["x"] + upper_w * 0.48),
                             cfg["upper_y"] - upper_h * 0.12, 0.08),
                            rot=(0, 8 * side, -cfg["rot"] * 0.45 * side),
                            bevel=b_mul * 0.026, hard=True))
        parts.append(block("rm_torso_side_dark_joint_#", 0.10, spine_h * 0.54, 0.28,
                            (side * (cfg["x"] + upper_w * 0.34),
                             cfg["upper_y"] - upper_h * 0.20, -0.10),
                            rot=(0, 6 * side, 0),
                            bevel=b_mul * 0.014, hard=True))

    keel_r, keel_h, keel_y = cfg["keel"]
    parts.append(keel("rm_torso_lower_keel_#", keel_r, keel_h,
                       (0, keel_y, cfg["z"] - 0.02)))

    if style == "heavy":
        for side in (-1.0, 1.0):
            parts.append(block("rm_torso_heavy_outer_#", 0.20, spine_h * 0.64, 0.18,
                                (side * (cfg["x"] + upper_w * 0.58),
                                 cfg["upper_y"] - 0.05, cfg["z"] - 0.02),
                                rot=(0, 0, -4 * side),
                                bevel=b_mul * 0.018, hard=True))
    elif style == "slim":
        parts.append(block("rm_torso_slim_center_#", 0.12, spine_h * 0.80, 0.06,
                            (0, -torso_h * 0.02, cfg["z"] + 0.09),
                            bevel=b_mul * 0.006, hard=True))
    elif style == "compact":
        parts.append(block("rm_torso_compact_brow_#", spine_w * 1.25, 0.14, 0.16,
                            (0, cfg["upper_y"] + upper_h * 0.48, cfg["z"] + 0.02),
                            bevel=b_mul * 0.018, hard=True))

    mc.parent(parts, grp)
    return grp


def build_waist(aggr: float, y_pos: float) -> str:
    r = 0.20 + aggr * 0.15
    h = 0.24
    waist = mc.polyCylinder(r=r, h=h, sa=4, name="rm_torso_waist_#")[0]
    mc.move(0, y_pos, 0, waist, relative=True)
    return finish(waist)


def build_reactor(aggr: float, body: str, style: str,
                   ntune: NucleusTune | None = None) -> str:
    grp = mc.group(empty=True, name="rm_torso_reactor_#")
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = bb[1] + (bb[4] - bb[1]) * 0.64
    cz = bb[5] - 0.02
    if ntune is None:
        ntune = NucleusTune()
    s = (1.0 + aggr * 0.54) * ntune.size
    g_mul = ntune.glow

    if style == "column":
        frame = mc.polyCube(w=0.28 * s, h=0.78 * s, d=0.075 * s,
                            name="rm_reactor_column_frame_#")[0]
        glow = mc.polyCube(w=0.09 * s * g_mul, h=0.64 * s * g_mul, d=0.040 * s * g_mul,
                           name="rm_reactor_column_glow_#")[0]
        cap_top = mc.polyCube(w=0.34 * s, h=0.08 * s, d=0.09 * s,
                              name="rm_reactor_column_cap_top_#")[0]
        cap_bot = mc.polyCube(w=0.34 * s, h=0.08 * s, d=0.09 * s,
                              name="rm_reactor_column_cap_bot_#")[0]
        mc.move(0, 0.35 * s, 0.02 * s, cap_top, relative=True)
        mc.move(0, -0.35 * s, 0.02 * s, cap_bot, relative=True)
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
        core = mc.polySphere(r=0.17 * s * g_mul, sa=14, sh=8,
                             name="rm_reactor_orb_core_#")[0]
        mc.scale(1.0, 1.0, 0.45, core)
        halo = mc.polyTorus(r=0.24 * s * g_mul, sr=0.016 * s * g_mul, sa=24, sh=4,
                            name="rm_reactor_orb_halo_#")[0]
        mc.rotate(90, 35, 0, halo)
        mc.parent(shell, core, halo, grp)
        mc.move(cx, cy, cz, grp, absolute=True)
        return grp

    if style == "cross":
        size = s * 0.45
        lz = cz + 0.04

        outer_ring = mc.polyTorus(r=size * 0.92, sr=size * 0.068 * g_mul,
                                  sa=24, sh=6,
                                  name='rm_reactor_cross_outer_#')[0]
        mc.rotate(90, 0, 0, outer_ring)
        mc.move(0, 0, size * 0.018, outer_ring, relative=True)
        assign_material(outer_ring, 'rm_graphite_mat')
        finish_bevel(outer_ring, 0.0, hard=True)

        arm_configs = [
            (  0.0, size * 1.60, size * 0.14),
            ( 90.0, size * 1.60, size * 0.14),
            ( 45.0, size * 1.10, size * 0.09),
            (-45.0, size * 1.10, size * 0.09),
        ]
        cross_parts = [outer_ring]
        for i, (angle, length_val, width) in enumerate(arm_configs):
            arm = mc.polyCube(w=length_val, h=width, d=0.022 * size * g_mul,
                              sx=4, sy=1, sz=1,
                              name=f'rm_reactor_cross_glow_arm_{i}_#')[0]
            mc.move(0, 0, size * 0.024, arm, relative=True)
            mc.rotate(0, 0, angle, arm)

            bb_a = mc.exactWorldBoundingBox(arm)
            cx_a = (bb_a[0] + bb_a[3]) * 0.5
            for v in mc.ls(f'{arm}.vtx[*]', flatten=True) or []:
                pos = mc.pointPosition(v, w=True)
                t = abs(pos[0] - cx_a) / (length_val * 0.5 or 1.0)
                taper = 1.0 - t * 0.80
                cy_a = (bb_a[1] + bb_a[4]) * 0.5
                mc.move(pos[0], cy_a + (pos[1] - cy_a) * taper, pos[2], v, ws=True)

            assign_material(arm, 'rm_cyan_glow_mat')
            finish_bevel(arm, 0.006, hard=True)
            cross_parts.append(arm)

        cross_core = mc.polyCube(w=size * 0.32, h=size * 0.32, d=size * 0.10 * g_mul,
                                 name='rm_reactor_cross_glow_core_#')[0]
        mc.rotate(0, 0, 45, cross_core)
        mc.move(0, 0, size * 0.032, cross_core, relative=True)
        assign_material(cross_core, 'rm_cyan_glow_mat')
        finish_bevel(cross_core, 0.014, hard=True)
        cross_parts.append(cross_core)

        inner_glow = mc.polyTorus(r=size * 0.42, sr=size * 0.038 * g_mul,
                                  sa=20, sh=4,
                                  name='rm_reactor_cross_glow_inner_#')[0]
        mc.rotate(90, 0, 0, inner_glow)
        mc.move(0, 0, size * 0.026, inner_glow, relative=True)
        assign_material(inner_glow, 'rm_cyan_glow_mat')
        finish_bevel(inner_glow, 0.0)
        cross_parts.append(inner_glow)

        for i, angle_deg in enumerate([0, 90, 180, 270]):
            angle_rad = math.radians(angle_deg)
            gx = math.cos(angle_rad) * size * 0.74
            gy = math.sin(angle_rad) * size * 0.74
            gem = mc.polyCylinder(r=size * 0.068, h=0.028 * size, sa=4,
                                  name=f'rm_reactor_cross_glow_gem_{i}_#')[0]
            mc.rotate(90, 45, 0, gem)
            mc.move(gx, gy, size * 0.030, gem, relative=True)
            assign_material(gem, 'rm_cyan_glow_mat')
            finish_bevel(gem, 0.0, hard=True)
            cross_parts.append(gem)

        mc.parent(cross_parts, grp)
        mc.move(cx, cy, lz, grp, absolute=True)
        return grp

    if style == "orb_cluster":
        cluster_z = cz + 0.04
        orb_configs = [
            ( 0.00, 0.00, 0.096),
            ( 0.13, 0.10, 0.058),
            (-0.13, 0.10, 0.058),
            ( 0.10, -0.12, 0.048),
            (-0.10, -0.12, 0.048),
        ]
        oc_parts = []
        for i, (ox, oy, r) in enumerate(orb_configs):
            ring = mc.polyTorus(r=r * s * 1.35, sr=r * s * 0.18 * g_mul,
                                sa=16, sh=4,
                                name=f'rm_reactor_orb_cluster_glow_ring_{i}_#')[0]
            mc.rotate(90, i * 22, 0, ring)
            mc.move(ox * s, oy * s, 0, ring, relative=True)
            assign_material(ring, 'rm_cyan_glow_mat')
            finish_bevel(ring, 0.0, hard=True)
            oc_parts.append(ring)

            core = mc.polySphere(r=r * s * 0.72, sa=10, sh=6,
                                 name=f'rm_reactor_orb_cluster_core_{i}_#')[0]
            mc.scale(1.0, 1.0, 0.55, core)
            mc.move(ox * s, oy * s, 0.012 * s, core, relative=True)
            assign_material(core, 'rm_cyan_glow_mat')
            finish_bevel(core, 0.0)
            oc_parts.append(core)

        mount = mc.polyCube(w=0.44 * s, h=0.44 * s, d=0.04 * s,
                            name='rm_reactor_orb_cluster_mount_#')[0]
        mc.move(0, 0, -0.032 * s, mount, relative=True)
        assign_material(mount, 'rm_graphite_mat')
        finish_bevel(mount, 0.016, hard=True)
        oc_parts.append(mount)

        for a, b in [(0,1),(0,2),(0,3),(0,4)]:
            ax, ay = orb_configs[a][0], orb_configs[a][1]
            bx, by = orb_configs[b][0], orb_configs[b][1]
            dx, dy = (bx - ax) * s, (by - ay) * s
            dist = math.sqrt(dx*dx + dy*dy) or 0.01
            angle = math.degrees(math.atan2(dy, dx))
            conn = mc.polyCube(w=dist, h=0.018 * s, d=0.014 * s,
                               name=f'rm_reactor_orb_cluster_conn_{a}_{b}_#')[0]
            mc.move((ax+bx)*0.5*s, (ay+by)*0.5*s, -0.010 * s, conn, relative=True)
            mc.rotate(0, 0, angle, conn)
            assign_material(conn, 'rm_graphite_mat')
            finish_bevel(conn, 0.004, hard=True)
            oc_parts.append(conn)

        mc.parent(oc_parts, grp)
        mc.move(cx, cy, cluster_z, grp, absolute=True)
        return grp

    # ring style (default)
    outer = mc.polyTorus(r=0.40 * s, sr=0.045 * s, sa=18, sh=8,
                         name="rm_reactor_outer_#")[0]
    mc.rotate(90, 0, 0, outer)
    assign_material(outer, 'rm_graphite_mat')

    inner = mc.polyTorus(r=0.28 * s * g_mul, sr=0.030 * s * g_mul, sa=14, sh=6,
                         name="rm_reactor_inner_#")[0]
    mc.rotate(90, 45, 0, inner)
    assign_material(inner, 'rm_cyan_glow_mat')

    core = mc.polyCube(w=0.16 * s * g_mul, h=0.16 * s * g_mul, d=0.16 * s * g_mul,
                       name="rm_reactor_core_#")[0]
    mc.rotate(45, 45, 0, core)
    mc.scale(1.0, 2.0, 1.0, core)
    assign_material(core, 'rm_cyan_glow_mat')

    spikes = []
    spike_r = 0.34 * s
    for i in range(4):
        sp = mc.polyCone(r=0.07 * s, h=0.14 * s, sa=4,
                         name=f"rm_reactor_spike_{i}_#")[0]
        ang = math.radians(i * 90 + 45)
        mc.move(spike_r * math.cos(ang), spike_r * 0.12 * math.sin(ang),
                0.06 * s, sp, relative=True)
        mc.rotate(90, math.degrees(ang) + 90, 0, sp, relative=True)
        assign_material(sp, 'rm_cyan_glow_mat')
        spikes.append(sp)

    mc.parent(outer, inner, core, *spikes, grp)
    mc.move(cx, cy, cz, grp, absolute=True)
    return grp


def build_chest_strip(aggr: float, body: str) -> str:
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = bb[1] + (bb[4] - bb[1]) * 0.34
    cz = bb[5] + 0.015
    strip = mc.polyCube(w=0.09 + aggr * 0.09, h=0.58, d=0.035,
                        name="rm_torso_cyan_strip_#")[0]
    mc.move(cx, cy, cz, strip, absolute=True)
    assign_material(strip, 'rm_cyan_glow_mat')
    try:
        mc.polyBevel(strip, offset=0.012, segments=1, chamfer=0, ch=0)
        mc.polySoftEdge(strip, angle=0, ch=0)
    except Exception:
        pass
    if mc.objExists(strip):
        mc.delete(strip, ch=True)
    return strip


def build_style_details(style: str, aggr: float, body: str) -> list:
    bb = mc.exactWorldBoundingBox(body)
    cx = (bb[0] + bb[3]) * 0.5
    cy = (bb[1] + bb[4]) * 0.5
    cz = bb[5] + 0.02
    half_w = (bb[3] - bb[0]) * 0.5
    parts = []

    if style == "heavy":
        for side in (-1.0, 1.0):
            slab = mc.polyCube(w=0.22 + aggr * 0.12,
                               h=(bb[4] - bb[1]) * 0.56, d=0.18,
                               name="rm_torso_heavy_slab_#")[0]
            mc.move(cx + side * half_w * 0.66, cy - 0.05, cz, slab, absolute=True)
            finish(slab)
            parts.append(slab)

    elif style == "slim":
        for side in (-1.0, 1.0):
            fin = mc.polyCone(r=0.08 + aggr * 0.06, h=0.58, sa=4,
                              name="rm_torso_slim_fin_#")[0]
            mc.move(cx + side * half_w * 0.52, bb[4] - 0.18, cz - 0.02,
                    fin, absolute=True)
            mc.rotate(0, 0, -14 * side, fin)
            mc.scale(0.65, 1.0, 0.22, fin)
            finish(fin)
            parts.append(fin)

    elif style == "compact":
        collar = mc.polyCube(w=(bb[3] - bb[0]) * 0.72, h=0.16, d=0.18,
                             name="rm_torso_compact_collar_#")[0]
        mc.move(cx, bb[4] - 0.08, cz, collar, absolute=True)
        finish(collar)
        parts.append(collar)

    return parts


def build_shoulder_pads(aggr: float, torso_h: float,
                         tune: TorsoTune | None = None) -> tuple:
    """Layered shoulder pods: dark mechanical root plus angled white armor."""
    if tune is None:
        tune = TorsoTune()
    sm = tune.shoulder
    pad_w = (0.42 + aggr * 0.54) * sm
    pad_h = (0.34 + aggr * 0.30) * sm
    pad_d = (0.92 + aggr * 0.30) * sm
    y = torso_h * 0.30
    spread = 1.06

    pads = []
    for side, label in ((-1.0, "l"), (1.0, "r")):
        grp = mc.group(empty=True, name=f"rm_torso_shoulder_{label}_#")

        socket = mc.polyCylinder(r=0.22 + aggr * 0.12, h=0.28, sa=4,
                                 name=f"rm_torso_shoulder_socket_{label}_#")[0]
        mc.rotate(90, 0, 0, socket)
        mc.move(side * (spread - 0.08), y - 0.02, 0.02, socket, relative=True)
        assign_material(socket, 'rm_graphite_mat')
        finish(socket)

        armor = mc.polyCube(w=pad_w, h=pad_h, d=pad_d, sx=2, sy=1, sz=2,
                            name=f"rm_torso_pad_{label}_#")[0]
        mc.move(side * spread, y + 0.08, -0.06, armor, relative=True)
        mc.rotate(0, 0, -8 * side, armor)
        mc.scale(1.0, 0.86, 1.08, armor)
        round_block(armor, 0.035)
        assign_material(armor, 'rm_white_armor_mat')
        finish(armor)

        trim = mc.polyCube(w=0.08, h=pad_h * 0.72, d=pad_d * 0.72,
                           name=f"rm_torso_pad_trim_{label}_#")[0]
        mc.move(side * (spread + pad_w * 0.44), y + 0.03, -0.02, trim, relative=True)
        mc.rotate(0, 0, -8 * side, trim)
        assign_material(trim, 'rm_graphite_mat')
        finish(trim)

        mc.parent(socket, armor, trim, grp)
        pads.append(grp)

    return tuple(pads)


def build(aggr: float, torso_h: float, tune: TorsoTune, ntune: NucleusTune,
          torso_style: str, nucleus_style: str) -> dict:
    body = _build_layered_torso(aggr, torso_h, torso_style, tune)
    spine_meshes = [n for n in (mc.listRelatives(body, allDescendents=True, type='mesh') or [])
                    if 'inner_spine' in n]
    ref = spine_meshes[-1] if spine_meshes else body
    spine_bb = mc.exactWorldBoundingBox(ref)
    spine_bot = spine_bb[1]

    waist_h = 0.24
    waist_y = spine_bot - waist_h * 0.5
    waist = build_waist(aggr, waist_y)

    reactor = build_reactor(aggr, body, nucleus_style, ntune)
    chest_strip = build_chest_strip(aggr, body)
    style_parts = build_style_details(torso_style, aggr, body)
    pad_l, pad_r = build_shoulder_pads(aggr, torso_h, tune)

    stub_h = 0.20
    stub = mc.polyCylinder(r=0.12 + aggr * 0.09, h=stub_h, sa=4,
                           name="rm_torso_stub_#")[0]
    mc.move(0, spine_bot - waist_h - stub_h * 0.5, 0, stub, relative=True)
    assign_material(stub, 'rm_graphite_mat')

    return {
        'body': body,
        'waist': waist,
        'reactor': reactor,
        'chest_strip': chest_strip,
        'style_parts': style_parts,
        'pad_l': pad_l,
        'pad_r': pad_r,
        'stub': stub,
    }
