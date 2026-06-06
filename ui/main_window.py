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
from ui.build_actions import _safe_ctrl_exists, save_scene, load_scene, list_saved_scenes, delete_scene
from ui.scene_utils import on_delimitar
from ui.widgets import mode_switch
from ui.panels import quick_panel, pro_panel

WIN_ID = 'RetroMechaWindow'

_mode_hint = [None]
_SCENE_GUARD = [False]  # evita recursión al setear optionMenu programáticamente


def _on_scene_change(*_):
    if _SCENE_GUARD[0]:
        return
    menu = state.get('scene_menu')
    if not _safe_ctrl_exists(menu):
        return
    val = mc.optionMenu(menu, q=True, value=True)
    if val and val != 'auto':
        _SCENE_GUARD[0] = True
        try:
            load_scene(val)
        finally:
            _SCENE_GUARD[0] = False


def _do_save():
    result = mc.promptDialog(
        title='Guardar escena',
        message='Nombre para la escena:',
        button=['Guardar', 'Cancelar'],
        defaultButton='Guardar',
        cancelButton='Cancelar',
        dismissString='Cancelar',
    )
    if result == 'Guardar':
        name = mc.promptDialog(q=True, text=True).strip()
        if name:
            save_scene(name)
            _refresh_scene_menu(name)


def _do_delete():
    menu = state.get('scene_menu')
    if not _safe_ctrl_exists(menu):
        return
    val = mc.optionMenu(menu, q=True, value=True)
    if not val or val == 'auto':
        return
    result = mc.confirmDialog(
        title='Eliminar escena',
        message=f'¿Eliminar "{val}"?',
        button=['Eliminar', 'Cancelar'],
        defaultButton='Cancelar',
        cancelButton='Cancelar',
        dismissString='Cancelar',
    )
    if result == 'Eliminar':
        delete_scene(val)
        _refresh_scene_menu()


def _refresh_scene_menu(select_name=None):
    _SCENE_GUARD[0] = True
    try:
        menu = state.get('scene_menu')
        if not _safe_ctrl_exists(menu):
            return
        items = mc.optionMenu(menu, q=True, itemListLong=True) or []
        for item in items:
            try:
                mc.deleteUI(item)
            except Exception:
                pass
        mc.menuItem(label='auto', parent=menu)
        for name in list_saved_scenes():
            mc.menuItem(label=name, parent=menu)
        if select_name:
            try:
                mc.optionMenu(menu, e=True, value=select_name)
            except Exception:
                pass
    finally:
        _SCENE_GUARD[0] = False


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

    try:
        state._MODE[0] = 'quick'

        win = mc.window(WIN_ID, title='RetroMecha',
                        sizeable=True, resizeToFitChildren=False,
                        width=360, height=600,
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
        
        mc.rowLayout(nc=4, cw4=[40, 40, 110, 22])
        mc.button(label='Guardar', height=18, backgroundColor=T.PANEL,
                  command=lambda *_: _do_save())
        mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
        menu = mc.optionMenu(width=108, height=18, changeCommand=_on_scene_change,
                             annotation='Escenas guardadas — seleccionar para cargar')
        mc.menuItem(label='auto', parent=menu)
        state.reg('scene_menu', menu)
        mc.button(label='✕', width=22, height=18, backgroundColor=T.PANEL,
                  command=lambda *_: _do_delete())
        mc.setParent('..')
        mc.setParent('..')

        # ── SWITCH RÁPIDO / PRO ────────────────────────────────
        mc.separator(h=10, style='none', backgroundColor=T.BG)

        mc.rowLayout(nc=1, columnAttach=[(1, 'both', 4)], backgroundColor=T.BG)
        mc.text(label='MODO', align='center', font='boldLabelFont', backgroundColor=T.BG)
        mc.setParent('..')

        mc.separator(h=6, style='none')
        mc.rowLayout(nc=1, columnAttach=[(1, 'both', 4)], backgroundColor=T.BG)
        mode_switch(_switch_mode, active_mode='quick')
        mc.setParent('..')

        mc.separator(h=6, style='none')
        T.sep()
        mc.separator(h=20, style='none')

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

        _refresh_scene_menu()
        mc.showWindow(win)
        print('[RetroMecha] UI abierta')
    except Exception as e:
        print(f'[RetroMecha] Error construyendo UI: {e}')
    finally:
        state._UI_BUILDING[0] = False


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
