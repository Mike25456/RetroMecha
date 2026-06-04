"""
RetroMecha - utils/render.py
Trigger de render Arnold a 1920x1080 desde Camara_for_render.
"""

try:
    import maya.cmds as mc
    import maya.mel as mel
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

RENDER_WIDTH  = 1920
RENDER_HEIGHT = 1080


def _has_arnold() -> bool:
    try:
        from utils.maya_materials import has_arnold
        return has_arnold()
    except Exception:
        return False


def set_render_settings():
    """Configura Arnold como renderer + resolucion 1920x1080.
    Marca Camara_for_render como UNICA camara renderable.
    """
    if not MAYA_AVAILABLE:
        return False

    # Arnold como renderer activo
    try:
        mc.setAttr('defaultRenderGlobals.currentRenderer',
                   'arnold', type='string')
    except Exception as e:
        print(f'[RetroMecha][Render] currentRenderer: {e}')

    # Resolucion 1920x1080
    try:
        mc.setAttr('defaultResolution.width',  RENDER_WIDTH)
        mc.setAttr('defaultResolution.height', RENDER_HEIGHT)
        mc.setAttr('defaultResolution.deviceAspectRatio',
                   float(RENDER_WIDTH) / float(RENDER_HEIGHT))
        mc.setAttr('defaultResolution.pixelAspect', 1.0)
        mc.setAttr('defaultResolution.aspectLock', False)
    except Exception as e:
        print(f'[RetroMecha][Render] resolution: {e}')

    # Camara_for_render como unica renderable
    from utils.camera import CAMERA_XFORM
    cam_shape = _camera_shape(CAMERA_XFORM)
    if not cam_shape:
        return False
    try:
        for c in (mc.ls(type='camera') or []):
            try:
                mc.setAttr(f'{c}.renderable', c == cam_shape)
            except Exception:
                pass
    except Exception as e:
        print(f'[RetroMecha][Render] renderable: {e}')
    return True


def render_now() -> bool:
    """Configura el render y lanza la Render View con Camara_for_render.

    Antes de renderizar, asegura que el setup completo este sincronizado
    con la paleta activa: sky + sky_material + luces + sync centralizada.
    Asi el render siempre refleja los cambios random de la ultima variacion.
    """
    if not MAYA_AVAILABLE:
        return False

    from utils.camera import CAMERA_XFORM, create_default_camera, look_through_camera, lock_camera

    # Paleta activa
    try:
        from ui.panels.material_panel import current_palette_label
        palette = current_palette_label()
    except Exception:
        palette = 'Default'

    # Asegurar que la camara existe
    if not mc.objExists(CAMERA_XFORM):
        print(f'[RetroMecha][Render] {CAMERA_XFORM} no existe — creandola')
        create_default_camera(frame_mecha=False, look_through=False)
        if not mc.objExists(CAMERA_XFORM):
            print('[RetroMecha][Render] No se pudo crear la camara')
            return False
    try:
        look_through_camera()
        lock_camera(True)
    except Exception as e:
        print(f'[RetroMecha][Render] Camara (look/lock): {e}')

    # Asegurar sky geometry
    try:
        from utils.sky import create_sky, has_sky
        if not has_sky():
            create_sky()
    except Exception as e:
        print(f'[RetroMecha][Render] Sky: {e}')

    # Asegurar sky material
    try:
        from materials.sky_material import create_sky_material, has_sky_material
        if not has_sky_material():
            create_sky_material(palette)
    except Exception as e:
        print(f'[RetroMecha][Render] SkyMat: {e}')

    # Asegurar luces
    try:
        from utils import lighting
        if not lighting.has_rm_lights():
            lighting.apply_lighting(palette)
        else:
            lighting.set_palette(palette)
    except Exception as e:
        print(f'[RetroMecha][Render] Luces: {e}')

    # Sync centralizada (idempotente: shaders + sky_ramp + luces)
    try:
        from materials.sync import apply_palette_full
        apply_palette_full(palette)
    except Exception as e:
        print(f'[RetroMecha][Render] Sync: {e}')

    if not _has_arnold():
        print('[RetroMecha][Render] Arnold no cargado — abortando')
        return False

    set_render_settings()

    # Abrir Render View y lanzar render
    try:
        mel.eval('RenderViewWindow')
    except Exception:
        pass

    try:
        mel.eval(
            f'renderWindowRenderCamera render renderView {CAMERA_XFORM}'
        )
        print(f'[RetroMecha][Render] Render {RENDER_WIDTH}x{RENDER_HEIGHT} '
              f'desde {CAMERA_XFORM}')
        return True
    except Exception as e:
        print(f'[RetroMecha][Render] Error lanzando render: {e}')
        # Fallback: comando render directo
        try:
            mc.render(CAMERA_XFORM, x=RENDER_WIDTH, y=RENDER_HEIGHT)
            return True
        except Exception as e2:
            print(f'[RetroMecha][Render] Fallback fallido: {e2}')
            return False


# ── Internos ─────────────────────────────────────────────────────────

def _camera_shape(xform: str) -> str | None:
    if not mc.objExists(xform):
        return None
    shapes = mc.listRelatives(xform, shapes=True, type='camera') or []
    return shapes[0] if shapes else None
