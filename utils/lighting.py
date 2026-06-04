"""
RetroMecha - utils/lighting.py  v5
Iluminacion con 5 luces aiArea/aiMesh palette-aware:

  luz_ambiente            - aiAreaLight quad  → color de rm_terrain_accent_mat
  foco_mecha              - aiAreaLight disk  → BLANCA
  background              - aiAreaLight quad  → BLANCA
  veam_light_izquierdo    - aiMeshLight cubo  → color de rm_cyan_glow_mat
  veam_light_derecho      - aiMeshLight cubo  → simetrico en X, mismo color

Cada luz tiene su intensidad propia (slider individual en el panel Pro).
Floor minimo INTENSITY_MIN = 4 en todas las intensidades.

luz_ambiente toma el color del accent del TERRENO (rm_terrain_accent_mat.color)
para integrarse con el suelo. Los veam_lights toman el color del glow del
MECHA (rm_cyan_glow_mat.color) para acompañar al sujeto. Así se ve la
naturaleza de la paleta aplicada tanto al mecha como al terreno.

background y foco_mecha quedan SIEMPRE blancos por especificacion.

background y los 2 veam_lights se posicionan a (skyline_back_z + 4) en Z
→ 4 unidades delante de los elementos de fondo (rm_skyline_*).

veam_lights llevan el aiMeshLight parenteado bajo el cubo → icono visual
de la luz queda pegado a la geometria real.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

_LIGHT_TAG = 'rmLight'

# ── Z offset respecto al fondo ───────────────────────────────────────
BACKGROUND_Z_OFFSET = 4.0
DEFAULT_BACK_Z      = -55.0

# ── Intensidad minima global ─────────────────────────────────────────
INTENSITY_MIN = 4.0
INTENSITY_MAX = 20.0   # tope sugerido para sliders

# ── luz_ambiente (aiAreaLight quad — color terrain_accent) ───────────
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
BG_TRANS_XY  = (0.0, 0.0)
BG_ROTATE    = (90.0, 0.0, 0.0)
BG_SCALE     = (81.476, 1.007, 43.871)
BG_INTENSITY = 10.000
BG_EXPOSURE  = 6.591
BG_COLOR     = (1.0, 1.0, 1.0)

# ── veam_light_* (aiMeshLight cubo simetrico — color cyan_glow) ──────
VEAM_NAME_L    = 'veam_light_izquierdo'
VEAM_NAME_R    = 'veam_light_derecho'
VEAM_LIGHT_SUF = '_light'
VEAM_TX_L      = -20.564
VEAM_TX_R      = +20.564
VEAM_TY        = 8.144
VEAM_SCALE     = (1.0, 387.639, 1.0)
VEAM_INTENSITY = 5.449
VEAM_EXPOSURE  = 8.524

# ── Specs factory (loop simétrico izq/der) ───────────────────────────
VEAM_SPECS = [
    {'name': VEAM_NAME_L, 'tx': VEAM_TX_L},
    {'name': VEAM_NAME_R, 'tx': VEAM_TX_R},
]

# ── Estado: intensidad por luz (clampada a >= INTENSITY_MIN) ─────────
_AMBIENT_I = [AMBIENT_INTENSITY]
_FOCO_I    = [FOCO_INTENSITY]
_BG_I      = [BG_INTENSITY]
_VEAM_I    = [VEAM_INTENSITY]


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


def _clamp_intensity(v) -> float:
    return max(INTENSITY_MIN, float(v))


def _palette_mecha_color(palette_label: str = 'Default'):
    """Color del glow accent del mecha (rm_cyan_glow_mat.color)."""
    try:
        from materials.presets import PRESETS
        preset_key = _resolve_preset_key(palette_label, PRESETS)
        if preset_key:
            return PRESETS.get(preset_key, {}) \
                          .get('rm_cyan_glow_mat', {}) \
                          .get('color', (0.04, 0.75, 1.0))
    except Exception:
        pass

    toon_col, _ = _toon_palette_colors(palette_label)
    if toon_col:
        return toon_col
    return (0.04, 0.75, 1.0)


def _palette_terrain_color(palette_label: str = 'Default'):
    """Color del accent del terreno (rm_terrain_accent_mat.color)."""
    try:
        from materials.presets import PRESETS
        preset_key = _resolve_preset_key(palette_label, PRESETS)
        if preset_key:
            return PRESETS.get(preset_key, {}) \
                          .get('rm_terrain_accent_mat', {}) \
                          .get('color', (0.42, 0.36, 0.28))
    except Exception:
        pass

    _, toon_col = _toon_palette_colors(palette_label)
    if toon_col:
        return toon_col
    return (0.42, 0.36, 0.28)


def _compute_background_z() -> float:
    """Z delante de skyline + monumento. Si no hay, usa DEFAULT_BACK_Z."""
    if not MAYA_AVAILABLE:
        return DEFAULT_BACK_Z + BACKGROUND_Z_OFFSET
    front = None
    for node in (mc.ls('rm_skyline_*', type='transform') or []) + \
                (mc.ls('rm_monument_*', type='transform') or []):
        if not mc.objExists(node):
            continue
        try:
            bb = mc.exactWorldBoundingBox(node)
            if front is None or bb[5] > front:
                front = bb[5]
        except Exception:
            pass
    if front is None:
        front = DEFAULT_BACK_Z
    return front + BACKGROUND_Z_OFFSET


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


def _resolve_preset_key(label: str, presets: dict) -> str | None:
    if not label:
        return None
    if label in presets:
        return label
    label_l = label.lower()
    for k in presets:
        if k.lower() == label_l:
            return k
    return None


def _ramp_mid_color(ramp):
    if not ramp:
        return None
    try:
        best = min(ramp, key=lambda item: abs(float(item[0]) - 0.5))
        rgb = best[1]
        return (float(rgb[0]), float(rgb[1]), float(rgb[2]))
    except Exception:
        return None


def _toon_palette_colors(palette_key: str):
    """Colores aproximados para paletas aiToon (quick mode)."""
    try:
        from utils.material_assigner import _load_palette
        palette = _load_palette(palette_key)
        if not palette:
            return None, None
        mecha_col = palette.get('GLOW')
        if mecha_col and len(mecha_col) >= 3:
            mecha_col = (float(mecha_col[0]), float(mecha_col[1]), float(mecha_col[2]))
        terrain_ramp = palette.get('DETAIL') or palette.get('ARMOR') or palette.get('JOINT')
        terrain_col = _ramp_mid_color(terrain_ramp)
        return mecha_col, terrain_col
    except Exception:
        return None, None


def _set_light_attr(shape: str, candidates: tuple[str, ...], value) -> bool:
    for attr in candidates:
        try:
            if mc.attributeQuery(attr, node=shape, exists=True):
                _set_attr(shape, attr, value)
                return True
        except Exception:
            pass
    print(f'[RetroMecha][Lighting] attr faltante en {shape}: {candidates}')
    return False


def _set_light_intensity(shape: str, value):
    return _set_light_attr(shape, ('aiIntensity', 'intensity'), value)


def _set_light_exposure(shape: str, value):
    return _set_light_attr(shape, ('aiExposure', 'exposure'), value)


def _tag(xform: str):
    if not mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
        mc.addAttr(xform, longName=_LIGHT_TAG,
                   attributeType='bool', defaultValue=True)
    mc.setAttr(f'{xform}.{_LIGHT_TAG}', True)


def _apply_visibility_defaults(shape: str):
    _set_attr(shape, 'aiCamera',        0.0)
    _set_attr(shape, 'aiTransmission',  0.0)
    _set_attr(shape, 'aiDiffuse',       1.0)
    _set_attr(shape, 'aiSpecular',      1.0)
    _set_attr(shape, 'aiSss',           1.0)
    _set_attr(shape, 'aiIndirect',      1.0)
    _set_attr(shape, 'aiVolume',        1.0)
    _set_attr(shape, 'aiMaxBounces',    999)


def _apply_area_shadow_defaults(shape: str):
    _set_light_attr(shape, ('aiSpread', 'spread'), 1.0)
    _set_light_attr(shape, ('aiSamples', 'samples'), 1)
    _set_light_attr(shape, ('aiNormalize', 'normalize'), 1)
    _set_light_attr(shape, ('aiCastShadows', 'castShadows'), 1)
    _set_light_attr(shape, ('aiShadowDensity', 'shadowDensity'), 1.0)
    _set_light_attr(shape, ('aiCastVolumetricShadows', 'castVolumetricShadows'), 1)
    _set_light_attr(shape, ('aiVolumeSamples', 'volumeSamples'), 2)
    _set_light_attr(shape, ('aiRoundness', 'roundness'), 0.0)
    _set_light_attr(shape, ('aiSoftEdge', 'softEdge'), 0.0)


def _apply_mesh_visibility(mesh_shape: str):
    _set_attr(mesh_shape, 'primaryVisibility', 0)
    _set_attr(mesh_shape, 'castsShadows', 0)
    _set_attr(mesh_shape, 'receiveShadows', 0)
    _set_attr(mesh_shape, 'visibleInReflections', 0)
    _set_attr(mesh_shape, 'visibleInRefractions', 0)
    _set_attr(mesh_shape, 'overrideEnabled', 1)
    _set_attr(mesh_shape, 'overrideDisplayType', 2)  # template (wire)
    _set_attr(mesh_shape, 'overrideShading', 0)


def _create_meshlight_with_mtoa(cube_xform: str, cube_shape: str, light_xform_name: str):
    """Intenta crear aiMeshLight usando mtoa.utils (si está disponible)."""
    if not _has_arnold():
        return None, None
    try:
        import mtoa.utils as mutils
    except Exception:
        return None, None

    prev_sel = mc.ls(selection=True) or []
    light_shape = None
    light_xform = None
    try:
        mc.select(cube_xform, replace=True)
        mutils.createMeshLight()
        lights = mc.listConnections(f'{cube_shape}.worldMesh[0]', type='aiMeshLight') or []
        if lights:
            light_shape = lights[-1]
            parents = mc.listRelatives(light_shape, parent=True) or []
            light_xform = parents[0] if parents else light_shape
            light_xform = mc.rename(light_xform, light_xform_name)
            light_shape = mc.listRelatives(light_xform, shapes=True)[0]
    except Exception as e:
        print(f'[RetroMecha][Lighting] mtoa meshLight: {e}')
    finally:
        try:
            if prev_sel:
                mc.select(prev_sel, replace=True)
            else:
                mc.select(clear=True)
        except Exception:
            pass
    return light_xform, light_shape


def _shape_of(xform: str, type_filter: str | None = None):
    """Primer shape del transform, opcionalmente filtrado por tipo."""
    if not mc.objExists(xform):
        return None
    if type_filter:
        shapes = mc.listRelatives(xform, shapes=True, type=type_filter) or []
    else:
        shapes = mc.listRelatives(xform, shapes=True) or []
    return shapes[0] if shapes else None


# ══════════════════════════════════════════════════════════════════════
#  CREADORES
# ══════════════════════════════════════════════════════════════════════

_LIGHT_SHAPE_NAME = {0: 'quad', 1: 'disk', 2: 'cylinder'}


def _create_area_light(name: str, light_shape_enum: int) -> tuple[str, str]:
    shape = mc.shadingNode('aiAreaLight', asLight=True, name=f'{name}Shape')
    parents = mc.listRelatives(shape, parent=True) or []
    xform = parents[0] if parents else shape
    xform = mc.rename(xform, name)
    shape = mc.listRelatives(xform, shapes=True)[0]

    shape_str = _LIGHT_SHAPE_NAME.get(light_shape_enum, 'quad')
    try:
        mc.setAttr(f'{shape}.aiTranslator', shape_str, type='string')
    except Exception:
        pass
    try:
        mc.setAttr(f'{shape}.aiLightShape', light_shape_enum)
    except Exception:
        pass
    return xform, shape


def _create_luz_ambiente(terrain_color):
    xform, shape = _create_area_light(AMBIENT_NAME, light_shape_enum=0)  # quad
    _set_xform(xform, AMBIENT_TRANSLATE, AMBIENT_ROTATE, AMBIENT_SCALE)
    _set_color(shape, 'color', terrain_color)
    _set_light_intensity(shape, _clamp_intensity(_AMBIENT_I[0]))
    _set_light_exposure(shape,  AMBIENT_EXPOSURE)
    _apply_area_shadow_defaults(shape)
    _apply_visibility_defaults(shape)
    _tag(xform)


def _create_foco_mecha():
    xform, shape = _create_area_light(FOCO_NAME, light_shape_enum=1)  # disk
    _set_xform(xform, FOCO_TRANSLATE, FOCO_ROTATE, FOCO_SCALE)
    _set_color(shape, 'color', FOCO_COLOR)
    _set_light_intensity(shape, _clamp_intensity(_FOCO_I[0]))
    _set_light_exposure(shape,  FOCO_EXPOSURE)
    _apply_area_shadow_defaults(shape)
    _apply_visibility_defaults(shape)
    _tag(xform)


def _create_background(bg_z: float):
    xform, shape = _create_area_light(BG_NAME, light_shape_enum=0)  # quad
    bx, by = BG_TRANS_XY
    _set_xform(xform, (bx, by, bg_z), BG_ROTATE, BG_SCALE)
    _set_color(shape, 'color', BG_COLOR)
    _set_light_intensity(shape, _clamp_intensity(_BG_I[0]))
    _set_light_exposure(shape,  BG_EXPOSURE)
    _apply_area_shadow_defaults(shape)
    _apply_visibility_defaults(shape)
    _tag(xform)


def _create_one_meshlight(spec: dict, bg_z: float,
                          mecha_color, use_mtoa: bool = True):
    """Crea un aiMeshLight desde un cubo escalado. Parenteo el light bajo el cubo.

    spec = {'name': 'veam_light_izquierdo', 'tx': -20.564}
    """
    cube_name = spec['name']
    tx = spec['tx']

    # Purga cualquier nodo previo con estos nombres (intento previo fallido)
    for orphan in (cube_name,
                   f'{cube_name}{VEAM_LIGHT_SUF}',
                   f'{cube_name}{VEAM_LIGHT_SUF}Shape',
                   f'{cube_name}Shape'):
        if mc.objExists(orphan):
            try:
                mc.delete(orphan)
            except Exception:
                pass

    cube_result = mc.polyCube(
        name=cube_name,
        width=1.0, height=1.0, depth=1.0,
        subdivisionsX=1, subdivisionsY=1, subdivisionsZ=1,
        axis=(0, 1, 0),
        createUVs=3,
        constructionHistory=False,
    )
    cube_xform = cube_result[0]
    if cube_xform != cube_name:
        cube_xform = mc.rename(cube_xform, cube_name)
    _set_xform(cube_xform, (tx, VEAM_TY, bg_z), (0, 0, 0), VEAM_SCALE)

    cube_shape = mc.listRelatives(cube_xform, shapes=True)[0]
    _apply_mesh_visibility(cube_shape)

    light_xform_name = f'{cube_name}{VEAM_LIGHT_SUF}'
    light_xform = None
    light_shape = None
    if use_mtoa:
        light_xform, light_shape = _create_meshlight_with_mtoa(
            cube_xform, cube_shape, light_xform_name
        )
    if not light_shape:
        light_shape_name = f'{light_xform_name}Shape'
        light_shape = mc.shadingNode('aiMeshLight', asLight=True, name=light_shape_name)
        parents = mc.listRelatives(light_shape, parent=True) or []
        light_xform = parents[0] if parents else light_shape
        light_xform = mc.rename(light_xform, light_xform_name)
        light_shape = mc.listRelatives(light_xform, shapes=True)[0]

    try:
        mc.connectAttr(f'{cube_shape}.worldMesh[0]',
                       f'{light_shape}.inMesh', force=True)
    except Exception as e:
        print(f'[RetroMecha][Lighting] connect mesh→light: {e}')

    # Parentear bajo el cubo (relative=True para mantener local identidad)
    try:
        mc.parent(light_xform, cube_xform, relative=True)
    except Exception as e:
        print(f'[RetroMecha][Lighting] parent light→cube: {e}')

    _set_color(light_shape, 'color', mecha_color)
    _set_light_intensity(light_shape, _clamp_intensity(_VEAM_I[0]))
    _set_light_exposure(light_shape,  VEAM_EXPOSURE)
    _set_light_attr(light_shape, ('aiLightVisible', 'lightVisible'), 0)
    _set_light_attr(light_shape, ('aiSamples', 'samples'), 1)
    _set_light_attr(light_shape, ('aiNormalize', 'normalize'), 1)
    _set_light_attr(light_shape, ('aiCastShadows', 'castShadows'), 1)
    _set_light_attr(light_shape, ('aiShadowDensity', 'shadowDensity'), 1.0)
    _set_light_attr(light_shape, ('aiCastVolumetricShadows', 'castVolumetricShadows'), 1)
    _set_light_attr(light_shape, ('aiVolumeSamples', 'volumeSamples'), 2)
    _set_light_attr(light_shape, ('aiMaxBounces', 'maxBounces'), 999)
    _set_light_attr(light_shape, ('aiDiffuse', 'diffuse'), 1.0)
    _set_light_attr(light_shape, ('aiSpecular', 'specular'), 1.0)
    _set_light_attr(light_shape, ('aiSss', 'sss'), 1.0)
    _set_light_attr(light_shape, ('aiIndirect', 'indirect'), 1.0)
    _set_light_attr(light_shape, ('aiVolume', 'volume'), 1.0)

    _tag(cube_xform)
    _tag(light_xform)
    return cube_xform, light_xform


def _create_veam_meshlights(mecha_color, bg_z: float):
    for spec in VEAM_SPECS:
        _create_one_meshlight(spec, bg_z, mecha_color)

    ok = sum(
        1 for s in VEAM_SPECS
        if mc.objExists(s['name'])
        and mc.objExists(f"{s['name']}{VEAM_LIGHT_SUF}")
    )
    print(f'[RetroMecha][Lighting] veam_lights: {ok}/{len(VEAM_SPECS)} OK')


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def apply_lighting(palette_label: str = 'Default'):
    """Crea (o recrea) las 5 luces palette-aware con las intensidades stored."""
    if not MAYA_AVAILABLE:
        return

    remove_lighting()

    if not _has_arnold():
        print('[RetroMecha][Lighting] Arnold no cargado — abortando')
        return

    mecha_col   = _palette_mecha_color(palette_label)
    terrain_col = _palette_terrain_color(palette_label)
    bg_z        = _compute_background_z()

    _create_luz_ambiente(terrain_col)
    _create_foco_mecha()
    _create_background(bg_z)
    _create_veam_meshlights(mecha_col, bg_z)

    print(
        f'[RetroMecha][Lighting] palette={palette_label} '
        f'terrain={tuple(round(v,3) for v in terrain_col)} '
        f'mecha={tuple(round(v,3) for v in mecha_col)} '
        f'bg_z={bg_z:.2f} | '
        f'I(amb={_AMBIENT_I[0]:.1f} foco={_FOCO_I[0]:.1f} '
        f'bg={_BG_I[0]:.1f} veam={_VEAM_I[0]:.1f})'
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


# ── Setters individuales (clampados a INTENSITY_MIN) ────────────────

def set_ambient_intensity(value: float):
    _AMBIENT_I[0] = _clamp_intensity(value)
    shape = _shape_of(AMBIENT_NAME, type_filter='aiAreaLight')
    if shape:
        _set_light_intensity(shape, _AMBIENT_I[0])


def set_foco_intensity(value: float):
    _FOCO_I[0] = _clamp_intensity(value)
    shape = _shape_of(FOCO_NAME, type_filter='aiAreaLight')
    if shape:
        _set_light_intensity(shape, _FOCO_I[0])


def set_background_intensity(value: float):
    _BG_I[0] = _clamp_intensity(value)
    shape = _shape_of(BG_NAME, type_filter='aiAreaLight')
    if shape:
        _set_light_intensity(shape, _BG_I[0])


def set_veam_intensity(value: float):
    _VEAM_I[0] = _clamp_intensity(value)
    for veam_name in (VEAM_NAME_L, VEAM_NAME_R):
        light_xform = f'{veam_name}{VEAM_LIGHT_SUF}'
        shape = _shape_of(light_xform, type_filter='aiMeshLight')
        if shape:
            _set_light_intensity(shape, _VEAM_I[0])


def get_intensities() -> dict:
    """Retorna las intensidades actuales por luz (clampadas)."""
    return {
        'ambient':    _AMBIENT_I[0],
        'foco':       _FOCO_I[0],
        'background': _BG_I[0],
        'veam':       _VEAM_I[0],
    }


def set_palette(palette_label: str):
    """Recolorea luz_ambiente (terrain) y veam_lights (mecha) con otra paleta."""
    if not MAYA_AVAILABLE:
        return
    terrain_col = _palette_terrain_color(palette_label)
    mecha_col   = _palette_mecha_color(palette_label)

    # luz_ambiente → terrain accent
    shape = _shape_of(AMBIENT_NAME, type_filter='aiAreaLight')
    if shape:
        _set_color(shape, 'color', terrain_col)

    # veam_lights → mecha cyan_glow accent
    for veam_name in (VEAM_NAME_L, VEAM_NAME_R):
        light_xform = f'{veam_name}{VEAM_LIGHT_SUF}'
        shape = _shape_of(light_xform, type_filter='aiMeshLight')
        if shape:
            _set_color(shape, 'color', mecha_col)

    print(
        f'[RetroMecha][Lighting] palette recoloreada → {palette_label} '
        f'terrain={tuple(round(v,3) for v in terrain_col)} '
        f'mecha={tuple(round(v,3) for v in mecha_col)}'
    )


def list_rm_lights() -> list:
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
