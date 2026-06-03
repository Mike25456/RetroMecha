"""MECHA panel v2 — solo muestra el módulo seleccionado."""

import json
from pathlib import Path

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.constants import ARM_STYLE_LABELS, WING_STYLE_LABELS, STYLE_MAPS
from ui import widgets
from ui.widgets import fsl
from ui.module_advanced import get_module_spec, get_slider_specs
from ui.build_actions import rebuild_mecha, _toggle_symmetry_ui

_current_sub = ['general']


def build_with_tabs(tab_ids, labels, colors):
    """Construye sub-tabs y el área de contenido dinámico."""
    widgets.tab_bar(tab_ids, labels, colors, _switch_sub, width=320, height=22)
    
    mc.separator(h=4, style='none')
    content = mc.columnLayout(adjustableColumn=True, rowSpacing=2)
    state.reg('mecha_sub_content', content)
    mc.setParent('..')
    
    _render_general()


def _switch_sub(tab_id):
    _current_sub[0] = tab_id
    content = state.get('mecha_sub_content')
    if not content or not mc.control(content, exists=True):
        return
    
    children = mc.columnLayout(content, q=True, childArray=True) or []
    for c in children:
        try:
            mc.deleteUI(c)
        except Exception:
            pass
    
    mc.setParent(content)
    if tab_id == 'general':
        _render_general()
    else:
        _render_module(tab_id)
    mc.setParent('..')


def _render_general():
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    
    path = Path(__file__).resolve().parent.parent.parent / 'config' / 'presets.json'
    try:
        with open(path, encoding='utf-8') as f:
            pdata = {k: v for k, v in json.load(f).items() if not k.startswith('_')}
    except Exception:
        pdata = {}
    labels = {data.get('_name', key): key for key, data in pdata.items()}

    mc.rowLayout(nc=2, cw2=[100, 220])
    mc.text(label='Preset', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu()
    mc.menuItem(label='Custom')
    for l in labels:
        mc.menuItem(label=l)
    mc.optionMenu(menu, e=True, changeCommand=lambda val: (
        __import__('ui.build_actions', fromlist=['apply_mecha_preset']).apply_mecha_preset(labels.get(val, val))
    ))
    mc.setParent('..')
    state.reg('mecha_preset_menu', menu)

    state.reg('height_sl', fsl('Altura', 0.5, 2.0, 1.0, step=0.05,
                                on_cc=_on_mecha_cc, annotation='Escala vertical'))
    
    mc.separator(h=4)
    state.reg('sym_cb', mc.checkBox(
        label='Simetría', value=True,
        changeCommand=lambda *_: (_toggle_symmetry_ui(), _on_mecha_cc()),
    ))
    state.reg('arms_cb', mc.checkBox(label='Módulo Brazos', value=True, changeCommand=_on_mecha_cc))
    state.reg('wings_cb', mc.checkBox(label='Módulo Alas', value=True, changeCommand=_on_mecha_cc))
    state.reg('energy_cb', mc.checkBox(label='Anillos de energía', value=True, changeCommand=_on_mecha_cc))
    
    mc.setParent('..')


def _render_module(module):
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    
    labels = STYLE_MAPS.get(module, {})
    if labels:
        mc.rowLayout(nc=2, cw2=[100, 220])
        mc.text(label='Estilo', align='right', font='smallPlainLabelFont')
        menu = mc.optionMenu(changeCommand=_on_mecha_cc)
        for l in labels:
            mc.menuItem(label=l)
        mc.setParent('..')
        state.reg(f'{module}_style_menu', menu)
    
    for s in get_slider_specs(module):
        ctrl = fsl(s['label'], float(s['min']), float(s['max']), float(s['default']),
                   step=float(s.get('step', 0.02)), annotation=s.get('description', ''),
                   on_cc=_on_mecha_cc)
        mc.floatSliderGrp(ctrl, e=True, dragCommand=_on_mecha_cc)
        state.reg(f'{module}.{s["key"]}', ctrl)
    
    if module in ('arm', 'wing'):
        row = mc.rowLayout(nc=2, cw2=[100, 220], visible=False)
        state.reg(f'{module}_right_row', row)
        mc.text(label=f'{module.capitalize()} der.', align='right', font='smallPlainLabelFont')
        menu = mc.optionMenu(changeCommand=_on_mecha_cc)
        src_labels = ARM_STYLE_LABELS if module == 'arm' else WING_STYLE_LABELS
        for l in src_labels:
            mc.menuItem(label=l)
        mc.setParent('..')
        state.reg(f'{module}_style_right_menu', menu)
        if not state._UI_BUILDING[0]:
            sym = state.get('sym_cb')
            if sym and mc.control(sym, exists=True):
                on = mc.checkBox(sym, q=True, value=True)
                mc.control(row, e=True, visible=not on)
    
    mc.setParent('..')


def _on_mecha_cc(*_):
    if state._UI_BUILDING[0] or state._APPLYING_MECHA_PRESET[0]:
        return
    rebuild_mecha()
