"""Small scene-wide Maya helpers used by builders and UI."""

try:
    import maya.cmds as mc
except ImportError:
    mc = None


def force_preview_one(root: str) -> int:
    """Force all mesh transforms under root to Maya smooth preview level 1."""
    if mc is None or not root or not mc.objExists(root):
        return 0

    shapes = mc.listRelatives(root, allDescendents=True, type="mesh",
                              fullPath=True) or []
    if mc.nodeType(root) == "transform":
        shapes.extend(mc.listRelatives(root, shapes=True, type="mesh",
                                       fullPath=True) or [])

    transforms = []
    seen = set()
    for shape in shapes:
        parent = (mc.listRelatives(shape, parent=True, fullPath=True) or [None])[0]
        if parent and parent not in seen:
            seen.add(parent)
            transforms.append(parent)

    for node in transforms:
        try:
            mc.displaySmoothness(
                node,
                divisionsU=0,
                divisionsV=0,
                pointsWire=4,
                pointsShaded=1,
                polygonObject=1,
            )
        except Exception:
            pass

    return len(transforms)
