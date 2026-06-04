"""
RetroMecha — modules/torso/_shared.py
Helpers compartidos por todos los estilos de torso.
"""
import math
try:
    import maya.cmds as mc
except ImportError:
    mc = None


def bbox_center(mesh: str) -> tuple:
    bb = mc.exactWorldBoundingBox(mesh)
    return ((bb[0] + bb[3]) * 0.5, (bb[1] + bb[4]) * 0.5, (bb[2] + bb[5]) * 0.5)


def taper_y(mesh: str, y_min: float, y_max: float, scale_bottom: float, scale_top: float) -> None:
    cx, _, cz = bbox_center(mesh)
    span = y_max - y_min or 1.0
    for v in mc.ls(f"{mesh}.vtx[*]", flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = max(0.0, min(1.0, (pos[1] - y_min) / span))
        s = scale_bottom + (scale_top - scale_bottom) * t
        mc.move(cx + (pos[0] - cx) * s, pos[1], cz + (pos[2] - cz) * s, v, ws=True)


def scale_bottom_faces(mesh: str, y_band: float = 0.14, face_scale: float = 0.38) -> None:
    bb = mc.exactWorldBoundingBox(mesh)
    y_cut = bb[1] + (bb[4] - bb[1]) * y_band
    cx, cz = (bb[0] + bb[3]) * 0.5, (bb[2] + bb[5]) * 0.5
    bottom_verts = set()
    n_faces = mc.polyEvaluate(mesh, face=True) or 0
    for i in range(n_faces):
        face = f"{mesh}.f[{i}]"
        verts = mc.polyListComponentConversion(face, fromFace=True, toVertex=True)
        verts = mc.ls(verts, flatten=True) or []
        if not verts:
            continue
        ys = [mc.pointPosition(v, w=True)[1] for v in verts]
        if sum(ys) / len(ys) <= y_cut:
            bottom_verts.update(verts)
    for v in bottom_verts:
        pos = mc.pointPosition(v, w=True)
        mc.move(cx + (pos[0] - cx) * face_scale, pos[1],
                cz + (pos[2] - cz) * face_scale, v, ws=True)


def bulge_front(mesh: str, amount: float) -> None:
    _, _, cz = bbox_center(mesh)
    for v in mc.ls(f"{mesh}.vtx[*]", flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        if pos[2] > cz:
            t = min(1.0, (pos[2] - cz) / 0.5)
            mc.move(pos[0], pos[1], pos[2] + amount * t, v, ws=True)


def round_block(mesh: str, bevel: float) -> None:
    try:
        mc.polyBevel(mesh, offset=bevel, segments=2, chamfer=0, ch=0)
    except Exception:
        pass
    try:
        mc.polySoftEdge(mesh, angle=180, ch=0)
    except Exception:
        pass


def finish(mesh: str) -> str:
    try:
        mc.displaySmoothness(mesh, divisionsU=0, divisionsV=0,
                              pointsWire=4, pointsShaded=1, polygonObject=1)
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def finish_bevel(mesh: str, bevel: float = 0.025, hard: bool = False) -> str:
    if bevel > 0:
        try:
            mc.polyBevel(mesh, offset=bevel, segments=1, chamfer=0, ch=0)
        except Exception:
            pass
    try:
        mc.polySoftEdge(mesh, angle=0 if hard else 45, ch=0)
    except Exception:
        pass
    try:
        mc.displaySmoothness(mesh, divisionsU=0, divisionsV=0,
                              pointsWire=4, pointsShaded=1, polygonObject=1)
    except Exception:
        pass
    if mc.objExists(mesh):
        mc.delete(mesh, ch=True)
    return mesh


def block(name: str, w: float, h: float, d: float,
          pos: tuple, rot: tuple = (0, 0, 0),
          bevel: float = 0.025, hard: bool = True) -> str:
    node = mc.polyCube(w=w, h=h, d=d, sx=2, sy=2, sz=1, name=name)[0]
    mc.move(pos[0], pos[1], pos[2], node, absolute=True)
    mc.rotate(rot[0], rot[1], rot[2], node)
    try:
        if bevel > 0:
            mc.polyBevel(node, offset=bevel, segments=1, chamfer=0, ch=0)
        mc.polySoftEdge(node, angle=0 if hard else 45, ch=0)
    except Exception:
        pass
    if mc.objExists(node):
        mc.delete(node, ch=True)
    return node


def keel(name: str, r: float, h: float, pos: tuple) -> str:
    node = mc.polyCone(r=r, h=h, sa=4, name=name)[0]
    mc.move(pos[0], pos[1], pos[2], node, absolute=True)
    mc.rotate(180, 45, 0, node)
    mc.scale(0.70, 1.0, 0.38, node)
    try:
        mc.polySoftEdge(node, angle=0, ch=0)
    except Exception:
        pass
    if mc.objExists(node):
        mc.delete(node, ch=True)
    return node
