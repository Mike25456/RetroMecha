"""
RetroMecha — modules/wing/_shared.py
Helpers compartidos por todos los estilos de ala.
"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material


def finish(mesh: str, bevel: float = 0.025, hard: bool = False) -> str:
    if bevel > 0:
        try:
            mc.polyBevel(mesh, offset=bevel, segments=1, chamfer=0, ch=0)
        except Exception:
            pass
    try:
        mc.polySoftEdge(mesh, angle=0 if hard else 45, ch=0)
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def build_root(side: float, scale: float, aggr: float, d_mul: float = 1.0) -> str:
    grp = mc.group(empty=True, name='rm_wing_root_#')

    hub = mc.polyCylinder(r=0.28*scale, h=0.28*scale, sa=14,
                          name='rm_wing_hub_#')[0]
    mc.rotate(90, 0, 0, hub)
    assign_material(hub, 'rm_graphite_mat')
    finish(hub, 0.0)

    glow = mc.polyTorus(r=0.25*scale, sr=0.016*scale*d_mul,
                        sa=24, sh=4, name='rm_wing_hub_glow_#')[0]
    mc.rotate(90, 0, 0, glow)
    assign_material(glow, 'rm_cyan_glow_mat')
    finish(glow, 0.0)

    armor = mc.polyCube(w=0.34*scale, h=0.52*scale, d=0.22*scale,
                        name='rm_wing_root_armor_#')[0]
    mc.move(side*0.13*scale, -0.06*scale, -0.08*scale, armor, relative=True)
    mc.rotate(0, 0, -18*side, armor)
    assign_material(armor, 'rm_graphite_mat')
    finish(armor, 0.03, hard=True)

    spikes = []
    for i, off in enumerate((-0.16, 0.02, 0.20)):
        spike = mc.polyCone(r=0.055*scale*d_mul,
                            h=(0.28+aggr*0.54)*scale*d_mul,
                            sa=4, name=f'rm_wing_root_spike_{i}_#')[0]
        mc.rotate(90, 0, 20*side, spike)
        mc.move(-side*0.08*scale, off*scale, -0.18*scale, spike, relative=True)
        assign_material(spike, 'rm_graphite_mat')
        finish(spike, 0.0, hard=True)
        spikes.append(spike)

    mc.parent(hub, glow, armor, *spikes, grp)
    return grp


def make_thruster(index, side, scale, x, y, z, d_mul=1.0):
    t = mc.polyCylinder(r=0.13*scale*d_mul, h=0.24*scale*d_mul,
                        sa=10, name=f'rm_wing_thruster_{index}_#')[0]
    mc.rotate(90, 0, 0, t)
    mc.move(side*x*scale, y*scale, z*scale, t, relative=True)
    assign_material(t, 'rm_graphite_mat')
    return finish(t, 0.0)
