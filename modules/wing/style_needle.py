"""Estilo NEEDLE — cuchillas largas y delgadas (default)."""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material
from modules.wing._shared import finish


SPECS = [
    (0, 3.16, 0.42, 25, -0.36, -0.06),
    (1, 2.78, 0.38, 17, -0.30, -0.02),
    (2, 2.42, 0.34,  9, -0.24,  0.02),
    (3, 2.12, 0.31,  2, -0.18,  0.00),
    (4, 2.36, 0.33, -6, -0.12, -0.04),
]


def make_blade(index, side, length, width, angle, y, z):
    blade = mc.polyCone(r=width, h=length, sa=4,
                        name=f'rm_wing_blade_{index}_#')[0]
    mc.scale(0.92, 1.0, 0.18, blade)
    mc.rotate(0, 0, angle*side, blade)
    mc.move(side*length*0.42, y+length*0.50, z, blade, relative=True)
    assign_material(blade, 'rm_white_armor_mat')
    return finish(blade, 0.022, hard=True)


def make_edge(index, side, length, angle, y, z, d_mul=1.0):
    edge = mc.polyCube(w=0.070*d_mul, h=length*0.70, d=0.070*d_mul,
                       name=f'rm_wing_edge_{index}_#')[0]
    mc.rotate(0, 0, angle*side, edge)
    mc.move(side*length*0.43, y+length*0.50, z+0.045, edge, relative=True)
    assign_material(edge, 'rm_graphite_mat')
    return finish(edge, 0.006, hard=True)


def build(side, scale, l_mul, w_mul, s_mul, d_mul):
    blades, edges = [], []
    for idx, length, width, angle, y, z in SPECS:
        l = length * scale * l_mul
        w = width  * scale * w_mul
        a = angle  * s_mul
        yy = y * scale * l_mul
        zz = z * scale
        blades.append(make_blade(idx, side, l, w, a, yy, zz))
        edges.append(make_edge(idx, side, l, a, yy, zz, d_mul))
    return blades, edges
