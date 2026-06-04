"""
RetroMecha - materials/sky_material.py
Material aiStandardSurface 'sky_material' para la malla 'sky' con un ramp V/Spike
conectado a baseColor + emissionColor. La paleta del ramp se selecciona segun
el preset de colores activo en el panel de materiales (composicion armonica).

Especificacion aiStandardSurface:
  base                = 1.0
  diffuseRoughness    = 0.0
  specular            = 0.0   (sin reflejos para fondo)
  specularRoughness   = 1.0
  specularIOR         = 1.0
  transmission        = 0.0
  subsurface          = 0.0
  coat                = 0.0
  emission            = 0.5
  thinWalled          = off
  opacity             = (1, 1, 1)

  baseColor      ← ramp.outColor
  emissionColor  ← ramp.outColor

Ramp:
  type           = 0  (V Ramp)
  interpolation  = 6  (Spike)
  uWave/vWave/noise = 0
  noiseFreq      = 0.5
  2 stops por paleta (default = azul oscuro / cian brillante)
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

SHADER_NAME = 'sky_material'
SG_NAME     = 'sky_materialSG'
RAMP_NAME   = 'rm_sky_ramp'           # equivalente al 'ramp1' del setup
SKY_MESH    = 'sky'

# Tag para limpieza segura
SHADER_TAG  = 'rmSkyShader'

# Maya enums
RAMP_TYPE_V              = 0
RAMP_INTERPOLATION_SPIKE = 6

# ── Stops del ramp (palette-aware, derivados en runtime) ──────────────
# Las posiciones son fijas del setup MEL del usuario:
#   - 0.548 : base oscura  (stop_bottom)
#   - 1.000 : extremo claro (stop_top)
# Los COLORES se derivan de la paleta:
#   - top    = rm_cyan_glow_mat.color de la paleta (acento brillante del mecha)
#   - bottom = top * SKY_DARK_FACTOR   (misma familia, mas oscuro)
# Asi cualquier paleta nueva agregada en materials.presets.PRESETS se refleja
# en el sky automaticamente sin tocar este modulo.
SKY_STOP_POS_BOTTOM = 0.548
SKY_STOP_POS_TOP    = 1.000
SKY_DARK_FACTOR     = 0.10   # 10% del top → base oscura azul-marino-style

DEFAULT_PRESET = 'Default'

# Pesos base (el usuario indico emission 0.5 a 1.0; usamos 0.5 como default)
BASE_WEIGHT      = 1.0
EMISSION_WEIGHT  = 0.5


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def create_sky_material(palette: str = DEFAULT_PRESET) -> str | None:
    """Crea (o recrea) sky_material + ramp y lo asigna a 'sky'.

    Args:
        palette: nombre del preset (Default/Atardecer/Frio/Oxidado/Neon)

    Retorna el shading group, o None si Arnold no esta disponible o sky no existe.
    """
    if not MAYA_AVAILABLE:
        return None
    if not _has_arnold():
        print('[RetroMecha][SkyMat] Arnold no cargado — sky_material omitido')
        return None
    if not mc.objExists(SKY_MESH):
        print(f'[RetroMecha][SkyMat] {SKY_MESH} no existe en escena')
        return None

    remove_sky_material()

    # 1. Ramp
    ramp = mc.shadingNode('ramp', asTexture=True, name=RAMP_NAME)
    _configure_ramp(ramp, palette)

    # 2. Shader aiStandardSurface
    shader = mc.shadingNode('aiStandardSurface', asShader=True, name=SHADER_NAME)
    _configure_shader(shader)

    # Conexiones ramp → baseColor + emissionColor
    try:
        mc.connectAttr(f'{ramp}.outColor', f'{shader}.baseColor',     force=True)
        mc.connectAttr(f'{ramp}.outColor', f'{shader}.emissionColor', force=True)
    except Exception as e:
        print(f'[RetroMecha][SkyMat] Connect ramp: {e}')

    # 3. Shading group + assign
    sg = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=SG_NAME)
    try:
        mc.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)
    except Exception as e:
        print(f'[RetroMecha][SkyMat] Connect SG: {e}')

    try:
        mc.sets(SKY_MESH, edit=True, forceElement=sg)
    except Exception as e:
        print(f'[RetroMecha][SkyMat] Assign to {SKY_MESH}: {e}')

    # Tag el shader para limpieza
    if not mc.attributeQuery(SHADER_TAG, node=shader, exists=True):
        mc.addAttr(shader, longName=SHADER_TAG,
                   attributeType='bool', defaultValue=True)
    mc.setAttr(f'{shader}.{SHADER_TAG}', True)

    print(f'[RetroMecha][SkyMat] {SHADER_NAME} aplicado (palette={palette})')
    return sg


def update_sky_ramp(palette: str):
    """Recolorea el ramp existente con una nueva paleta sin recrear el material."""
    if not MAYA_AVAILABLE:
        return
    if not mc.objExists(RAMP_NAME):
        return
    _configure_ramp(RAMP_NAME, palette)
    print(f'[RetroMecha][SkyMat] ramp recoloreado → {palette}')


def remove_sky_material():
    """Elimina sky_material, su SG y el ramp asociado."""
    if not MAYA_AVAILABLE:
        return
    for name in (SG_NAME, SHADER_NAME, RAMP_NAME):
        if mc.objExists(name):
            try:
                mc.delete(name)
            except Exception:
                pass


def has_sky_material() -> bool:
    return MAYA_AVAILABLE and mc.objExists(SHADER_NAME)


def list_palettes() -> list[str]:
    """Las paletas soportadas son las de materials.presets.PRESETS."""
    try:
        from materials.presets import PRESETS
        return list(PRESETS.keys())
    except Exception:
        return [DEFAULT_PRESET]


# ══════════════════════════════════════════════════════════════════════
#  INTERNOS
# ══════════════════════════════════════════════════════════════════════

def _has_arnold() -> bool:
    try:
        from utils.maya_materials import has_arnold
        return has_arnold()
    except Exception:
        return False


def _stops_for_palette(palette: str):
    """Deriva los 2 stops del ramp del sky desde la paleta:
      - top    = rm_cyan_glow_mat.color (acento brillante del mecha)
      - bottom = top * SKY_DARK_FACTOR (misma familia, oscuro)
    """
    try:
        from materials.presets import PRESETS
        top_rgb = (PRESETS.get(palette, {})
                          .get('rm_cyan_glow_mat', {})
                          .get('color', (0.04, 0.75, 1.0)))
    except Exception:
        top_rgb = (0.04, 0.75, 1.0)

    bottom_rgb = tuple(round(c * SKY_DARK_FACTOR, 4) for c in top_rgb)
    return (
        (SKY_STOP_POS_BOTTOM, bottom_rgb),
        (SKY_STOP_POS_TOP,    top_rgb),
    )


def _configure_ramp(ramp: str, palette: str):
    """Limpia el ramp y aplica las 2 paradas derivadas de la paleta."""
    stops = _stops_for_palette(palette)

    # Atributos generales del ramp
    try:
        mc.setAttr(f'{ramp}.type',          RAMP_TYPE_V)
        mc.setAttr(f'{ramp}.interpolation', RAMP_INTERPOLATION_SPIKE)
        mc.setAttr(f'{ramp}.uWave',     0.0)
        mc.setAttr(f'{ramp}.vWave',     0.0)
        mc.setAttr(f'{ramp}.noise',     0.0)
        mc.setAttr(f'{ramp}.noiseFreq', 0.5)
    except Exception as e:
        print(f'[RetroMecha][SkyMat] ramp attrs: {e}')

    # Limpiar entries existentes del ramp
    try:
        indices = mc.getAttr(f'{ramp}.colorEntryList', multiIndices=True) or []
        for i in indices:
            try:
                mc.removeMultiInstance(f'{ramp}.colorEntryList[{i}]', b=True)
            except Exception:
                pass
    except Exception:
        pass

    # Aplicar las 2 paradas
    for idx, (pos, rgb) in enumerate(stops):
        try:
            mc.setAttr(f'{ramp}.colorEntryList[{idx}].position', float(pos))
            mc.setAttr(f'{ramp}.colorEntryList[{idx}].color',
                       float(rgb[0]), float(rgb[1]), float(rgb[2]),
                       type='double3')
        except Exception as e:
            print(f'[RetroMecha][SkyMat] ramp stop {idx}: {e}')


def _configure_shader(shader: str):
    """Aplica los valores fijos de aiStandardSurface segun la especificacion."""
    # Base
    _set(shader, 'base',             BASE_WEIGHT)
    _set(shader, 'diffuseRoughness', 0.0)
    # Specular off
    _set(shader, 'specular',          0.0)
    _set(shader, 'specularRoughness', 1.0)
    _set(shader, 'specularIOR',       1.0)
    # Transmission off
    _set(shader, 'transmission',     0.0)
    # SSS off
    _set(shader, 'subsurface',       0.0)
    # Coat off
    _set(shader, 'coat',             0.0)
    # Emission
    _set(shader, 'emission',         EMISSION_WEIGHT)
    # Geometry
    _set(shader, 'thinWalled',       0)
    # Opacity (1,1,1) — default, pero lo forzamos por si acaso
    _set_color(shader, 'opacity', (1.0, 1.0, 1.0))


def _set(node: str, attr: str, value):
    try:
        mc.setAttr(f'{node}.{attr}', value)
    except Exception as e:
        print(f'[RetroMecha][SkyMat] setAttr {node}.{attr}: {e}')


def _set_color(node: str, attr: str, rgb):
    try:
        mc.setAttr(f'{node}.{attr}', rgb[0], rgb[1], rgb[2], type='double3')
    except Exception as e:
        print(f'[RetroMecha][SkyMat] setAttr {node}.{attr}: {e}')
