try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material

_IGNORE_TOKENS = frozenset({'rm', 'l', 'r', 'head', 'arm', 'wing', 'torso'})


def _tokenize(name: str) -> tuple[list[str], str]:
    parts = name.lower().split('_')
    tokens = [p for p in parts if p not in _IGNORE_TOKENS and not p.isdigit()]
    return tokens, '_'.join(tokens)


_MULTI_GRAPHITE = [
    'side_fin',
    'eye_ring',
    'upper_core',
    'pad_trim',
]

_MULTI_CYAN = [
    'cannon_core',
]

_GLOW_TOKENS = frozenset({
    'glow', 'visor', 'slit', 'halo', 'inner', 'strip', 'accent', 'energy',
})

_WHITE_TOKENS = frozenset({
    'main', 'tower', 'blade', 'plate', 'block', 'forearm',
    'crest', 'shell', 'body', 'fin', 'armor', 'tip',
    'collar', 'pad', 'upper',
})


def _resolve_mecha_material(mesh_name: str) -> str:
    tokens, combined = _tokenize(mesh_name)

    for pattern in _MULTI_CYAN:
        if pattern in combined:
            return "rm_cyan_glow_mat"

    for pattern in _MULTI_GRAPHITE:
        if pattern in combined:
            return "rm_graphite_mat"

    for token in tokens:
        if token in _GLOW_TOKENS:
            return "rm_cyan_glow_mat"

    if 'eye' in tokens:
        return "rm_cyan_glow_mat"

    if 'core' in tokens:
        return "rm_cyan_glow_mat"

    for token in tokens:
        if token in _WHITE_TOKENS:
            return "rm_white_armor_mat"

    return "rm_graphite_mat"


def materialize_mecha(root_group: str) -> int:
    if mc is None or not root_group or not mc.objExists(root_group):
        return 0

    meshes = mc.listRelatives(root_group, allDescendents=True, type="mesh") or []
    meshes = list(set(meshes))
    count = 0
    for mesh in meshes:
        transform = mc.listRelatives(mesh, parent=True)[0]
        mat = _resolve_mecha_material(transform)
        assign_material(transform, mat)
        count += 1

    if count:
        print(f"[RetroMecha][Materializer] {count} mecha meshes materializados")
    return count


_TERRAIN_BASE_TOKENS = frozenset({
    'ground', 'surface', 'border', 'monument', 'central', 'wing',
    'tower', 'shaft', 'skyline', 'blk', 'plat', 'platform',
    'pillar', 'base',
})

_TERRAIN_DARK_TOKENS = frozenset({
    'debris', 'deb', 'fragment', 'frag', 'slab', 'slab2',
    'ramp', 'ramps', 'wedge',
})

_TERRAIN_ACCENT_TOKENS = frozenset({
    'lip', 'slot', 'ring', 'cap', 'col', 'tip',
})


def _resolve_terrain_material(mesh_name: str) -> str:
    parts = [p for p in mesh_name.lower().split('_') if p and not p.isdigit()]

    for token in parts:
        if token in _TERRAIN_ACCENT_TOKENS:
            return 'rm_terrain_accent_mat'

    for token in parts:
        if token in _TERRAIN_DARK_TOKENS:
            return 'rm_terrain_dark_mat'

    for token in parts:
        if token in _TERRAIN_BASE_TOKENS:
            return 'rm_terrain_base_mat'

    return 'rm_terrain_dark_mat'


def materialize_terrain(root_group: str) -> int:
    if mc is None or not root_group or not mc.objExists(root_group):
        return 0

    meshes = mc.listRelatives(root_group, allDescendents=True, type="mesh") or []
    meshes = list(set(meshes))
    count = 0
    for mesh in meshes:
        transform = mc.listRelatives(mesh, parent=True)[0]
        mat = _resolve_terrain_material(transform)
        assign_material(transform, mat)
        count += 1

    if count:
        print(f"[RetroMecha][Materializer] {count} terrain meshes materializados")
    return count
