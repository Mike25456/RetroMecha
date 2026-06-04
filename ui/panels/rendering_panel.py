"""Panel RENDERING — Render, iluminacion, cielo y camara.

  - Boton RENDER 1920x1080 (Arnold) desde Camera_for_render
  - Iluminacion: 5 luces (luz_ambiente, foco_mecha, background,
                 veam_light izquierdo/derecho) palette-aware
  - Sliders individuales de intensidad por luz
  - Slider de densidad de aiAtmosphereVolume
  - Cielo: sky polyPlane + bends + sky_material
  - Camara: crear/eliminar/look through/lift mecha
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl
import ui.theme as T

from utils.lighting import (
    AMBIENT_INTENSITY, FOCO_INTENSITY, BG_INTENSITY, VEAM_INTENSITY,
    INTENSITY_MIN, INTENSITY_MAX,
)

DEFAULT_DENSITY    = 0.034
DENSITY_MIN        = 0.02
DENSITY_MAX        = 0.08
DEFAULT_ANISOTROPY = 0.666


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=4,
                    columnAttach=('both', 4))

    mc.separator(h=8, style='none')

    # ── RENDER ─────────────────────────────────────────────────
    mc.text(
        label='  RENDER',
        align='left', font='boldLabelFont', h=22,
        backgroundColor=T.PANEL,
    )
    mc.separator(h=4, style='none')
    mc.text(
        label='  1920 x 1080  |  Camera_for_render  |  Arnold',
        align='left', font='smallPlainLabelFont',
    )
    mc.button(
        label='Render', h=34,
        backgroundColor=T.CYAN,
        command=lambda *_: _do_render(),
        annotation='Configura Arnold + resolucion 1920x1080 y lanza el render '
                   'desde Camera_for_render en la Render View',
    )

    # ── ILUMINACION ────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(
        label='  ILUMINACION',
        align='left', font='boldLabelFont', h=22,
        backgroundColor=T.PANEL,
    )
    mc.separator(h=4, style='none')

    mc.text(
        label='  luz_ambiente: color terreno  |  veam: color mecha  |  '
              'foco + bg: BLANCAS',
        align='left', font='smallPlainLabelFont',
    )

    state.reg('render_ambient_i_sl', fsl(
        'Ambient (luz_ambiente)', INTENSITY_MIN, INTENSITY_MAX, AMBIENT_INTENSITY,
        step=0.1, prec=2,
        on_cc=_on_ambient_intensity,
        annotation='Intensidad de luz_ambiente (aiAreaLight quad, '
                   'color del terreno segun paleta)',
    ))
    state.reg('render_foco_i_sl', fsl(
        'Foco (foco_mecha)', INTENSITY_MIN, INTENSITY_MAX, FOCO_INTENSITY,
        step=0.1, prec=2,
        on_cc=_on_foco_intensity,
        annotation='Intensidad de foco_mecha (aiAreaLight disk, BLANCA)',
    ))
    state.reg('render_bg_i_sl', fsl(
        'Background', INTENSITY_MIN, INTENSITY_MAX, BG_INTENSITY,
        step=0.1, prec=2,
        on_cc=_on_bg_intensity,
        annotation='Intensidad de background (aiAreaLight quad, BLANCA, '
                   'Z = skyline + 4)',
    ))
    state.reg('render_veam_i_sl', fsl(
        'Mesh (veam izq/der)', INTENSITY_MIN, INTENSITY_MAX, VEAM_INTENSITY,
        step=0.1, prec=2,
        on_cc=_on_veam_intensity,
        annotation='Intensidad de veam_light_izquierdo y veam_light_derecho '
                   '(aiMeshLight, color glow del mecha)',
    ))

    state.reg('render_atmosphere_density_sl', fsl(
        'Densidad atmosfera', DENSITY_MIN, DENSITY_MAX, DEFAULT_DENSITY,
        step=0.001, prec=3,
        on_cc=_on_atmosphere_density,
        annotation='Densidad del aiAtmosphereVolume (volumetrica Arnold). '
                   f'Rango: {DENSITY_MIN}-{DENSITY_MAX} (default {DEFAULT_DENSITY})',
    ))

    mc.rowLayout(nc=2, cw2=[160, 160],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Crear / Recrear luces', h=26,
              backgroundColor=T.CYAN,
              command=lambda *_: _apply_lighting(),
              annotation='Crea las 5 luces (ambient/foco/bg/2 mesh) + atmosfera. '
                         'Colores segun la paleta activa.')
    mc.button(label='Eliminar luces', h=26,
              backgroundColor=T.SLATE,
              command=lambda *_: _remove_lighting(),
              annotation='Elimina luces y atmosfera creadas por RetroMecha')
    mc.setParent('..')

    # ── CIELO ──────────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(
        label='  CIELO',
        align='left', font='boldLabelFont', h=22,
        backgroundColor=T.PANEL,
    )
    mc.separator(h=4, style='none')

    mc.rowLayout(nc=2, cw2=[160, 160],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Crear / Recrear cielo', h=26,
              backgroundColor=T.CYAN,
              command=lambda *_: _apply_sky(),
              annotation='Crea sky (polyPlane 24x24 + bend1 envelope 2 + bend2) '
                         '+ sky_material acorde a paleta')
    mc.button(label='Eliminar cielo', h=26,
              backgroundColor=T.SLATE,
              command=lambda *_: _remove_sky_cb(),
              annotation='Elimina el sky, sus deformadores y el sky_material')
    mc.setParent('..')

    # ── CAMARA ─────────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(
        label='  CAMARA',
        align='left', font='boldLabelFont', h=22,
        backgroundColor=T.PANEL,
    )
    mc.separator(h=4, style='none')

    mc.text(
        label='  Camera_for_render: focal 21.39  |  fStop 5.6  |  '
              'pos fija del setup',
        align='left', font='smallPlainLabelFont',
    )

    mc.rowLayout(nc=2, cw2=[160, 160],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Crear / Recrear camara', h=26,
              backgroundColor=T.CYAN,
              command=lambda *_: _apply_default_camera(),
              annotation='Crea Camera_for_render con la config final del setup '
                         '(posicion / rotacion fijas del usuario)')
    mc.button(label='Eliminar camara', h=26,
              backgroundColor=T.SLATE,
              command=lambda *_: _remove_default_camera(),
              annotation='Elimina Camera_for_render de la escena')
    mc.setParent('..')

    mc.rowLayout(nc=2, cw2=[160, 160],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Look through', h=26,
              backgroundColor=T.CYAN,
              command=lambda *_: _look_through_camera(),
              annotation='Mira a traves de Camera_for_render en el panel activo')
    mc.button(label='Lift mecha +6', h=26,
              backgroundColor=T.CYAN,
              command=lambda *_: _lift_mecha_default(),
              annotation='Desplaza el grupo del mecha +6 en Y '
                         '(replica el ajuste manual del setup)')
    mc.setParent('..')

    mc.separator(h=6, style='none')
    mc.setParent('..')

    _ensure_default_lighting()


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _current_palette():
    try:
        from ui.panels.material_panel import current_palette_label
        return current_palette_label()
    except Exception:
        return 'Default'


def _ensure_default_lighting():
    try:
        from utils import lighting
        if not lighting.has_rm_lights():
            lighting.apply_lighting(_current_palette())
    except Exception as e:
        print(f'[RetroMecha][Render] Auto-luces: {e}')
    try:
        from utils import atmosphere
        if not atmosphere.has_atmosphere():
            atmosphere.ensure_atmosphere(DEFAULT_DENSITY, DEFAULT_ANISOTROPY)
    except Exception as e:
        print(f'[RetroMecha][Render] Auto-atmosfera: {e}')


# ══════════════════════════════════════════════════════════════
#  CALLBACKS — Render
# ══════════════════════════════════════════════════════════════

def _do_render(*_):
    try:
        from utils.render import render_now
        render_now()
    except Exception as e:
        print(f'[RetroMecha][Render] {e}')


# ══════════════════════════════════════════════════════════════
#  CALLBACKS — Iluminacion
# ══════════════════════════════════════════════════════════════

def _apply_lighting(*_):
    try:
        from utils import lighting
        for slider_key, setter in (
            ('render_ambient_i_sl', lighting.set_ambient_intensity),
            ('render_foco_i_sl',    lighting.set_foco_intensity),
            ('render_bg_i_sl',      lighting.set_background_intensity),
            ('render_veam_i_sl',    lighting.set_veam_intensity),
        ):
            sl = state.get(slider_key)
            if sl and mc.floatSliderGrp(sl, exists=True):
                try:
                    setter(mc.floatSliderGrp(sl, q=True, value=True))
                except Exception:
                    pass
        lighting.apply_lighting(_current_palette())
    except Exception as e:
        print(f'[RetroMecha][Render] Lighting: {e}')

    try:
        from utils import atmosphere
        density = mc.floatSliderGrp(
            state.get('render_atmosphere_density_sl'), q=True, value=True)
        atmosphere.ensure_atmosphere(density, DEFAULT_ANISOTROPY)
    except Exception as e:
        print(f'[RetroMecha][Render] Atmosfera: {e}')


def _remove_lighting(*_):
    try:
        from utils import lighting
        lighting.remove_lighting()
    except Exception as e:
        print(f'[RetroMecha][Render] Lighting: {e}')
    try:
        from utils import atmosphere
        atmosphere.remove_atmosphere()
    except Exception as e:
        print(f'[RetroMecha][Render] Atmosfera: {e}')
    print('[RetroMecha][Render] Luces y atmosfera eliminadas')


def _on_ambient_intensity(val):
    try:
        from utils import lighting
        lighting.set_ambient_intensity(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Ambient I: {e}')


def _on_foco_intensity(val):
    try:
        from utils import lighting
        lighting.set_foco_intensity(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Foco I: {e}')


def _on_bg_intensity(val):
    try:
        from utils import lighting
        lighting.set_background_intensity(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] BG I: {e}')


def _on_veam_intensity(val):
    try:
        from utils import lighting
        lighting.set_veam_intensity(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Veam I: {e}')


def _on_atmosphere_density(val):
    try:
        from utils import atmosphere
        atmosphere.set_density(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Atmosfera density: {e}')


# ══════════════════════════════════════════════════════════════
#  CALLBACKS - Camara
# ══════════════════════════════════════════════════════════════

def _apply_default_camera(*_):
    try:
        from utils.camera import create_default_camera
        create_default_camera(frame_mecha=True, look_through=True)
    except Exception as e:
        print(f'[RetroMecha][Render] Camara: {e}')


def _remove_default_camera(*_):
    try:
        from utils.camera import remove_camera
        remove_camera()
        print('[RetroMecha][Render] Camara eliminada')
    except Exception as e:
        print(f'[RetroMecha][Render] Camara: {e}')


def _look_through_camera(*_):
    try:
        from utils.camera import look_through_camera
        look_through_camera()
    except Exception as e:
        print('[RetroMecha][Render] Look through: {e}')


def _lift_mecha_default(*_):
    try:
        from utils.camera import lift_mecha_default
        if not lift_mecha_default():
            print('[RetroMecha][Render] No hay mecha en escena para desplazar')
    except Exception as e:
        print(f'[RetroMecha][Render] Lift: {e}')


# ══════════════════════════════════════════════════════════════
#  CALLBACKS - Cielo
# ══════════════════════════════════════════════════════════════

def _apply_sky(*_):
    try:
        from utils.sky import create_sky
        create_sky()
    except Exception as e:
        print(f'[RetroMecha][Render] Cielo: {e}')
    try:
        from materials.sky_material import create_sky_material
        create_sky_material(_current_palette())
    except Exception as e:
        print(f'[RetroMecha][Render] Sky material: {e}')


def _remove_sky_cb(*_):
    try:
        from utils.sky import remove_sky
        remove_sky()
    except Exception as e:
        print(f'[RetroMecha][Render] Cielo: {e}')
    try:
        from materials.sky_material import remove_sky_material
        remove_sky_material()
    except Exception as e:
        print(f'[RetroMecha][Render] Sky material: {e}')
    print('[RetroMecha][Render] Cielo eliminado')
