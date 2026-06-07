"""
RetroMecha — materials/materializer.py  v2

MEJORAS sobre v1:
  - Tokens ampliados para cubrir los nuevos módulos (greeble, barrier, cable)
  - rm_terrain_accent2_mat: cuarto material — acento estructural más cálido
    (cables, pilares ring, barrera slot, greeble slot) → diferencia de tono
    entre el accent frío del suelo y los detalles calientes de la estructura
  - _resolve_terrain_material prioriza accent2 antes que accent1
  - materialize_terrain crea el SG de accent2 si no existe
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import assign_material, ensure_material

_IGNORE_TOKENS = frozenset({'rm', 'l', 'r', 'head', 'arm', 'wing', 'torso'})


def _tokenize(name: str) -> tuple[list[str], str]:
    parts = name.lower().split('_')
    tokens = [p for p in parts if p not in _IGNORE_TOKENS and not p.isdigit()]
    return tokens, '_'.join(tokens)


_MULTI_GRAPHITE = ['side_fin', 'eye_ring', 'upper_core', 'pad_trim']
_MULTI_CYAN     = ['cannon_core']

_GLOW_TOKENS  = frozenset({'glow', 'visor', 'slit', 'halo', 'inner', 'strip',
                            'accent', 'energy'})
_WHITE_TOKENS = frozenset({'main', 'tower', 'blade', 'plate', 'block', 'forearm',
                            'crest', 'shell', 'body', 'fin', 'armor', 'tip',
                            'collar', 'pad', 'upper'})


def _resolve_mecha_material(mesh_name: str) -> str:
    tokens, combined = _tokenize(mesh_name)
    for pattern in _MULTI_CYAN:
        if pattern in combined:
            return 'rm_cyan_glow_mat'
    for pattern in _MULTI_GRAPHITE:
        if pattern in combined:
            return 'rm_graphite_mat'
    for token in tokens:
        if token in _GLOW_TOKENS:
            return 'rm_cyan_glow_mat'
    if 'eye' in tokens:
        return 'rm_cyan_glow_mat'
    if 'core' in tokens:
        return 'rm_cyan_glow_mat'
    for token in tokens:
        if token in _WHITE_TOKENS:
            return 'rm_white_armor_mat'
    return 'rm_graphite_mat'


def materialize_mecha(root_group: str) -> int:
    if mc is None or not root_group or not mc.objExists(root_group):
        return 0
    meshes = list(set(mc.listRelatives(root_group, allDescendents=True, type='mesh') or []))
    count  = 0
    for mesh in meshes:
        transform = mc.listRelatives(mesh, parent=True)[0]
        mat = _resolve_mecha_material(transform)
        assign_material(transform, mat)
        count += 1
    if count:
        print(f'[RetroMecha][Materializer] {count} mecha meshes materializados')
    return count


# ──────────────────────────────────────────────────────────────────────────────
#  TERRAIN MATERIAL RESOLUTION
# ──────────────────────────────────────────────────────────────────────────────

# accent2: cables, ranuras/slots de greebles y barriers → tono cálido/acento estr.
_TERRAIN_ACCENT2_TOKENS = frozenset({
    'cable', 'brace', 'conduit', 'lama', 'vent',
})

# accent: bordes, anillos, tapas, ranuras de suelo y plataforma
_TERRAIN_ACCENT_TOKENS = frozenset({
    'lip', 'slot', 'ring', 'cap', 'col', 'tip',
    'landing', 'strip', 'corner',   # nuevos del ground_plane v5
    'panel', 'step',                 # nuevos del platform v3
    'barrier',                       # barreras completas → accent
})

_TERRAIN_DARK_TOKENS = frozenset({
    'debris', 'deb', 'fragment', 'frag', 'slab', 'slab2',
    'ramp', 'ramps', 'wedge', 'chip',
    'greeble',                       # greebles base → dark para contraste
})

_TERRAIN_BASE_TOKENS = frozenset({
    'ground', 'surface', 'border', 'monument', 'central', 'wing',
    'tower', 'shaft', 'skyline', 'blk', 'plat', 'platform',
    'pillar', 'base', 'body',
})


def _resolve_terrain_material(mesh_name: str) -> str:
    parts = [p for p in mesh_name.lower().split('_') if p and not p.isdigit()]

    # Prioridad 1: accent2 (cables y detalles calientes)
    for token in parts:
        if token in _TERRAIN_ACCENT2_TOKENS:
            return 'rm_terrain_accent2_mat'

    # Prioridad 2: accent (bordes, ranuras, anillos)
    for token in parts:
        if token in _TERRAIN_ACCENT_TOKENS:
            return 'rm_terrain_accent_mat'

    # Prioridad 3: dark (escombros, fragmentos)
    for token in parts:
        if token in _TERRAIN_DARK_TOKENS:
            return 'rm_terrain_dark_mat'

    # Prioridad 4: base (suelo, plataformas, torres)
    for token in parts:
        if token in _TERRAIN_BASE_TOKENS:
            return 'rm_terrain_base_mat'

    return 'rm_terrain_dark_mat'


def materialize_terrain(root_group: str) -> int:
    if mc is None or not root_group or not mc.objExists(root_group):
        return 0

    meshes = list(set(mc.listRelatives(root_group, allDescendents=True, type='mesh') or []))
    sgs = {
        'rm_terrain_base_mat':    ensure_material('rm_terrain_base_mat'),
        'rm_terrain_dark_mat':    ensure_material('rm_terrain_dark_mat'),
        'rm_terrain_accent_mat':  ensure_material('rm_terrain_accent_mat'),
        'rm_terrain_accent2_mat': ensure_material('rm_terrain_accent2_mat'),
    }
    count = 0
    for mesh in meshes:
        transform = mc.listRelatives(mesh, parent=True)[0]
        mat = _resolve_terrain_material(transform)
        sg  = sgs.get(mat)
        if sg:
            try:
                mc.sets(transform, edit=True, forceElement=sg)
            except Exception:
                assign_material(transform, mat)
        else:
            assign_material(transform, mat)
        count += 1

    if count:
        print(f'[RetroMecha][Materializer] {count} terrain meshes materializados')
    return count