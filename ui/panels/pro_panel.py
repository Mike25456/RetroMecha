"""Modo Pro: tabbed editing for all RetroMecha sections."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.build_actions import (
    rebuild_mecha, rebuild_terrain_only, random_mecha, random_terrain,
    random_all, on_reset, on_generar, _safe_ctrl_exists,
)
from ui.panels import terrain_panel, material_panel, animation_panel
from ui.panels.mecha_panel_v2 import build_with_tabs

_TABS = [
    ('mecha', 'MECHA', [0.18, 0.42, 0.28]),
    ('terrain', 'TERRENO', [0.16, 0.32, 0.55]),
    ('materials', 'MAT', [0.55, 0.35, 0.12]),
    ('animation', 'ANIM', [0.45, 0.20, 0.40]),
]

_current_tab = ['mecha']
_tab_buttons = {}


def build():
    _current_tab[0] = 'mecha'
    _tab_buttons.clear()

    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mc.rowLayout(nc=3, cw3=[110, 110, 110],
                 columnAttach3=['both', 'both', 'both'])
    widgets.secondary_button('Random Todo', [0.30, 0.15, 0.35], random_all, height=30)
    widgets.secondary_button('Generar Todo', widgets.ACCENT_ACTION, on_generar, height=30)
    widgets.secondary_button('Reset', widgets.ACCENT_DANGER, on_reset, height=30)
    mc.setParent('..')
    mc.separator(h=6, style='none')

    _build_tab_bar()
    mc.separator(h=8, style='none')

    content = mc.columnLayout(adjustableColumn=True, rowSpacing=4)
    state.reg('pro_content', content)

    _render_tab('mecha')
    mc.setParent('..')
    mc.setParent('..')


def _build_tab_bar():
    width = 340
    count = len(_TABS)
    cw = width // count
    mc.rowLayout(
        nc=count,
        columnWidth=[(i + 1, cw) for i in range(count)],
        columnAttach=[(i + 1, 'both', 2) for i in range(count)],
    )
    for tab_id, label, active_color in _TABS:
        is_active = tab_id == _current_tab[0]
        _tab_buttons[tab_id] = mc.button(
            label=label,
            height=28,
            backgroundColor=active_color if is_active else widgets.BG_HOVER,
            command=lambda *_, t=tab_id: _switch_tab(t),
        )
    mc.setParent('..')


def _clear_content(content):
    children = mc.columnLayout(content, q=True, childArray=True) or []
    for child in children:
        try:
            mc.deleteUI(child)
        except Exception:
            pass


def _switch_tab(tab_id):
    if tab_id == _current_tab[0]:
        return
    _current_tab[0] = tab_id

    for tid, _label, active_color in _TABS:
        btn = _tab_buttons.get(tid)
        if _safe_ctrl_exists(btn):
            mc.button(btn, e=True,
                      backgroundColor=active_color if tid == tab_id else widgets.BG_HOVER)

    content = state.get('pro_content')
    if not _safe_ctrl_exists(content):
        return

    _clear_content(content)
    mc.setParent(content)
    _render_tab(tab_id)
    mc.setParent('..')


def _render_tab(tab_id):
    if tab_id == 'mecha':
        _render_mecha()
    elif tab_id == 'terrain':
        _render_terrain()
    elif tab_id == 'materials':
        material_panel.build(wrapped=False)
    elif tab_id == 'animation':
        animation_panel.build(wrapped=False)


def _render_mecha():
    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'])
    widgets.secondary_button('Random Mecha', [0.20, 0.40, 0.28], random_mecha, height=30)
    widgets.secondary_button('Reconstruir', [0.14, 0.36, 0.52], rebuild_mecha, height=30)
    mc.setParent('..')
    mc.separator(h=6, style='none')

    build_with_tabs(
        ['general', 'head', 'arm', 'torso', 'wing', 'nucleus'],
        ['General', 'Head', 'Arms', 'Torso', 'Wings', 'Nucleus'],
        [[0.18, 0.18, 0.20]] * 6,
    )


def _render_terrain():
    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'])
    widgets.secondary_button('Random Terreno', [0.18, 0.32, 0.52], random_terrain, height=30)
    widgets.secondary_button('Reconstruir', [0.14, 0.36, 0.52], rebuild_terrain_only, height=30)
    mc.setParent('..')
    mc.separator(h=6, style='none')
    terrain_panel.build(wrapped=False)
