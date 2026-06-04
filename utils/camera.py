"""
RetroMecha - utils/camera.py
Camara default 'Camara_for_render' con la configuracion final del usuario:

  Transform:
    translate (0.0, 0.62, 20.715)
    rotate    (6.6, 3.6, 0)
  Shape:
    horizontalFilmAperture 1.417
    verticalFilmAperture   0.945
    focalLength            21.387
    fStop                  5.6
    nearClip 0.1 / farClip 10000
    DOF on

Esta camara reemplaza a la antigua 'rm_camera_compo'. Es la que usa
el boton Render del panel Rendering (resolucion 1920x1080).
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

# Nombre y tag de la camara generada por RetroMecha
CAMERA_XFORM = 'Camara_for_render'
CAMERA_TAG   = 'rmCamera'

# ── Setup final (valores exactos del setup del usuario) ─────────────
FOCAL_LENGTH              = 21.387
F_STOP                    = 5.6
FOCUS_DISTANCE            = 30.0
DEPTH_OF_FIELD            = True
HORIZONTAL_FILM_APERTURE  = 1.417
VERTICAL_FILM_APERTURE    = 0.945
NEAR_CLIP                 = 0.1
FAR_CLIP                  = 10000.0
SHUTTER_ANGLE             = 144.0
CENTER_OF_INTEREST        = 5.0

# Posicion y rotacion fijas (del Channel Box del usuario)
CAM_TRANSLATE = (0.0, 0.62, 20.715)
CAM_ROTATE    = (6.6, 3.6, 0.0)

# Lift vertical aplicado al mecha (replica el ajuste manual en Maya)
MECHA_LIFT_Y = 6.0


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def create_default_camera(*, look_through=True, frame_mecha=False):
    """Crea (o recrea) Camara_for_render con la config final.

    - look_through: cambia el panel activo para mirar a traves de la camara.
    - frame_mecha:  False por defecto (posicion fija del usuario);
                    si True, sobreescribe con un encuadre automatico al mecha.
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

    # Asegurar atributos reales de la camara
    _apply_camera_shape_settings(xform, shape)

    # Tag para limpieza
    if not mc.attributeQuery(CAMERA_TAG, node=xform, exists=True):
        mc.addAttr(xform, longName=CAMERA_TAG,
                   attributeType='bool', defaultValue=True)
    mc.setAttr(f'{xform}.{CAMERA_TAG}', True)

    # Posicion / rotacion fijas
    _apply_fixed_transform(xform)

    if frame_mecha:
        _frame_on_mecha(xform, shape)

    # Forzar X = 0 siempre (incluso si frame_mecha lo desplazo)
    try:
        mc.setAttr(f'{xform}.translateX', 0.0)
    except Exception:
        pass

    if look_through:
        _look_through_in_active_panel(xform)

    # Lock de transforms — la camara no debe moverse accidentalmente
    lock_camera(True)

    print(
        f'[RetroMecha][Camera] {CAMERA_XFORM} '
        f'(focal={FOCAL_LENGTH:.3f}, fStop={F_STOP:.2f}, '
        f'pos=(0.0, {CAM_TRANSLATE[1]}, {CAM_TRANSLATE[2]}), '
        f'rot={CAM_ROTATE}, LOCKED)'
    )
    return xform


def remove_camera():
    """Elimina la camara RetroMecha si existe (por tag o por nombre).
    Desbloquea los transforms primero por si estaba locked."""
    if not MAYA_AVAILABLE:
        return
    # Unlock primero para que delete no falle con attrs locked
    lock_camera(False)
    for shape in (mc.ls(type='camera') or []):
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(CAMERA_TAG, node=xform, exists=True):
            try:
                mc.delete(xform)
            except Exception:
                pass
    for name in (CAMERA_XFORM, 'Camera_for_render', 'rm_camera_compo'):  # incluye nombre legacy
        if mc.objExists(name):
            try:
                mc.delete(name)
            except Exception:
                pass


def has_rm_camera() -> bool:
    if not MAYA_AVAILABLE:
        return False
    for shape in (mc.ls(type='camera') or []):
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(CAMERA_TAG, node=xform, exists=True):
            return True
    return False


def look_through_camera():
    """Hace que el viewport activo mire a traves de Camara_for_render."""
    if not MAYA_AVAILABLE or not mc.objExists(CAMERA_XFORM):
        return
    _look_through_in_active_panel(CAMERA_XFORM)


