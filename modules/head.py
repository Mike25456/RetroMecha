"""RetroMecha - modules/head.py
Floating head with helmet, drone and sentinel styles; advanced tuning via params.
"""

from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from utils.maya_materials import assign_material


@dataclass(frozen=True)
class HeadTune:
    """Multiplicadores desde la UI (config avanzada de cabeza)."""
    width: float = 1.0
    height: float = 1.0
    depth: float = 1.0
    detail: float = 1.0
    eye: float = 1.0

    @classmethod
    def from_params(cls, getter) -> 'HeadTune':
        return cls(
            width=float(getter('head_width_mul', 1.0)),
            height=float(getter('head_height_mul', 1.0)),
            depth=float(getter('head_depth_mul', 1.0)),
            detail=float(getter('head_detail_mul', 1.0)),
            eye=float(getter('head_eye_mul', 1.0)),
        )


def _finish(mesh: str, bevel: float = 0.03, hard: bool = False) -> str:
    if bevel > 0:
        try:
            mc.polyBevel(mesh, offset=bevel, segments=1, chamfer=0, ch=0)
        except Exception:
            pass
    try:
        mc.polySoftEdge(mesh, angle=0 if hard else 55, ch=0)
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def _make_fin(name: str, side: float, aggr: float, tune: HeadTune) -> str:
    fin_h = (0.72 + aggr * 0.84) * tune.detail
    fin = mc.polyCone(r=0.11 * tune.detail, h=fin_h, sa=4, name=name)[0]
    mc.rotate(0, 0, -18 * side, fin)
    mc.scale(0.55, 1.0, 0.18, fin)
    mc.move(side * 0.52 * tune.width, 0.54 * tune.height, -0.02, fin, relative=True)
    assign_material(fin, "rm_white_armor_mat")
    return _finish(fin, 0.0, hard=True)


def _build_helmet_head(grp: str, aggr: float, tune: HeadTune) -> None:
    main = mc.polyCube(
        w=0.86 * tune.width, h=0.74 * tune.height, d=0.74 * tune.depth,
        sx=2, sy=2, sz=2, name='rm_head_main_#',
    )[0]
    mc.scale(1.0, 1.12, 0.88, main)
    assign_material(main, "rm_white_armor_mat")
    _finish(main, 0.08)

    brow = mc.polyCube(
        w=0.70 * tune.width, h=0.16 * tune.height, d=0.10 * tune.depth,
        name='rm_head_brow_#',
    )[0]
    mc.move(0, 0.14 * tune.height, 0.39 * tune.depth, brow, relative=True)
    mc.rotate(-8, 0, 0, brow)
    assign_material(brow, "rm_graphite_mat")
    _finish(brow, 0.025, hard=True)

    jaw = mc.polyCube(
        w=0.42 * tune.width, h=0.30 * tune.height, d=0.16 * tune.depth,
        name='rm_head_jaw_#',
    )[0]
    mc.move(0, -0.30 * tune.height, 0.39 * tune.depth, jaw, relative=True)
    mc.scale(0.72, 1.0, 1.0, jaw)
    assign_material(jaw, "rm_graphite_mat")
    _finish(jaw, 0.025, hard=True)

    visor_w = 0.32 * tune.eye
    visor_h = 0.055 * tune.eye
    visor_l = mc.polyCube(w=visor_w, h=visor_h, d=0.035 * tune.depth,
                          name='rm_head_visor_l_#')[0]
    mc.move(-0.17 * tune.width, 0.04 * tune.height, 0.46 * tune.depth,
            visor_l, relative=True)
    mc.rotate(0, 0, -16, visor_l)
    assign_material(visor_l, "rm_cyan_glow_mat")
    _finish(visor_l, 0.01, hard=True)

    visor_r = mc.polyCube(w=visor_w, h=visor_h, d=0.035 * tune.depth,
                          name='rm_head_visor_r_#')[0]
    mc.move(0.17 * tune.width, 0.04 * tune.height, 0.46 * tune.depth,
            visor_r, relative=True)
    mc.rotate(0, 0, 16, visor_r)
    assign_material(visor_r, "rm_cyan_glow_mat")
    _finish(visor_r, 0.01, hard=True)

    ear_h = (0.42 + aggr * 0.54) * tune.detail
    ear_l = mc.polyCube(w=0.16 * tune.detail, h=ear_h, d=0.28 * tune.detail,
                        name='rm_head_ear_l_#')[0]
    mc.move(-0.50 * tune.width, 0.08 * tune.height, 0, ear_l, relative=True)
    assign_material(ear_l, "rm_graphite_mat")
    _finish(ear_l, 0.025, hard=True)

    ear_r = mc.polyCube(w=0.16 * tune.detail, h=ear_h, d=0.28 * tune.detail,
                        name='rm_head_ear_r_#')[0]
    mc.move(0.50 * tune.width, 0.08 * tune.height, 0, ear_r, relative=True)
    assign_material(ear_r, "rm_graphite_mat")
    _finish(ear_r, 0.025, hard=True)

    fin_l = _make_fin('rm_head_fin_l_#', -1.0, aggr, tune)
    fin_r = _make_fin('rm_head_fin_r_#', 1.0, aggr, tune)

    mc.parent(main, brow, jaw, visor_l, visor_r,
              ear_l, ear_r, fin_l, fin_r, grp)


