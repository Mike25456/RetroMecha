"""Panel RENDERING — Arnold materials + lighting con controles avanzados.

Esta pestaña agrupa todo lo relacionado con el render final:
  - Asignación de materiales (Lambert VP2.0 o Arnold aiToon)
  - Preset de iluminación (3 opciones)
  - Sliders de intensidad por luz, intensidad skydome y temperatura
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl

# Materiales que el usuario puede asignar al mecha desde rendering
_MATERIAL_MODES = {
    'Lambert (VP 2.0)':  'lambert',
    'Arnold (aiToon)':   'aitoon',
}

_AITOON_PALETTE_LABELS = {
    'Industrial': 'industrial',
    'Oxidado':    'oxidado',
    'Artico':     'artico',
    'Carmesi':    'carmesi',
}

_LAMBERT_PRESET_LABELS = ['Default', 'Atardecer', 'Frio', 'Oxidado', 'Neon']

_LIGHTING_PRESET_LABELS = {
    'Estudio':   'studio',
    'Dramatico': 'dramatic',
    'Retro':     'retro',
}

DEFAULT_LIGHT_INTENSITY = 1.5
DEFAULT_SKYDOME_INTENSITY = 0.35
DEFAULT_TEMPERATURE = 6500


def build():
    """Construye el panel completo de rendering."""
    mc.columnLayout(adjustableColumn=True, rowSpacing=4,
                    columnAttach=('both', 4))

    mc.separator(h=8, style='none')

    # ── MATERIALES ─────────────────────────────────────────────
    mc.text(
        label='  MATERIALES',
        align='left', font='boldLabelFont', h=22,
        backgroundColor=[0.22, 0.18, 0.10],
    )
    mc.separator(h=4, style='none')

    # Selector: tipo de material
    mc.rowLayout(nc=2, cw2=[120, 200],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Tipo', align='right', font='smallPlainLabelFont')
    mode_menu = mc.optionMenu(
        changeCommand=_on_mode_changed,
        annotation='Lambert: Viewport 2.0 — Arnold: aiToon con silhouette')
    for lbl in _MATERIAL_MODES:
        mc.menuItem(label=lbl)
    state.reg('render_mode_menu', mode_menu)
    mc.setParent('..')

    # Estado Arnold
    state.reg('render_arnold_status', mc.text(
        label=_arnold_status_label(),
        align='left', font='smallPlainLabelFont',
    ))

    # Paleta (cambia según modo)
    mc.rowLayout(nc=2, cw2=[120, 200],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Paleta', align='right', font='smallPlainLabelFont')
    palette_menu = mc.optionMenu(
        annotation='Paleta de colores a aplicar')
    for lbl in _LAMBERT_PRESET_LABELS:
        mc.menuItem(label=lbl)
    state.reg('render_palette_menu', palette_menu)
    mc.setParent('..')

    mc.button(
        label='Aplicar materiales al mecha', h=28,
        backgroundColor=[0.58, 0.38, 0.12],
        command=lambda *_: _apply_materials(),
        annotation='Aplica los materiales del modo seleccionado al mecha en escena',
    )

    # ── ILUMINACIÓN ────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(
        label='  ILUMINACION',
        align='left', font='boldLabelFont', h=22,
        backgroundColor=[0.18, 0.18, 0.28],
    )
    mc.separator(h=4, style='none')

    # Preset
    mc.rowLayout(nc=2, cw2=[120, 200],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset', align='right', font='smallPlainLabelFont')
    light_preset_menu = mc.optionMenu(
        changeCommand=_on_lighting_preset_changed,
        annotation='Preset de iluminación: 3 luces direccionales + skydome')
    for lbl in _LIGHTING_PRESET_LABELS:
        mc.menuItem(label=lbl)
    state.reg('render_light_preset_menu', light_preset_menu)
    mc.setParent('..')

    # Sliders
    state.reg('render_lights_intensity_sl', fsl(
        'Intensidad luces', 0.0, 5.0, DEFAULT_LIGHT_INTENSITY,
        on_cc=_on_lights_intensity,
        annotation='Intensidad de las luces direccionales (key/fill/back)',
    ))
    state.reg('render_skydome_intensity_sl', fsl(
        'Intensidad skydome', 0.0, 3.0, DEFAULT_SKYDOME_INTENSITY,
        on_cc=_on_skydome_intensity,
        annotation='Intensidad del aiSkyDomeLight (requiere Arnold)',
    ))
    state.reg('render_temperature_sl', fsl(
        'Temperatura (K)', 1500.0, 12000.0, DEFAULT_TEMPERATURE,
        step=100, prec=0,
        on_cc=_on_temperature,
        annotation='Temperatura de color en Kelvin (3200K=cálida, 6500K=neutra, 9000K=fría)',
    ))

    mc.rowLayout(nc=2, cw2=[160, 160],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Crear / Recrear luces', h=26,
              backgroundColor=[0.60, 0.40, 0.14],
              command=lambda *_: _apply_lighting_preset(),
              annotation='Crea luces direccionales + aiSkyDomeLight')
    mc.button(label='Eliminar luces', h=26,
              backgroundColor=[0.46, 0.16, 0.12],
              command=lambda *_: _remove_lighting(),
              annotation='Elimina luces y sky dome creados por RetroMecha')
    mc.setParent('..')

    mc.separator(h=6, style='none')
    mc.setParent('..')

    # Auto-generar luces al abrir si no hay
    _ensure_default_lighting()


# ══════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════

def _find_mecha_group():
    from ui import scene_utils as sc
    return sc.find_mecha_group()


def _arnold_status_label() -> str:
    try:
        from utils.material_assigner import _has_arnold
        available = _has_arnold()
    except Exception:
        available = False
    if available:
        return '  Arnold disponible — se usará aiToon'
    return '  Arnold no detectado — fallback a Lambert'


def _current_mode() -> str:
    menu = state.get('render_mode_menu')
    if menu and mc.optionMenu(menu, exists=True):
        return _MATERIAL_MODES.get(mc.optionMenu(menu, q=True, value=True), 'lambert')
    return 'lambert'


def _refresh_palette_menu():
    """Cambia las entradas del menú Paleta según el modo seleccionado."""
    menu = state.get('render_palette_menu')
    if not menu or not mc.optionMenu(menu, exists=True):
        return
    for item in mc.optionMenu(menu, q=True, itemListLong=True) or []:
        mc.deleteUI(item)
    mode = _current_mode()
    labels = _LAMBERT_PRESET_LABELS if mode == 'lambert' else list(_AITOON_PALETTE_LABELS.keys())
    for lbl in labels:
        mc.menuItem(label=lbl, parent=menu)


def _ensure_default_lighting():
    """Si no hay luces RetroMecha en escena, crea el preset 'studio' por defecto."""
    try:
        from utils import lighting
        if not lighting.has_rm_lights():
            lighting.apply_lighting('studio', sky_dome=True)
            # Aplicar valores actuales de los sliders
            _on_lights_intensity(DEFAULT_LIGHT_INTENSITY)
            _on_skydome_intensity(DEFAULT_SKYDOME_INTENSITY)
            _on_temperature(DEFAULT_TEMPERATURE)
    except Exception as e:
        print(f'[RetroMecha][Render] Auto-luces: {e}')


# ══════════════════════════════════════════════════════════════
#  CALLBACKS — Materiales
# ══════════════════════════════════════════════════════════════

def _on_mode_changed(*_):
    _refresh_palette_menu()


def _apply_materials(*_):
    mode = _current_mode()
    palette_menu = state.get('render_palette_menu')
    if not palette_menu or not mc.optionMenu(palette_menu, exists=True):
        return
    label = mc.optionMenu(palette_menu, q=True, value=True)

    mecha_grp = _find_mecha_group()
    if not mecha_grp:
        print('[RetroMecha][Render] No hay mecha en escena')
        return

    if mode == 'lambert':
        try:
            from materials.presets import apply_preset
            from materials.materializer import materialize_mecha
            apply_preset(label)
            materialize_mecha(mecha_grp)
            # Sincronizar con el menú de la pestaña Escena
            lambert_menu = state.get('lambert_preset_menu')
            if lambert_menu and mc.optionMenu(lambert_menu, exists=True):
                mc.optionMenu(lambert_menu, e=True, value=label)
            print(f'[RetroMecha][Render] Lambert "{label}" aplicado')
        except Exception as e:
            print(f'[RetroMecha][Render] Error VP2.0: {e}')
    else:  # aitoon
        palette = _AITOON_PALETTE_LABELS.get(label)
        if not palette:
            print('[RetroMecha][Render] Paleta aiToon no válida')
            return
        try:
            from utils.material_assigner import assign_palette_to_group, clear_material_cache
            clear_material_cache()
            assign_palette_to_group(mecha_grp, palette)
            # Sincronizar con menú legacy
            aitoon_menu = state.get('aitoon_menu')
            if aitoon_menu and mc.optionMenu(aitoon_menu, exists=True):
                mc.optionMenu(aitoon_menu, e=True, value=label)
            # Refrescar estado Arnold
            status = state.get('render_arnold_status')
            if status and mc.text(status, exists=True):
                mc.text(status, e=True, label=_arnold_status_label())
        except Exception as e:
            print(f'[RetroMecha][Render] Error Arnold: {e}')


# ══════════════════════════════════════════════════════════════
#  CALLBACKS — Iluminación
# ══════════════════════════════════════════════════════════════

def _on_lighting_preset_changed(*_):
    """Al cambiar el preset, recrear las luces si ya existen."""
    try:
        from utils import lighting
        if lighting.has_rm_lights():
            _apply_lighting_preset()
    except Exception:
        pass


def _apply_lighting_preset(*_):
    """Crea/recrea las luces con el preset seleccionado y aplica los sliders."""
    menu = state.get('render_light_preset_menu')
    if not menu or not mc.optionMenu(menu, exists=True):
        return
    label = mc.optionMenu(menu, q=True, value=True)
    preset = _LIGHTING_PRESET_LABELS.get(label, 'studio')

    try:
        from utils import lighting
        lighting.apply_lighting(preset, sky_dome=True)
        # Re-aplicar valores actuales de los sliders
        _on_lights_intensity(mc.floatSliderGrp(state.get('render_lights_intensity_sl'),
                                                q=True, value=True))
        _on_skydome_intensity(mc.floatSliderGrp(state.get('render_skydome_intensity_sl'),
                                                 q=True, value=True))
        _on_temperature(mc.floatSliderGrp(state.get('render_temperature_sl'),
                                          q=True, value=True))
    except Exception as e:
        print(f'[RetroMecha][Render] Lighting: {e}')


def _remove_lighting(*_):
    try:
        from utils import lighting
        lighting.remove_lighting()
        print('[RetroMecha][Render] Luces eliminadas')
    except Exception as e:
        print(f'[RetroMecha][Render] Lighting: {e}')


def _on_lights_intensity(val):
    try:
        from utils import lighting
        lighting.set_lights_intensity(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Lights intensity: {e}')


def _on_skydome_intensity(val):
    try:
        from utils import lighting
        lighting.set_skydome_intensity(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Skydome intensity: {e}')


def _on_temperature(val):
    try:
        from utils import lighting
        lighting.set_lights_temperature(float(val))
        lighting.set_skydome_temperature(float(val))
    except Exception as e:
        print(f'[RetroMecha][Render] Temperature: {e}')
