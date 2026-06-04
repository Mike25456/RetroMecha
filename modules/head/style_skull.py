"""RetroMecha — modules/head/style_skull.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from modules.head._shared import finish, HeadTune


def build(grp: str, aggr: float, tune: HeadTune) -> None:
    parts = []

    cranium = mc.polyCube(w=0.82 * tune.width, h=0.62 * tune.height,
                          d=0.70 * tune.depth, sx=3, sy=3, sz=3,
                          name='rm_head_skull_main_#')[0]
    mc.scale(1.0, 1.08, 0.92, cranium)
    for v in mc.ls(f'{cranium}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        if pos[1] > 0.18 * tune.height:
            mc.move(pos[0], pos[1] * 0.88, pos[2], v, ws=True)
    finish(cranium, 0.055, hard=True)
    parts.append(cranium)

    brow = mc.polyCube(w=0.72 * tune.width, h=0.10 * tune.height,
                       d=0.09 * tune.depth, sx=2, sy=1, sz=1,
                       name='rm_head_skull_brow_#')[0]
    mc.move(0, 0.12 * tune.height, 0.36 * tune.depth, brow, relative=True)
    mc.rotate(-12, 0, 0, brow)
    finish(brow, 0.014, hard=True)
    parts.append(brow)

    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        cheek = mc.polyCube(w=0.10 * tune.detail, h=0.14 * tune.height,
                            d=0.38 * tune.depth, sx=2, sy=1, sz=1,
                            name=f'rm_head_skull_cheek_{label}_#')[0]
        mc.move(side * 0.42 * tune.width, -0.04 * tune.height,
                0.08 * tune.depth, cheek, relative=True)
        mc.rotate(0, side * 8, side * -4, cheek)
        finish(cheek, 0.012, hard=True)
        parts.append(cheek)

    for side in (-1.0, 1.0):
        ring = mc.polyTorus(r=0.15 * tune.eye, sr=0.028 * tune.eye,
                            sa=16, sh=4,
                            name='rm_head_skull_glow_socket_#')[0]
        mc.rotate(90, 0, 0, ring)
        mc.move(side * 0.20 * tune.width, 0.04 * tune.height,
                0.38 * tune.depth, ring, relative=True)
        finish(ring, 0.0, hard=True)
        parts.append(ring)

        sensor = mc.polySphere(r=0.09 * tune.eye, sa=10, sh=6,
                               name='rm_head_skull_glow_sensor_#')[0]
        mc.scale(1.0, 1.0, 0.40, sensor)
        mc.move(side * 0.20 * tune.width, 0.04 * tune.height,
                0.38 * tune.depth + 0.06 * tune.eye, sensor, relative=True)
        finish(sensor, 0.0)
        parts.append(sensor)

    nasal = mc.polyCube(w=0.18 * tune.width, h=0.09 * tune.height,
                        d=0.07 * tune.depth, sx=2, sy=1, sz=1,
                        name='rm_head_skull_nasal_#')[0]
    mc.move(0, -0.06 * tune.height, 0.40 * tune.depth, nasal, relative=True)
    finish(nasal, 0.010, hard=True)
    parts.append(nasal)

    jaw_drop = -(0.28 + aggr * 0.08) * tune.height
    jaw = mc.polyCube(w=0.52 * tune.width, h=0.22 * tune.height,
                      d=0.36 * tune.depth, sx=2, sy=1, sz=2,
                      name='rm_head_skull_jaw_armor_#')[0]
    mc.move(0, jaw_drop, 0.08 * tune.depth, jaw, relative=True)
    mc.rotate(-6, 0, 0, jaw)
    mc.scale(0.82, 1.0, 0.88, jaw)
    finish(jaw, 0.022, hard=True)
    parts.append(jaw)

    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        hinge = mc.polyCylinder(r=0.055 * tune.detail, h=0.09 * tune.detail,
                                sa=8, name=f'rm_head_skull_hinge_{label}_#')[0]
        mc.rotate(0, 0, 90, hinge)
        mc.move(side * 0.28 * tune.width, jaw_drop + 0.14 * tune.height,
                0, hinge, relative=True)
        finish(hinge, 0.0, hard=True)
        parts.append(hinge)

    occipital = mc.polyCube(w=0.56 * tune.width, h=0.16 * tune.height,
                            d=0.10 * tune.depth, sx=2, sy=1, sz=1,
                            name='rm_head_skull_occipital_armor_#')[0]
    mc.move(0, 0.10 * tune.height, -0.38 * tune.depth, occipital, relative=True)
    mc.rotate(8, 0, 0, occipital)
    finish(occipital, 0.020, hard=True)
    parts.append(occipital)

    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        temple = mc.polyCube(w=0.08 * tune.detail,
                             h=(0.36 + aggr * 0.18) * tune.height,
                             d=0.44 * tune.depth, sx=2, sy=1, sz=1,
                             name=f'rm_head_skull_temple_{label}_#')[0]
        mc.move(side * 0.44 * tune.width, 0.02 * tune.height,
                -0.04 * tune.depth, temple, relative=True)
        mc.rotate(0, side * 6, 0, temple)
        finish(temple, 0.016, hard=True)
        parts.append(temple)

    spine_port = mc.polyCylinder(r=0.10 * tune.detail, h=0.12 * tune.detail,
                                 sa=6, name='rm_head_skull_spine_port_#')[0]
    mc.move(0, -(0.34 + aggr * 0.06) * tune.height,
            -0.12 * tune.depth, spine_port, relative=True)
    mc.rotate(14, 0, 0, spine_port)
    finish(spine_port, 0.0, hard=True)
    parts.append(spine_port)

    mc.parent(parts, grp)
