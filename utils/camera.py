"""
RetroMecha - utils/camera.py
Camara default 'rm_camera_compo' replicando el setup hecho en Maya:
  focalLength 24.92 | fStop 11.9 | focusDistance 30 | DOF on
  aperture 1.41732 x 0.94488 | shutter 144 | clip 0.1 - 10000
La camara se posiciona automaticamente para encuadrar al mecha
considerando el lift vertical (+6) aplicado al grupo del personaje.
"""

import math

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

# Nombre y tag de la camara generada por RetroMecha
CAMERA_XFORM = 'rm_camera_compo'
CAMERA_TAG   = 'rmCamera'

# ── Setup replicado desde el historial MEL ─────────────────────────────
FOCAL_LENGTH              = 24.919871
F_STOP                    = 11.903846
FOCUS_DISTANCE            = 30.0
DEPTH_OF_FIELD            = True
HORIZONTAL_FILM_APERTURE  = 1.41732
VERTICAL_FILM_APERTURE    = 0.94488
NEAR_CLIP                 = 0.1
FAR_CLIP                  = 10000.0
SHUTTER_ANGLE             = 144.0
CENTER_OF_INTEREST        = 5.0

# Lift vertical aplicado al mecha en Maya (grupo desplazado +6 en Y)
MECHA_LIFT_Y = 6.0

# Encuadre default del mecha (yaw/pitch para hero shot 3/4)
FRAME_YAW_DEG   = 32.0
FRAME_PITCH_DEG = 8.0


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def create_default_camera(*, frame_mecha=True, look_through=True):
    """Crea (o recrea) la camara compo con la configuracion calibrada.

    - frame_mecha:  posiciona la camara para encuadrar el mecha existente
    - look_through: cambia el panel activo para mirar a traves de la camara
    """
    if not MAYA_AVAILABLE:
        return None

    remove_camera()

    xform, _ = mc.camera(
        centerOfInterest=CENTER_OF_INTEREST,
        focalLength=FOCAL_LENGTH,
        lensSqueezeRatio=1.0,
        cameraScale=1.0,
        horizontalFilmAperture=HORIZONTAL_FILM_APERTURE,
        horizontalFilmOffset=0.0,
        verticalFilmAperture=VERTICAL_FILM_APERTURE,
        verticalFilmOffset=0.0,
        filmFit='fill',
        overscan=1.0,
        motionBlur=False,
        shutterAngle=SHUTTER_ANGLE,
        nearClipPlane=NEAR_CLIP,
        farClipPlane=FAR_CLIP,
        orthographic=False,
        orthographicWidth=30.0,
        panZoomEnabled=False,
        horizontalPan=0.0,
        verticalPan=0.0,
        zoom=1.0,
    )

    xform = mc.rename(xform, CAMERA_XFORM)
    shape = mc.listRelatives(xform, shapes=True)[0]

    # Depth of Field final del setup MEL
    mc.setAttr(f'{shape}.depthOfField', 1 if DEPTH_OF_FIELD else 0)
    mc.setAttr(f'{shape}.fStop', F_STOP)
    mc.setAttr(f'{shape}.focusDistance', FOCUS_DISTANCE)

    # Tag para limpieza posterior
    if not mc.attributeQuery(CAMERA_TAG, node=xform, exists=True):
        mc.addAttr(xform, longName=CAMERA_TAG,
                   attributeType='bool', defaultValue=True)
    mc.setAttr(f'{xform}.{CAMERA_TAG}', True)

    if frame_mecha:
        _frame_on_mecha(xform, shape)

    if look_through:
        _look_through_in_active_panel(xform)

    print(
        f'[RetroMecha][Camera] {CAMERA_XFORM} creada '
        f'(focal={FOCAL_LENGTH:.2f}, fStop={F_STOP:.2f}, '
        f'focus={mc.getAttr(f"{shape}.focusDistance"):.1f}, DOF={DEPTH_OF_FIELD})'
    )
    return xform


def remove_camera():
    """Elimina la camara compo si existe."""
    if not MAYA_AVAILABLE:
        return
    for shape in (mc.ls(type='camera') or []):
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(CAMERA_TAG, node=xform, exists=True):
            try:
                mc.delete(xform)
            except Exception:
                pass
    if mc.objExists(CAMERA_XFORM):
        try:
            mc.delete(CAMERA_XFORM)
        except Exception:
            pass


