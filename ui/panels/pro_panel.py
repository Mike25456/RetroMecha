"""Modo Pro — Tabs claros tipo navegación."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.build_actions import (
    rebuild_mecha, rebuild_terrain_only, random_mecha, random_terrain,
    random_all, on_reset, on_generar
)
from ui.panels import terrain_panel, material_panel, animation_panel
from ui.panels.mecha_panel_v2 import build_with_tabs

# Tabs principales: ID, Label, Color activo
_TABS = [
    ('mecha',     '◈  MECHA',     [0.18, 0.42, 0.28]),
    ('terrain',   '■  TERRENO',   [0.16, 0.32, 0.55]),
    ('materials', '●  MAT',       [0.55, 0.35, 0.12]),
    ('animation', '▲  ANIM',      [0.45, 0.20, 0.40]),
]

_current_tab = ['mecha']
_tab_buttons = {}


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    # ── Barra de Tabs (navegación principal) ───────────────
    mc.separator(h=6, style='none')
    _build_tab_bar()
    mc.separator(h=8, style='none')

    # ── Área de contenido dinámico ─────────────────────────
    content = mc.columnLayout(adjustableColumn=True, rowSpacing=4)
    state.reg('pro_content', content)
    mc.setParent('..')

    # ── Botones globales fijos abajo ───────────────────────
    mc.separator(h=8, style='single')
    mc.separator(h=6, style='none')
    mc.rowLayout(nc=3, cw3=[110, 110, 110],
                 columnAttach3=['both', 'both', 'both'])
    widgets.secondary_button('↺ Random Todo', [0.30, 0.15, 0.35], random_all)
    widgets.secondary_button('▶ Generar Todo', widgets.ACCENT_ACTION, on_generar, height=32)
    widgets.secondary_button('✕ Reset', widgets.ACCENT_DANGER, on_reset)
    mc.setParent('..')
    mc.separator(h=6, style='none')

    # Render inicial
    _render_tab('mecha')
    mc.setParent('..')


def _build_tab_bar():
    """Crea la barra de tabs. El activo tiene color, los demás gris."""
    n = len(_TABS)
    cw = 340 // n
    mc.rowLayout(nc=n,
                 columnWidth=[(i+1, cw) for i in range(n)],
                 columnAttach=[(i+1, 'both', 2) for i in range(n)])
    
    for i, (tid, label, active_color) in enumerate(_TABS):
        is_active = (_current_tab[0] == tid)
        bg = active_color if is_active else widgets.BG_HOVER
        
        btn = mc.button(
            label=label, height=28,
            backgroundColor=bg,
            command=lambda *_, t=tid: _switch_tab(t),
            annotation=f'Panel de {tid}',
        )
        _tab_buttons[tid] = btn
    mc.setParent('..')


def _switch_tab(tab_id):
    if tab_id == _current_tab[0]:
        return
    _current_tab[0] = tab_id
    
    # Actualizar colores de tabs
    for tid, label, active_color in _TABS:
        is_active = (tid == tab_id)
        mc.button(_tab_buttons[tid], e=True,
                  backgroundColor=active_color if is_active else widgets.BG_HOVER)
    
    # Reconstruir contenido
    content = state.get('pro_content')
    if not content or not mc.control(content, exists=True):
        return
    
    children = mc.columnLayout(content, q=True, childArray=True) or []
    for c in children:
        try:
            mc.deleteUI(c)
        except Exception:
            pass
    
    mc.setParent(content)
    _render_tab(tab_id)
    mc.setParent('..')


def _render_tab(tab_id):
    if tab_id == 'mecha':
        _render_mecha()
    elif tab_id == 'terrain':
        _render_terrain()
    elif tab_id == 'materials':
        _render_materials()
    elif tab_id == 'animation':
        _render_animation()


def _render_mecha():
    # Header de acciones del tab
    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'])
    widgets.secondary_button('🎲 Random Mecha', [0.20, 0.40, 0.28], random_mecha, height=30)
    widgets.secondary_button('▶ Reconstruir', [0.14, 0.36, 0.52], rebuild_mecha, height=30)
    mc.setParent('..')
    mc.separator(h=6, style='none')
    
    # Contenido del panel mecha con sub-tabs
    build_with_tabs(
        ['general', 'head', 'arm', 'torso', 'wing', 'nucleus'],
        ['General', 'Head', 'Arms', 'Torso', 'Wings', 'Nucleus'],
        [[0.18, 0.18, 0.20]] * 6
    )


def _render_terrain():
    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'])
    widgets.secondary_button('🎲 Random Terreno', [0.18, 0.32, 0.52], random_terrain, height=30)
    widgets.secondary_button('▶ Reconstruir', [0.14, 0.36, 0.52], rebuild_terrain_only, height=30)
    mc.setParent('..')
    mc.separator(h=6, style='none')
    terrain_panel.build()


def _render_materials():
    material_panel.build()


def _render_animation():
    animation_panel.build()