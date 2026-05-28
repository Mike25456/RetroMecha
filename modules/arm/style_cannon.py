"""RetroMecha — modules/arm/style_cannon.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None
from utils.maya_materials import assign_material
from modules.arm._shared import finish, armor_block

def build(grp, w, l, d_mul, hm, side, aggr):
    parts = []
    upper=armor_block("rm_arm_upper_#",0.40*w,0.88*l,0.45*w,0.08)
    mc.rotate(0,0,-3*side,upper)
    upper_core=mc.polyCylinder(r=0.18*w,h=0.30*l,sa=12,name="rm_arm_shoulder_core_#")[0]
    mc.rotate(90,0,0,upper_core); mc.move(0,0.60*l,0,upper_core,relative=True)
    assign_material(upper_core,"rm_graphite_mat"); finish(upper_core,0.0)
    shoulder_glow=mc.polyTorus(r=0.22*w,sr=0.013*d_mul,sa=24,sh=4,name="rm_arm_shoulder_glow_#")[0]
    mc.rotate(90,0,0,shoulder_glow); mc.move(0,0.60*l,0,shoulder_glow,relative=True)
    assign_material(shoulder_glow,"rm_cyan_glow_mat"); finish(shoulder_glow,0.0)
    elbow=mc.polyCylinder(r=0.16*w,h=0.32*l,sa=12,name="rm_arm_elbow_#")[0]
    mc.rotate(90,0,0,elbow); mc.move(0,-0.45*l,0,elbow,relative=True)
    assign_material(elbow,"rm_graphite_mat"); finish(elbow,0.0)
    fore_h=0.9*l
    forearm=mc.polyCylinder(r=0.22*w,h=fore_h,sa=12,name="rm_arm_forearm_#")[0]
    mc.move(0,-1.0*l,0,forearm,relative=True)
    assign_material(forearm,"rm_white_armor_mat"); finish(forearm,0.02)
    tip_h=0.35*hm
    tip=mc.polyCylinder(r=0.18*hm,h=tip_h,sa=12,name="rm_arm_tip_#")[0]
    mc.move(0,-1.0*l-fore_h*0.5-tip_h*0.5,0,tip,relative=True)
    assign_material(tip,"rm_graphite_mat"); finish(tip,0.02,hard=True)
    cannon_core=mc.polyCylinder(r=0.12*w,h=0.36*d_mul,sa=12,name="rm_arm_cannon_core_#")[0]
    mc.move(0,-1.0*l-fore_h*0.5-tip_h-0.01,0,cannon_core,relative=True)
    assign_material(cannon_core,"rm_cyan_glow_mat"); finish(cannon_core,0.0,hard=True)
    parts.extend([upper,upper_core,shoulder_glow,elbow,forearm,tip,cannon_core])
    mc.parent(parts,grp)
