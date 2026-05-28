"""
RetroMecha — utils/maya_materials.py  v2
Material helpers — bridge entre el sistema Lambert antiguo y aiToon nuevo.

assign_material(node, role) ahora delega al material_assigner si hay paleta activa,
cayendo a Lambert si no hay Arnold o no hay paleta configurada.

roles: 'armor' | 'joint' | 'glow'  (equivalen a los tiers ARMOR/JOINT/GLOW)
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

# Mapa role → tier del sistema aiToon
_ROLE_TO_TIER = {
    'rm_white_armor_mat': 'ARMOR',
    'rm_graphite_mat':    'JOINT',
    'rm_cyan_glow_mat':   'GLOW',
}

# Materiales Lambert de fallback (sin Arnold)
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
}

# Paleta activa — se actualiza desde la UI vía set_active_palette()
_ACTIVE_PALETTE = [None]


def set_active_palette(palette_name: str):
    """Llamado desde la UI al cambiar paleta. Limpia el cache de materiales."""
    _ACTIVE_PALETTE[0] = palette_name
    try:
        from utils.material_assigner import clear_material_cache
        clear_material_cache()
    except ImportError:
        pass


def ensure_material(name: str) -> str | None:
    """Crea el material Lambert si no existe. Retorna el shading group."""
    if mc is None:
        return None
    shader = name
    sg = f'{name}SG'
    if not mc.objExists(shader):
        shader = mc.shadingNode('lambert', asShader=True, name=name)
        for attr, val in MATERIALS.get(name, {}).items():
            if isinstance(val, tuple):
                mc.setAttr(f'{shader}.{attr}', *val, type='double3')
            else:
                mc.setAttr(f'{shader}.{attr}', val)
    if not mc.objExists(sg):
        sg = mc.sets(renderable=True, noSurfaceShader=True,
                     empty=True, name=sg)
        mc.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)
    return sg


def assign_material(node: str, name: str) -> None:
    """
    Asigna material a un nodo.
    Si hay paleta activa Y Arnold disponible → usa aiToon del tier correspondiente.
    Si no → usa Lambert de fallback.
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
                # Crear/reusar el aiToon de este tier
                _assign_aitoon(node, tier, p, palette)
                return
        except Exception:
            pass

    # Fallback Lambert
    sg = ensure_material(name)
    if sg:
        try:
            mc.sets(node, edit=True, forceElement=sg)
        except Exception:
            pass