def lock_camera(lock: bool = True) -> bool:
    """Bloquea/desbloquea los canales de transform de Camara_for_render."""
    if not MAYA_AVAILABLE or not mc.objExists(CAMERA_XFORM):
        return False
    for attr in (
        'translateX', 'translateY', 'translateZ',
        'rotateX', 'rotateY', 'rotateZ',
        'scaleX', 'scaleY', 'scaleZ',
    ):
        try:
            mc.setAttr(f'{CAMERA_XFORM}.{attr}', lock=lock)
        except Exception:
            pass
    return True


def lift_mecha_default(extra_y: float = MECHA_LIFT_Y) -> bool:
    """Desplaza el grupo del mecha hacia arriba (+Y) replicando el ajuste manual."""
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

def _apply_fixed_transform(xform: str):
    """Aplica las posicion/rotacion fijas del setup del usuario."""
    try:
        mc.setAttr(f'{xform}.translateX', CAM_TRANSLATE[0])
        mc.setAttr(f'{xform}.translateY', CAM_TRANSLATE[1])
        mc.setAttr(f'{xform}.translateZ', CAM_TRANSLATE[2])
        mc.setAttr(f'{xform}.rotateX',    CAM_ROTATE[0])
        mc.setAttr(f'{xform}.rotateY',    CAM_ROTATE[1])
        mc.setAttr(f'{xform}.rotateZ',    CAM_ROTATE[2])
    except Exception as e:
        print(f'[RetroMecha][Camera] Transform error: {e}')


def _apply_camera_shape_settings(xform: str, shape: str):
    try:
        mc.setAttr(f'{xform}.centerOfInterest', CENTER_OF_INTEREST)
    except Exception:
        pass

    for attr, value in (
        ('focalLength', FOCAL_LENGTH),
        ('lensSqueezeRatio', 1.0),
        ('cameraScale', 1.0),
        ('horizontalFilmAperture', HORIZONTAL_FILM_APERTURE),
        ('horizontalFilmOffset', 0.0),
        ('verticalFilmAperture', VERTICAL_FILM_APERTURE),
        ('verticalFilmOffset', 0.0),
        ('overscan', 1.0),
        ('nearClipPlane', NEAR_CLIP),
        ('farClipPlane', FAR_CLIP),
        ('shutterAngle', SHUTTER_ANGLE),
        ('panZoomEnabled', 0),
        ('horizontalPan', 0.0),
        ('verticalPan', 0.0),
        ('zoom', 1.0),
        ('depthOfField', 1 if DEPTH_OF_FIELD else 0),
        ('fStop', F_STOP),
        ('focusDistance', FOCUS_DISTANCE),
    ):
        try:
            mc.setAttr(f'{shape}.{attr}', value)
        except Exception as e:
            print(f'[RetroMecha][Camera] Attr {attr}: {e}')


def _frame_on_mecha(xform: str, shape: str):
    """Opcional: sobreescribe la posicion fija con un encuadre auto al mecha."""
    import math
    try:
        from ui.scene_utils import find_mecha_group
        mecha = find_mecha_group()
        if mecha and mc.objExists(mecha):
            bb = mc.exactWorldBoundingBox(mecha)
            cx = (bb[0] + bb[3]) * 0.5
            cy = (bb[1] + bb[4]) * 0.5
            cz = (bb[2] + bb[5]) * 0.5
        else:
            cx, cy, cz = 0.0, MECHA_LIFT_Y, 0.0
    except Exception:
        cx, cy, cz = 0.0, MECHA_LIFT_Y, 0.0

    dist  = FOCUS_DISTANCE
    yaw   = math.radians(32.0)
    pitch = math.radians(8.0)
    cam_x = cx + dist * math.cos(pitch) * math.sin(yaw)
    cam_y = cy + dist * math.sin(pitch)
    cam_z = cz + dist * math.cos(pitch) * math.cos(yaw)

    mc.setAttr(f'{xform}.translateX', cam_x)
    mc.setAttr(f'{xform}.translateY', cam_y)
    mc.setAttr(f'{xform}.translateZ', cam_z)

    _aim_at(xform, (cx, cy, cz))
    actual = math.sqrt(
        (cam_x - cx) ** 2 + (cam_y - cy) ** 2 + (cam_z - cz) ** 2
    )
    mc.setAttr(f'{shape}.focusDistance', actual)


def _aim_at(xform: str, target):
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


def _look_through_in_active_panel(xform: str):
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
