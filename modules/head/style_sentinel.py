"""RetroMecha — modules/head/style_sentinel.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from modules.head._shared import finish, HeadTune


def build(grp: str, aggr: float, tune: HeadTune) -> None:
    tower = mc.polyCube(w=0.58 * tune.width,
                        h=(0.98 + aggr * 0.36) * tune.height,
                        d=0.58 * tune.depth, sx=2, sy=3, sz=2,
                        name='rm_head_sentinel_tower_#')[0]
    mc.scale(0.86, 1.0, 0.82, tower)
    finish(tower, 0.055, hard=True)

    face = mc.polyCube(w=0.28 * tune.eye, h=0.54 * tune.eye,
                       d=0.08 * tune.eye,
                       name='rm_head_sentinel_face_#')[0]
    mc.move(0, 0.02 * tune.height, 0.32 * tune.depth, face, relative=True)
    finish(face, 0.018, hard=True)

    slit = mc.polyCube(w=0.08 * tune.eye, h=0.42 * tune.eye,
                       d=0.035 * tune.eye,
                       name='rm_head_sentinel_slit_#')[0]
    mc.move(0, 0.06 * tune.height, 0.38 * tune.depth, slit, relative=True)
    finish(slit, 0.006, hard=True)

    crest = mc.polyCone(r=0.12 * tune.detail,
                        h=(0.42 + aggr * 0.30) * tune.detail, sa=4,
                        name='rm_head_sentinel_crest_#')[0]
    mc.move(0, 0.66 * tune.height, 0, crest, relative=True)
    mc.scale(0.70, 1.0, 0.25, crest)
    finish(crest, 0.0, hard=True)

    mc.parent(tower, face, slit, crest, grp)
