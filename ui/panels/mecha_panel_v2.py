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


def build_with_tabs(tab_ids, labels, colors):
    _current_sub[0] = 'general'
    widgets.tab_bar(tab_ids, labels, colors, _switch_sub, width=320, height=28)

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
        label='Simetría',
        value=params.get('symmetry', True),
        changeCommand=lambda *_: (_toggle_symmetry_ui(), _on_mecha_cc()),
    ))
    state.reg('arms_cb', mc.checkBox(
        label='Brazos',
        value=params.get('use_arms', True),
        changeCommand=_on_mecha_cc,
    ))
    state.reg('wings_cb', mc.checkBox(
        label='Alas',
        value=params.get('use_wings', True),
        changeCommand=_on_mecha_cc,
    ))
    state.reg('energy_cb', mc.checkBox(
        label='Anillos de energía',
        value=params.get('use_energy_fields', True),
        changeCommand=_on_mecha_cc,
    ))
    mc.setParent('..')


def _render_module(module):
    params = state._MECHA_PARAMS
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    labels = STYLE_MAPS.get(module, {})
    if labels:
        _build_style_buttons(module, labels)

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

    mc.setParent('..')


def _build_style_buttons(module, labels):
    """Buttons de estilo en filas, como swatches de paleta."""
    params = state._MECHA_PARAMS
    current_val = params.get(f'{module}_style', '')
    items = list(labels.items())

    for i in range(0, len(items), 4):
        chunk = items[i:i + 4]
        n = len(chunk)
        mc.rowLayout(nc=n, columnWidth=[(i + 1, 80) for i in range(n)],
                     columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for label, value in chunk:
            is_active = (current_val == value)
            btn = mc.button(
                label=label, height=24,
                backgroundColor=widgets.ACCENT_ACTION if is_active else widgets.BG_HOVER,
                command=lambda *_, v=value: _on_style_click(module, v),
            )
            state.reg(f'{module}_style_btn_{value}', btn)
        mc.setParent('..')

    # Botón para estilo derecho (solo arm/wing, visible cuando simetría off)
    if module in ('arm', 'wing'):
        right_labels = ARM_STYLE_LABELS if module == 'arm' else WING_STYLE_LABELS
        right_val = params.get(f'{module}_style_right', '')
        col = mc.columnLayout(adjustableColumn=True, visible=not params.get('symmetry', True))
        state.reg(f'{module}_right_row', col)
        right_items = list(right_labels.items())
        for j in range(0, len(right_items), 4):
            chunk = right_items[j:j + 4]
            nn = len(chunk)
            mc.rowLayout(nc=nn, columnWidth=[(k + 1, 80) for k in range(nn)],
                         columnAttach=[(k + 1, 'both', 2) for k in range(nn)])
            for label, value in chunk:
                is_active = (right_val == value)
                btn = mc.button(
                    label=label, height=24,
                    backgroundColor=widgets.ACCENT_ACTION if is_active else widgets.BG_HOVER,
                    command=lambda *_, v=value: _on_style_right_click(module, v),
                )
                state.reg(f'{module}_style_right_btn_{value}', btn)
            mc.setParent('..')
        mc.setParent('..')


def _update_style_colors(module):
    """Actualiza backgroundColor de todos los botones de estilo del módulo."""
    params = state._MECHA_PARAMS
    for _, value in STYLE_MAPS.get(module, {}).items():
        ctrl = state.get(f'{module}_style_btn_{value}')
        if ctrl and mc.control(ctrl, q=True, exists=True):
            is_active = (params.get(f'{module}_style', '') == value)
            mc.button(ctrl, e=True,
                      backgroundColor=widgets.ACCENT_ACTION if is_active else widgets.BG_HOVER)
    if module not in ('arm', 'wing'):
        return
    for _, value in (ARM_STYLE_LABELS if module == 'arm' else WING_STYLE_LABELS).items():
        ctrl = state.get(f'{module}_style_right_btn_{value}')
        if ctrl and mc.control(ctrl, q=True, exists=True):
            is_active = (params.get(f'{module}_style_right', '') == value)
            mc.button(ctrl, e=True,
                      backgroundColor=widgets.ACCENT_ACTION if is_active else widgets.BG_HOVER)


def _on_style_click(module, value):
    params = state._MECHA_PARAMS
    params[f'{module}_style'] = value
    _update_style_colors(module)
    _on_mecha_cc()


def _on_style_right_click(module, value):
    params = state._MECHA_PARAMS
    params[f'{module}_style_right'] = value
    _update_style_colors(module)
    _on_mecha_cc()


def _on_mecha_cc(*_):
    if state._UI_BUILDING[0] or state._APPLYING_MECHA_PRESET[0]:
        return
    rebuild_mecha()
