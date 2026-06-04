"""
RetroMecha - utils/lighting.py  v4
Iluminacion completa con 5 luces aiArea/aiMesh basadas en paleta:

  luz_ambiente            - aiAreaLight quad  (suelo, color paleta)
  foco_mecha              - aiAreaLight disk  (foco del mecha, BLANCA)
  background              - aiAreaLight quad  (fondo, BLANCA)
  veam_light_izquierdo    - aiMeshLight cubo  (rayo izq, color paleta)
  veam_light_derecho      - aiMeshLight cubo  (rayo der simetrico, color paleta)

Reglas:
  - luz_ambiente y veam_light_* toman color del cyan_glow de la paleta activa
    (acento del mecha → composicion armonica con el resto de materiales).
  - background y foco_mecha son BLANCAS por especificacion.
  - background.translateZ y veam_light_*.translateZ se calculan como
    (skyline_back_z + 4)  →  4 unidades delante de los elementos de fondo.
  - veam_light_izquierdo / veam_light_derecho son simetricos en X.

Todas las luces llevan el tag rmLight para limpieza segura.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

_LIGHT_TAG = 'rmLight'

# ── Z offset respecto al fondo ───────────────────────────────────────
BACKGROUND_Z_OFFSET = 4.0      # 4 unidades delante del skyline
DEFAULT_BACK_Z      = -55.0    # fallback si no hay rm_skyline_* en escena

# ── luz_ambiente (aiAreaLight quad — color paleta) ───────────────────
AMBIENT_NAME      = 'luz_ambiente'
AMBIENT_TRANSLATE = (0.0, 0.189, 0.0)
AMBIENT_ROTATE    = (90.0, 0.0, 0.0)
AMBIENT_SCALE     = (72.185, 72.185, 72.185)
AMBIENT_INTENSITY = 8.974
AMBIENT_EXPOSURE  = 9.522

# ── foco_mecha (aiAreaLight disk — BLANCA) ──────────────────────────
FOCO_NAME      = 'foco_mecha'
FOCO_TRANSLATE = (0.0, 0.414, 0.0)
FOCO_ROTATE    = (90.0, 0.0, 0.0)
FOCO_SCALE     = (2.345, 2.345, 2.345)
FOCO_INTENSITY = 5.577
FOCO_EXPOSURE  = 3.766
FOCO_COLOR     = (1.0, 1.0, 1.0)

# ── background (aiAreaLight quad — BLANCA, Z dinamico) ──────────────
BG_NAME      = 'background'
BG_TRANS_XY  = (0.0, 0.0)   # X, Y; Z se calcula
BG_ROTATE    = (90.0, 0.0, 0.0)
BG_SCALE     = (81.476, 1.007, 43.871)
BG_INTENSITY = 10.000
BG_EXPOSURE  = 6.591
BG_COLOR     = (1.0, 1.0, 1.0)

# ── veam_light_* (aiMeshLight cubo simetrico — color paleta) ─────────
VEAM_NAME_L    = 'veam_light_izquierdo'
VEAM_NAME_R    = 'veam_light_derecho'
VEAM_LIGHT_SUF = '_light'        # nombre del aiMeshLight: <name>_light
VEAM_TX_L      = -20.564
VEAM_TX_R      = +20.564
VEAM_TY        = 8.144
VEAM_SCALE     = (1.0, 387.639, 1.0)
VEAM_INTENSITY = 5.449
VEAM_EXPOSURE  = 8.524

# Multiplicador global de intensidad (slider de la UI)
_INTENSITY_MULT = [1.0]

# Rango sugerido para sliders individuales
INTENSITY_MIN = 4.0
INTENSITY_MAX = 20.0

# Almacen individual de intensidad por luz (para sliders separados)
_LIGHT_INTENSITIES = {
    AMBIENT_NAME: AMBIENT_INTENSITY,
    FOCO_NAME:    FOCO_INTENSITY,
    BG_NAME:      BG_INTENSITY,
}
_VEAM_INTENSITY = [VEAM_INTENSITY]


# ══════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════

def _has_arnold() -> bool:
    if not MAYA_AVAILABLE:
        return False
    try:
        return 'mtoa' in (mc.pluginInfo(q=True, listPlugins=True) or [])
    except Exception:
        return False


def _palette_accent_color(palette_label: str = 'Default'):
    """Color de acento del mecha (cyan_glow) para tenir las luces palette-aware."""
    try:
        from materials.presets import PRESETS
        return PRESETS.get(palette_label, {}) \
                      .get('rm_cyan_glow_mat', {}) \
                      .get('color', (0.04, 0.75, 1.0))
    except Exception:
        return (0.04, 0.75, 1.0)


def _compute_background_z() -> float:
    """Z = (back del skyline) + 4. Si no hay skyline, usa DEFAULT_BACK_Z."""
    if not MAYA_AVAILABLE:
        return DEFAULT_BACK_Z + BACKGROUND_Z_OFFSET
    back = None
    for node in (mc.ls('rm_skyline_*', type='transform') or []):
        if not mc.objExists(node):
            continue
        try:
            bb = mc.exactWorldBoundingBox(node)
            if back is None or bb[2] < back:
                back = bb[2]
        except Exception:
            pass
    if back is None:
        back = DEFAULT_BACK_Z
    return back + BACKGROUND_Z_OFFSET


def _set_xform(node: str, t=None, r=None, s=None):
    if t is not None:
        for ax, v in zip('XYZ', t):
            try: mc.setAttr(f'{node}.translate{ax}', float(v))
            except Exception: pass
    if r is not None:
        for ax, v in zip('XYZ', r):
            try: mc.setAttr(f'{node}.rotate{ax}', float(v))
            except Exception: pass
    if s is not None:
        for ax, v in zip('XYZ', s):
            try: mc.setAttr(f'{node}.scale{ax}', float(v))
            except Exception: pass


def _set_attr(node: str, attr: str, value):
    try:
        mc.setAttr(f'{node}.{attr}', value)
    except Exception as e:
        print(f'[RetroMecha][Lighting] setAttr {node}.{attr}: {e}')


def _set_color(node: str, attr: str, rgb):
    try:
        mc.setAttr(f'{node}.{attr}', rgb[0], rgb[1], rgb[2], type='double3')
    except Exception as e:
        print(f'[RetroMecha][Lighting] color {node}.{attr}: {e}')


def _tag(xform: str):
    if not mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
        mc.addAttr(xform, longName=_LIGHT_TAG,
                   attributeType='bool', defaultValue=True)
    mc.setAttr(f'{xform}.{_LIGHT_TAG}', True)


def _apply_visibility_defaults(shape: str):
    """Visibility contributions standard: camera/transmission 0, resto 1."""
    _set_attr(shape, 'aiCamera',        0.0)
    _set_attr(shape, 'aiTransmission',  0.0)
    _set_attr(shape, 'aiDiffuse',       1.0)
    _set_attr(shape, 'aiSpecular',      1.0)
    _set_attr(shape, 'aiSss',           1.0)
    _set_attr(shape, 'aiIndirect',      1.0)
    _set_attr(shape, 'aiVolume',        1.0)
    _set_attr(shape, 'aiMaxBounces',    999)


def _apply_area_shadow_defaults(shape: str):
    _set_attr(shape, 'aiSpread',                1.0)
    _set_attr(shape, 'aiSamples',               1)
    _set_attr(shape, 'aiNormalize',             1)
    _set_attr(shape, 'aiCastShadows',           1)
    _set_attr(shape, 'aiShadowDensity',         1.0)
    _set_attr(shape, 'aiCastVolumetricShadows', 1)
    _set_attr(shape, 'aiVolumeSamples',         2)
    _set_attr(shape, 'aiRoundness',             0.0)
    _set_attr(shape, 'aiSoftEdge',              0.0)


# ══════════════════════════════════════════════════════════════════════
#  CREADORES
# ══════════════════════════════════════════════════════════════════════

def _create_area_light(name: str, light_shape_enum: int) -> tuple[str, str]:
    """Crea aiAreaLight con nombre y light shape (0=quad, 1=disk, ...).
    Retorna (transform, shape)."""
    shape = mc.shadingNode('aiAreaLight', asLight=True, name=f'{name}Shape')
    parents = mc.listRelatives(shape, parent=True) or []
    xform = parents[0] if parents else shape
    xform = mc.rename(xform, name)
    shape = mc.listRelatives(xform, shapes=True)[0]
    # Light shape (0=quad, 1=disk, 2=cylinder)
    try:
        mc.setAttr(f'{shape}.aiTranslator', 'quad', type='string')
    except Exception:
        pass
    # Algunos MtoA usan aiLightShape (enum)
    try:
        mc.setAttr(f'{shape}.aiLightShape', light_shape_enum)
    except Exception:
        pass
    return xform, shape


def _create_luz_ambiente(accent_rgb, mult: float, intensity: float | None = None):
    xform, shape = _create_area_light(AMBIENT_NAME, light_shape_enum=0)  # quad
    _set_xform(xform, AMBIENT_TRANSLATE, AMBIENT_ROTATE, AMBIENT_SCALE)
    _set_color(shape, 'color', accent_rgb)
    _set_attr(shape, 'aiIntensity', intensity if intensity is not None else AMBIENT_INTENSITY * mult)
    _set_attr(shape, 'aiExposure',  AMBIENT_EXPOSURE)


def _create_foco_mecha(mult: float, intensity: float | None = None):
    xform, shape = _create_area_light(FOCO_NAME, light_shape_enum=1)  # disk
    _set_xform(xform, FOCO_TRANSLATE, FOCO_ROTATE, FOCO_SCALE)
    _set_color(shape, 'color', FOCO_COLOR)
    _set_attr(shape, 'aiIntensity', intensity if intensity is not None else FOCO_INTENSITY * mult)
    _set_attr(shape, 'aiExposure',  FOCO_EXPOSURE)


def _create_background(bg_z: float, mult: float, intensity: float | None = None):
    xform, shape = _create_area_light(BG_NAME, light_shape_enum=0)  # quad
    _set_xform(xform, (bx, by, bg_z), BG_ROTATE, BG_SCALE)
    _set_color(shape, 'color', BG_COLOR)
    _set_attr(shape, 'aiIntensity', intensity if intensity is not None else BG_INTENSITY * mult)
    _set_attr(shape, 'aiExposure',  BG_EXPOSURE)
    _apply_area_shadow_defaults(shape)
    _apply_visibility_defaults(shape)
    _tag(xform)


def _create_one_meshlight(cube_name: str, tx: float, bg_z: float,
                          accent_rgb, mult: float, intensity: float | None = None):
    """Crea un aiMeshLight a partir de un cubo escalado, simetrico en X."""
    # 1. Cubo base
    cube_result = mc.polyCube(
        name=cube_name,
        width=1.0, height=1.0, depth=1.0,
        subdivisionsX=1, subdivisionsY=1, subdivisionsZ=1,
        axis=(0, 1, 0),
        createUVs=3,           # Normalize
        constructionHistory=False,
    )
    cube_xform = cube_result[0]
    if cube_xform != cube_name:
        cube_xform = mc.rename(cube_xform, cube_name)
    _set_xform(cube_xform, (tx, VEAM_TY, bg_z), (0, 0, 0), VEAM_SCALE)

    cube_shape = mc.listRelatives(cube_xform, shapes=True)[0]

    # 2. aiMeshLight
    light_xform_name = f'{cube_name}{VEAM_LIGHT_SUF}'
    light_shape_name = f'{light_xform_name}Shape'
    light_shape = mc.shadingNode('aiMeshLight', asLight=True, name=light_shape_name)
    parents = mc.listRelatives(light_shape, parent=True) or []
    light_xform = parents[0] if parents else light_shape
    light_xform = mc.rename(light_xform, light_xform_name)
    light_shape = mc.listRelatives(light_xform, shapes=True)[0]

    # 3. Conexion mesh → light
    try:
        mc.connectAttr(f'{cube_shape}.outMesh',
                       f'{light_shape}.inMesh', force=True)
    except Exception as e:
        print(f'[RetroMecha][Lighting] connect mesh→light: {e}')

    # 4. Atributos de la luz (color paleta)
    _set_color(light_shape, 'color', accent_rgb)
    _set_attr(light_shape, 'aiIntensity',           intensity if intensity is not None else VEAM_INTENSITY * mult)
    _set_attr(light_shape, 'aiExposure',            VEAM_EXPOSURE)
    _set_attr(light_shape, 'aiLightVisible',        0)
    _set_attr(light_shape, 'aiSamples',             1)
    _set_attr(light_shape, 'aiNormalize',           1)
    _set_attr(light_shape, 'aiCastShadows',         1)
    _set_attr(light_shape, 'aiShadowDensity',       1.0)
    _set_attr(light_shape, 'aiCastVolumetricShadows', 1)
    _set_attr(light_shape, 'aiVolumeSamples',       2)
    _set_attr(light_shape, 'aiMaxBounces',          999)
    _set_attr(light_shape, 'aiDiffuse',             1.0)
    _set_attr(light_shape, 'aiSpecular',            1.0)
    _set_attr(light_shape, 'aiSss',                 1.0)
    _set_attr(light_shape, 'aiIndirect',            1.0)
    _set_attr(light_shape, 'aiVolume',              1.0)

    # Tag tanto la geometria como la luz
    _tag(cube_xform)
    _tag(light_xform)


def _create_veam_meshlights(accent_rgb, bg_z: float, mult: float, intensity: float | None = None):
    _create_one_meshlight(VEAM_NAME_L, VEAM_TX_L, bg_z, accent_rgb, mult, intensity=intensity)
    _create_one_meshlight(VEAM_NAME_R, VEAM_TX_R, bg_z, accent_rgb, mult, intensity=intensity)


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def apply_lighting(palette_label: str = 'Default', intensity_mult: float | None = None):
    """Crea (o recrea) las 5 luces palette-aware.

    Los sliders individuales (ambient/foco/bg/veam) se toman de
    _LIGHT_INTENSITIES / _VEAM_INTENSITY si fueron seteados.

    Args:
        palette_label:   nombre del preset (Default/Atardecer/Frio/Oxidado/Neon)
        intensity_mult:  multiplicador global (None = mantiene el actual)
    """
    if not MAYA_AVAILABLE:
        return

    remove_lighting()

    if not _has_arnold():
        print('[RetroMecha][Lighting] Arnold no cargado — abortando')
        return

    if intensity_mult is not None:
        _INTENSITY_MULT[0] = float(intensity_mult)
    mult = _INTENSITY_MULT[0]

    accent = _palette_accent_color(palette_label)
    bg_z   = _compute_background_z()

    _create_luz_ambiente(accent, mult, intensity=_LIGHT_INTENSITIES.get(AMBIENT_NAME))
    _create_foco_mecha(mult, intensity=_LIGHT_INTENSITIES.get(FOCO_NAME))
    _create_background(bg_z, mult, intensity=_LIGHT_INTENSITIES.get(BG_NAME))
    _create_veam_meshlights(accent, bg_z, mult, intensity=_VEAM_INTENSITY[0])

    print(
        f'[RetroMecha][Lighting] palette={palette_label} '
        f'accent={tuple(round(v,3) for v in accent)} bg_z={bg_z:.2f} mult={mult}'
    )


def remove_lighting():
    """Elimina TODAS las luces (legacy + nuevas) por tag rmLight + nombres."""
    if not MAYA_AVAILABLE:
        return

    candidates = set()
    for ltype in ('directionalLight', 'aiAreaLight', 'aiMeshLight',
                  'aiSkyDomeLight'):
        for shape in (mc.ls(type=ltype) or []):
            parents = mc.listRelatives(shape, parent=True) or []
            xform = parents[0] if parents else shape
            candidates.add(xform)

    for xform in candidates:
        if not mc.objExists(xform):
            continue
        try:
            if mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
                mc.delete(xform)
        except Exception:
            pass

    # Por nombre — el cubo del mesh light no es light type, hay que buscarlo aparte
    for name in (
        VEAM_NAME_L, VEAM_NAME_R,
        f'{VEAM_NAME_L}{VEAM_LIGHT_SUF}', f'{VEAM_NAME_R}{VEAM_LIGHT_SUF}',
        AMBIENT_NAME, FOCO_NAME, BG_NAME,
        # Legacy
        'rm_key_light', 'rm_fill_light', 'rm_back_light',
        'aiSkyDomeLight1', 'aiSkyDomeLightShape1',
    ):
        if mc.objExists(name):
            try:
                mc.delete(name)
            except Exception:
                pass


def has_rm_lights() -> bool:
    if not MAYA_AVAILABLE:
        return False
    return any(mc.objExists(n) for n in (AMBIENT_NAME, FOCO_NAME, BG_NAME))


def set_lights_intensity(value: float):
    """Multiplicador global de intensidad para todas las luces RetroMecha."""
    if not MAYA_AVAILABLE:
        return
    _INTENSITY_MULT[0] = float(value)
    mult = _INTENSITY_MULT[0]

    for name, base in (
        (AMBIENT_NAME, AMBIENT_INTENSITY),
        (FOCO_NAME,    FOCO_INTENSITY),
        (BG_NAME,      BG_INTENSITY),
    ):
        if not mc.objExists(name):
            continue
        shapes = mc.listRelatives(name, shapes=True) or []
        if shapes:
            try:
                mc.setAttr(f'{shapes[0]}.aiIntensity', base * mult)
            except Exception:
                pass

    for veam_name in (VEAM_NAME_L, VEAM_NAME_R):
        light_xform = f'{veam_name}{VEAM_LIGHT_SUF}'
        if not mc.objExists(light_xform):
            continue
        shapes = mc.listRelatives(light_xform, shapes=True) or []
        if shapes:
            try:
                mc.setAttr(f'{shapes[0]}.aiIntensity', VEAM_INTENSITY * mult)
            except Exception:
                pass


def _set_intensity(name: str, value: float):
    """Actualiza una intensidad individual en memoria + luz en escena si existe."""
    if not MAYA_AVAILABLE:
        return
    _LIGHT_INTENSITIES[name] = float(value)
    if mc.objExists(name):
        shapes = mc.listRelatives(name, shapes=True) or []
        if shapes:
            try:
                mc.setAttr(f'{shapes[0]}.aiIntensity', float(value))
            except Exception:
                pass


def set_ambient_intensity(value: float):
    _set_intensity(AMBIENT_NAME, value)


def set_foco_intensity(value: float):
    _set_intensity(FOCO_NAME, value)


def set_background_intensity(value: float):
    _set_intensity(BG_NAME, value)


def set_veam_intensity(value: float):
    if not MAYA_AVAILABLE:
        return
    _VEAM_INTENSITY[0] = float(value)
    for veam_name in (VEAM_NAME_L, VEAM_NAME_R):
        light_xform = f'{veam_name}{VEAM_LIGHT_SUF}'
        if mc.objExists(light_xform):
            shapes = mc.listRelatives(light_xform, shapes=True) or []
            if shapes:
                try:
                    mc.setAttr(f'{shapes[0]}.aiIntensity', float(value))
                except Exception:
                    pass


def set_palette(palette_label: str):
    """Recolorea luz_ambiente y veam_light_* con el accent de otra paleta."""
    if not MAYA_AVAILABLE:
        return
    accent = _palette_accent_color(palette_label)
    # luz_ambiente
    if mc.objExists(AMBIENT_NAME):
        shapes = mc.listRelatives(AMBIENT_NAME, shapes=True) or []
        if shapes:
            _set_color(shapes[0], 'color', accent)
    # veam_lights
    for veam_name in (VEAM_NAME_L, VEAM_NAME_R):
        light_xform = f'{veam_name}{VEAM_LIGHT_SUF}'
        if mc.objExists(light_xform):
            shapes = mc.listRelatives(light_xform, shapes=True) or []
            if shapes:
                _set_color(shapes[0], 'color', accent)
    print(f'[RetroMecha][Lighting] palette recoloreada → {palette_label}')


def list_rm_lights() -> list:
    """Lista xforms con tag rmLight."""
    if not MAYA_AVAILABLE:
        return []
    result = []
    for ltype in ('aiAreaLight', 'aiMeshLight'):
        for shape in (mc.ls(type=ltype) or []):
            parents = mc.listRelatives(shape, parent=True) or []
            xform = parents[0] if parents else shape
            if mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
                result.append(xform)
    return result
