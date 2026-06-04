"""RetroMecha — modules/arm/style_shield.py"""
import math
try:
    import maya.cmds as mc
except ImportError:
    mc = None
from utils.maya_materials import assign_material
from modules.arm._shared import finish, armor_block


def _build_circular_shield(cx, cy, cz, radius, hm, d_mul):
    parts = []
    r = radius

    rim = mc.polyTorus(r=r, sr=0.10 * hm, sa=32, sh=6, name='rm_arm_shield_rim_#')[0]
    mc.rotate(90, 0, 0, rim)
    mc.move(cx, cy, cz, rim, relative=True)
    assign_material(rim, 'rm_white_armor_mat')
    finish(rim, 0.012, hard=True)
    parts.append(rim)

    ring_mid = mc.polyTorus(r=r * 0.72, sr=0.032 * hm, sa=32, sh=4,
                            name='rm_arm_shield_ring_mid_#')[0]
    mc.rotate(90, 0, 0, ring_mid)
    mc.move(cx, cy, cz + 0.04 * hm, ring_mid, relative=True)
    assign_material(ring_mid, 'rm_graphite_mat')
    finish(ring_mid, 0.0, hard=True)
    parts.append(ring_mid)

    face = mc.polyCylinder(r=r * 0.88, h=0.048 * hm, sa=32, sh=1,
                           name='rm_arm_shield_face_#')[0]
    mc.rotate(90, 0, 0, face)
    mc.move(cx, cy, cz + 0.06 * hm, face, relative=True)
    assign_material(face, 'rm_white_armor_mat')
    finish(face, 0.008)
    parts.append(face)

    inner_zone = mc.polyTorus(r=r * 0.44, sr=0.028 * hm, sa=32, sh=4,
                              name='rm_arm_shield_inner_zone_#')[0]
    mc.rotate(90, 0, 0, inner_zone)
    mc.move(cx, cy, cz + 0.08 * hm, inner_zone, relative=True)
    assign_material(inner_zone, 'rm_graphite_mat')
    finish(inner_zone, 0.0, hard=True)
    parts.append(inner_zone)

    for i in range(6):
        angle = math.radians(i * 60)
        seg_x = cx + math.cos(angle) * r * 0.60
        seg_y = cy + math.sin(angle) * r * 0.60
        seg = mc.polyCube(w=0.036 * d_mul, h=r * 0.46, d=0.028 * d_mul,
                          name=f'rm_arm_shield_seg_{i}_#')[0]
        mc.move(seg_x, seg_y, cz + 0.088 * hm, seg, relative=True)
        mc.rotate(0, 0, math.degrees(angle), seg)
        assign_material(seg, 'rm_white_armor_mat')
        finish(seg, 0.006, hard=True)
        parts.append(seg)

    boss_base = mc.polyCylinder(r=r * 0.22, h=0.10 * hm, sa=16, sh=1,
                                name='rm_arm_shield_boss_base_#')[0]
    mc.rotate(90, 0, 0, boss_base)
    mc.move(cx, cy, cz + 0.12 * hm, boss_base, relative=True)
    assign_material(boss_base, 'rm_graphite_mat')
    finish(boss_base, 0.018, hard=True)
    parts.append(boss_base)

    boss_tip = mc.polyCone(r=r * 0.14, h=0.08 * hm, sa=16,
                           name='rm_arm_shield_boss_tip_#')[0]
    mc.rotate(-90, 0, 0, boss_tip)
    mc.move(cx, cy, cz + 0.20 * hm, boss_tip, relative=True)
    assign_material(boss_tip, 'rm_white_armor_mat')
    finish(boss_tip, 0.0, hard=True)
    parts.append(boss_tip)

    boss_glow = mc.polyTorus(r=r * 0.20, sr=0.014 * hm, sa=24, sh=4,
                             name='rm_arm_shield_boss_glow_#')[0]
    mc.rotate(90, 0, 0, boss_glow)
    mc.move(cx, cy, cz + 0.13 * hm, boss_glow, relative=True)
    assign_material(boss_glow, 'rm_cyan_glow_mat')
    finish(boss_glow, 0.0)
    parts.append(boss_glow)

    mount_arm = mc.polyCube(w=0.07 * d_mul, h=0.07 * d_mul, d=0.32 * hm,
                            name='rm_arm_shield_mount_arm_#')[0]
    mc.move(cx, cy, cz - 0.16 * hm, mount_arm, relative=True)
    assign_material(mount_arm, 'rm_graphite_mat')
    finish(mount_arm, 0.014, hard=True)
    parts.append(mount_arm)

    mount_clamp_a = mc.polyCylinder(r=0.06 * hm, h=0.08 * hm, sa=8,
                                    name='rm_arm_shield_mount_clamp_a_#')[0]
    mc.move(cx, cy, cz - 0.30 * hm, mount_clamp_a, relative=True)
    assign_material(mount_clamp_a, 'rm_graphite_mat')
    finish(mount_clamp_a, 0.010, hard=True)
    parts.append(mount_clamp_a)

    return parts


