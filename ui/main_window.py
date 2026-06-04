"""RetroMecha — main_window.py v8.1
Header minimalista, switch prominente, footer limpio.
CRITICAL: try/finally en _switch_mode para nunca atorar _UI_BUILDING.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui import theme as T
from ui.build_actions import _safe_ctrl_exists
from ui.scene_utils import on_delimitar
from ui.widgets import mode_switch
from ui.panels import quick_panel, pro_panel

WIN_ID = 'RetroMechaWindow'

_mode_hint = [None]


def build_ui(*, recreate: bool = True):
    if not MAYA_AVAILABLE:
        print('[RetroMecha] Ejecutar dentro de Maya')
        return

    if mc.window(WIN_ID, exists=True):
        if not recreate:
            mc.showWindow(WIN_ID)
            return
        mc.deleteUI(WIN_ID, window=True)

    state.clear()
    state._UI_BUILDING[0] = True
    state._MODE[0] = 'quick'

    win = mc.window(WIN_ID, title='RetroMecha',
                    sizeable=True, resizeToFitChildren=False,
                    width=360, height=680,
                    backgroundColor=T.BG)

    mc.columnLayout(adjustableColumn=True, rowSpacing=0,
                    backgroundColor=T.BG)

    # ═══════════════════════════════════════════════════════
    # HEADER
    # ═══════════════════════════════════════════════════════
    mc.rowLayout(nc=2, cw2=[140, 220],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[6, 4],
                 backgroundColor=T.BG, height=36)
    mc.text(label='◈  RETROMECHA', font='boldLabelFont', align='left',
            backgroundColor=T.BG)
    
    mc.rowLayout(nc=2, cw2=[50, 100])
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
    state.reg('seed_field', mc.textField(
        width=90, height=18, placeholderText='auto',
        annotation='Semilla para reproducir generaciones',
    ))
    mc.setParent('..')
    mc.setParent('..')

    # ── SWITCH RÁPIDO / PRO ────────────────────────────────
    mc.separator(h=6, style='none', backgroundColor=T.BG)
    mode_switch(_switch_mode, active_mode='quick')
    T.sep()
    mc.separator(h=4, style='none')

    # ═══════════════════════════════════════════════════════
    # CONTENT
    # ═══════════════════════════════════════════════════════
    main_content = mc.columnLayout(adjustableColumn=True, rowSpacing=0)
    state.reg('main_content', main_content)
    quick_panel.build()
    mc.setParent('..')

    # ═══════════════════════════════════════════════════════
    # FOOTER
    # ═══════════════════════════════════════════════════════
    mc.separator(h=4, style='in')
    mc.rowLayout(nc=2, cw2=[180, 180],
                 columnAttach2=['both', 'both'])
    mc.button(label='◈ Delimitar Escena', h=26,
              backgroundColor=T.CYAN,
              command=on_delimitar)
    _mode_hint[0] = mc.text(label='Modo Rápido · 3 decisiones',
                            align='right', font='smallPlainLabelFont')
    mc.setParent('..')
    mc.separator(h=4, style='none')

    state._UI_BUILDING[0] = False
    mc.showWindow(win)
    print('[RetroMecha] UI v8.1 abierta')


def _switch_mode(mode):
    if state._UI_BUILDING[0] or mode == state._MODE[0]:
        return

    state._UI_BUILDING[0] = True

    state._MODE[0] = mode

    try:
        # 🔥 LIMPIAR controles del modo anterior para no tener referencias stale
        state.clear_dynamic()

        # Actualizar hint
        if _safe_ctrl_exists(_mode_hint[0]):
            label = 'Modo Rápido · aleatorio inmediato' if mode == 'quick' else 'Modo Pro · control total'
            mc.text(_mode_hint[0], e=True, label=label)

        main = state.get('main_content')
        if _safe_ctrl_exists(main):
            # Borrar todo lo que esté dentro de main
            children = mc.columnLayout(main, q=True, childArray=True) or []
            for c in children:
                if _safe_ctrl_exists(c):
                    try:
                        mc.deleteUI(c)
                    except Exception:
                        pass
            
            # Reconstruir desde main
            mc.setParent(main)
            if mode == 'quick':
                quick_panel.build()
            else:
                pro_panel.build()
            mc.setParent('..')

    except Exception as e:
        print(f'[RetroMecha] Error cambiando a {mode}: {e}')
    finally:
        state._UI_BUILDING[0] = False
