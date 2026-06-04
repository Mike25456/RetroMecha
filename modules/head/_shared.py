"""RetroMecha — modules/head/_shared.py"""
from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None


@dataclass(frozen=True)
class HeadTune:
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


def finish(mesh: str, bevel: float = 0.03, hard: bool = False) -> str:
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
