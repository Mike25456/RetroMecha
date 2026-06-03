"""
RetroMecha — utils/lighting.py
Presets de iluminacion procedural + control granular de intensidad y temperatura.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

_LIGHT_TAG    = 'rmLight'
_DOME_XFORM   = 'aiSkyDomeLight1'
_DOME_SHAPE   = 'aiSkyDomeLightShape1'

PRESETS = {
    'studio': [
        dict(name='rm_key_light',  intensity=1.5, color=[1.00, 0.97, 0.92], rot=[-45,  45, 0]),
        dict(name='rm_fill_light', intensity=0.4, color=[0.70, 0.82, 1.00], rot=[ 30,-120, 0]),
        dict(name='rm_back_light', intensity=0.8, color=[1.00, 0.95, 0.80], rot=[-20, 160, 0]),
    ],
    'dramatic': [
        dict(name='rm_key_light',  intensity=3.0, color=[1.00, 0.85, 0.60], rot=[-60,  30, 0]),
        dict(name='rm_fill_light', intensity=0.5, color=[0.40, 0.50, 1.00], rot=[ 20,-150, 0]),
        dict(name='rm_back_light', intensity=1.2, color=[1.00, 0.70, 0.50], rot=[-10, 180, 0]),
    ],
    'retro': [
        dict(name='rm_key_light',  intensity=2.0, color=[1.00, 0.90, 0.70], rot=[-80,   0, 0]),
        dict(name='rm_fill_light', intensity=0.7, color=[0.80, 0.40, 1.00], rot=[  0,  90, 0]),
        dict(name='rm_back_light', intensity=0.5, color=[0.40, 0.80, 1.00], rot=[ 20, -90, 0]),
    ],
}

DEFAULT_SKYDOME_INTENSITY = 0.35
DEFAULT_TEMPERATURE = 6500   # neutral white (D65)


# ══════════════════════════════════════════════════════════════════════════════
#  API PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def apply_lighting(preset_name: str = 'studio', sky_dome: bool = True):
    """Aplica un preset, eliminando luces anteriores creadas por RetroMecha."""
    if not MAYA_AVAILABLE:
        return

    remove_lighting()

    for cfg in PRESETS.get(preset_name, PRESETS['studio']):
        _create_dir_light(cfg['name'], cfg['intensity'], cfg['color'], cfg['rot'])

    if sky_dome:
        _create_sky_dome()

    msg = f'[RetroMecha][Lighting] "{preset_name}" aplicado'
    print(msg + (' + aiSkyDomeLight' if sky_dome else ''))


def remove_lighting():
    if not MAYA_AVAILABLE:
        return

    for shape in mc.ls(type='directionalLight') or []:
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
            try:
                mc.delete(xform)
            except Exception:
                pass

    _delete_sky_dome()


def sky_dome_exists() -> bool:
    return MAYA_AVAILABLE and (
        mc.objExists(_DOME_XFORM) or mc.objExists(_DOME_SHAPE)
        or bool(mc.ls(type='aiSkyDomeLight'))
    )


def list_rm_lights() -> list:
    """Devuelve los transforms de las luces direccionales taggeadas como rmLight."""
    if not MAYA_AVAILABLE:
        return []
    result = []
    for shape in mc.ls(type='directionalLight') or []:
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
            result.append(xform)
    return result


def set_lights_intensity(value: float):
    """Setea la intensidad de TODAS las luces direccionales rmLight."""
    if not MAYA_AVAILABLE:
        return
    for xform in list_rm_lights():
        shapes = mc.listRelatives(xform, shapes=True, type='directionalLight') or []
        for shape in shapes:
            try:
                mc.setAttr(f'{shape}.intensity', value)
            except Exception:
                pass


def set_skydome_intensity(value: float):
    """Setea la intensidad del aiSkyDomeLight."""
    if not MAYA_AVAILABLE:
        return
    for shape in mc.ls(type='aiSkyDomeLight') or []:
        try:
            mc.setAttr(f'{shape}.intensity', value)
        except Exception:
            pass


def set_lights_temperature(kelvin: float):
    """Aplica una temperatura de color (Kelvin) a las luces direccionales."""
    if not MAYA_AVAILABLE:
        return
    rgb = _kelvin_to_rgb(kelvin)
    for xform in list_rm_lights():
        shapes = mc.listRelatives(xform, shapes=True, type='directionalLight') or []
        for shape in shapes:
            try:
                mc.setAttr(f'{shape}.color', rgb[0], rgb[1], rgb[2], type='double3')
            except Exception:
                pass
            # Si Arnold está cargado, activar useColorTemperature también
            for attr in ('aiUseColorTemperature', 'aiColorTemperature'):
                full = f'{shape}.{attr}'
                if mc.attributeQuery(attr, node=shape, exists=True):
                    try:
                        if attr == 'aiUseColorTemperature':
                            mc.setAttr(full, 1)
                        else:
                            mc.setAttr(full, kelvin)
                    except Exception:
                        pass


def set_skydome_temperature(kelvin: float):
    """Aplica temperatura al aiSkyDomeLight (usa atributo Arnold si existe)."""
    if not MAYA_AVAILABLE:
        return
    rgb = _kelvin_to_rgb(kelvin)
    for shape in mc.ls(type='aiSkyDomeLight') or []:
        try:
            mc.setAttr(f'{shape}.color', rgb[0], rgb[1], rgb[2], type='double3')
        except Exception:
            pass
        for attr in ('aiUseColorTemperature', 'aiColorTemperature'):
            if mc.attributeQuery(attr, node=shape, exists=True):
                try:
                    if attr == 'aiUseColorTemperature':
                        mc.setAttr(f'{shape}.{attr}', 1)
                    else:
                        mc.setAttr(f'{shape}.{attr}', kelvin)
                except Exception:
                    pass


def has_rm_lights() -> bool:
    return MAYA_AVAILABLE and bool(list_rm_lights())


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNOS
# ══════════════════════════════════════════════════════════════════════════════

def _create_dir_light(name: str, intensity: float, color: list, rot: list):
    if mc.objExists(name):
        mc.delete(name)

    result = mc.directionalLight(name=name, intensity=intensity, rgb=color)
    if mc.nodeType(result) != 'transform':
        parents = mc.listRelatives(result, parent=True) or []
        xform = parents[0] if parents else result
    else:
        xform = result

    mc.rotate(rot[0], rot[1], rot[2], xform, absolute=True)

    if not mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
        mc.addAttr(xform, longName=_LIGHT_TAG, attributeType='bool', defaultValue=True)
    return xform


def _create_sky_dome():
    if not _has_arnold():
        print('[RetroMecha][Lighting] MtoA no disponible — aiSkyDomeLight omitido')
        return None

    _delete_sky_dome()

    try:
        xform = mc.createNode('transform', name=_DOME_XFORM)
        shape = mc.createNode('aiSkyDomeLight', name=_DOME_SHAPE, parent=xform)
        mc.setAttr(f'{shape}.intensity', DEFAULT_SKYDOME_INTENSITY)
        mc.setAttr(f'{shape}.color', 0.35, 0.45, 0.65, type='double3')
        print(f'[RetroMecha][Lighting] {_DOME_XFORM} creado')
        return xform
    except Exception as e:
        print(f'[RetroMecha][Lighting] Error creando aiSkyDomeLight: {e}')
        return None


def _delete_sky_dome():
    for existing in mc.ls(type='aiSkyDomeLight') or []:
        parents = mc.listRelatives(existing, parent=True) or []
        target = parents[0] if parents else existing
        try:
            mc.delete(target)
        except Exception:
            pass
    for name in (_DOME_XFORM, _DOME_SHAPE):
        if mc.objExists(name):
            try:
                mc.delete(name)
            except Exception:
                pass


def _has_arnold() -> bool:
    if not MAYA_AVAILABLE:
        return False
    try:
        return 'mtoa' in (mc.pluginInfo(q=True, listPlugins=True) or [])
    except Exception:
        return False


def _kelvin_to_rgb(kelvin: float) -> tuple:
    """
    Aproximación Tanner Helland de blackbody → RGB normalizado [0..1].
    Rango útil: 1000 K – 12000 K.
    """
    import math
    k = max(1000.0, min(40000.0, float(kelvin))) / 100.0

    if k <= 66:
        r = 255.0
        g = 99.4708025861 * math.log(max(k, 1e-6)) - 161.1195681661
    else:
        r = 329.698727446 * ((k - 60) ** -0.1332047592)
        g = 288.1221695283 * ((k - 60) ** -0.0755148492)

    if k >= 66:
        b = 255.0
    elif k <= 19:
        b = 0.0
    else:
        b = 138.5177312231 * math.log(max(k - 10, 1e-6)) - 305.0447927307

    def clamp(v):
        return max(0.0, min(255.0, v)) / 255.0

    return (clamp(r), clamp(g), clamp(b))
