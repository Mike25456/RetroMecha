"""RetroMecha — modules/arm/style_heavy.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None
from utils.maya_materials import assign_material
from modules.arm._shared import finish, armor_block

def build(grp, w, l, d_mul, hm, side, aggr):
    parts = []
    upper = armor_block("rm_arm_upper_#", 0.58*w, 1.0*l, 0.48*w, 0.08)
    mc.rotate(0,0,-5*side, upper)
    upper_core = mc.polyCylinder(r=0.22*w, h=0.34*l, sa=12, name="rm_arm_shoulder_core_#")[0]
    mc.rotate(90,0,0,upper_core); mc.move(0,0.60*l,0,upper_core,relative=True)
    assign_material(upper_core,"rm_graphite_mat"); finish(upper_core,0.0)
    shoulder_glow = mc.polyTorus(r=0.25*w, sr=0.015*d_mul, sa=24, sh=4, name="rm_arm_shoulder_glow_#")[0]
    mc.rotate(90,0,0,shoulder_glow); mc.move(0,0.60*l,0,shoulder_glow,relative=True)
    assign_material(shoulder_glow,"rm_cyan_glow_mat"); finish(shoulder_glow,0.0)
    elbow = mc.polyCube(w=0.35*w, h=0.35*l, d=0.35*w, name="rm_arm_elbow_#")[0]
    mc.move(0,-0.55*l,0,elbow,relative=True)
    assign_material(elbow,"rm_graphite_mat"); finish(elbow,0.03)
    fore_h=0.95*l
    forearm=armor_block("rm_arm_forearm_#",0.52*w,fore_h,0.45*w,-1.15*l)
    mc.rotate(0,0,4*side,forearm)
    tip_h=0.4*hm
    tip=mc.polyCube(w=0.45*hm,h=tip_h,d=0.35*hm,name="rm_arm_tip_#")[0]
    mc.move(0,-1.15*l-fore_h*0.5-tip_h*0.5,0,tip,relative=True)
    parts.extend([upper,upper_core,shoulder_glow,elbow,forearm,tip])
    mc.parent(parts,grp)
