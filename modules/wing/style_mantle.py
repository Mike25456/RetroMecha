"""Estilo MANTLE — mochila estructural con columnas de propulsores."""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.wing._shared import finish


def _propulsor(name, cx, cy, cz, r, d, d_mul, toe_angle=0.0, cant_angle=0.0):
    grp = mc.group(empty=True, name=f'{name}_grp_#')
    parts = []

    barrel = mc.polyCylinder(r=r, h=d, sa=16, sh=1,
                             name=f'{name}_barrel_#')[0]
    mc.rotate(90, 0, 0, barrel)
    assign_material(barrel, 'rm_graphite_mat')
    finish(barrel, 0.018)
    parts.append(barrel)

    collar = mc.polyTorus(r=r * 1.12, sr=r * 0.12, sa=18, sh=4,
                          name=f'{name}_collar_ring_#')[0]
    mc.rotate(90, 0, 0, collar)
    mc.move(0, 0, d * 0.32, collar, relative=True)
    assign_material(collar, 'rm_graphite_mat')
    finish(collar, 0.0, hard=True)
    parts.append(collar)

    nozzle_outer = mc.polyTorus(r=r * 0.88, sr=r * 0.090, sa=18, sh=5,
                                name=f'{name}_nozzle_outer_#')[0]
    mc.rotate(90, 0, 0, nozzle_outer)
    mc.move(0, 0, -d * 0.48, nozzle_outer, relative=True)
    assign_material(nozzle_outer, 'rm_graphite_mat')
    finish(nozzle_outer, 0.0, hard=True)
    parts.append(nozzle_outer)

    nozzle_glow = mc.polyTorus(r=r * 0.56, sr=r * 0.050 * d_mul,
                               sa=16, sh=4,
                               name=f'{name}_glow_nozzle_#')[0]
    mc.rotate(90, 0, 0, nozzle_glow)
    mc.move(0, 0, -d * 0.50, nozzle_glow, relative=True)
    assign_material(nozzle_glow, 'rm_cyan_glow_mat')
    finish(nozzle_glow, 0.0)
    parts.append(nozzle_glow)

    heat_shield = mc.polyCube(w=r * 0.18 * d_mul, h=r * 2.10, d=d * 0.60,
                              name=f'{name}_heat_shield_#')[0]
    mc.move(0, r * 1.10, -d * 0.08, heat_shield, relative=True)
    assign_material(heat_shield, 'rm_graphite_mat')
    finish(heat_shield, 0.012, hard=True)
    parts.append(heat_shield)

    mc.parent(parts, grp)
    mc.move(cx, cy, cz, grp, absolute=True)
    if toe_angle != 0:
        mc.rotate(0, 0, toe_angle, grp,
                  pivot=(cx, cy, cz), worldSpace=True)
    if cant_angle != 0:
        mc.rotate(cant_angle, 0, 0, grp,
                  pivot=(cx, cy, cz), worldSpace=True)
    return grp


