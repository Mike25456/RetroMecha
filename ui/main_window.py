"""RetroMecha - main_window.py v6
Three-zone layout: permanent header, dynamic content, permanent footer.
Supports Rápido/Pro modes.
"""

import random as _random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.scene_utils import on_delimitar
from ui.widgets import mode_toggle
from ui.panels import quick_panel, pro_panel

WIN_ID = 'RetroMechaWindow'

_seed_row = [None]
_mode_hint = [None]


def build_ui(*, recreate: bool = True):
    if not MAYA_AVAILABLE:
        print('[RetroMecha] Ejecutar dentro de Maya')
        return

    if mc.window(WIN_ID, exists=True):
        if not recreate:
            mc.showWindow(WIN_ID)
            print('[RetroMecha] UI ya abierta')
            return
        mc.deleteUI(WIN_ID, window=True)

    state.clear()
    state._UI_BUILDING[0] = True
    state._MODE[0] = 'quick'

    win = mc.window(WIN_ID, title='RetroMecha v6',
                    sizeable=True, resizeToFitChildren=False,
                    minimizeButton=True, maximizeButton=False,
                    width=360, height=640)

    # ── HEADER: fondo oscuro fijo ──────────────────────────
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    bg = [0.07, 0.07, 0.12]
    mc.separator(h=6, style='none', backgroundColor=bg)
    header_row = mc.rowLayout(nc=3, cw3=[120, 140, 100],
                               columnAttach3=['both', 'both', 'both'],
                               columnOffset3=[4, 2, 2],
                               backgroundColor=bg,
                               height=30)
    mc.text(label='RETROMECHA', font='boldLabelFont', align='center',
            backgroundColor=bg)

    # - seed row (visible only in pro mode)
    seed_r = mc.rowLayout(nc=3, cw3=[48, 70, 26],
                           columnAttach3=['both', 'both', 'right'],
                           columnOffset3=[2, 2, 2],
                           backgroundColor=bg, visible=False)
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont',
            backgroundColor=bg)
    state.reg('seed_field', mc.textField(
        width=62, height=18,
        placeholderText='vacío=random',
        editable=True,
        annotation='Semilla para reproducir generaciones',
    ))
    mc.button(label='↺', h=18, width=24,
              backgroundColor=[0.15, 0.15, 0.18],
              command=lambda *_: (
                  mc.textField(state.get('seed_field'), e=True,
                               text=str(_random.randint(0, 99999)))
              ),
              annotation='Semilla aleatoria')
    mc.setParent('..')
    _seed_row[0] = seed_r

    # - mode toggle
    mode_toggle(_switch_mode)

    mc.setParent('..')
    mc.separator(h=5, style='none', backgroundColor=bg)
    mc.separator(h=4, style='in')

    # ── DYNAMIC CONTENT ──────────────────────────────────
    mc.scrollLayout(childResizable=True)
    main_content = mc.columnLayout(adjustableColumn=True, rowSpacing=0)
    state.reg('main_content', main_content)

    # build default (quick)
    quick_panel.build()
    state._MODE[0] = 'quick'

    mc.setParent('..')

    # ── FOOTER: Delimitar + mode hint ─────────────────────
    mc.separator(h=4, style='in')
    mc.rowLayout(nc=2, cw2=[160, 190],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[3, 3])
    mc.button(label='◈ Delimitar escena', h=28,
              backgroundColor=[0.18, 0.34, 0.42],
              command=on_delimitar,
              annotation='Aplica aristas de soporte + smooth preview')
    hint = mc.text(label='Modo Rápido · 5 decisiones',
                   align='right', font='smallPlainLabelFont')
    _mode_hint[0] = hint
    mc.setParent('..')

    mc.separator(h=4, style='none')

    state._UI_BUILDING[0] = False

    mc.showWindow(win)
    print('[RetroMecha] UI v6 abierta')


# ── mode switching ───────────────────────────────────────────

def _switch_mode(mode):
    if state._UI_BUILDING[0]:
        return
    if mode == state._MODE[0]:
        return

    # Preserve permanent header controls across mode switch
    saved_seed = state.get('seed_field')
    saved_main = state.get('main_content')

    state.clear()
    state._UI_BUILDING[0] = True
    state._MODE[0] = mode

    # Restore permanent controls
    if saved_seed:
        state.reg('seed_field', saved_seed)
    if saved_main:
        state.reg('main_content', saved_main)

    # show/hide seed row in header
    seed_row = _seed_row[0]
    if seed_row and mc.control(seed_row, exists=True):
        mc.control(seed_row, e=True, visible=(mode == 'pro'))

    # rebuild dynamic content
    main = saved_main
    if main and mc.control(main, exists=True):
        children = mc.columnLayout(main, q=True, childArray=True) or []
        if children:
            try:
                mc.deleteUI(children)
            except Exception:
                for c in children:
                    try:
                        mc.deleteUI(c)
                    except Exception:
                        pass

    if mode == 'quick':
        quick_panel.build()
    else:
        pro_panel.build()
        from ui.build_actions import _toggle_symmetry_ui
        _toggle_symmetry_ui()

    hint_ctrl = _mode_hint[0]
    if hint_ctrl and mc.control(hint_ctrl, exists=True):
        if mode == 'quick':
            mc.text(hint_ctrl, e=True, label='Modo Rápido · 5 decisiones')
        else:
            mc.text(hint_ctrl, e=True, label='Modo Pro · control total')

    state._UI_BUILDING[0] = False
