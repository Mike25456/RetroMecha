"""MECHA section of the RetroMecha UI."""

import json
from pathlib import Path

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl
from ui.module_advanced import get_module_spec, get_slider_specs
from ui.build_actions import rebuild_mecha, random_mecha, apply_mecha_preset, _toggle_symmetry_ui

HEAD_STYLE_LABELS = {
    'Casco': 'helmet', 'Drone': 'drone', 'Centinela': 'sentinel',
}
ARM_STYLE_LABELS = {
    'Estandar': 'standard', 'Pesado': 'heavy',
    'Cuchilla': 'blade', 'Cañon': 'cannon',
}
WING_STYLE_LABELS = {
    'Agujas': 'needle', 'Compactas': 'compact', 'Abanico': 'fan',
}
TORSO_STYLE_LABELS = {
    'Base': 'core', 'Pesado': 'heavy', 'Delgado': 'slim', 'Compacto': 'compact',
}
NUCLEUS_STYLE_LABELS = {
    'Anillo': 'ring', 'Columna': 'column', 'Orbe': 'orb',
}

STYLE_MAPS = {
    'head': HEAD_STYLE_LABELS,
    'arm': ARM_STYLE_LABELS,
    'wing': WING_STYLE_LABELS,
    'torso': TORSO_STYLE_LABELS,
    'nucleus': NUCLEUS_STYLE_LABELS,
}


# ── helpers ──────────────────────────────────────────────────

def _on_mecha_cc(*_):
    if state._UI_BUILDING[0] or state._APPLYING_MECHA_PRESET[0]:
        return
    rebuild_mecha()


def _adv_section(module):
    spec = get_module_spec(module)
    if not spec:
        return
    mc.frameLayout(
        label=f'  {spec.get("frame_label", f"{module.capitalize()} — avanzado")}',
        collapsable=True, collapse=True,
        borderStyle='etchedIn', marginHeight=4, marginWidth=4,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=2)
    for s in get_slider_specs(module):
        ctrl = fsl(
            s['label'],
            float(s['min']), float(s['max']), float(s['default']),
            step=float(s.get('step', 0.02)),
            annotation=s.get('description', ''),
            on_cc=_on_mecha_cc,
        )
        mc.floatSliderGrp(ctrl, e=True, dragCommand=_on_mecha_cc)
        state.reg(f'{module}.{s["key"]}', ctrl)
    mc.setParent('..')
    mc.setParent('..')


def _style_row(label_text, ctrl_name, module_key):
    labels = STYLE_MAPS[module_key]
    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label=label_text, align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(changeCommand=_on_mecha_cc)
    for l in labels:
        mc.menuItem(label=l)
    mc.setParent('..')
    state.reg(ctrl_name, menu)


def _preset_row():
    path = Path(__file__).resolve().parent.parent.parent / 'config' / 'presets.json'
    try:
        with open(path, encoding='utf-8') as f:
            pdata = {k: v for k, v in json.load(f).items() if not k.startswith('_')}
    except Exception:
        pdata = {}
    labels = {data.get('_name', key): key for key, data in pdata.items()}

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset mecha', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu()
    mc.menuItem(label='Custom')
    for l in labels:
        mc.menuItem(label=l)
    mc.optionMenu(menu, e=True, changeCommand=lambda val: (
        apply_mecha_preset(labels.get(val, val))
    ))
    mc.setParent('..')
    state.reg('mecha_preset_menu', menu)


# ── build ────────────────────────────────────────────────────

def build():
    mc.frameLayout(
        label='  >  MECHA',
        collapsable=True, collapse=False,
        borderStyle='etchedIn',
        backgroundColor=[0.10, 0.36, 0.24],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    _preset_row()
    mc.separator(h=4)

    state.reg('height_sl', fsl(
        'Altura', 0.50, 2.0, 1.0, step=0.05, on_cc=_on_mecha_cc,
        annotation='Escala vertical del mecha',
    ))
    mc.floatSliderGrp(state.get('height_sl'), e=True, dragCommand=_on_mecha_cc)

    mc.separator(h=4)

    state.reg('sym_cb', mc.checkBox(
        label='Simetría', value=True,
        changeCommand=lambda *_: (_toggle_symmetry_ui(), _on_mecha_cc()),
        annotation='Mismo estilo de brazos/alas en ambos lados',
    ))
    state.reg('arms_cb', mc.checkBox(
        label='Módulo Brazos', value=True, changeCommand=_on_mecha_cc,
        annotation='Incluir brazos en el mecha',
    ))
    state.reg('wings_cb', mc.checkBox(
        label='Módulo Alas', value=True, changeCommand=_on_mecha_cc,
        annotation='Incluir alas en el mecha',
    ))
    state.reg('energy_cb', mc.checkBox(
        label='Anillos de energía', value=True, changeCommand=_on_mecha_cc,
        annotation='Anillos decorativos alrededor del torso',
    ))

    mc.separator(h=4)

    _style_row('Cabeza', 'head_style_menu', 'head')
    _adv_section('head')

    _style_row('Brazos', 'arm_style_menu', 'arm')
    rrow = mc.rowLayout(nc=2, cw2=[128, 180],
                         columnAttach2=['both', 'both'],
                         columnOffset2=[0, 4])
    state.reg('arm_right_row', rrow)
    mc.text(label='Brazo der.', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(changeCommand=_on_mecha_cc)
    for l in ARM_STYLE_LABELS:
        mc.menuItem(label=l)
    mc.setParent('..')
    state.reg('arm_style_right_menu', menu)
    _adv_section('arm')

    _style_row('Alas', 'wing_style_menu', 'wing')
    rrow = mc.rowLayout(nc=2, cw2=[128, 180],
                         columnAttach2=['both', 'both'],
                         columnOffset2=[0, 4])
    state.reg('wing_right_row', rrow)
    mc.text(label='Ala der.', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(changeCommand=_on_mecha_cc)
    for l in WING_STYLE_LABELS:
        mc.menuItem(label=l)
    mc.setParent('..')
    state.reg('wing_style_right_menu', menu)
    _adv_section('wing')

    _style_row('Torso', 'torso_style_menu', 'torso')
    _adv_section('torso')

    _style_row('Núcleo', 'nucleus_style_menu', 'nucleus')
    _adv_section('nucleus')

    mc.separator(h=6)
    mc.button(
        label='Aleatorio Mecha', h=28,
        backgroundColor=[0.20, 0.52, 0.34],
        command=lambda *_: random_mecha(),
        annotation='Genera valores aleatorios para todos los parámetros del mecha',
    )

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')
