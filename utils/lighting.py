"""
RetroMecha — utils/lighting.py
Presets de iluminacion procedural para escena mecha.
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
        dict(name='rm_rim_light',  intensity=0.6, color=[0.40, 0.50, 1.00], rot=[ 20,-150, 0]),
    ],
    'retro': [
        dict(name='rm_top_light',  intensity=2.0, color=[1.00, 0.90, 0.70], rot=[-80,   0, 0]),
        dict(name='rm_side_light', intensity=0.7, color=[0.80, 0.40, 1.00], rot=[  0,  90, 0]),
        dict(name='rm_back_light', intensity=0.5, color=[0.40, 0.80, 1.00], rot=[ 20, -90, 0]),
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
#  API PÚBLICA
# ══════════════════════════════════════════════════════════════════════════════

def apply_lighting(preset_name: str = 'studio', sky_dome: bool = False):
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
    """Devuelve True si ya hay un aiSkyDomeLight en la escena."""
    return MAYA_AVAILABLE and (
        mc.objExists(_DOME_XFORM) or mc.objExists(_DOME_SHAPE)
        or bool(mc.ls(type='aiSkyDomeLight'))
    )


# ══════════════════════════════════════════════════════════════════════════════
#  INTERNOS
# ══════════════════════════════════════════════════════════════════════════════

def _create_dir_light(name: str, intensity: float, color: list, rot: list):
    if mc.objExists(name):
        mc.delete(name)

    result = mc.directionalLight(name=name, intensity=intensity, rgb=color)
    # directionalLight puede devolver el transform o el shape según la versión
    if mc.nodeType(result) != 'transform':
        parents = mc.listRelatives(result, parent=True) or []
        xform = parents[0] if parents else result
    else:
        xform = result

    mc.rotate(rot[0], rot[1], rot[2], xform, absolute=True)

    if not mc.attributeQuery(_LIGHT_TAG, node=xform, exists=True):
        mc.addAttr(xform, longName=_LIGHT_TAG, attributeType='bool',
                   defaultValue=True)
    return xform


def _create_sky_dome():
    if not _has_arnold():
        print('[RetroMecha][Lighting] MtoA no disponible — aiSkyDomeLight omitido')
        return None

    _delete_sky_dome()

    try:
        xform = mc.createNode('transform', name=_DOME_XFORM)
        shape = mc.createNode('aiSkyDomeLight', name=_DOME_SHAPE, parent=xform)
        mc.setAttr(f'{shape}.intensity', 0.35)
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
