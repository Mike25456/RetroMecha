"""Modo Rápido — interfaz simplificada con 5 bloques de decisión."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.build_actions import on_generar, random_all, on_reset, apply_mecha_preset, random_mecha
from ui.panels.material_panel import apply_palette_quick
from ui.panels.animation_panel import apply_animation_quick, remove_animation_quick


_PROFILE_MAP = {
    'Explorador': 'balanced',
    'Centinela': 'sentinel',
    'Dron': 'aerial',
}

_PALETTES = {
    'Industrial': [0.55, 0.54, 0.51],
    'Oxidado':    [0.55, 0.30, 0.15],
    'Ártico':     [0.30, 0.55, 0.75],
    'Carmesí':    [0.65, 0.22, 0.35],
}

_PALETTE_KEYS = {
    'Industrial': 'industrial',
    'Oxidado': 'oxidado',
    'Ártico': 'artico',
    'Carmesí': 'carmesi',
}

_ACTIVE_PROFILE = [None]
_ACTIVE_PALETTE = [None]


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=6)

    # ── Bloque 1: Perfil de mecha ───────────────────────────
    mc.text(label='PERFIL DE MECHA', align='left', font='smallPlainLabelFont')

    _profile_btns = {}
    mc.rowColumnLayout(nc=2, columnWidth=[(1, 144), (2, 144)],
                        columnOffset=[(1, 'both', 4), (2, 'both', 4)],
                        rowSpacing=[(1, 4), (2, 4)])

    for name in ('Explorador', 'Centinela', 'Dron', 'Sorpréndeme'):
        bg = [0.14, 0.14, 0.16]
        cmd = lambda *_, n=name: _select_profile(n, _profile_btns)
        btn = mc.button(label=name, h=36, backgroundColor=bg, command=cmd,
                        annotation=f'Carga preset {name}')
        _profile_btns[name] = btn
        state._QUICK_PROFILE_BTNS[name] = btn

    mc.setParent('..')
    mc.separator(h=4, style='none')

    # ── Bloque 2: Ajustes rápidos ──────────────────────────
    mc.text(label='AJUSTES', align='left', font='smallPlainLabelFont')

    state.reg('height_sl', widgets.fsl(
        'Tamaño', 0.5, 2.0, 1.0, step=0.05,
        annotation='Escala vertical del mecha',
    ))

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Escenario', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(annotation='Selecciona un preset de escenario')
    for label in ('Avanzada', 'Hangar', 'Campo de batalla', 'Centinela'):
        mc.menuItem(label=label)
    mc.setParent('..')
    state.reg('t_preset_menu', menu)

    mc.separator(h=4, style='none')

    # ── Bloque 3: Paleta de color ──────────────────────────
    mc.text(label='PALETA DE COLOR', align='left', font='smallPlainLabelFont')

    _palette_btns = {}
    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80],
                 columnAttach4=['both', 'both', 'both', 'both'],
                 columnOffset4=[2, 2, 2, 2])

    for name, color in _PALETTES.items():
        cmd = lambda *_, n=name: _select_palette(n, _palette_btns)
        btn = mc.button(label=name, h=30, backgroundColor=color, command=cmd,
                        annotation=f'Paleta {name}')
        _palette_btns[name] = btn

    mc.setParent('..')
    mc.separator(h=4, style='none')

    # ── Bloque 4: Animación ────────────────────────────────
    mc.text(label='ANIMACIÓN', align='left', font='smallPlainLabelFont')

    coll = mc.radioCollection()
    state.reg('quick_anim_radio', coll)

    mc.rowLayout(nc=4, cw4=[72, 72, 72, 72],
                 columnAttach4=['both', 'both', 'both', 'both'],
                 columnOffset4=[2, 2, 2, 2])
    for name, label in [('ninguna', 'Ninguna'), ('idle', 'Idle'),
                        ('flight', 'Vuelo'), ('spin', 'Spin')]:
        if name == 'ninguna':
            cmd = lambda *_: remove_animation_quick()
        else:
            cmd = lambda *_, n=name: apply_animation_quick(n)
        mc.radioButton(label=label, h=24, onCommand=cmd,
                       annotation=f'Animación {label}')
    mc.setParent('..')

    mc.separator(h=4, style='none')

    # ── Bloque 5: Acciones ─────────────────────────────────
    mc.button(label='▶ Generar', h=38,
              backgroundColor=[0.10, 0.46, 0.26],
              command=on_generar,
              annotation='Genera escena completa con configuración actual')

    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[3, 3])
    mc.button(label='↺ Todo aleatorio', h=30, command=random_all,
              annotation='Valores aleatorios + genera escena')
    mc.button(label='✕ Resetear', h=30, command=on_reset,
              annotation='Elimina todo de la escena')
    mc.setParent('..')

    mc.setParent('..')


# ── profile selection ────────────────────────────────────────

def _select_profile(name, btns):
    prev = _ACTIVE_PROFILE[0]
    if prev and prev in btns:
        try:
            mc.button(btns[prev], e=True, backgroundColor=[0.14, 0.14, 0.16])
        except Exception:
            pass
    if name == 'Sorpréndeme':
        _ACTIVE_PROFILE[0] = None
        random_mecha()
        return
    _ACTIVE_PROFILE[0] = name
    btn = btns.get(name)
    if btn:
        try:
            mc.button(btn, e=True, backgroundColor=[0.10, 0.46, 0.26])
        except Exception:
            pass
    key = _PROFILE_MAP.get(name)
    if key:
        apply_mecha_preset(key)


# ── palette selection ────────────────────────────────────────

def _select_palette(name, btns):
    prev = _ACTIVE_PALETTE[0]
    if prev and prev in btns:
        try:
            mc.button(btns[prev], e=True, backgroundColor=_PALETTES.get(prev, [0.3, 0.3, 0.3]))
        except Exception:
            pass
    _ACTIVE_PALETTE[0] = name
    btn = btns.get(name)
    if btn:
        try:
            bg = _PALETTES.get(name, [0.3, 0.3, 0.3])
            darker = [max(0, c - 0.2) for c in bg]
            mc.button(btn, e=True, backgroundColor=darker)
        except Exception:
            pass
    key = _PALETTE_KEYS.get(name)
    if key:
        apply_palette_quick(key)
