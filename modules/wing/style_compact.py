"""Estilo COMPACT — placas anchas y cortas con thrusters."""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.wing._shared import finish, make_thruster


SPECS = [
    (0, 1.52, 0.46, 18, -0.10, -0.03),
    (1, 1.22, 0.38,  7, -0.20,  0.02),
    (2, 1.05, 0.32, -7, -0.30, -0.02),
]


def make_plate(index, side, length, width, angle, y, z):
    plate = mc.polyCube(w=width, h=length, d=0.12, sx=2, sy=2, sz=1,
                        name=f'rm_wing_compact_plate_{index}_#')[0]
    mc.rotate(0, 0, angle*side, plate)
    mc.move(side*length*0.24, y+length*0.24, z, plate, relative=True)
    assign_material(plate, 'rm_white_armor_mat')
    return finish(plate, 0.035, hard=True)


def build(side, scale, l_mul, w_mul, s_mul, d_mul):
    blades = []
    for idx, length, width, angle, y, z in SPECS:
        l = length * scale * l_mul
        w = width  * scale * w_mul
        a = angle  * s_mul
        blades.append(make_plate(idx, side, l, w, a,
                                 y*scale*l_mul, z*scale))
    extras = [
        make_thruster(0, side, scale, 0.28, -0.08, -0.22, d_mul),
        make_thruster(1, side, scale, 0.46,  0.18, -0.20, d_mul),
    ]
    return blades, extras
