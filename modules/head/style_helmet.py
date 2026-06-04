"""RetroMecha — modules/head/style_helmet.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from modules.head._shared import finish, HeadTune


def _make_fin(name: str, side: float, aggr: float, tune: HeadTune) -> str:
    fin_h = (0.72 + aggr * 0.84) * tune.detail
    fin = mc.polyCone(r=0.11 * tune.detail, h=fin_h, sa=4, name=name)[0]
    mc.rotate(0, 0, -18 * side, fin)
    mc.scale(0.55, 1.0, 0.18, fin)
    mc.move(side * 0.52 * tune.width, 0.54 * tune.height, -0.02, fin, relative=True)
    return finish(fin, 0.0, hard=True)


def build(grp: str, aggr: float, tune: HeadTune) -> None:
    main = mc.polyCube(w=0.86 * tune.width, h=0.74 * tune.height,
                       d=0.74 * tune.depth, sx=2, sy=2, sz=2,
                       name='rm_head_main_#')[0]
    mc.scale(1.0, 1.12, 0.88, main)
    finish(main, 0.08)

    brow = mc.polyCube(w=0.70 * tune.width, h=0.16 * tune.height,
                       d=0.10 * tune.depth, name='rm_head_brow_#')[0]
    mc.move(0, 0.14 * tune.height, 0.39 * tune.depth, brow, relative=True)
    mc.rotate(-8, 0, 0, brow)
    finish(brow, 0.025, hard=True)

    jaw = mc.polyCube(w=0.42 * tune.width, h=0.30 * tune.height,
                      d=0.16 * tune.depth, name='rm_head_jaw_#')[0]
    mc.move(0, -0.30 * tune.height, 0.39 * tune.depth, jaw, relative=True)
    mc.scale(0.72, 1.0, 1.0, jaw)
    finish(jaw, 0.025, hard=True)

    visor_w = 0.32 * tune.eye
    visor_h = 0.055 * tune.eye
    visor_l = mc.polyCube(w=visor_w, h=visor_h, d=0.035 * tune.depth,
                          name='rm_head_visor_l_#')[0]
    mc.move(-0.17 * tune.width, 0.04 * tune.height, 0.46 * tune.depth,
            visor_l, relative=True)
    mc.rotate(0, 0, -16, visor_l)
    finish(visor_l, 0.01, hard=True)

    visor_r = mc.polyCube(w=visor_w, h=visor_h, d=0.035 * tune.depth,
                          name='rm_head_visor_r_#')[0]
    mc.move(0.17 * tune.width, 0.04 * tune.height, 0.46 * tune.depth,
            visor_r, relative=True)
    mc.rotate(0, 0, 16, visor_r)
    finish(visor_r, 0.01, hard=True)

    ear_h = (0.42 + aggr * 0.54) * tune.detail
    ear_l = mc.polyCube(w=0.16 * tune.detail, h=ear_h, d=0.28 * tune.detail,
                        name='rm_head_ear_l_#')[0]
    mc.move(-0.50 * tune.width, 0.08 * tune.height, 0, ear_l, relative=True)
    finish(ear_l, 0.025, hard=True)

    ear_r = mc.polyCube(w=0.16 * tune.detail, h=ear_h, d=0.28 * tune.detail,
                        name='rm_head_ear_r_#')[0]
    mc.move(0.50 * tune.width, 0.08 * tune.height, 0, ear_r, relative=True)
    finish(ear_r, 0.025, hard=True)

    fin_l = _make_fin('rm_head_fin_l_#', -1.0, aggr, tune)
    fin_r = _make_fin('rm_head_fin_r_#', 1.0, aggr, tune)

    mc.parent(main, brow, jaw, visor_l, visor_r,
              ear_l, ear_r, fin_l, fin_r, grp)