def _build_drone_head(grp: str, aggr: float, tune: HeadTune) -> None:
    base_r = (0.44 + aggr * 0.36) * ((tune.width + tune.depth) * 0.5)
    shell = mc.polySphere(
        r=base_r,
        sa=16, sh=8, name='rm_head_drone_shell_#',
    )[0]
    mc.scale(1.10 * tune.width, 0.82 * tune.height, 0.86 * tune.depth, shell)
    assign_material(shell, "rm_white_armor_mat")
    _finish(shell, 0.0)

    shell_x_edge = base_r * 1.10 * tune.width
    shell_z_edge = base_r * 0.86 * tune.depth

    eye_ring = mc.polyTorus(
        r=0.22 * tune.eye, sr=0.025 * tune.eye, sa=24, sh=6,
        name='rm_head_drone_eye_ring_#',
    )[0]
    mc.rotate(90, 0, 0, eye_ring)
    mc.move(0, 0.02 * tune.height, shell_z_edge + 0.02 + 0.01 * tune.eye,
            eye_ring, relative=True)
    assign_material(eye_ring, "rm_graphite_mat")
    _finish(eye_ring, 0.0)

    eye = mc.polySphere(r=0.12 * tune.eye, sa=12, sh=6,
                        name='rm_head_drone_eye_#')[0]
    mc.scale(1.0, 1.0, 0.35, eye)
    mc.move(0, 0.02 * tune.height, shell_z_edge + 0.06 + 0.02 * tune.eye,
            eye, relative=True)
    assign_material(eye, "rm_cyan_glow_mat")
    _finish(eye, 0.0)

    fins = []
    for side in (-1.0, 1.0):
        fin_w = 0.12 * tune.detail
        fin = mc.polyCube(
            w=fin_w, h=(0.38 + aggr * 0.36) * tune.detail,
            d=0.24 * tune.detail, name='rm_head_drone_side_fin_#',
        )[0]
        mc.move(side * (shell_x_edge + fin_w * 0.5 + 0.02),
                0.03 * tune.height, -0.04, fin, relative=True)
        mc.rotate(0, 0, -12 * side, fin)
        assign_material(fin, "rm_graphite_mat")
        _finish(fin, 0.018, hard=True)
        fins.append(fin)

    mc.parent(shell, eye_ring, eye, *fins, grp)


def _build_sentinel_head(grp: str, aggr: float, tune: HeadTune) -> None:
    tower = mc.polyCube(
        w=0.58 * tune.width, h=(0.98 + aggr * 0.36) * tune.height,
        d=0.58 * tune.depth, sx=2, sy=3, sz=2,
        name='rm_head_sentinel_tower_#',
    )[0]
    mc.scale(0.86, 1.0, 0.82, tower)
    assign_material(tower, "rm_white_armor_mat")
    _finish(tower, 0.055, hard=True)

    face = mc.polyCube(
        w=0.28 * tune.eye, h=0.54 * tune.eye, d=0.08 * tune.eye,
        name='rm_head_sentinel_face_#',
    )[0]
    mc.move(0, 0.02 * tune.height, 0.32 * tune.depth, face, relative=True)
    assign_material(face, "rm_graphite_mat")
    _finish(face, 0.018, hard=True)

    slit = mc.polyCube(
        w=0.08 * tune.eye, h=0.42 * tune.eye, d=0.035 * tune.eye,
        name='rm_head_sentinel_slit_#',
    )[0]
    mc.move(0, 0.06 * tune.height, 0.38 * tune.depth, slit, relative=True)
    assign_material(slit, "rm_cyan_glow_mat")
    _finish(slit, 0.006, hard=True)

    crest = mc.polyCone(
        r=0.12 * tune.detail, h=(0.42 + aggr * 0.30) * tune.detail, sa=4,
        name='rm_head_sentinel_crest_#',
    )[0]
    mc.move(0, 0.66 * tune.height, 0, crest, relative=True)
    mc.scale(0.70, 1.0, 0.25, crest)
    assign_material(crest, "rm_white_armor_mat")
    _finish(crest, 0.0, hard=True)

    mc.parent(tower, face, slit, crest, grp)


@register('HEAD')
class HeadModule(BaseModule):
    MODULE_NAME = 'HEAD'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_head_DEBUG'

        grp = mc.group(empty=True, name='rm_head_#')
        aggr = 0.5
        style = self._get('head_style', 'helmet')
        tune = HeadTune.from_params(self._get)

        if style == 'drone':
            _build_drone_head(grp, aggr, tune)
        elif style == 'sentinel':
            _build_sentinel_head(grp, aggr, tune)
        else:
            _build_helmet_head(grp, aggr, tune)

        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)
