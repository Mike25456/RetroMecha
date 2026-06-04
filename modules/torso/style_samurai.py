"""Estilo SAMURAI — do-maru laminado, pectorales, hombros sode, reactor cruz."""
import math
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.torso._shared import finish, finish_bevel
from modules.torso import style_base


def _taper_verts(mesh, y_min, y_max, scale_bot, scale_top):
    bb = mc.exactWorldBoundingBox(mesh)
    cx = (bb[0] + bb[3]) * 0.5
    cz = (bb[2] + bb[5]) * 0.5
    span = y_max - y_min or 1.0
    for v in mc.ls(f'{mesh}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = max(0.0, min(1.0, (pos[1] - y_min) / span))
        s = scale_bot + (scale_top - scale_bot) * t
        mc.move(cx + (pos[0] - cx) * s, pos[1],
                cz + (pos[2] - cz) * s, v, ws=True)


# ── Do-maru (coraza central) ────────────────────────────────────────────────

def _build_do_maru(aggr, s):
    core = mc.polyCube(w=(0.78 + aggr * 0.20) * s,
                       h=(1.60 + aggr * 0.36) * s,
                       d=(0.54 + aggr * 0.14) * s,
                       sx=3, sy=8, sz=2,
                       name='rm_samurai_do_frame_#')[0]
    mc.move(0, 0.04 * s, 0, core, relative=True)
    bb = mc.exactWorldBoundingBox(core)
    for v in mc.ls(f'{core}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = (pos[1] - bb[1]) / ((bb[4] - bb[1]) or 1.0)
        waist_t = 1.0 - 4.0 * (t - 0.5) ** 2
        squeeze = 1.0 - waist_t * (0.18 + aggr * 0.08)
        cx = (bb[0] + bb[3]) * 0.5
        cz = (bb[2] + bb[5]) * 0.5
        mc.move(cx + (pos[0] - cx) * squeeze, pos[1],
                cz + (pos[2] - cz) * squeeze, v, ws=True)
    assign_material(core, 'rm_graphite_mat')
    return finish_bevel(core, 0.045, hard=True)


# ── Láminas frontales (kusazuri) ────────────────────────────────────────────

def _build_lamellar_plates(aggr, s, plate_count=6):
    parts = []
    y_start = -(0.18 + aggr * 0.04) * s
    y_step  = -(0.20 + aggr * 0.04) * s
    z_front = (0.28 + aggr * 0.08) * s

    for i in range(plate_count):
        t = i / max(plate_count - 1, 1)
        pw = (0.82 - t * 0.28 + aggr * 0.12) * s
        ph = (0.068 + aggr * 0.012) * s
        pd = (0.055 + aggr * 0.010) * s
        py = y_start + i * y_step
        pz = z_front + t * 0.04 * s

        plate = mc.polyCube(w=pw, h=ph, d=pd, sx=4, sy=1, sz=1,
                            name=f'rm_samurai_lamellar_plate_{i}_#')[0]
        mc.move(0, py, pz, plate, relative=True)
        for v in mc.ls(f'{plate}.vtx[*]', flatten=True) or []:
            pos = mc.pointPosition(v, w=True)
            bb  = mc.exactWorldBoundingBox(plate)
            cx  = (bb[0] + bb[3]) * 0.5
            dist = 1.0 - abs(pos[0] - cx) / (pw * 0.5 or 1.0)
            mc.move(pos[0], pos[1], pos[2] + dist * 0.022 * s, v, ws=True)
        mc.rotate(-(4 + t * 3), 0, 0, plate)
        assign_material(plate, 'rm_white_armor_mat')
        finish_bevel(plate, 0.008, hard=True)
        parts.append(plate)

        for side in (-1.0, 1.0):
            rivet = mc.polyCylinder(r=0.018 * s, h=0.022 * s, sa=6,
                                    name=f'rm_samurai_rivet_{i}_{int(side)}_#')[0]
            mc.rotate(90, 0, 0, rivet)
            mc.move(side * pw * 0.42, py, pz + pd * 0.5, rivet, relative=True)
            assign_material(rivet, 'rm_graphite_mat')
            finish_bevel(rivet, 0.0, hard=True)
            parts.append(rivet)

    return parts


# ── Pectorales (o-yoroi) ────────────────────────────────────────────────────

def _build_chest_panels(aggr, s):
    parts = []
    configs = [
        (-1.0, 0.46, 0.58, 0.09, 0.22, 0.38, 0.30, -10,  6),
        ( 1.0, 0.46, 0.58, 0.09, 0.22, 0.38, 0.30,  10, -6),
    ]
    for side, w, h, d, xo, yo, zo, rz, ry in configs:
        panel = mc.polyCube(w=w * s, h=h * s, d=d * s, sx=3, sy=4, sz=1,
                            name='rm_samurai_chest_plate_#')[0]
        mc.move(side * xo * s, yo * s, zo * s, panel, relative=True)
        mc.rotate(0, ry, rz * side, panel)

        bb = mc.exactWorldBoundingBox(panel)
        bot_verts = [v for v in mc.ls(f'{panel}.vtx[*]', flatten=True) or []
                     if mc.pointPosition(v, w=True)[1] < bb[1] + (bb[4]-bb[1]) * 0.22]
        for v in bot_verts:
            pos = mc.pointPosition(v, w=True)
            mc.move(pos[0], pos[1] - 0.04 * s, pos[2] + 0.025 * s, v, ws=True)

        assign_material(panel, 'rm_white_armor_mat')
        finish_bevel(panel, 0.030, hard=True)
        parts.append(panel)

        rib = mc.polyCube(w=0.030 * s, h=h * s * 0.72, d=0.030 * s,
                          name='rm_samurai_chest_rib_#')[0]
        mc.move(side * xo * s, yo * s, (zo + d * 0.5 + 0.015) * s, rib, relative=True)
        mc.rotate(0, ry, rz * side, rib)
        assign_material(rib, 'rm_graphite_mat')
        finish_bevel(rib, 0.006, hard=True)
        parts.append(rib)

    return parts


# ── Placa dorsal ────────────────────────────────────────────────────────────

def _build_backplate(aggr, s):
    back = mc.polyCube(w=(0.80 + aggr * 0.18) * s,
                       h=(1.10 + aggr * 0.24) * s,
                       d=(0.10 + aggr * 0.04) * s,
                       sx=3, sy=5, sz=1,
                       name='rm_samurai_back_armor_#')[0]
    mc.move(0, 0.12 * s, -(0.30 + aggr * 0.08) * s, back, relative=True)
    bb = mc.exactWorldBoundingBox(back)
    _taper_verts(back, bb[1], bb[4], 0.60 + aggr * 0.10, 1.08)
    assign_material(back, 'rm_white_armor_mat')
    finish_bevel(back, 0.032, hard=True)

    parts = [back]
    for i in range(4):
        t = (i + 0.5) / 4
        laca_y = bb[1] + (bb[4] - bb[1]) * t
        laca = mc.polyCube(w=(0.72 + aggr * 0.14) * s * (1.0 - t * 0.25),
                           h=0.016 * s, d=0.016 * s,
                           name=f'rm_samurai_laca_{i}_#')[0]
        mc.move(0, laca_y, -(0.30 + aggr * 0.08) * s - 0.058 * s, laca, relative=True)
        assign_material(laca, 'rm_graphite_mat')
        finish_bevel(laca, 0.004, hard=True)
        parts.append(laca)

    return parts


# ── Cuerpo completo ─────────────────────────────────────────────────────────

def _build_body_group(aggr, s, plate_count):
    grp = mc.group(empty=True, name='rm_samurai_body_#')
    parts = [
        _build_do_maru(aggr, s),
        *_build_chest_panels(aggr, s),
        *_build_lamellar_plates(aggr, s, plate_count),
        *_build_backplate(aggr, s),
    ]
    mc.parent(parts, grp)
    return grp


# ── Reactor en cruz ─────────────────────────────────────────────────────────

def _build_reactor_group(aggr, s, d_mul):
    grp = mc.group(empty=True, name='rm_samurai_reactor_#')
    parts = []

    rz   = (0.36 + aggr * 0.06) * s
    ry   = (0.38 + aggr * 0.06) * s
    size = (0.22 + aggr * 0.08) * s

    outer_ring = mc.polyTorus(r=size * 0.92, sr=size * 0.068 * d_mul,
                              sa=24, sh=6,
                              name='rm_samurai_reactor_glow_outer_#')[0]
    mc.rotate(90, 0, 0, outer_ring)
    mc.move(0, ry, rz + 0.018 * s, outer_ring, relative=True)
    assign_material(outer_ring, 'rm_graphite_mat')
    finish_bevel(outer_ring, 0.0, hard=True)
    parts.append(outer_ring)

    arm_configs = [
        (  0.0, size * 1.60, size * 0.14),
        ( 90.0, size * 1.60, size * 0.14),
        ( 45.0, size * 1.10, size * 0.09),
        (-45.0, size * 1.10, size * 0.09),
    ]
    for i, (angle, length_val, width) in enumerate(arm_configs):
        arm = mc.polyCube(w=length_val, h=width, d=0.022 * s * d_mul,
                          sx=4, sy=1, sz=1,
                          name=f'rm_samurai_reactor_glow_arm_{i}_#')[0]
        mc.move(0, ry, rz + 0.024 * s, arm, relative=True)
        mc.rotate(0, 0, angle, arm)

        bb = mc.exactWorldBoundingBox(arm)
        cx = (bb[0] + bb[3]) * 0.5
        for v in mc.ls(f'{arm}.vtx[*]', flatten=True) or []:
            pos = mc.pointPosition(v, w=True)
            t = abs(pos[0] - cx) / (length_val * 0.5 or 1.0)
            taper = 1.0 - t * 0.80
            cy_arm = (bb[1] + bb[4]) * 0.5
            mc.move(pos[0], cy_arm + (pos[1] - cy_arm) * taper, pos[2], v, ws=True)

        assign_material(arm, 'rm_cyan_glow_mat')
        finish_bevel(arm, 0.006, hard=True)
        parts.append(arm)

    core = mc.polyCube(w=size * 0.32, h=size * 0.32, d=size * 0.10 * d_mul,
                       name='rm_samurai_reactor_glow_core_#')[0]
    mc.rotate(0, 0, 45, core)
    mc.move(0, ry, rz + 0.032 * s, core, relative=True)
    assign_material(core, 'rm_cyan_glow_mat')
    finish_bevel(core, 0.014, hard=True)
    parts.append(core)

    inner_glow = mc.polyTorus(r=size * 0.42, sr=size * 0.038 * d_mul,
                              sa=20, sh=4,
                              name='rm_samurai_reactor_glow_inner_#')[0]
    mc.rotate(90, 0, 0, inner_glow)
    mc.move(0, ry, rz + 0.026 * s, inner_glow, relative=True)
    assign_material(inner_glow, 'rm_cyan_glow_mat')
    finish_bevel(inner_glow, 0.0)
    parts.append(inner_glow)

    for i, angle_deg in enumerate([0, 90, 180, 270]):
        angle_rad = math.radians(angle_deg)
        gx = math.cos(angle_rad) * size * 0.74
        gy = math.sin(angle_rad) * size * 0.74
        gem = mc.polyCylinder(r=size * 0.068, h=0.028 * s, sa=4,
                              name=f'rm_samurai_reactor_glow_gem_{i}_#')[0]
        mc.rotate(90, 45, 0, gem)
        mc.move(gx, ry + gy, rz + 0.030 * s, gem, relative=True)
        assign_material(gem, 'rm_cyan_glow_mat')
        finish_bevel(gem, 0.0, hard=True)
        parts.append(gem)

    mc.parent(parts, grp)
    return grp


# ── Hombros sode ────────────────────────────────────────────────────────────

def _build_shoulders(aggr, s):
    result = []
    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        grp = mc.group(empty=True, name=f'rm_torso_shoulder_{label}_#')
        parts = []
        sx = side * (0.48 + aggr * 0.16) * s
        sy = (0.52 + aggr * 0.10) * s

        sode_configs = [
            ( 0.00, 1.00, 0.10, 0.0),
            (-0.10, 0.86, 0.09, -8.0),
            (-0.20, 0.70, 0.08, -16.0),
        ]
        sode_w = (0.44 + aggr * 0.14) * s
        sode_h = (0.68 + aggr * 0.18) * s
        for j, (dy, ws, d, rz) in enumerate(sode_configs):
            sode = mc.polyCube(w=sode_w * ws, h=sode_h * (1.0 - j * 0.18),
                               d=d * s, sx=2, sy=3, sz=1,
                               name=f'rm_samurai_sode_pad_{label}_{j}_#')[0]
            mc.move(sx, sy + dy * s, (0.02 + j * 0.005) * s, sode, relative=True)
            mc.rotate(0, 0, -side * (6 + j * 4), sode)
            assign_material(sode, 'rm_white_armor_mat')
            finish_bevel(sode, 0.022, hard=True)
            parts.append(sode)

        joint = mc.polyTorus(r=(0.14 + aggr * 0.04) * s, sr=0.038 * s,
                             sa=12, sh=4,
                             name=f'rm_samurai_shoulder_joint_{label}_#')[0]
        mc.rotate(90, 0, 0, joint)
        mc.move(sx, sy - 0.05 * s, 0, joint, relative=True)
        assign_material(joint, 'rm_graphite_mat')
        finish_bevel(joint, 0.0, hard=True)
        parts.append(joint)

        flap = mc.polyCube(w=(0.18 + aggr * 0.06) * s,
                           h=(0.22 + aggr * 0.06) * s,
                           d=(0.38 + aggr * 0.10) * s,
                           name=f'rm_samurai_shoulder_flap_plate_{label}_#')[0]
        mc.move(sx + side * (0.22 + aggr * 0.06) * s,
                sy - 0.16 * s, -0.04 * s, flap, relative=True)
        mc.rotate(0, side * 8, side * -12, flap)
        assign_material(flap, 'rm_white_armor_mat')
        finish_bevel(flap, 0.020, hard=True)
        parts.append(flap)

        mc.parent(parts, grp)
        result.append(grp)

    return result[0], result[1]


# ── Cintura ─────────────────────────────────────────────────────────────────

def _build_waist(aggr, s):
    parts = []

    waist = mc.polyCylinder(r=(0.18 + aggr * 0.06) * s,
                            h=(0.22 + aggr * 0.04) * s,
                            sa=8,
                            name='rm_samurai_waist_#')[0]
    mc.move(0, -(0.72 + aggr * 0.10) * s, 0, waist, relative=True)
    mc.scale(1.0, 1.0, 0.78, waist)
    assign_material(waist, 'rm_graphite_mat')
    finish_bevel(waist, 0.0, hard=True)
    parts.append(waist)

    waist_glow = mc.polyTorus(r=(0.20 + aggr * 0.06) * s, sr=0.014 * s,
                              sa=20, sh=4,
                              name='rm_samurai_waist_glow_#')[0]
    mc.rotate(0, 22.5, 0, waist_glow)
    mc.move(0, -(0.72 + aggr * 0.10) * s, 0, waist_glow, relative=True)
    assign_material(waist_glow, 'rm_cyan_glow_mat')
    finish_bevel(waist_glow, 0.0)
    parts.append(waist_glow)

    return parts


# ── Build principal ─────────────────────────────────────────────────────────

def build(aggr, torso_h, tune, ntune, torso_style=None, nucleus_style=None):
    s = (1.0 + aggr * 0.50) * tune.width
    d_mul = tune.detail
    plate_count = 6

    body_grp = _build_body_group(aggr, s, plate_count)
    shoulder_l, shoulder_r = _build_shoulders(aggr, s)
    waist_parts = _build_waist(aggr, s)

    reactor = None
    children = [body_grp, shoulder_l, shoulder_r, *waist_parts]

    if nucleus_style == 'cross' or nucleus_style is None:
        reactor_internal = _build_reactor_group(aggr, s, d_mul)
        children.append(reactor_internal)
        grp = mc.group(empty=True, name='rm_torso_samurai_#')
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

    grp = mc.group(empty=True, name='rm_torso_samurai_#')
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
