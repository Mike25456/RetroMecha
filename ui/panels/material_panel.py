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
from utils.maya_materials import ensure_material

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

    mc.separator(h=8)
    mc.button(
        label='Aplicar materiales al mecha', h=28,
        backgroundColor=T.CYAN,
        command=lambda *_: _apply_materials(),
        annotation='Aplica la paleta actual y reasigna los shaders al mecha y terreno',
    )

    mc.separator(h=4, style='none')
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
        mc.setAttr(f'{sh}.color',
                   float(rgb[0]), float(rgb[1]), float(rgb[2]),
                   type='double3')
    except Exception:
        pass


def _set_shader_diffuse(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh):
        try:
            mc.setAttr(f'{sh}.diffuse', val)
        except Exception:
            pass


def _set_shader_incandescence(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh) and sh == 'rm_cyan_glow_mat':
        try:
            mc.setAttr(f'{sh}.incandescence', val, val, val, type='double3')
        except Exception:
            pass


def _update_shader_sliders():
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    _APPLYING_SHADER[0] = True
    try:
        col = mc.getAttr(f'{sh}.color')[0]
        mc.colorSliderGrp(state.get('color_sl'), e=True, rgb=col)
        d = mc.getAttr(f'{sh}.diffuse')
        mc.floatSliderGrp(state.get('d_sl'), e=True, value=d)
        is_glow = (sh == 'rm_cyan_glow_mat')
        mc.control(state.get('i_sl'), e=True, visible=is_glow)
        if is_glow:
            inc = mc.getAttr(f'{sh}.incandescence')[0]
            mc.floatSliderGrp(state.get('i_sl'), e=True, value=inc[0])
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


def _find_mecha_group():
    from ui import scene_utils as sc
    return sc.find_mecha_group()


def _find_scene_group():
    from ui import scene_utils as sc
    return sc.find_scene_group()


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


def _apply_materials(*_):
    """Aplica la paleta + reasigna shaders al mecha, terreno y sky."""
    palette_label = current_palette_label()
    preset_menu = state.get('materials_preset_menu')
    if _safe_ctrl_exists(preset_menu):
        try:
            apply_preset(palette_label)
            _update_shader_sliders()
        except Exception:
            pass

    mecha_grp = _find_mecha_group()
    scene_grp = _find_scene_group()
    target = scene_grp or mecha_grp
    if not target:
        print('[RetroMecha][Mat] No hay mecha en escena')
        return

    try:
        from materials.materializer import materialize_mecha, materialize_terrain
        if mecha_grp:
            materialize_mecha(mecha_grp)
        if scene_grp:
            for child in (mc.listRelatives(scene_grp, children=True, type='transform') or []):
                if child.startswith('rm_terrain_'):
                    materialize_terrain(child)
        print('[RetroMecha][Mat] Materiales aplicados')
    except Exception as e:
        print(f'[RetroMecha][Mat] Error: {e}')

    try:
        from materials.sky_material import (
            create_sky_material, update_sky_ramp, has_sky_material,
        )
        if mc.objExists('sky'):
            if has_sky_material():
                update_sky_ramp(palette_label)
            else:
                create_sky_material(palette_label)
    except Exception as e:
        print(f'[RetroMecha][Mat] Sky: {e}')


def current_palette_label() -> str:
    """Devuelve el label del preset seleccionado (Default si no hay)."""
    preset_menu = state.get('materials_preset_menu')
    if _safe_ctrl_exists(preset_menu):
        try:
            return mc.optionMenu(preset_menu, q=True, value=True) or 'Default'
        except Exception:
            pass
    return 'Default'


def apply_palette_quick(palette_key):
    """Aplica una paleta aiToon directamente por key (modo Rapido)."""
    grp = _find_mecha_group()
    if not grp:
        print('[RetroMecha][aiToon] No hay mecha en escena')
        return
    try:
        from utils.material_assigner import assign_palette_to_group, clear_material_cache
        clear_material_cache()
        assign_palette_to_group(grp, palette_key)
        print(f'[RetroMecha][aiToon] Paleta {palette_key} aplicada')
    except ImportError as e:
        print(f'[RetroMecha][aiToon] material_assigner no disponible: {e}')
    except Exception as e:
        print(f'[RetroMecha][aiToon] Error aplicando paleta: {e}')


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
