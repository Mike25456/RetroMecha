"""Estilo FAN — placas anchas en abanico con costilla y punta."""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.wing._shared import finish


SPECS = [
    (0, 2.55, 0.74, 34, -0.24, -0.08),
    (1, 2.35, 0.68, 24, -0.22, -0.04),
    (2, 2.15, 0.61, 14, -0.19,  0.00),
    (3, 1.95, 0.54,  5, -0.15,  0.02),
    (4, 1.82, 0.50, -5, -0.10, -0.02),
    (5, 2.05, 0.55,-15, -0.05, -0.07),
]


def make_plate(index, side, length, width, angle, y, z, d_mul=1.0):
    grp = mc.group(empty=True, name=f'rm_wing_fan_plate_{index}_#')

    body = mc.polyCube(w=width, h=length*0.74, d=0.13, sx=2, sy=3, sz=1,
                       name=f'rm_wing_fan_body_{index}_#')[0]
    mc.move(0, length*0.16, 0, body, relative=True)
    assign_material(body, 'rm_white_armor_mat')
    finish(body, 0.040, hard=True)

    tip = mc.polyCone(r=width*0.36, h=length*0.24, sa=4,
                      name=f'rm_wing_fan_tip_{index}_#')[0]
    mc.move(0, length*0.64, 0, tip, relative=True)
    mc.scale(0.90, 1.0, 0.34, tip)
    assign_material(tip, 'rm_white_armor_mat')
    finish(tip, 0.0, hard=True)

    rib = mc.polyCube(w=0.060*d_mul, h=length*0.62, d=0.060*d_mul,
                      name=f'rm_wing_fan_rib_{index}_#')[0]
    mc.move(side*width*0.30, length*0.20, 0.045, rib, relative=True)
    assign_material(rib, 'rm_graphite_mat')
    finish(rib, 0.006, hard=True)

    mc.parent(body, tip, rib, grp)
    mc.rotate(0, 0, angle*side, grp)
    mc.move(side*length*0.34, y+length*0.34, z, grp, relative=True)
    return grp


def build(side, scale, l_mul, w_mul, s_mul, d_mul):
    blades = []
    for idx, length, width, angle, y, z in SPECS:
        l = length * scale * l_mul
        w = width  * scale * w_mul
        a = angle  * s_mul
        blades.append(make_plate(idx, side, l, w, a,
                                 y*scale*l_mul, z*scale, d_mul))
    return blades, []
