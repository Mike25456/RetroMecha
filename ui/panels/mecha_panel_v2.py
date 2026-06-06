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
from ui.build_actions import rebuild_mecha, _toggle_symmetry_ui, _safe_ctrl_exists, apply_mecha_preset

_current_sub = ['head']


def _on_mecha_preset_click(label, key):
    apply_mecha_preset(key)
    _update_mecha_preset_btn_colors(label)


def _update_mecha_preset_btn_colors(active_label=None):
    for label, key in _load_preset_labels().items():
        ctrl = state.get(f'm_preset_btn_{key}')
        if ctrl and mc.control(ctrl, q=True, exists=True):
            is_active = (label == active_label)
            mc.button(ctrl, e=True,
                      backgroundColor=widgets.ACCENT_ACTION if is_active else widgets.BG_HOVER)


def build_with_tabs(tab_ids, labels, colors):
    _current_sub[0] = tab_ids[0] if tab_ids else 'head'

    params = state._MECHA_PARAMS

    # Preset buttons
    mc.text(label='Presets', align='left', font='smallPlainLabelFont')
    preset_items = list(_load_preset_labels().items())
    for i in range(0, len(preset_items), 4):
        chunk = preset_items[i:i + 4]
        n = len(chunk)
        mc.rowLayout(nc=n, columnWidth=[(j + 1, 80) for j in range(n)],
                     columnAttach=[(j + 1, 'both', 2) for j in range(n)])
        for p_label, p_key in chunk:
            btn = mc.button(
                label=p_label, height=32,
                backgroundColor=widgets.BG_HOVER,
                command=lambda *_, l=p_label, k=p_key: _on_mecha_preset_click(l, k),
            )
            state.reg(f'm_preset_btn_{p_key}', btn)
        mc.setParent('..')
    mc.separator(h=8, style='in')
    mc.separator(h=2, style='none')

    # Module sub-tabs
    mc.text(label='Módulos', align='left', font='smallPlainLabelFont')
    widgets.tab_bar(tab_ids, labels, colors, _switch_sub, width=500, height=38)
    mc.separator(h=4, style='none')

    # Dynamic content for the selected sub-tab
    content = mc.columnLayout(adjustableColumn=True, rowSpacing=2)
    state.reg('mecha_sub_content', content)
    _render_module(_current_sub[0])
    mc.setParent('..')

    # Always-visible controls below sub-tabs
    mc.separator(h=8, style='in')
    mc.separator(h=2, style='none')
    state.reg('height_sl', fsl(
        'Altura', 0.5, 2.0, params.get('height_scale', 1.0),
        step=0.05, on_cc=_on_mecha_cc, annotation='Escala vertical',
    ))
    mc.rowLayout(nc=3, cw3=[100, 80, 80])
    mc.text(label='Anillos de energía', align='right', font='smallPlainLabelFont')
    col_e = mc.radioCollection()
    en_on = mc.radioButton(label='Activados', onCommand=lambda *_: (
        state._MECHA_PARAMS.__setitem__('use_energy_fields', True), _on_mecha_cc()))
    en_off = mc.radioButton(label='Desactivados', onCommand=lambda *_: (
        state._MECHA_PARAMS.__setitem__('use_energy_fields', False), _on_mecha_cc()))
    mc.radioCollection(col_e, e=True, select=en_on if params.get('use_energy_fields', True) else en_off)
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


def _sync_right_styles_on_symmetry_toggle():
    """Al apagar simetría, copia el estilo izquierdo al derecho si está vacío."""
    if state._MECHA_PARAMS.get('symmetry', True):
        return
    module = _current_sub[0]
    if module not in ('arm', 'wing'):
        return
    right_key = f'{module}_style_right'
    if not state._MECHA_PARAMS.get(right_key):
        left = state._MECHA_PARAMS.get(f'{module}_style')
        if left:
            state._MECHA_PARAMS[right_key] = left
    _update_style_colors(module)


def _toggle_module_disabled(module):
    """Desactiva/activa todos los controles del módulo según su estado."""
    wrapper = state.get(f'{module}_content')
    if not wrapper:
        return
    try:
        key = 'use_arms' if module == 'arm' else 'use_wings'
        enabled = state._MECHA_PARAMS.get(key, True)
        if mc.control(wrapper, exists=True):
            mc.columnLayout(wrapper, e=True, enable=enabled)
    except Exception:
        pass


