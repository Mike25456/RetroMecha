"""
RetroMecha — utils/maya_materials.py  v4
Materiales aiStandardSurface (Arnold). Sin fallback a Lambert.

Los presets y la UI hablan en terminos "semanticos" (color, diffuse,
incandescence, ambientColor). Este modulo traduce esos nombres al atributo
real de aiStandardSurface:

  - color         → baseColor
  - diffuse       → base (peso 0-1)
  - incandescence → emissionColor + emission (peso)
  - ambientColor  → (ignorado: aiSS no tiene ambient)

assign_material(node, role) respeta la paleta activa:
  - Si hay paleta + Arnold → aiToon del tier correcto
  - Si no                  → aiStandardSurface base
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

# Paleta aiToon activa — None = usar aiStandardSurface base
_ACTIVE_PALETTE = [None]

# Defaults en terminos semanticos.
MATERIALS = {
    'rm_white_armor_mat': {
        'color':   (0.86, 0.84, 0.78),
        'diffuse': 0.82,
    },
    'rm_graphite_mat': {
        'color':   (0.12, 0.13, 0.13),
        'diffuse': 0.72,
    },
    'rm_cyan_glow_mat': {
        'color':         (0.04, 0.75, 1.0),
        'incandescence': (0.0, 0.55, 0.85),
        'diffuse':       0.45,
    },
    'rm_terrain_base_mat': {
        'color':   (0.30, 0.31, 0.29),
        'diffuse': 0.68,
    },
    'rm_terrain_dark_mat': {
        'color':   (0.13, 0.14, 0.13),
        'diffuse': 0.58,
    },
    'rm_terrain_accent_mat': {
        'color':   (0.42, 0.36, 0.28),
        'diffuse': 0.64,
    },
}


# ══════════════════════════════════════════════════════════════════════
#  ARNOLD DETECTION
# ══════════════════════════════════════════════════════════════════════

def _has_arnold() -> bool:
    if mc is None:
        return False
    try:
        return 'mtoa' in (mc.pluginInfo(q=True, listPlugins=True) or [])
    except Exception:
        return False


def _ensure_arnold() -> bool:
    """Carga mtoa si no esta cargado. Retorna True si quedo disponible."""
    if mc is None:
        return False
    if _has_arnold():
        return True
    try:
        mc.loadPlugin('mtoa', quiet=True)
    except Exception as e:
        print(f'[RetroMecha][Material] No se pudo cargar mtoa: {e}')
    return _has_arnold()


# ══════════════════════════════════════════════════════════════════════
#  TRADUCCION SEMANTICA → ATRIBUTOS DE aiStandardSurface
# ══════════════════════════════════════════════════════════════════════

def set_semantic_attr(shader: str, semantic: str, value) -> bool:
    """Aplica un valor 'semantico' al shader aiStandardSurface."""
    if mc is None or not shader or not mc.objExists(shader):
        return False
    try:
        if semantic == 'color':
            mc.setAttr(f'{shader}.baseColor', *value, type='double3')
        elif semantic == 'diffuse':
            mc.setAttr(f'{shader}.base', float(value))
        elif semantic == 'incandescence':
            # Emission: peso = 1 si el color tiene algun canal > 0, sino 0
            weight = 1.0 if any(v > 1e-4 for v in value) else 0.0
            mc.setAttr(f'{shader}.emissionColor', *value, type='double3')
            mc.setAttr(f'{shader}.emission', weight)
        elif semantic == 'ambientColor':
            # aiSS no tiene ambient — se ignora silenciosamente
            return True
        else:
            return False
        return True
    except Exception as e:
        print(f'[RetroMecha][Material] setAttr {shader}.{semantic}: {e}')
        return False


def get_semantic_attr(shader: str, semantic: str):
    """Lee el valor 'semantico' del shader aiStandardSurface."""
    if mc is None or not shader or not mc.objExists(shader):
        return None
    try:
        if semantic == 'color':
            return mc.getAttr(f'{shader}.baseColor')[0]
        if semantic == 'diffuse':
            return mc.getAttr(f'{shader}.base')
        if semantic == 'incandescence':
            return mc.getAttr(f'{shader}.emissionColor')[0]
        if semantic == 'ambientColor':
            return None
    except Exception:
        return None
    return None


# ══════════════════════════════════════════════════════════════════════
#  PALETA aiToon
# ══════════════════════════════════════════════════════════════════════

def set_active_palette(palette_name):
    """
    Activa una paleta aiToon. Llamar desde la UI al cambiar la seleccion.
    Pasar None para desactivar (vuelve a aiStandardSurface base).
    """
    _ACTIVE_PALETTE[0] = palette_name
    try:
        from utils.material_assigner import clear_material_cache
        clear_material_cache()
    except ImportError:
        pass
    print(f'[RetroMecha][Materials] Paleta activa: {palette_name or "aiStandardSurface base"}')


def get_active_palette():
    return _ACTIVE_PALETTE[0]


# ══════════════════════════════════════════════════════════════════════
#  CREACION / ASIGNACION
# ══════════════════════════════════════════════════════════════════════

def ensure_material(name: str) -> str | None:
    """Crea el shader aiStandardSurface si no existe y su SG.
    Retorna el shading group, o None si Arnold no esta disponible.
    """
    if mc is None:
        return None
    if not _ensure_arnold():
        print('[RetroMecha][Material] Arnold (mtoa) no disponible — '
              'no se puede crear aiStandardSurface')
        return None

    shader = name
    sg     = f'{name}SG'

    if not mc.objExists(shader):
        try:
            shader = mc.shadingNode('aiStandardSurface', asShader=True, name=name)
        except Exception as e:
            print(f'[RetroMecha][Material] Error creando aiStandardSurface {name}: {e}')
            return None
        # Aplicar defaults semanticos
        for semantic, val in MATERIALS.get(name, {}).items():
            set_semantic_attr(shader, semantic, val)

    if not mc.objExists(sg):
        sg = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg)
        mc.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)
    return sg


def assign_material(node: str, name: str) -> None:
    """
    Asigna material a un nodo.
    - Con paleta activa → aiToon del tier
    - Sin paleta        → aiStandardSurface base
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
            pass

    sg = ensure_material(name)
    if sg:
        try:
            mc.sets(node, edit=True, forceElement=sg)
        except Exception:
            pass


def verify_materials_on_group(group: str) -> dict:
    """Verifica que materiales estan asignados en el grupo."""
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
