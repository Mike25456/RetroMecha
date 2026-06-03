"""Modo Rápido — 3 decisiones visuales + aleatoriedad."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.build_actions import on_generar, random_all, on_reset, random_mecha, rebuild_terrain_only
from ui.panels.material_panel import apply_palette_quick
from ui.panels.animation_panel import apply_animation_quick, remove_animation_quick

_PALETTES = {
    'Industrial': ([0.55, 0.54, 0.51], 'industrial'),
    'Oxidado':    ([0.55, 0.30, 0.15], 'oxidado'),
    'Ártico':     ([0.30, 0.55, 0.75], 'artico'),
    'Carmesí':    ([0.65, 0.22, 0.35], 'carmesi'),
}

_ACTIVE_SWATCH = [None]


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    # ── 1. MECHA ───────────────────────────────────────────
    widgets.section_title('Mecha')
    mc.separator(h=4, style='none')
    
    # Botón gigante de aleatoriedad mecha
    widgets.big_button(
        '🎲  GENERAR MECHA ALEATORIO',
        widgets.ACCENT_RAND,
        lambda *_: random_mecha(),
        height=48,
        annotation='Crea un mecha completamente aleatorio',
    )
    mc.separator(h=6, style='none')

    # ── 2. ESCENARIO ───────────────────────────────────────
    widgets.section_title('Escenario')
    mc.separator(h=4, style='none')
    
    widgets.big_button(
        '🎲  GENERAR ESCENARIO ALEATORIO',
        widgets.ACCENT_RAND,
        lambda *_: _random_terrain_and_build(),
        height=48,
        annotation='Crea un escenario procedural aleatorio',
    )
    
    # Preset sutil debajo
    mc.rowLayout(nc=2, cw2=[90, 230],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])
    mc.text(label='Base', align='right', font='smallPlainLabelFont',
            annotation='Tipo de escenario base (afecta la arquitectura general)')
    menu = mc.optionMenu(annotation='Preset de escenario base')
    for label in ('Avanzada', 'Hangar', 'Campo de batalla', 'Centinela'):
        mc.menuItem(label=label)
    mc.setParent('..')
    state.reg('t_preset_menu', menu)
    mc.separator(h=8, style='none')

    # ── 3. ESTILO ──────────────────────────────────────────
    widgets.section_title('Estilo')
    
    # Paletas de color (swatches cuadrados sin texto)
    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80],
                 columnAttach4=['both', 'both', 'both', 'both'],
                 columnOffset4=[2, 2, 2, 2])
    _swatch_btns = {}
    for name, (color, key) in _PALETTES.items():
        # Borde de selección: cuando está activo, lo oscurecemos
        btn = widgets.swatch_button(color, lambda *_, k=key, n=name: _select_swatch(n, k, _swatch_btns), size=36)
        _swatch_btns[name] = (btn, color)
    mc.setParent('..')
    
    # Labels debajo de swatches
    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80],
                 columnAttach4=['both', 'both', 'both', 'both'])
    for name in _PALETTES:
        mc.text(label=name, align='center', font='smallPlainLabelFont')
    mc.setParent('..')
    mc.separator(h=8, style='none')

    # Animación
    mc.text(label='MOVIMIENTO', align='left', font='smallPlainLabelFont')
    mc.separator(h=2, style='none')
    coll = mc.radioCollection()
    state.reg('quick_anim_radio', coll)
    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80])
    mc.radioButton(label='Ninguna', select=True,
                   onCommand=lambda *_: remove_animation_quick())
    for key, lbl in [('idle', 'Idle'), ('flight', 'Vuelo'), ('spin', 'Spin')]:
        mc.radioButton(label=lbl,
                       onCommand=lambda *_, k=key: apply_animation_quick(k))
    mc.setParent('..')
    mc.separator(h=12, style='none')

    # ── ACCIÓN PRINCIPAL ───────────────────────────────────
    mc.separator(h=4, style='single')
    mc.separator(h=8, style='none')
    
    widgets.big_button(
        '▶  DESPLEGAR ESCENA COMPLETA',
        widgets.ACCENT_ACTION,
        on_generar,
        height=52,
        annotation='Genera mecha + terreno + materiales con la configuración actual',
    )
    mc.separator(h=6, style='none')

    # Acciones secundarias
    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[3, 3])
    widgets.secondary_button('✨ Todo Aleatorio', [0.35, 0.20, 0.40], random_all)
    widgets.secondary_button('✕ Limpiar Escena', widgets.ACCENT_DANGER, on_reset)
    mc.setParent('..')

    mc.separator(h=8, style='none')
    mc.setParent('..')


def _select_swatch(name, palette_key, btns_map):
    """Marca visualmente el swatch activo oscureciéndolo."""
    # Restaurar todos
    for n, (btn, original_color) in btns_map.items():
        mc.button(btn, e=True, backgroundColor=original_color)
    
    # Oscurecer seleccionado
    btn, orig = btns_map[name]
    darker = [max(0.05, c - 0.18) for c in orig]
    mc.button(btn, e=True, backgroundColor=darker)
    _ACTIVE_SWATCH[0] = name
    state._QUICK_PALETTE[0] = palette_key
    
    apply_palette_quick(palette_key)


def _random_terrain_and_build(*_):
    """Wrapper para randomizar terreno respetando el preset actual."""
    from ui.build_actions import randomize_terrain_controls
    randomize_terrain_controls()
    rebuild_terrain_only()
