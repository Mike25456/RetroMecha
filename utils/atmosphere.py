"""
RetroMecha - utils/atmosphere.py
Gestion del aiAtmosphereVolume para neblina volumetrica en Arnold.

Defaults:
  - density:     0.034
  - attenuation: (0, 0, 0)
  - anisotropy:  0.666
  - color:       default (1, 1, 1)

El nodo se conecta a defaultArnoldRenderOptions.atmosphere.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

NODE_NAME    = 'rm_aiAtmosphereVolume'
RENDER_OPTS  = 'defaultArnoldRenderOptions'
ATMO_PLUG    = 'defaultArnoldRenderOptions.atmosphere'

DEFAULT_DENSITY    = 0.034
DEFAULT_ATTENUATION = (0.0, 0.0, 0.0)
DEFAULT_ANISOTROPY = 0.666

DENSITY_MIN = 0.02
DENSITY_MAX = 0.08


# ══════════════════════════════════════════════════════════════════════
#  ARNOLD
# ══════════════════════════════════════════════════════════════════════

def _has_arnold() -> bool:
    try:
        from utils.maya_materials import has_arnold
        return has_arnold()
    except Exception:
        return False


def _ensure_arnold_options():
    """Asegura que defaultArnoldRenderOptions exista (lo crea Arnold al cargar)."""
    if mc.objExists(RENDER_OPTS):
        return True
    try:
        import mtoa.core as core
        core.createOptions()
    except Exception as e:
        print(f'[RetroMecha][Atmosphere] No se pudo crear Arnold options: {e}')
    return mc.objExists(RENDER_OPTS)


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def ensure_atmosphere(density: float = DEFAULT_DENSITY,
                      anisotropy: float = DEFAULT_ANISOTROPY) -> str | None:
    """Crea (o reutiliza) el aiAtmosphereVolume y lo conecta a Arnold.

    Retorna el nombre del nodo, o None si Arnold no esta disponible.
    """
    if not MAYA_AVAILABLE:
        return None
    if not _has_arnold():
        print('[RetroMecha][Atmosphere] Arnold no cargado — '
              'aiAtmosphereVolume omitido')
        return None

    _ensure_arnold_options()

    if not mc.objExists(NODE_NAME):
        try:
            atmo = mc.createNode('aiAtmosphereVolume', name=NODE_NAME)
        except Exception as e:
            print(f'[RetroMecha][Atmosphere] Error creando aiAtmosphereVolume: {e}')
            return None
    else:
        atmo = NODE_NAME

    # Configuracion base
    _set_attr_safe(atmo, 'density', float(density))
    _set_color_safe(atmo, 'attenuation', DEFAULT_ATTENUATION)
    _set_anisotropy(atmo, float(anisotropy))

    # Conectar a Arnold render options
    if mc.objExists(RENDER_OPTS):
        try:
            current_src = mc.connectionInfo(ATMO_PLUG, sourceFromDestination=True)
            target = f'{atmo}.message'
            if current_src != target:
                mc.connectAttr(target, ATMO_PLUG, force=True)
        except Exception as e:
            print(f'[RetroMecha][Atmosphere] Connect error: {e}')

    print(f'[RetroMecha][Atmosphere] {NODE_NAME} '
          f'(density={density:.3f}, anisotropy={anisotropy:.3f})')
    return atmo


def remove_atmosphere():
    """Elimina el aiAtmosphereVolume creado por RetroMecha."""
    if not MAYA_AVAILABLE:
        return
    if mc.objExists(NODE_NAME):
        try:
            mc.delete(NODE_NAME)
        except Exception:
            pass


def has_atmosphere() -> bool:
    return MAYA_AVAILABLE and mc.objExists(NODE_NAME)


def set_density(value: float):
    """Setea density manteniendo el clamp [0.02, 0.08] del slider."""
    if not MAYA_AVAILABLE:
        return
    v = max(DENSITY_MIN, min(DENSITY_MAX, float(value)))
    if not mc.objExists(NODE_NAME):
        ensure_atmosphere(density=v)
        return
    _set_attr_safe(NODE_NAME, 'density', v)


def set_anisotropy(value: float):
    if not MAYA_AVAILABLE or not mc.objExists(NODE_NAME):
        return
    _set_anisotropy(NODE_NAME, float(value))


# ══════════════════════════════════════════════════════════════════════
#  INTERNOS
# ══════════════════════════════════════════════════════════════════════

def _set_attr_safe(node: str, attr: str, value: float):
    try:
        mc.setAttr(f'{node}.{attr}', value)
    except Exception as e:
        print(f'[RetroMecha][Atmosphere] setAttr {node}.{attr}: {e}')


def _set_color_safe(node: str, attr: str, rgb: tuple):
    try:
        mc.setAttr(f'{node}.{attr}', rgb[0], rgb[1], rgb[2], type='double3')
    except Exception as e:
        print(f'[RetroMecha][Atmosphere] setAttr {node}.{attr}: {e}')


def _set_anisotropy(node: str, value: float):
    """aiAtmosphereVolume usa 'eccentricity' en MtoA viejo, 'anisotropy' en nuevo."""
    for attr in ('eccentricity', 'anisotropy'):
        if mc.attributeQuery(attr, node=node, exists=True):
            try:
                mc.setAttr(f'{node}.{attr}', value)
                return
            except Exception:
                pass
    print(f'[RetroMecha][Atmosphere] anisotropy/eccentricity no encontrado en {node}')
