"""Estilo DELTA — placa triangular con nervaduras, borde afilado y punta."""
import math
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.wing._shared import finish


def build(side, scale, l_mul, w_mul, s_mul, d_mul):
    sweep_angle = 52.0
    aggr_factor = (scale - 1.0) / 0.75 if scale > 1.0 else 0.0

    wing_span  = (2.60 + aggr_factor * 0.80) * l_mul * scale
    wing_chord = (1.40 + aggr_factor * 0.40) * w_mul * scale
    wing_thick = (0.055 + aggr_factor * 0.025) * d_mul

    p_cx = side * (0.32 * scale + wing_span * 0.5)
    p_cy = 0.0
    p_cz = -0.12 * scale

    # ── Placa principal ──────────────────────────────────────────────────────
    plate = mc.polyCube(w=wing_span, h=wing_chord, d=wing_thick,
                        sx=6, sy=4, sz=1,
                        name='rm_wing_delta_plate_#')[0]
    mc.move(p_cx, p_cy, p_cz, plate, relative=True)

    sweep_rad = math.radians(sweep_angle)
    verts = mc.ls(f'{plate}.vtx[*]', flatten=True) or []
    bb = mc.exactWorldBoundingBox(plate)
    x_min, x_max = bb[0], bb[3]
    y_min, y_max = bb[1], bb[4]
    x_range = max(x_max - x_min, 0.001)
    y_range = max(y_max - y_min, 0.001)

    for v in verts:
        pos = mc.pointPosition(v, w=True)
        if side < 0:
            t_x = 1.0 - (pos[0] - x_min) / x_range
        else:
            t_x = (pos[0] - x_min) / x_range
        chord_scale = 1.0 - t_x * 0.92
        new_y = p_cy + (pos[1] - p_cy) * chord_scale
        mc.move(pos[0], new_y, pos[2], v, ws=True)

    assign_material(plate, 'rm_white_armor_mat')
    finish(plate, 0.018, hard=True)
    blades = [plate]

    # ── Borde de ataque ──────────────────────────────────────────────────────
    edge = mc.polyCube(w=wing_span * 0.88, h=0.06 * scale * d_mul,
                       d=wing_thick * 1.8, sx=4, sy=1, sz=1,
                       name='rm_wing_delta_glow_edge_#')[0]
    mc.move(p_cx, p_cy + wing_chord * 0.46, p_cz, edge, relative=True)
    mc.rotate(0, 0, -side * 4, edge)
    assign_material(edge, 'rm_cyan_glow_mat')
    finish(edge, 0.008, hard=True)

    # ── Nervaduras ───────────────────────────────────────────────────────────
    ribs = []
    for i in range(5):
        t = (i + 0.5) / 5.0
        rx = side * (0.32 * scale + wing_span * t)
        rh = wing_chord * (1.0 - t * 0.88) * 0.72
        rt = wing_thick * 1.6
        rd = (0.28 + aggr_factor * 0.12) * scale * (1.0 - t * 0.5)
        rib = mc.polyCube(w=rt, h=rh, d=rd,
                          name=f'rm_wing_delta_rib_{i}_#')[0]
        mc.move(rx, p_cy, p_cz + wing_thick * 0.5 + rd * 0.5,
                rib, relative=True)
        assign_material(rib, 'rm_graphite_mat')
        ribs.append(finish(rib, 0.010, hard=True))

    # ── Punta ────────────────────────────────────────────────────────────────
    tip_h = (0.18 + aggr_factor * 0.22) * scale * d_mul
    tip = mc.polyCone(r=0.045 * scale, h=tip_h, sa=4,
                      name='rm_wing_delta_tip_#')[0]
    mc.rotate(0, 0, 90 * side, tip)
    mc.move(side * (0.32 * scale + wing_span + tip_h * 0.5),
            p_cy, p_cz, tip, relative=True)
    assign_material(tip, 'rm_white_armor_mat')
    finish(tip, 0.0, hard=True)

    # ── Strut raíz ───────────────────────────────────────────────────────────
    strut = mc.polyCube(w=0.06 * scale * d_mul,
                        h=wing_chord * 0.55,
                        d=0.10 * scale * d_mul,
                        name='rm_wing_delta_glow_strut_#')[0]
    mc.move(side * (0.32 * scale + wing_span * 0.22),
            p_cy - wing_chord * 0.24, p_cz - 0.06 * scale,
            strut, relative=True)
    mc.rotate(0, 0, side * 12, strut)
    assign_material(strut, 'rm_cyan_glow_mat')
    finish(strut, 0.014, hard=True)

    # ── Anillo de energía raíz ───────────────────────────────────────────────
    root_glow = mc.polyTorus(r=0.14 * scale * d_mul,
                             sr=0.012 * scale * d_mul,
                             sa=18, sh=4,
                             name='rm_wing_delta_root_glow_#')[0]
    mc.rotate(90, 0, 0, root_glow)
    mc.move(side * (0.32 * scale + wing_span * 0.08),
            p_cy, p_cz + wing_thick, root_glow, relative=True)
    assign_material(root_glow, 'rm_cyan_glow_mat')
    finish(root_glow, 0.0)

    extras = [edge, *ribs, tip, strut, root_glow]
    return blades, extras
