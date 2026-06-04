"""
RetroMecha — utils/maya_materials.py  v4
Materiales aiStandardSurface (Arnold).

Los presets y la UI hablan en terminos "semanticos" (color, diffuse,
incandescence, ambientColor). Este modulo traduce esos nombres al atributo
real de aiStandardSurface:

  - color         → baseColor
  - diffuse       → base (peso 0-1)
  - incandescence → emissionColor + emission (peso)
  - ambientColor  → (ignorado: aiSS no tiene ambient)

assign_material(node, role) crea y asigna aiStandardSurface base.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

# Default global de diffuseRoughness para reducir reflejos del lobulo difuso.
DEFAULT_DIFFUSE_ROUGHNESS = 0.5

# Defaults en terminos semanticos. terrain_accent es emisivo segun su color base.
MATERIALS = {
    'rm_white_armor_mat': {
        'color':            (0.86, 0.84, 0.78),
        'diffuse':          0.82,
        'diffuseRoughness': DEFAULT_DIFFUSE_ROUGHNESS,
    },
    'rm_graphite_mat': {
        'color':            (0.12, 0.13, 0.13),
        'diffuse':          0.72,
        'diffuseRoughness': DEFAULT_DIFFUSE_ROUGHNESS,
    },
    'rm_cyan_glow_mat': {
        'color':            (0.04, 0.75, 1.0),
        'incandescence':    (0.0, 0.55, 0.85),
        'diffuse':          0.45,
        'diffuseRoughness': DEFAULT_DIFFUSE_ROUGHNESS,
    },
    'rm_terrain_base_mat': {
        'color':            (0.30, 0.31, 0.29),
        'diffuse':          0.68,
        'diffuseRoughness': DEFAULT_DIFFUSE_ROUGHNESS,
    },
    'rm_terrain_dark_mat': {
        'color':            (0.13, 0.14, 0.13),
        'diffuse':          0.58,
        'diffuseRoughness': DEFAULT_DIFFUSE_ROUGHNESS,
    },
    'rm_terrain_accent_mat': {
        'color':            (0.42, 0.36, 0.28),
        # Familia del emisivo del mecha (cyan_glow.incandescence) × 0.5 → oscuro
        'incandescence':    (0.0, 0.275, 0.425),
        'emission':         0.5,                  # peso explicito (0.5, no 1)
        'diffuse':          0.64,
        'diffuseRoughness': DEFAULT_DIFFUSE_ROUGHNESS,
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
    """Aplica un valor 'semantico' al shader aiStandardSurface.

    Semantics:
      color            → baseColor
      diffuse          → base (peso difuso 0-1)
      diffuseRoughness → diffuseRoughness
      incandescence    → emissionColor + emission=1.0 (auto si color != 0).
                          Si quieres un peso especifico, usa 'emission'
                          DESPUES de incandescence para sobreescribirlo.
      emission         → emission (peso explicito 0-1)
      ambientColor     → ignorado (aiSS no tiene ambient)
    """
    if mc is None or not shader or not mc.objExists(shader):
        return False
    try:
        if semantic == 'color':
            mc.setAttr(f'{shader}.baseColor', *value, type='double3')
        elif semantic == 'diffuse':
            mc.setAttr(f'{shader}.base', float(value))
        elif semantic == 'diffuseRoughness':
            mc.setAttr(f'{shader}.diffuseRoughness', float(value))
        elif semantic == 'incandescence':
            # Emission: peso auto = 1 si el color tiene algun canal > 0
            weight = 1.0 if any(v > 1e-4 for v in value) else 0.0
            mc.setAttr(f'{shader}.emissionColor', *value, type='double3')
            mc.setAttr(f'{shader}.emission', weight)
        elif semantic == 'emission':
            # Override explicito del peso de emision (despues de incandescence)
            mc.setAttr(f'{shader}.emission', float(value))
        elif semantic == 'ambientColor':
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
        if semantic == 'diffuseRoughness':
            return mc.getAttr(f'{shader}.diffuseRoughness')
        if semantic == 'incandescence':
            return mc.getAttr(f'{shader}.emissionColor')[0]
        if semantic == 'emission':
            return mc.getAttr(f'{shader}.emission')
        if semantic == 'ambientColor':
            return None
    except Exception:
        return None
    return None


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
    Asigna material aiStandardSurface base a un nodo.
    """
    if mc is None or not node or not mc.objExists(node):
        return

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
