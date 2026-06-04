"""RetroMecha — modules/head/style_drone.py"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from modules.head._shared import finish, HeadTune


def build(grp: str, aggr: float, tune: HeadTune) -> None:
    base_r = (0.44 + aggr * 0.36) * ((tune.width + tune.depth) * 0.5)
    shell = mc.polySphere(r=base_r, sa=16, sh=8,
                          name='rm_head_drone_shell_#')[0]
    mc.scale(1.10 * tune.width, 0.82 * tune.height, 0.86 * tune.depth, shell)
    finish(shell, 0.0)

    shell_x_edge = base_r * 1.10 * tune.width
    shell_z_edge = base_r * 0.86 * tune.depth

    eye_ring = mc.polyTorus(r=0.22 * tune.eye, sr=0.025 * tune.eye,
                            sa=24, sh=6,
                            name='rm_head_drone_eye_ring_#')[0]
    mc.rotate(90, 0, 0, eye_ring)
    mc.move(0, 0.02 * tune.height, shell_z_edge + 0.02 + 0.01 * tune.eye,
            eye_ring, relative=True)
    finish(eye_ring, 0.0)

    eye = mc.polySphere(r=0.12 * tune.eye, sa=12, sh=6,
                        name='rm_head_drone_eye_#')[0]
    mc.scale(1.0, 1.0, 0.35, eye)
    mc.move(0, 0.02 * tune.height, shell_z_edge + 0.06 + 0.02 * tune.eye,
            eye, relative=True)
    finish(eye, 0.0)

    fins = []
    for side in (-1.0, 1.0):
        fin_w = 0.12 * tune.detail
        fin = mc.polyCube(w=fin_w, h=(0.38 + aggr * 0.36) * tune.detail,
                          d=0.24 * tune.detail,
                          name='rm_head_drone_side_fin_#')[0]
        mc.move(side * (shell_x_edge + fin_w * 0.5 + 0.02),
                0.03 * tune.height, -0.04, fin, relative=True)
        mc.rotate(0, 0, -12 * side, fin)
        finish(fin, 0.018, hard=True)
        fins.append(fin)

    mc.parent(shell, eye_ring, eye, *fins, grp)
