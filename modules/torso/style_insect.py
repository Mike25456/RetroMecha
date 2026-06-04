"""Estilo INSECT — caparazón, costillas abdominales, hombros con colmillos, reactor orbes."""
import math
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.torso._shared import finish_bevel
from modules.torso import style_base


def _taper_verts(mesh, y_min, y_max, scale_bot, scale_top):
    bb = mc.exactWorldBoundingBox(mesh)
    cx = (bb[0] + bb[3]) * 0.5
    cz = (bb[2] + bb[5]) * 0.5
    span = y_max - y_min or 1.0
    for v in mc.ls(f'{mesh}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = max(0.0, min(1.0, (pos[1] - y_min) / span))
        sc = scale_bot + (scale_top - scale_bot) * t
        mc.move(cx + (pos[0] - cx) * sc, pos[1],
                cz + (pos[2] - cz) * sc, v, ws=True)


# ── Caparazón ───────────────────────────────────────────────────────────────

def _build_carapace(aggr, s):
    cara = mc.polyCube(w=(0.88 + aggr * 0.22) * s,
                       h=(1.80 + aggr * 0.40) * s,
                       d=(0.52 + aggr * 0.14) * s,
                       sx=4, sy=8, sz=3,
                       name='rm_insect_carapace_armor_#')[0]
    mc.move(0, 0.10 * s, -(0.28 + aggr * 0.08) * s, cara, relative=True)
    bb = mc.exactWorldBoundingBox(cara)
    tip_verts = [v for v in mc.ls(f'{cara}.vtx[*]', flatten=True) or []
                 if mc.pointPosition(v, w=True)[1] > bb[1] + (bb[4] - bb[1]) * 0.70]
    tip_cx = (bb[0] + bb[3]) * 0.5
    tip_cz = (bb[2] + bb[5]) * 0.5
    for v in tip_verts:
        pos = mc.pointPosition(v, w=True)
        t = (pos[1] - (bb[1] + (bb[4] - bb[1]) * 0.70)) / ((bb[4] - bb[1]) * 0.30 or 1.0)
        sc = 1.0 - t * 0.88
        mc.move(tip_cx + (pos[0] - tip_cx) * sc, pos[1],
                tip_cz + (pos[2] - tip_cz) * sc, v, ws=True)
    _taper_verts(cara, bb[1], bb[4], 0.28 + aggr * 0.08, 1.0)
    assign_material(cara, 'rm_white_armor_mat')
    return finish_bevel(cara, 0.035, hard=True)


# ── Placas pectorales ───────────────────────────────────────────────────────

def _build_chest_plates(aggr, s):
    parts = []
    configs = [
        (-1.0, 0.44, 0.62, 0.10, 0.22, 0.28, 0.32, -18, 8),
        ( 1.0, 0.40, 0.58, 0.10, 0.22, 0.32, 0.34, 14, -6),
        (-1.0, 0.28, 0.38, 0.08, 0.38, -0.10, 0.28, -28, 12),
        ( 1.0, 0.30, 0.42, 0.08, 0.36, -0.08, 0.30, 22, -10),
    ]
    for side, w, h, d, xo, yo, zo, rz, ry in configs:
        plate = mc.polyCube(w=w * s, h=h * s, d=d * s, sx=2, sy=3, sz=1,
                            name='rm_insect_chest_plate_#')[0]
        mc.move(side * xo * s, yo * s, zo * s, plate, relative=True)
        mc.rotate(0, ry, rz * side, plate)
        assign_material(plate, 'rm_white_armor_mat')
        finish_bevel(plate, 0.028, hard=True)
        parts.append(plate)
    return parts


# ── Costillas abdominales ───────────────────────────────────────────────────

def _build_abdomen_ribs(aggr, s, rib_count):
    parts = []
    y_start = -0.10 * s
    y_step  = -(0.22 + aggr * 0.06) * s
    for i in range(rib_count):
        t = i / max(rib_count - 1, 1)
        rw = (0.72 - t * 0.34 + aggr * 0.14) * s
        rh = (0.06 + aggr * 0.02) * s
        rd = (0.38 - t * 0.14 + aggr * 0.08) * s
        rib = mc.polyCube(w=rw, h=rh, d=rd, sx=3, sy=1, sz=1,
                          name=f'rm_insect_rib_{i}_#')[0]
        ry = y_start + i * y_step
        mc.move(0, ry, (0.10 + t * 0.04) * s, rib, relative=True)
        for v in mc.ls(f'{rib}.vtx[*]', flatten=True) or []:
            pos = mc.pointPosition(v, w=True)
            bb  = mc.exactWorldBoundingBox(rib)
            cx  = (bb[0] + bb[3]) * 0.5
            dist = 1.0 - abs(pos[0] - cx) / (rw * 0.5 or 1.0)
            mc.move(pos[0], pos[1], pos[2] + dist * 0.04 * s, v, ws=True)
        assign_material(rib, 'rm_graphite_mat')
        finish_bevel(rib, 0.012, hard=True)
        parts.append(rib)
    return parts


# ── Esternón ────────────────────────────────────────────────────────────────

def _build_sternum(aggr, s):
    stern = mc.polyCube(w=(0.14 + aggr * 0.04) * s,
                        h=(1.10 + aggr * 0.30) * s,
                        d=(0.08 + aggr * 0.02) * s,
                        sx=1, sy=6, sz=1,
                        name='rm_insect_sternum_#')[0]
    mc.move(0, 0.05 * s, (0.36 + aggr * 0.08) * s, stern, relative=True)
    bb = mc.exactWorldBoundingBox(stern)
    for v in mc.ls(f'{stern}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = abs(pos[1] - (bb[1] + bb[4]) * 0.5) / ((bb[4] - bb[1]) * 0.5 or 1.0)
        sc = 0.5 + t * 0.5
        cx = (bb[0] + bb[3]) * 0.5
        mc.move(cx + (pos[0] - cx) * sc, pos[1], pos[2], v, ws=True)
    assign_material(stern, 'rm_graphite_mat')
    return finish_bevel(stern, 0.010, hard=True)


# ── Cuerpo completo ─────────────────────────────────────────────────────────

def _build_body_group(aggr, s, rib_count):
    grp = mc.group(empty=True, name='rm_insect_body_#')
    parts = [
        _build_carapace(aggr, s),
        _build_sternum(aggr, s),
        *_build_chest_plates(aggr, s),
        *_build_abdomen_ribs(aggr, s, rib_count),
    ]
    mc.parent(parts, grp)
    return grp


# ── Reactor: cluster de 5 orbes ─────────────────────────────────────────────

def _build_reactor_group(aggr, s, d_mul):
    grp = mc.group(empty=True, name='rm_insect_reactor_#')
    parts = []

    orb_configs = [
        ( 0.00, 0.00, 0.096),
        ( 0.13, 0.10, 0.058),
        (-0.13, 0.10, 0.058),
        ( 0.10, -0.12, 0.048),
        (-0.10, -0.12, 0.048),
    ]
    cluster_z = (0.40 + aggr * 0.06) * s
    cluster_y = (0.18 + aggr * 0.04) * s

    for i, (ox, oy, r) in enumerate(orb_configs):
        ring = mc.polyTorus(r=r * s * 1.35, sr=r * s * 0.18 * d_mul,
                            sa=16, sh=4,
                            name=f'rm_insect_orb_glow_ring_{i}_#')[0]
        mc.rotate(90, i * 22, 0, ring)
        mc.move(ox * s, cluster_y + oy * s, cluster_z, ring, relative=True)
        assign_material(ring, 'rm_cyan_glow_mat')
        finish_bevel(ring, 0.0, hard=True)
        parts.append(ring)

        core = mc.polySphere(r=r * s * 0.72, sa=10, sh=6,
                             name=f'rm_insect_orb_core_{i}_#')[0]
        mc.scale(1.0, 1.0, 0.55, core)
        mc.move(ox * s, cluster_y + oy * s, cluster_z + 0.012 * s, core, relative=True)
        assign_material(core, 'rm_cyan_glow_mat')
        finish_bevel(core, 0.0)
        parts.append(core)

    mount = mc.polyCube(w=0.44 * s, h=0.44 * s, d=0.04 * s,
                        name='rm_insect_orb_mount_#')[0]
    mc.move(0, cluster_y, cluster_z - 0.032 * s, mount, relative=True)
    assign_material(mount, 'rm_graphite_mat')
    finish_bevel(mount, 0.016, hard=True)
    parts.append(mount)

    for a, b in [(0,1),(0,2),(0,3),(0,4)]:
        ax, ay = orb_configs[a][0], orb_configs[a][1]
        bx, by = orb_configs[b][0], orb_configs[b][1]
        dx, dy = (bx - ax) * s, (by - ay) * s
        dist   = math.sqrt(dx*dx + dy*dy) or 0.01
        angle  = math.degrees(math.atan2(dy, dx))
        conn = mc.polyCube(w=dist, h=0.018 * s, d=0.014 * s,
                           name=f'rm_insect_orb_conn_{a}_{b}_#')[0]
        mc.move((ax+bx)*0.5*s, cluster_y+(ay+by)*0.5*s,
                cluster_z - 0.010*s, conn, relative=True)
        mc.rotate(0, 0, angle, conn)
        assign_material(conn, 'rm_graphite_mat')
        finish_bevel(conn, 0.004, hard=True)
        parts.append(conn)

    mc.parent(parts, grp)
    return grp


# ── Hombros ─────────────────────────────────────────────────────────────────

def _build_shoulders(aggr, s):
    result = []
    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        side_grp = mc.group(empty=True, name=f'rm_torso_shoulder_{label}_#')
        sx = side * (0.52 + aggr * 0.16) * s

        upper = mc.polyCube(w=(0.32 + aggr * 0.12) * s,
                            h=(0.28 + aggr * 0.10) * s,
                            d=(0.62 + aggr * 0.18) * s,
                            sx=2, sy=1, sz=2,
                            name=f'rm_insect_shoulder_armor_{label}_#')[0]
        mc.move(sx, (0.62 + aggr * 0.12) * s, 0, upper, relative=True)
        mc.rotate(0, 0, -18 * side, upper)
        assign_material(upper, 'rm_white_armor_mat')
        finish_bevel(upper, 0.028, hard=True)

        fang = mc.polyCone(r=(0.10 + aggr * 0.04) * s,
                           h=(0.32 + aggr * 0.14) * s,
                           sa=4, name=f'rm_insect_shoulder_fang_{label}_#')[0]
        mc.move(sx + side * (0.14 + aggr * 0.04) * s,
                (0.36 + aggr * 0.08) * s,
                (0.16 + aggr * 0.04) * s, fang, relative=True)
        mc.rotate(0, 45, 90 * side, fang)
        assign_material(fang, 'rm_graphite_mat')
        finish_bevel(fang, 0.0, hard=True)

        joint = mc.polySphere(r=(0.14 + aggr * 0.06) * s, sa=8, sh=6,
                              name=f'rm_insect_shoulder_joint_{label}_#')[0]
        mc.move(sx, (0.52 + aggr * 0.08) * s, 0, joint, relative=True)
        assign_material(joint, 'rm_graphite_mat')
        finish_bevel(joint, 0.0)

        mc.parent(upper, fang, joint, side_grp)
        result.append(side_grp)

    return result[0], result[1]


# ── Cintura ─────────────────────────────────────────────────────────────────

def _build_waist(aggr, s):
    parts = []
    waist = mc.polyCylinder(r=(0.16 + aggr * 0.06) * s,
                            h=(0.20 + aggr * 0.04) * s,
                            sa=6,
                            name='rm_insect_waist_#')[0]
    mc.move(0, -(0.78 + aggr * 0.12) * s, 0, waist, relative=True)
    mc.scale(1.0, 1.0, 0.70, waist)
    assign_material(waist, 'rm_graphite_mat')
    finish_bevel(waist, 0.0, hard=True)
    parts.append(waist)

    waist_glow = mc.polyTorus(r=(0.19 + aggr * 0.06) * s, sr=0.016 * s,
                              sa=18, sh=4,
                              name='rm_insect_waist_glow_#')[0]
    mc.rotate(0, 30, 0, waist_glow)
    mc.move(0, -(0.78 + aggr * 0.12) * s, 0, waist_glow, relative=True)
    assign_material(waist_glow, 'rm_cyan_glow_mat')
    finish_bevel(waist_glow, 0.0)
    parts.append(waist_glow)

    return parts


# ── Build principal ─────────────────────────────────────────────────────────

def build(aggr, torso_h, tune, ntune, torso_style=None, nucleus_style=None):
    s = (1.0 + aggr * 0.50) * tune.width
    d_mul = tune.detail
    rib_count = 5

    body_grp = _build_body_group(aggr, s, rib_count)
    shoulder_l, shoulder_r = _build_shoulders(aggr, s)
    waist_parts = _build_waist(aggr, s)

    children = [body_grp, shoulder_l, shoulder_r, *waist_parts]

    if nucleus_style == 'orb_cluster' or nucleus_style is None:
        reactor_internal = _build_reactor_group(aggr, s, d_mul)
        children.append(reactor_internal)
        grp = mc.group(empty=True, name='rm_torso_insect_#')
        mc.parent(children, grp)
        return {
            'body': grp,
            'waist': None,
            'reactor': None,
            'chest_strip': None,
            'style_parts': [],
            'pad_l': shoulder_l,
            'pad_r': shoulder_r,
            'stub': None,
        }

    grp = mc.group(empty=True, name='rm_torso_insect_#')
    mc.parent(children, grp)
    reactor = style_base.build_reactor(aggr, body_grp, nucleus_style, ntune)
    return {
        'body': grp,
        'waist': None,
        'reactor': reactor,
        'chest_strip': None,
        'style_parts': [],
        'pad_l': shoulder_l,
        'pad_r': shoulder_r,
        'stub': None,
    }
