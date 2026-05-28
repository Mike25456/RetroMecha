"""Helpers compartidos para módulos de brazo."""
try:
    import maya.cmds as mc
except ImportError:
    mc = None
from utils.maya_materials import assign_material


def finish(mesh, bevel=0.035, hard=False):
    if bevel > 0:
        try: mc.polyBevel(mesh, offset=bevel, segments=1, chamfer=0, ch=0)
        except: pass
    try: mc.polySoftEdge(mesh, angle=0 if hard else 45, ch=0)
    except: pass
    if mc.objExists(mesh): mc.delete(mesh, ch=True)
    return mesh


def armor_block(name, w, h, d, y):
    block = mc.polyCube(w=w, h=h, d=d, sx=2, sy=3, sz=1, name=name)[0]
    mc.move(0, y, 0, block, relative=True)
    assign_material(block, 'rm_white_armor_mat')
    return finish(block, 0.055)
