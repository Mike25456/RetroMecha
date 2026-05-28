"""
RetroMecha — utils/maya_materials.py  v2
Bridge entre Lambert (fallback) y aiToon (Arnold).

assign_material(node, role) respeta la paleta activa:
  - Si hay paleta + Arnold → aiToon del tier correcto
  - Si no             → Lambert original (sin cambios de comportamiento)

Paleta activa se establece llamando set_active_palette(name) desde la UI.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

# Mapa nombre-material → tier aiToon
_ROLE_TO_TIER = {
    'rm_white_armor_mat': 'ARMOR',
    'rm_graphite_mat':    'JOINT',
    'rm_cyan_glow_mat':   'GLOW',
}

# Paleta activa — None = usar Lambert (comportamiento original)
_ACTIVE_PALETTE = [None]

# Materiales Lambert originales (sin cambios)
MATERIALS = {
    'rm_white_armor_mat': {
        'color': (0.86, 0.84, 0.78),
        'ambientColor': (0.12, 0.12, 0.11),
        'diffuse': 0.82,
    },
    'rm_graphite_mat': {
        'color': (0.12, 0.13, 0.13),
        'ambientColor': (0.03, 0.04, 0.04),
        'diffuse': 0.72,
    },
    'rm_cyan_glow_mat': {
        'color': (0.04, 0.75, 1.0),
        'ambientColor': (0.0, 0.22, 0.28),
        'incandescence': (0.0, 0.55, 0.85),
        'diffuse': 0.45,
    },
    "rm_terrain_base_mat": {
        "color": (0.30, 0.31, 0.29),
        "ambientColor": (0.05, 0.05, 0.045),
        "diffuse": 0.68,
    },
    "rm_terrain_dark_mat": {
        "color": (0.13, 0.14, 0.13),
        "ambientColor": (0.025, 0.025, 0.022),
        "diffuse": 0.58,
    },
    "rm_terrain_accent_mat": {
        "color": (0.42, 0.36, 0.28),
        "ambientColor": (0.07, 0.055, 0.04),
        "diffuse": 0.64,
    },
}


def set_active_palette(palette_name):
    """
    Activa una paleta. Llamar desde la UI al cambiar la selección.
    Pasar None para desactivar (vuelve a Lambert).
    """
    _ACTIVE_PALETTE[0] = palette_name
    # Limpiar cache para que los materiales se recreen con la nueva paleta
    try:
        from utils.material_assigner import clear_material_cache
        clear_material_cache()
    except ImportError:
        pass
    print(f'[RetroMecha][Materials] Paleta activa: {palette_name or "Lambert (default)"}')


def get_active_palette():
    return _ACTIVE_PALETTE[0]


def ensure_material(name: str) -> str | None:
    """Crea el material Lambert si no existe. Retorna shading group."""
    if mc is None:
        return None
    shader = name
    sg     = f'{name}SG'
    if not mc.objExists(shader):
        shader = mc.shadingNode('lambert', asShader=True, name=name)
        for attr, val in MATERIALS.get(name, {}).items():
            if isinstance(val, tuple):
                mc.setAttr(f'{shader}.{attr}', *val, type='double3')
            else:
                mc.setAttr(f'{shader}.{attr}', val)
    if not mc.objExists(sg):
        sg = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
        mc.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)
    return sg


def assign_material(node: str, name: str) -> None:
    """
    Asigna material a un nodo.
    - Con paleta activa + Arnold → aiToon del tier
    - Sin paleta o sin Arnold    → Lambert original
    """
    if mc is None or not node or not mc.objExists(node):
        return

    palette = _ACTIVE_PALETTE[0]
    tier    = _ROLE_TO_TIER.get(name)

    if palette and tier:
        try:
            from utils.material_assigner import _assign_aitoon, _load_palette
            p = _load_palette(palette)
            if p:
                _assign_aitoon(node, tier, p, palette)
                return
        except Exception:
            pass  # fallback a Lambert silenciosamente

    # Lambert original — sin cambios de comportamiento
    sg = ensure_material(name)
    if sg:
        try:
            mc.sets(node, edit=True, forceElement=sg)
        except Exception:
            pass


def verify_materials_on_group(group: str) -> dict:
    """
    Verifica qué materiales están asignados en el grupo.
    Retorna {'assigned': int, 'unassigned': int, 'nodes': [nombres sin material]}
    """
    if mc is None or not group or not mc.objExists(group):
        return {'assigned': 0, 'unassigned': 0, 'nodes': []}

    default_sg = 'initialShadingGroup'
    assigned   = 0
    unassigned = 0
    no_mat     = []

    descendants = mc.listRelatives(group, allDescendents=True, type='mesh') or []
    for shape in descendants:
        sgs = mc.listSets(type=1, object=shape) or []
        if not sgs or (len(sgs) == 1 and sgs[0] == default_sg):
            unassigned += 1
            no_mat.append(shape)
        else:
            assigned += 1

    return {'assigned': assigned, 'unassigned': unassigned, 'nodes': no_mat}