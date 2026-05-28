"""RetroMecha - main_window.py v5
Thin orchestrator — delegates section building to panel modules.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.scene_utils import on_delimitar
from ui.build_actions import on_generar, random_all, on_reset, _toggle_symmetry_ui
from ui.panels import mecha_panel, terrain_panel, animation_panel, material_panel

WIN_ID = 'RetroMechaWindow'


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

    state._UI_BUILDING[0] = True

    win = mc.window(WIN_ID, title='RetroMecha v5',
                    sizeable=True, resizeToFitChildren=True,
                    minimizeButton=True, maximizeButton=False,
                    width=360)

    mc.scrollLayout(childResizable=True)
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    # ── header ──────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(label='RETROMECHA - GENERADOR PROCEDURAL',
            font='boldLabelFont', align='center', h=28,
            backgroundColor=[0.08, 0.15, 0.25])
    mc.separator(h=6, style='in')

    # ── seed ────────────────────────────────────────────────
    mc.rowLayout(nc=2, cw2=[60, 280],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
    state.reg('seed_field', mc.textField(
        placeholderText='dejar vacío = aleatoria',
        editable=True,
        annotation='Número de semilla para reproducir generaciones',
    ))
    mc.setParent('..')
    mc.separator(h=8, style='none')

    # ── sections ────────────────────────────────────────────
    mecha_panel.build()
    terrain_panel.build()
    animation_panel.build()
    material_panel.build()

    # ── global buttons (bottom) ─────────────────────────────
    mc.separator(h=8, style='in')
    mc.rowLayout(nc=3, cw3=[114, 114, 114],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[3, 3, 3])
    mc.button(label='Generar', h=38,
              backgroundColor=[0.18, 0.42, 0.22],
              command=on_generar,
              annotation='Genera mecha + terreno con configuración actual')
    mc.button(label='Aleatorio', h=38,
              backgroundColor=[0.40, 0.20, 0.38],
              command=random_all,
              annotation='Valores aleatorios + genera escena completa')
    mc.button(label='Resetear', h=38,
              backgroundColor=[0.40, 0.16, 0.16],
              command=on_reset,
              annotation='Elimina todo de la escena')
    mc.setParent('..')

    mc.separator(h=4, style='none')
    mc.button(label='Delimitar escena', h=32,
              backgroundColor=[0.18, 0.34, 0.42],
              command=on_delimitar,
              annotation='Aplica aristas de soporte + smooth preview')

    mc.separator(h=6, style='none')

    state._UI_BUILDING[0] = False
    _toggle_symmetry_ui()
    mc.showWindow(win)
    print('[RetroMecha] UI v5 abierta')
