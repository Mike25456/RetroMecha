"""Reusable hard-surface support pass for Maya meshes.

Adds small support bevels to low-poly primitive meshes so smooth
preview keeps their mechanical shape instead of melting the silhouette. It also
triangulates n-gons, because our generated geometry should never contain faces
with more than four vertices.
"""

import math

try:
    import maya.cmds as mc
    import maya.api.OpenMaya as om
except ImportError:
    mc = None
    om = None


SKIP_TOKENS = (
    "glow",
    "ring",
    "torus",
    "orb",
    "eye",
    "halo",
)


def _mesh_transforms(root: str) -> list[str]:
    if mc is None or not root or not mc.objExists(root):
        return []

    shapes = mc.listRelatives(root, allDescendents=True, type="mesh",
                              fullPath=True) or []
    if mc.nodeType(root) == "transform":
        own_shapes = mc.listRelatives(root, shapes=True, type="mesh",
                                      fullPath=True) or []
        shapes.extend(own_shapes)

    transforms = []
    seen = set()
    for shape in shapes:
        parent = (mc.listRelatives(shape, parent=True, fullPath=True) or [None])[0]
        if parent and parent not in seen:
            seen.add(parent)
            transforms.append(parent)
    return transforms


def _face_vertex_count(face: str) -> int:
    verts = mc.polyListComponentConversion(face, fromFace=True, toVertex=True)
    return len(mc.ls(verts, flatten=True) or [])


def _triangulate_ngons(node: str, max_sides: int = 4) -> int:
    """Convert any face with more than max_sides vertices into triangles."""
    try:
        face_count = mc.polyEvaluate(node, face=True) or 0
    except Exception:
        return 0

    fixed = 0
    for index in reversed(range(face_count)):
        face = f"{node}.f[{index}]"
        try:
            if _face_vertex_count(face) <= max_sides:
                continue
            mc.polyTriangulate(face, ch=0)
            fixed += 1
        except Exception:
            continue

    if fixed and mc.objExists(node):
        try:
            mc.delete(node, ch=True)
        except Exception:
            pass
    return fixed


def _hard_edge_components(node: str, angle_threshold: float = 35.0) -> list[str]:
    """Return edges where adjacent faces make a visible hard corner."""
    if mc is None or om is None:
        return []

    shapes = mc.listRelatives(node, shapes=True, type="mesh", fullPath=True) or []
    if not shapes:
        return []

    try:
        selection = om.MSelectionList()
        selection.add(shapes[0])
        dag = selection.getDagPath(0)
        mesh = om.MFnMesh(dag)
        edge_iter = om.MItMeshEdge(dag)
    except Exception:
        return []

    edges = []
    while not edge_iter.isDone():
        try:
            faces = edge_iter.getConnectedFaces()
            include = len(faces) < 2
            if len(faces) >= 2:
                normal = mesh.getPolygonNormal(faces[0], om.MSpace.kWorld)
                for face in faces[1:]:
                    other = mesh.getPolygonNormal(face, om.MSpace.kWorld)
                    if math.degrees(normal.angle(other)) >= angle_threshold:
                        include = True
                        break
            if include:
                edges.append(f"{node}.e[{edge_iter.index()}]")
        except Exception:
            pass
        edge_iter.next()
    return edges


def _crease_all_edges(node: str, value: float = 10.0) -> bool:
    edge_component = f"{node}.e[*]"
    for kwargs in ({"value": value}, {"v": value}):
        try:
            mc.polyCrease(edge_component, **kwargs)
            return True
        except Exception:
            continue
    return False


def _support_bevel(node: str, offset: float, fraction: float,
                   segments: int, hard_angle: float) -> bool:
    """Apply Maya's fraction bevel, with a classic bevel fallback."""
    hard_edges = _hard_edge_components(node, hard_angle)
    if not hard_edges:
        return False

    try:
        mc.select(hard_edges, replace=True)
        mc.polyBevel3(
            fraction=fraction,
            offsetAsFraction=True,
            autoFit=True,
            segments=segments,
            worldSpace=True,
            smoothingAngle=hard_angle,
            fillNgons=True,
            mergeVertices=True,
            mergeVertexTolerance=0.0001,
            miteringAngle=180,
            angleTolerance=180,
            ch=0,
        )
        return True
    except Exception:
        try:
            mc.select(hard_edges, replace=True)
            mc.polyBevel(hard_edges, offset=offset, segments=segments,
                         chamfer=0, ch=0)
            return True
        except Exception:
            return False
    finally:
        try:
            mc.select(clear=True)
        except Exception:
            pass


def apply_support_edges(root: str, offset: float = 0.012,
                        fraction: float = 0.045,
                        segments: int = 2,
                        max_faces: int = 80,
                        min_faces: int = 20,
                        hard_angle: float = 35.0,
                        crease_value: float = 0.0,
                        transforms: list = None) -> int:
    """Apply a bevel/n-gon cleanup pass to low-poly meshes under root.

    Args:
        root: Transform group or mesh transform (ignored if transforms provided).
        offset: Fallback bevel width if polyBevel3 is unavailable.
        fraction: Relative support bevel size used by polyBevel3.
        segments: Bevel segment count. Two gives center edge plus two supports.
        max_faces: Skip dense meshes (e.g. torus, ground plane).
        min_faces: Skip trivial meshes that don't need beveling (e.g. small debris).
        hard_angle: polySoftEdge angle after bevel.
        crease_value: Optional Maya crease strength. Zero disables creasing.
        transforms: Optional pre-resolved list of transform names (avoids DAG walk).

    Returns:
        Number of transforms processed.
    """
    if mc is None:
        return 0

    nodes = transforms if transforms is not None else _mesh_transforms(root)

    processed = 0
    found = 0
    skipped = 0
    skipped_small = 0
    for node in nodes:
        found += 1
        short = node.rsplit("|", 1)[-1].lower()
        if any(token in short for token in SKIP_TOKENS):
            skipped += 1
            continue

        try:
            faces = mc.polyEvaluate(node, face=True) or 0
        except Exception:
            continue
        if faces <= 0 or faces > max_faces:
            continue
        if faces < min_faces:
            skipped_small += 1
            continue

        _triangulate_ngons(node)

        changed = _support_bevel(node, offset, fraction, segments, hard_angle)

        try:
            mc.polySoftEdge(node, angle=hard_angle, ch=0)
            changed = True
        except Exception:
            pass

        fixed_after_bevel = _triangulate_ngons(node)
        changed = changed or bool(fixed_after_bevel)

        if mc.objExists(node):
            try:
                mc.delete(node, ch=True)
            except Exception:
                pass

        if crease_value > 0:
            changed = _crease_all_edges(node, crease_value) or changed
        if changed:
            processed += 1

    print(f'[RetroMecha][HardSurface] encontrados={found}, '
          f'omitidos={skipped}, pequeños={skipped_small}, '
          f'procesados={processed}, segments={segments}')
    return processed