def build(grp, w, l, d_mul, hm, side, aggr):
    parts = []

    upper = armor_block('rm_arm_upper_#', 0.42 * w, 0.92 * l, 0.38 * w, 0.08)
    mc.rotate(0, 0, -5 * side, upper)
    parts.append(upper)

    upper_core = mc.polyCylinder(r=0.16 * w, h=0.28 * l, sa=12,
                                 name='rm_arm_shoulder_core_#')[0]
    mc.rotate(90, 0, 0, upper_core)
    mc.move(0, 0.60 * l, 0, upper_core, relative=True)
    assign_material(upper_core, 'rm_graphite_mat')
    finish(upper_core, 0.0)
    parts.append(upper_core)

    shoulder_glow = mc.polyTorus(r=0.19 * w, sr=0.012 * d_mul, sa=24, sh=4,
                                 name='rm_arm_shoulder_glow_#')[0]
    mc.rotate(90, 0, 0, shoulder_glow)
    mc.move(0, 0.60 * l, 0, shoulder_glow, relative=True)
    assign_material(shoulder_glow, 'rm_cyan_glow_mat')
    finish(shoulder_glow, 0.0)
    parts.append(shoulder_glow)

    elbow = mc.polySphere(r=0.18 * w, sa=8, sh=6, name='rm_arm_elbow_#')[0]
    mc.move(0, -0.52 * l, 0, elbow, relative=True)
    assign_material(elbow, 'rm_graphite_mat')
    finish(elbow, 0.0)
    parts.append(elbow)

    elbow_glow = mc.polyTorus(r=0.20 * w, sr=0.012 * d_mul, sa=24, sh=4,
                              name='rm_arm_elbow_glow_#')[0]
    mc.move(0, -0.52 * l, 0, elbow_glow, relative=True)
    assign_material(elbow_glow, 'rm_cyan_glow_mat')
    finish(elbow_glow, 0.0)
    parts.append(elbow_glow)

    fore_h = 0.82 * l
    fore_y = -1.05 * l
    forearm = armor_block('rm_arm_forearm_#', 0.36 * w, fore_h, 0.34 * w, fore_y)
    mc.rotate(0, 0, 7 * side, forearm)
    parts.append(forearm)

    tip_h = (0.34 + aggr * 0.42) * hm
    tip_y = fore_y - fore_h * 0.5 - tip_h * 0.5
    tip = mc.polyCone(r=0.16 * hm, h=tip_h, sa=4, name='rm_arm_tip_#')[0]
    mc.move(0, tip_y, 0, tip, relative=True)
    mc.rotate(180, 45, 0, tip)
    assign_material(tip, 'rm_white_armor_mat')
    finish(tip, 0.0, hard=True)
    parts.append(tip)

    accent = mc.polyCube(w=0.045 * d_mul, h=0.46 * d_mul, d=0.035 * d_mul,
                         name='rm_arm_cyan_strip_#')[0]
    mc.move(0, fore_y, 0.20, accent, relative=True)
    assign_material(accent, 'rm_cyan_glow_mat')
    finish(accent, 0.006, hard=True)
    parts.append(accent)

    wrist_y = fore_y - fore_h * 0.5
    shield_radius = 0.75
    shield_z = 0.34 * w * 0.5 + shield_radius

    shield_parts = _build_circular_shield(
        cx=0.0, cy=wrist_y, cz=shield_z,
        radius=shield_radius * hm, hm=hm, d_mul=d_mul,
    )

    shield_grp = mc.group(empty=True, name='rm_arm_shield_disc_grp_#')
    mc.parent(shield_parts, shield_grp)
    mc.move(0, 0, -0.35, shield_grp, relative=True)
    mc.rotate(0, 35 * side, 0, shield_grp, relative=True)
    parts.append(shield_grp)

    mc.parent(parts, grp)
