"""Reusable hard-surface support pass for Maya meshes.

Adds small support bevels to low-poly primitive meshes so smooth preview keeps
their mechanical shape instead of melting the silhouette.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None


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


def apply_support_edges(root: str, offset: float = 0.012,
                        max_faces: int = 80,
                        hard_angle: float = 35.0) -> int:
    """Apply a small bevel/hard-normal pass to low-poly meshes under root.

    Args:
        root: Transform group or mesh transform.
        offset: Bevel width. Keep small; this is a support edge, not a style bevel.
        max_faces: Skip dense meshes like torus/spheres to avoid unnecessary cost.
        hard_angle: polySoftEdge angle after bevel.

    Returns:
        Number of transforms processed.
    """
    if mc is None:
        return 0

    processed = 0
    for node in _mesh_transforms(root):
        short = node.rsplit("|", 1)[-1].lower()
        if any(token in short for token in SKIP_TOKENS):
            continue

        try:
            faces = mc.polyEvaluate(node, face=True) or 0
        except Exception:
            continue
        if faces <= 0 or faces > max_faces:
            continue

        try:
            mc.polyBevel(node, offset=offset, segments=1, chamfer=0, ch=0)
            mc.polySoftEdge(node, angle=hard_angle, ch=0)
            if mc.objExists(node):
                mc.delete(node, ch=True)
            processed += 1
        except Exception:
            continue

    return processed
