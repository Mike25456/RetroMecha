"""Small Maya material helpers shared by procedural modules."""

try:
    import maya.cmds as mc
except ImportError:
    mc = None


MATERIALS = {
    "rm_white_armor_mat": {
        "color": (0.86, 0.84, 0.78),
        "ambientColor": (0.12, 0.12, 0.11),
        "diffuse": 0.82,
    },
    "rm_graphite_mat": {
        "color": (0.12, 0.13, 0.13),
        "ambientColor": (0.03, 0.04, 0.04),
        "diffuse": 0.72,
    },
    "rm_cyan_glow_mat": {
        "color": (0.04, 0.75, 1.0),
        "ambientColor": (0.0, 0.22, 0.28),
        "incandescence": (0.0, 0.55, 0.85),
        "diffuse": 0.45,
    },
}


def ensure_material(name: str) -> str | None:
    if mc is None:
        return None

    shader = name
    shading_group = f"{name}SG"

    if not mc.objExists(shader):
        shader = mc.shadingNode("lambert", asShader=True, name=name)
        attrs = MATERIALS.get(name, {})
        for attr, value in attrs.items():
            if isinstance(value, tuple):
                mc.setAttr(f"{shader}.{attr}", *value, type="double3")
            else:
                mc.setAttr(f"{shader}.{attr}", value)

    if not mc.objExists(shading_group):
        shading_group = mc.sets(
            renderable=True,
            noSurfaceShader=True,
            empty=True,
            name=shading_group,
        )
        mc.connectAttr(f"{shader}.outColor", f"{shading_group}.surfaceShader", force=True)

    return shading_group


def assign_material(node: str, name: str) -> None:
    if mc is None or not node or not mc.objExists(node):
        return

    shading_group = ensure_material(name)
    if shading_group:
        try:
            mc.sets(node, edit=True, forceElement=shading_group)
        except Exception:
            pass
