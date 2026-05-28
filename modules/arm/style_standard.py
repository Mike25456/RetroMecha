"""RetroMecha — modules/arm/style_standard.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None
from utils.maya_materials import assign_material
from modules.arm._shared import finish, armor_block

def build(grp, w, l, d_mul, hm, side, aggr):
    parts = []
    upper = armor_block("rm_arm_upper_#", 0.42*w, 0.92*l, 0.38*w, 0.08)
    mc.rotate(0,0,-5*side, upper)
    upper_core = mc.polyCylinder(r=0.16*w, h=0.28*l, sa=12, name="rm_arm_shoulder_core_#")[0]
    mc.rotate(90,0,0, upper_core); mc.move(0,0.60*l,0, upper_core, relative=True)
    assign_material(upper_core, "rm_graphite_mat"); finish(upper_core,0.0)
    shoulder_glow = mc.polyTorus(r=0.19*w, sr=0.012*d_mul, sa=24, sh=4, name="rm_arm_shoulder_glow_#")[0]
    mc.rotate(90,0,0, shoulder_glow); mc.move(0,0.60*l,0, shoulder_glow, relative=True)
    assign_material(shoulder_glow, "rm_cyan_glow_mat"); finish(shoulder_glow,0.0)
    elbow = mc.polySphere(r=0.18*w, sa=8, sh=6, name="rm_arm_elbow_#")[0]
    mc.move(0,-0.52*l,0, elbow, relative=True)
    assign_material(elbow, "rm_graphite_mat"); finish(elbow,0.0)
    elbow_glow = mc.polyTorus(r=0.20*w, sr=0.012*d_mul, sa=24, sh=4, name="rm_arm_elbow_glow_#")[0]
    mc.move(0,-0.52*l,0, elbow_glow, relative=True)
    assign_material(elbow_glow, "rm_cyan_glow_mat"); finish(elbow_glow,0.0)
    fore_h = 0.82*l
    forearm = armor_block("rm_arm_forearm_#", 0.36*w, fore_h, 0.34*w, -1.05*l)
    mc.rotate(0,0,7*side, forearm)
    tip_h = (0.34+aggr*0.42)*hm
    tip = mc.polyCone(r=0.16*hm, h=tip_h, sa=4, name="rm_arm_tip_#")[0]
    mc.move(0,-1.05*l-fore_h*0.5-tip_h*0.5,0, tip, relative=True)
    mc.rotate(180,45,0, tip)
    assign_material(tip, "rm_graphite_mat"); finish(tip,0.0,hard=True)
    accent = mc.polyCube(w=0.045*d_mul, h=0.46*d_mul, d=0.035*d_mul, name="rm_arm_cyan_strip_#")[0]
    mc.move(0,-1.05*l,0.20, accent, relative=True)
    assign_material(accent, "rm_cyan_glow_mat"); finish(accent,0.006,hard=True)
    parts.extend([upper,upper_core,shoulder_glow,elbow,elbow_glow,forearm,tip,accent])
    mc.parent(parts, grp)
