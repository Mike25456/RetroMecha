"""MECHA panel v2: one visible module section at a time."""

import json
from pathlib import Path

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.constants import ARM_STYLE_LABELS, WING_STYLE_LABELS, STYLE_MAPS
from ui.widgets import fsl
from ui.module_advanced import get_slider_specs
from ui.build_actions import rebuild_mecha, _toggle_symmetry_ui, _safe_ctrl_exists

_current_sub = ['general']

def _label_for(mapping, value, default=None):
    for label, mapped in mapping.items():
        if mapped == value:
            return label
    return default or next(iter(mapping), '')


def build_with_tabs(tab_ids, labels, colors):
    _current_sub[0] = 'general'
    widgets.tab_bar(tab_ids, labels, colors, _switch_sub, width=320, height=22)

    mc.separator(h=4, style='none')
    content = mc.columnLayout(adjustableColumn=True, rowSpacing=2)
    state.reg('mecha_sub_content', content)
    _render_general()
    mc.setParent('..')


def _clear_content(content):
    children = mc.columnLayout(content, q=True, childArray=True) or []
    for child in children:
        try:
            mc.deleteUI(child)
        except Exception:
            pass


def _switch_sub(tab_id):
    _current_sub[0] = tab_id
    content = state.get('mecha_sub_content')
    if not _safe_ctrl_exists(content):
        return

    _clear_content(content)
    mc.setParent(content)
    if tab_id == 'general':
        _render_general()
    else:
        _render_module(tab_id)
    mc.setParent('..')


def _load_preset_labels():
    path = Path(__file__).resolve().parent.parent.parent / 'config' / 'presets.json'
    try:
        with open(path, encoding='utf-8') as f:
            data = {k: v for k, v in json.load(f).items() if not k.startswith('_')}
    except Exception:
        data = {}
    return {preset.get('_name', key): key for key, preset in data.items()}


def _render_general():
    params = state._MECHA_PARAMS
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    labels = _load_preset_labels()
    mc.rowLayout(nc=2, cw2=[100, 220])
    mc.text(label='Preset', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(backgroundColor=widgets.BG_HOVER)
    mc.menuItem(label='Custom')
    for label in labels:
        mc.menuItem(label=label)
    mc.optionMenu(
        menu, e=True,
        changeCommand=lambda val: __import__(
            'ui.build_actions', fromlist=['apply_mecha_preset']
        ).apply_mecha_preset(labels.get(val, val))
    )
    mc.setParent('..')
    state.reg('mecha_preset_menu', menu)

    state.reg('height_sl', fsl(
        'Altura', 0.5, 2.0, params.get('height_scale', 1.0),
        step=0.05, on_cc=_on_mecha_cc, annotation='Escala vertical',
    ))

    mc.separator(h=4)
    state.reg('sym_cb', mc.checkBox(
        label='Simetria',
        value=params.get('symmetry', True),
        changeCommand=lambda *_: (_toggle_symmetry_ui(), _on_mecha_cc()),
    ))
    state.reg('arms_cb', mc.checkBox(
        label='Modulo Brazos',
        value=params.get('use_arms', True),
        changeCommand=_on_mecha_cc,
    ))
    state.reg('wings_cb', mc.checkBox(
        label='Modulo Alas',
        value=params.get('use_wings', True),
        changeCommand=_on_mecha_cc,
    ))
    state.reg('energy_cb', mc.checkBox(
        label='Anillos de energia',
        value=params.get('use_energy_fields', True),
        changeCommand=_on_mecha_cc,
    ))
    mc.setParent('..')


def _render_module(module):
    params = state._MECHA_PARAMS
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    labels = STYLE_MAPS.get(module, {})
    if labels:
        mc.rowLayout(nc=2, cw2=[100, 220])
        mc.text(label='Estilo', align='right', font='smallPlainLabelFont')
        menu = mc.optionMenu(changeCommand=_on_mecha_cc,
                             backgroundColor=widgets.BG_HOVER)
        for label in labels:
            mc.menuItem(label=label)
        current = _label_for(labels, params.get(f'{module}_style'))
        if current:
            mc.optionMenu(menu, e=True, value=current)
        mc.setParent('..')
        state.reg(f'{module}_style_menu', menu)

    for spec in get_slider_specs(module):
        key = spec['key']
        ctrl = fsl(
            spec['label'],
            float(spec['min']),
            float(spec['max']),
            params.get(key, float(spec['default'])),
            step=float(spec.get('step', 0.02)),
            annotation=spec.get('description', ''),
            on_cc=_on_mecha_cc,
        )
        mc.floatSliderGrp(ctrl, e=True, dragCommand=_on_mecha_cc)
        state.reg(f'{module}.{key}', ctrl)

    if module in ('arm', 'wing'):
        row = mc.rowLayout(nc=2, cw2=[100, 220], visible=False)
        state.reg(f'{module}_right_row', row)
        mc.text(label=f'{module.capitalize()} der.', align='right', font='smallPlainLabelFont')
        menu = mc.optionMenu(changeCommand=_on_mecha_cc,
                             backgroundColor=widgets.BG_HOVER)
        src_labels = ARM_STYLE_LABELS if module == 'arm' else WING_STYLE_LABELS
        for label in src_labels:
            mc.menuItem(label=label)
        current = _label_for(src_labels, params.get(f'{module}_style_right'))
        if current:
            mc.optionMenu(menu, e=True, value=current)
        mc.setParent('..')
        state.reg(f'{module}_style_right_menu', menu)

        sym = state.get('sym_cb')
        if _safe_ctrl_exists(sym):
            try:
                visible = not mc.checkBox(sym, q=True, value=True)
                mc.control(row, e=True, visible=visible)
            except Exception:
                pass

    mc.setParent('..')


def _on_mecha_cc(*_):
    if state._UI_BUILDING[0] or state._APPLYING_MECHA_PRESET[0]:
        return
    rebuild_mecha()