def build(side, scale, l_mul, w_mul, s_mul, d_mul):
    aggr_factor = (scale - 1.0) / 0.60 if scale > 1.0 else 0.0
    prop_count = 3
    toe_out = 8.0
    cant_down = 12.0

    # ── Cuerpo central de la mochila ──────────────────────────────────────────
    body_w = (0.72 + aggr_factor * 0.24) * scale
    body_h = (1.10 + aggr_factor * 0.36) * l_mul * scale
    body_d = (0.42 + aggr_factor * 0.16) * scale

    body = mc.polyCube(w=body_w, h=body_h, d=body_d,
                       sx=2, sy=4, sz=1,
                       name='rm_wing_mantle_body_#')[0]
    mc.move(0, 0, -body_d * 0.5, body, relative=True)
    assign_material(body, 'rm_white_armor_mat')
    finish(body, 0.040, hard=True)
    blades = [body]

    body_face = mc.polyCube(w=body_w * 0.70, h=body_h * 0.82, d=0.06 * scale,
                            name='rm_wing_mantle_body_face_#')[0]
    mc.move(0, 0, -0.03 * scale, body_face, relative=True)
    assign_material(body_face, 'rm_white_armor_mat')
    finish(body_face, 0.016, hard=True)
    blades.append(body_face)

    # ── Columnas laterales de propulsores ─────────────────────────────────────
    col_x = side * (body_w * 0.50 + (0.28 + aggr_factor * 0.12) * scale * s_mul)
    col_w = (0.28 + aggr_factor * 0.10) * scale * d_mul
    col_h = body_h * 0.92
    col_d = (0.32 + aggr_factor * 0.12) * scale

    col = mc.polyCube(w=col_w, h=col_h, d=col_d,
                      sx=1, sy=3, sz=1,
                      name='rm_wing_mantle_col_block_#')[0]
    mc.move(col_x, 0, -body_d * 0.5, col, relative=True)
    assign_material(col, 'rm_white_armor_mat')
    finish(col, 0.022, hard=True)
    blades.append(col)

    # Ranuras horizontales de la columna
    slots = []
    for ri in range(prop_count + 1):
        t = ri / prop_count
        ry = body_h * 0.46 - t * body_h * 0.92
        slot = mc.polyCube(w=col_w * 0.88, h=0.022 * scale, d=col_d * 1.1,
                           name=f'rm_wing_mantle_slot_{ri}_#')[0]
        mc.move(col_x, ry, -body_d * 0.5, slot, relative=True)
        assign_material(slot, 'rm_graphite_mat')
        slots.append(finish(slot, 0.006, hard=True))

    # Propulsores distribuidos a lo largo de la columna
    prop_r  = (0.14 + aggr_factor * 0.08) * scale * w_mul
    prop_d  = (0.52 + aggr_factor * 0.20) * scale * l_mul
    prop_cx = col_x + side * (col_w * 0.5 + prop_r * 0.6)

    y_top  = body_h * 0.38
    y_step = body_h * 0.88 / max(prop_count - 1, 1)

    props = []
    for pi in range(prop_count):
        prop_cy = y_top - pi * y_step
        toe  = toe_out + pi * 2.0
        cant = cant_down + pi * 3.0

        prop = _propulsor(
            f'rm_wing_mantle_prop_{pi}',
            cx=prop_cx, cy=prop_cy, cz=-body_d * 0.5,
            r=prop_r, d=prop_d, d_mul=d_mul,
            toe_angle=toe * side * (-1),
            cant_angle=-cant,
        )
        props.append(prop)

    # ── Hombrera ──────────────────────────────────────────────────────────────
    shoulder_w = (body_w * 0.55 + col_w)
    shoulder_h = (0.22 + aggr_factor * 0.08) * scale
    shoulder_d = (0.28 + aggr_factor * 0.10) * scale

    shoulder = mc.polyCube(w=shoulder_w, h=shoulder_h, d=shoulder_d,
                           name='rm_wing_mantle_shoulder_pad_#')[0]
    mc.move(side * body_w * 0.16, body_h * 0.50 + shoulder_h * 0.5,
            -body_d * 0.5, shoulder, relative=True)
    assign_material(shoulder, 'rm_white_armor_mat')
    finish(shoulder, 0.028, hard=True)
    blades.append(shoulder)

    # ── Placa de escape central ───────────────────────────────────────────────
    exhaust_plate = mc.polyCube(w=body_w * 0.58, h=0.18 * scale,
                                d=body_d * 0.88,
                                name='rm_wing_mantle_exhaust_plate_#')[0]
    mc.move(0, -body_h * 0.50 - 0.09 * scale, -body_d * 0.5,
            exhaust_plate, relative=True)
    assign_material(exhaust_plate, 'rm_white_armor_mat')
    finish(exhaust_plate, 0.022, hard=True)
    blades.append(exhaust_plate)

    # Toberas de escape con brillo
    exhaust_nozzles = []
    for ei in range(3):
        ex = (ei - 1) * body_w * 0.20
        e_nozzle = mc.polyTorus(r=0.052 * scale, sr=0.018 * scale,
                                sa=12, sh=4,
                                name=f'rm_wing_mantle_glow_nozzle_{ei}_#')[0]
        mc.rotate(0, 0, 90, e_nozzle)
        mc.move(ex, -body_h * 0.50 - 0.18 * scale,
                -body_d * 0.38, e_nozzle, relative=True)
        assign_material(e_nozzle, 'rm_cyan_glow_mat')
        exhaust_nozzles.append(finish(e_nozzle, 0.0))

    extras = [*slots, *props, *exhaust_nozzles]
    return blades, extras
