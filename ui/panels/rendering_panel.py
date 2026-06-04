"""Panel RENDERING — Render, iluminacion, viewport.

  - Boton RENDER 1920x1080 (Arnold) desde Camara_for_render
  - Iluminacion: 5 luces palette-aware (auto-creadas en Generar/Render)
  - Sliders individuales de intensidad por luz
  - Slider de densidad de aiAtmosphereVolume
  - Look through camara + Lift mecha +6 (viewport/transform)

  Cielo, luces y camara se crean automaticamente en el flujo Generar/Render.
  No hay botones de setup: el sync de paleta se aplica implicitamente.
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
        label='  1920 x 1080  |  Camara_for_render  |  Arnold',
        align='left', font='smallPlainLabelFont',
    )
    mc.button(
        label='Render', h=34,
        backgroundColor=T.CYAN,
        command=lambda *_: _do_render(),
        annotation='Configura Arnold + resolucion 1920x1080 y lanza el render '
                   'desde Camara_for_render en la Render View',
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
        label='  luz_ambiente + veam: glow del mecha  |  foco + bg: BLANCAS',
        align='left', font='smallPlainLabelFont',
    )

    state.reg('render_ambient_i_sl', fsl(
        'Ambient (luz_ambiente)', INTENSITY_MIN, INTENSITY_MAX, AMBIENT_INTENSITY,
        step=0.1, prec=2,
        on_cc=_on_ambient_intensity,
        annotation='Intensidad de luz_ambiente (aiAreaLight quad, '
                   'color = rm_cyan_glow_mat de la paleta)',
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
    mc.button(label='Look through', h=26,
              backgroundColor=T.CYAN,
              command=lambda *_: _look_through_camera(),
        annotation='Mira a traves de Camara_for_render en el panel activo')
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
#  CALLBACKS — Sliders
# ══════════════════════════════════════════════════════════════

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
#  CALLBACKS - Viewport / Transform
# ══════════════════════════════════════════════════════════════

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