def _render_module(module):
    params = state._MECHA_PARAMS
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    if module == 'arm':
        mc.rowLayout(nc=3, cw3=[60, 90, 90])
        mc.text(label='Brazos', align='right', font='smallPlainLabelFont')
        col_a = mc.radioCollection()
        a_on = mc.radioButton(label='Activados', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('use_arms', True), _toggle_module_disabled('arm'), _on_mecha_cc()))
        a_off = mc.radioButton(label='Desactivados', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('use_arms', False), _toggle_module_disabled('arm'), _on_mecha_cc()))
        mc.radioCollection(col_a, e=True, select=a_on if params.get('use_arms', True) else a_off)
        mc.setParent('..')

        mc.rowLayout(nc=3, cw3=[60, 90, 90])
        mc.text(label='Simetría', align='right', font='smallPlainLabelFont')
        col_s = mc.radioCollection()
        s_on = mc.radioButton(label='Activada', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('symmetry', True), _toggle_symmetry_ui(),
            _sync_right_styles_on_symmetry_toggle(), _on_mecha_cc()))
        s_off = mc.radioButton(label='Desactivada', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('symmetry', False), _toggle_symmetry_ui(),
            _sync_right_styles_on_symmetry_toggle(), _on_mecha_cc()))
        mc.radioCollection(col_s, e=True, select=s_on if params.get('symmetry', True) else s_off)
        mc.setParent('..')
        mc.separator(h=4, style='none')
    elif module == 'wing':
        mc.rowLayout(nc=3, cw3=[60, 90, 90])
        mc.text(label='Alas', align='right', font='smallPlainLabelFont')
        col_w = mc.radioCollection()
        w_on = mc.radioButton(label='Activadas', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('use_wings', True), _toggle_module_disabled('wing'), _on_mecha_cc()))
        w_off = mc.radioButton(label='Desactivadas', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('use_wings', False), _toggle_module_disabled('wing'), _on_mecha_cc()))
        mc.radioCollection(col_w, e=True, select=w_on if params.get('use_wings', True) else w_off)
        mc.setParent('..')

        mc.rowLayout(nc=3, cw3=[60, 90, 90])
        mc.text(label='Simetría', align='right', font='smallPlainLabelFont')
        col_s2 = mc.radioCollection()
        s2_on = mc.radioButton(label='Activada', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('symmetry', True), _toggle_symmetry_ui(),
            _sync_right_styles_on_symmetry_toggle(), _on_mecha_cc()))
        s2_off = mc.radioButton(label='Desactivada', onCommand=lambda *_: (
            state._MECHA_PARAMS.__setitem__('symmetry', False), _toggle_symmetry_ui(),
            _sync_right_styles_on_symmetry_toggle(), _on_mecha_cc()))
        mc.radioCollection(col_s2, e=True, select=s2_on if params.get('symmetry', True) else s2_off)
        mc.setParent('..')
        mc.separator(h=4, style='none')

    # Wrapper que se desactiva cuando el módulo está desactivado
    if module in ('arm', 'wing'):
        enabled = params.get('use_arms' if module == 'arm' else 'use_wings', True)
        wrapper = mc.columnLayout(adjustableColumn=True, enable=enabled)
        state.reg(f'{module}_content', wrapper)

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

    if module in ('arm', 'wing'):
        mc.setParent('..')
    mc.setParent('..')


def _build_style_buttons(module, labels):
    """Buttons de estilo en filas, como swatches de paleta."""
    params = state._MECHA_PARAMS
    current_val = params.get(f'{module}_style', '')
    items = list(labels.items())

    mc.text(label='Estilos', align='left', font='smallPlainLabelFont')

    if module in ('arm', 'wing'):
        mc.separator(h=8, style='none')
        mc.text(label='Izquierdo', align='left', font='smallPlainLabelFont')

    for i in range(0, len(items), 4):
        chunk = items[i:i + 4]
        n = len(chunk)
        mc.rowLayout(nc=n, columnWidth=[(i + 1, 80) for i in range(n)],
                     columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for label, value in chunk:
            is_active = (current_val == value)
            btn = mc.button(
                label=label, height=22,
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
        mc.text(label='Derecho', align='left', font='smallPlainLabelFont')
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
                    label=label, height=22,
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