def has_rm_camera():
    if not MAYA_AVAILABLE:
        return False
    for shape in (mc.ls(type='camera') or []):
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(CAMERA_TAG, node=xform, exists=True):
            return True
    return False


def look_through_camera():
    """Hace que el viewport activo mire a traves de la camara compo."""
    if not MAYA_AVAILABLE or not mc.objExists(CAMERA_XFORM):
        return
    _look_through_in_active_panel(CAMERA_XFORM)


def lift_mecha_default(extra_y=MECHA_LIFT_Y):
    """Desplaza el grupo del mecha hacia arriba (+Y) por la cantidad indicada.
    Replica el ajuste manual hecho en Maya: 'movi el personaje +6 en Y'."""
    if not MAYA_AVAILABLE:
        return False
    try:
        from ui.scene_utils import find_mecha_group
    except Exception:
        return False
    mecha = find_mecha_group()
    if not mecha or not mc.objExists(mecha):
        return False
    try:
        mc.move(0, float(extra_y), 0, mecha,
                relative=True, worldSpace=True)
        print(f'[RetroMecha][Camera] Mecha desplazado +{extra_y} en Y')
        return True
    except Exception as e:
        print(f'[RetroMecha][Camera] Lift error: {e}')
        return False


# ══════════════════════════════════════════════════════════════════════
#  INTERNOS
# ══════════════════════════════════════════════════════════════════════

def _frame_on_mecha(xform, shape):
    """Posiciona la camara a FOCUS_DISTANCE del centro del mecha (3/4)."""
    target = _mecha_center()
    cx, cy, cz = target

    dist  = FOCUS_DISTANCE
    yaw   = math.radians(FRAME_YAW_DEG)
    pitch = math.radians(FRAME_PITCH_DEG)

    cam_x = cx + dist * math.cos(pitch) * math.sin(yaw)
    cam_y = cy + dist * math.sin(pitch)
    cam_z = cz + dist * math.cos(pitch) * math.cos(yaw)

    mc.setAttr(f'{xform}.translateX', cam_x)
    mc.setAttr(f'{xform}.translateY', cam_y)
    mc.setAttr(f'{xform}.translateZ', cam_z)

    _aim_at(xform, target)

    # Reajustar focusDistance al real (mantiene la sensacion DOF del setup)
    actual = math.sqrt(
        (cam_x - cx) ** 2 + (cam_y - cy) ** 2 + (cam_z - cz) ** 2
    )
    mc.setAttr(f'{shape}.focusDistance', actual)


def _mecha_center():
    """Centro del bbox del mecha; si no hay mecha usa (0, MECHA_LIFT_Y, 0)."""
    try:
        from ui.scene_utils import find_mecha_group
        mecha = find_mecha_group()
        if mecha and mc.objExists(mecha):
            bb = mc.exactWorldBoundingBox(mecha)
            return (
                (bb[0] + bb[3]) * 0.5,
                (bb[1] + bb[4]) * 0.5,
                (bb[2] + bb[5]) * 0.5,
            )
    except Exception:
        pass
    return (0.0, MECHA_LIFT_Y, 0.0)


def _aim_at(xform, target):
    """Orienta xform hacia target usando un aimConstraint temporal."""
    loc = mc.spaceLocator(name='_rm_cam_aim_tmp', position=target)[0]
    try:
        cons = mc.aimConstraint(
            loc, xform,
            aimVector=(0, 0, -1),
            upVector=(0, 1, 0),
            worldUpType='vector',
            worldUpVector=(0, 1, 0),
        )
        if cons:
            mc.delete(cons)
    finally:
        if mc.objExists(loc):
            mc.delete(loc)


def _look_through_in_active_panel(xform):
    """Pone la camara en el modelPanel con foco; si no hay foco, el primero."""
    panel = None
    try:
        focused = mc.getPanel(withFocus=True)
        if focused and mc.getPanel(typeOf=focused) == 'modelPanel':
            panel = focused
    except Exception:
        pass
    if not panel:
        panels = mc.getPanel(type='modelPanel') or []
        panel = panels[0] if panels else None
    if not panel:
        return
    try:
        mc.lookThru(panel, xform)
    except Exception as e:
        print(f'[RetroMecha][Camera] lookThru: {e}')
