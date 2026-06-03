"""RetroMecha - main_window.py v6
Pestañas Escena (mecha + terreno + materiales VP2.0) y Rendering (Arnold + luces).
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.scene_utils import on_delimitar
from ui.build_actions import on_generar, random_all, on_reset, _toggle_symmetry_ui
from ui.panels import (
    mecha_panel,
    terrain_panel,
    animation_panel,
    material_panel,
    rendering_panel,
)

WIN_ID = 'RetroMechaWindow'


def _clear_state():
    """Limpia el estado incluso si Maya conserva un ui.state viejo en cache."""
    if hasattr(state, 'clear'):
        state.clear()
        return
    try:
        state.CTRLS.clear()
        state._SEED[0] = None
        state._APPLYING_MECHA_PRESET[0] = False
        state._APPLYING_TERRAIN_VALUES[0] = False
        state._UI_BUILDING[0] = False
    except Exception:
        pass


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

    _clear_state()
    state._UI_BUILDING[0] = True

    # resizeToFitChildren=False + height explicito: el scrollLayout interno
    # tiene tamaño natural pequeño, asi que con resizeToFitChildren=True la
    # ventana se encogia y solo mostraba el primer panel.
    win = mc.window(WIN_ID, title='RetroMecha v6',
                    sizeable=True, resizeToFitChildren=False,
                    minimizeButton=True, maximizeButton=False,
                    width=380, height=720)

    root = mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    # ── header ──────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(label='RETROMECHA - GENERADOR PROCEDURAL',
            font='boldLabelFont', align='center', h=28,
            backgroundColor=[0.10, 0.30, 0.48])
    mc.separator(h=6, style='in')

    # ── seed (compartida entre pestañas) ────────────────────
    mc.rowLayout(nc=2, cw2=[60, 300],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
    state.reg('seed_field', mc.textField(
        placeholderText='dejar vacío = aleatoria',
        editable=True,
        annotation='Número de semilla para reproducir generaciones',
    ))
    mc.setParent('..')
    mc.separator(h=6, style='none')

    # ── tabs ────────────────────────────────────────────────
    tabs = mc.tabLayout(innerMarginWidth=4, innerMarginHeight=4)

    # ── Tab 1: ESCENA ────────────────────────────────────────
    escena_scroll = mc.scrollLayout(childResizable=True, parent=tabs)
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mecha_panel.build()
    terrain_panel.build()
    animation_panel.build()
    material_panel.build()

    # global buttons
    mc.separator(h=8, style='in')
    mc.rowLayout(nc=3, cw3=[118, 118, 118],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[3, 3, 3])
    mc.button(label='Generar', h=38,
              backgroundColor=[0.14, 0.56, 0.28],
              command=on_generar,
              annotation='Genera mecha + terreno con configuración actual')
    mc.button(label='Aleatorio', h=38,
              backgroundColor=[0.50, 0.20, 0.54],
              command=random_all,
              annotation='Valores aleatorios + genera escena completa')
    mc.button(label='Resetear', h=38,
              backgroundColor=[0.58, 0.16, 0.16],
              command=on_reset,
              annotation='Elimina todo de la escena')
    mc.setParent('..')

    mc.separator(h=4, style='none')
    mc.button(label='Delimitar escena', h=32,
              backgroundColor=[0.18, 0.34, 0.42],
              command=on_delimitar,
              annotation='Aplica aristas de soporte + smooth preview')

    mc.separator(h=6, style='none')
    mc.setParent('..')   # cierra columnLayout interno
    mc.setParent('..')   # cierra scrollLayout escena

    # ── Tab 2: RENDERING ────────────────────────────────────
    rendering_scroll = mc.scrollLayout(childResizable=True, parent=tabs)
    rendering_panel.build()
    mc.setParent('..')   # cierra scrollLayout rendering

    # ── etiquetas pestañas ──────────────────────────────────
    mc.tabLayout(tabs, edit=True,
                 tabLabel=((escena_scroll, 'Escena'),
                           (rendering_scroll, 'Rendering')))

    state._UI_BUILDING[0] = False
    # Se ejecuta una vez despues del build inicial para ocultar/mostrar filas
    # dependientes de simetria sin disparar rebuilds durante la construccion.
    _toggle_symmetry_ui()
    mc.showWindow(win)
    print('[RetroMecha] UI v6 abierta (Escena | Rendering)')
