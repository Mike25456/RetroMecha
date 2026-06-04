"""MATERIALES section — shaders aiStandardSurface con paleta.

Gestiona los shaders del mecha y terreno:
  - Paleta (preset de colores)
  - Selector de shader + sliders (color, difuso, brillo)
  - Boton 'Aplicar materiales al mecha'
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.build_actions import _safe_ctrl_exists
from ui.widgets import fsl
import ui.theme as T

from materials.presets import SHADER_NAMES, list_presets, apply_preset
from utils.maya_materials import ensure_material, set_semantic_attr, get_semantic_attr

_SHADER_LABELS = {
    'Armadura': 'rm_white_armor_mat',
    'Estructura': 'rm_graphite_mat',
    'Brillo': 'rm_cyan_glow_mat',
    'Terreno base': 'rm_terrain_base_mat',
    'Terreno oscuro': 'rm_terrain_dark_mat',
    'Terreno acento': 'rm_terrain_accent_mat',
}

_current_shader = ['rm_white_armor_mat']
_APPLYING_SHADER = [False]


def build(wrapped=True):
    if wrapped:
        mc.frameLayout(
            label='  >  MATERIALES',
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            backgroundColor=T.PANEL,
            marginHeight=8, marginWidth=6,
        )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)

    for shader_name in SHADER_NAMES:
        ensure_material(shader_name)

    presets_list = list_presets()
    _current_shader[0] = 'rm_white_armor_mat'

    if presets_list:
        mc.rowLayout(nc=2, cw2=[128, 180],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label='Paleta', align='right', font='smallPlainLabelFont')
        preset_menu = mc.optionMenu(
            changeCommand=lambda *_: _on_preset_changed(),
            backgroundColor=T.LINE,
            annotation='Preset de colores aplicado a los 6 shaders del mecha y terreno')
        for p in presets_list:
            mc.menuItem(label=p)
        state.reg('materials_preset_menu', preset_menu)
        mc.setParent('..')
    else:
        mc.text(label='(sin presets)', align='left', font='smallPlainLabelFont')
        state.reg('materials_preset_menu', None)

    mc.separator(h=4)
    _build_shader_tabs()

    state.reg('color_sl', mc.colorSliderGrp(
        label='Color', rgb=(0.86, 0.84, 0.78),
        columnWidth3=[60, 180, 52],
        changeCommand=_set_shader_color,
        annotation='Color principal del shader (click para abrir selector)',
    ))

    state.reg('d_sl', fsl('Difuso', 0.0, 1.0, 0.82, on_cc=_set_shader_diffuse,
                           annotation='Intensidad de luz difusa del material'))

    state.reg('i_sl', fsl('Brillo', 0.0, 1.0, 0.0, on_cc=_set_shader_incandescence,
                           annotation='Brillo auto-emitido (solo para shader Brillo)'))
    mc.control(state.get('i_sl'), e=True, visible=False)

    _update_shader_sliders()

    mc.separator(h=4)
    mc.setParent('..')
    if wrapped:
        mc.setParent('..')


def _set_shader_color(*_):
    if _APPLYING_SHADER[0]:
        return
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    try:
        rgb = mc.colorSliderGrp(state.get('color_sl'), q=True, rgb=True)
        set_semantic_attr(sh, 'color', tuple(float(c) for c in rgb))
    except Exception:
        pass


def _set_shader_diffuse(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh):
        set_semantic_attr(sh, 'diffuse', float(val))


def _set_shader_incandescence(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh) and sh == 'rm_cyan_glow_mat':
        v = float(val)
        set_semantic_attr(sh, 'incandescence', (v, v, v))


def _update_shader_sliders():
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    _APPLYING_SHADER[0] = True
    try:
        col = get_semantic_attr(sh, 'color')
        if col is not None:
            mc.colorSliderGrp(state.get('color_sl'), e=True, rgb=tuple(col))
        d = get_semantic_attr(sh, 'diffuse')
        if d is not None:
            mc.floatSliderGrp(state.get('d_sl'), e=True, value=float(d))
        is_glow = (sh == 'rm_cyan_glow_mat')
        mc.control(state.get('i_sl'), e=True, visible=is_glow)
        if is_glow:
            inc = get_semantic_attr(sh, 'incandescence')
            if inc is not None:
                mc.floatSliderGrp(state.get('i_sl'), e=True, value=float(inc[0]))
    except Exception:
        pass
    finally:
        _APPLYING_SHADER[0] = False


def _on_shader_sel(label):
    sh = _SHADER_LABELS.get(label)
    if sh:
        _current_shader[0] = sh
        _update_shader_sliders()


def _build_shader_tabs():
    labels = list(_SHADER_LABELS.keys())

    def _select(idx):
        label = labels[idx]
        sh = _SHADER_LABELS.get(label)
        if sh:
            _current_shader[0] = sh
            _update_shader_sliders()
        for j, lbl in enumerate(labels):
            btn = state.get(f'shader_tab_{lbl}')
            if btn:
                try:
                    mc.button(btn, e=True, backgroundColor=T.CYAN if j == idx else T.PANEL)
                except Exception:
                    pass

    for row_ofs in (0, 3):
        row_labels = labels[row_ofs:row_ofs + 3]
        n = len(row_labels)
        mc.rowLayout(nc=n,
            columnWidth=[(i + 1, 110) for i in range(n)],
            columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for i, label in enumerate(row_labels):
            idx = row_ofs + i
            is_active = (label == 'Armadura')
            btn = mc.button(label=label, height=24,
                            backgroundColor=T.CYAN if is_active else T.PANEL,
                            command=lambda *_, idx=idx: _select(idx))
            state.reg(f'shader_tab_{label}', btn)
        mc.setParent('..')


def _on_preset_changed(*_):
    """Al cambiar la paleta, actualizar los shaders en memoria + sky + luces."""
    preset_menu = state.get('materials_preset_menu')
    if not _safe_ctrl_exists(preset_menu):
        return
    try:
        label = mc.optionMenu(preset_menu, q=True, value=True)
    except Exception:
        return
    apply_preset(label)
    _update_shader_sliders()
    try:
        from materials.sky_material import update_sky_ramp, has_sky_material
        if has_sky_material():
            update_sky_ramp(label)
    except Exception:
        pass
    try:
        from utils import lighting
        if lighting.has_rm_lights():
            lighting.set_palette(label)
    except Exception:
        pass


def current_palette_label() -> str:
    """Devuelve el label del preset seleccionado (Default si no hay)."""
    preset_menu = state.get('materials_preset_menu')
    if _safe_ctrl_exists(preset_menu):
        try:
            return mc.optionMenu(preset_menu, q=True, value=True) or 'Predeterminado'
        except Exception:
            pass
    return 'Predeterminado'


def apply_color_preset_quick(preset_name):
    """Aplica un preset de colores por nombre (modo Rapido)."""
    apply_preset(preset_name)
    preset_menu = state.get('materials_preset_menu')
    if _safe_ctrl_exists(preset_menu):
        try:
            mc.optionMenu(preset_menu, e=True, value=preset_name)
        except Exception:
            pass
    _update_shader_sliders()
