"""Modo Rapido: compact scene generation controls."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.build_actions import (
    random_all, on_reset, random_mecha, rebuild_terrain_only,
)
from ui.panels.material_panel import apply_palette_quick
from ui.panels.animation_panel import apply_animation_quick

_PALETTES = {
    'Industrial': ([0.55, 0.54, 0.51], 'industrial'),
    'Oxidado': ([0.55, 0.30, 0.15], 'oxidado'),
    'Artico': ([0.30, 0.55, 0.75], 'artico'),
    'Carmesi': ([0.65, 0.22, 0.35], 'carmesi'),
}

_ACTIVE_SWATCH = [None]


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mc.rowLayout(nc=2, cw2=[165, 165],
                 columnAttach2=['both', 'both'])
    widgets.secondary_button('Aleatorio', [0.35, 0.20, 0.40], random_all, height=32)
    widgets.secondary_button('Reset', widgets.ACCENT_DANGER, on_reset, height=32)
    mc.setParent('..')
    mc.separator(h=8, style='none')

    widgets.section_title('Mecha')
    widgets.big_button(
        'Generar Mecha Aleatorio',
        widgets.ACCENT_RAND,
        lambda *_: random_mecha(),
        height=42,
    )
    mc.separator(h=6, style='none')

    widgets.section_title('Escenario')
    widgets.big_button(
        'Generar Escenario Aleatorio',
        widgets.ACCENT_RAND,
        lambda *_: _random_terrain_and_build(),
        height=42,
    )
    mc.separator(h=8, style='none')

    widgets.section_title('Estilo')
    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80],
                 columnAttach4=['both', 'both', 'both', 'both'],
                 columnOffset4=[2, 2, 2, 2])
    swatch_btns = {}
    for name, (color, key) in _PALETTES.items():
        btn = widgets.swatch_button(
            color,
            lambda *_, k=key, n=name: _select_swatch(n, k, swatch_btns),
            size=30,
        )
        swatch_btns[name] = (btn, color)
    mc.setParent('..')

    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80],
                 columnAttach4=['both', 'both', 'both', 'both'])
    for name in _PALETTES:
        mc.text(label=name, align='center', font='smallPlainLabelFont')
    mc.setParent('..')
    mc.separator(h=8, style='none')

    mc.text(label='MOVIMIENTO', align='left', font='smallPlainLabelFont')
    coll = mc.radioCollection()
    mc.rowLayout(nc=3, cw3=[105, 105, 105])
    rb_map = {}
    for key, label in [('idle', 'Idle'), ('flight', 'Vuelo'), ('spin', 'Spin')]:
        rb = mc.radioButton(label=label,
                            onCommand=lambda *_, k=key: apply_animation_quick(k))
        rb_map[key] = rb
    mc.setParent('..')
    active = state._ACTIVE_ANIM[0]
    if active in rb_map:
        mc.radioCollection(coll, e=True, select=rb_map[active])

    mc.separator(h=6, style='none')
    mc.setParent('..')


def _select_swatch(name, palette_key, btns_map):
    for _name, (btn, original_color) in btns_map.items():
        mc.button(btn, e=True, backgroundColor=original_color)

    btn, original = btns_map[name]
    mc.button(btn, e=True, backgroundColor=[max(0.05, c - 0.18) for c in original])
    _ACTIVE_SWATCH[0] = name
    state._QUICK_PALETTE[0] = palette_key
    apply_palette_quick(palette_key)


def _random_terrain_and_build(*_):
    from ui.build_actions import randomize_terrain_controls
    randomize_terrain_controls()
    rebuild_terrain_only()
