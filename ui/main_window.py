"""RetroMecha - main_window.py v6
Pestañas Escena (mecha + terreno + materiales aiStandardSurface)
y Rendering (iluminacion + camara).
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

    # ── Ventana sin resizeToFitChildren — formLayout controla el layout ──────
    # columnLayout como raiz NO estira la altura del tabLayout.
    # formLayout SI permite anclar el tabLayout al borde inferior de la ventana.
    win = mc.window(WIN_ID, title='RetroMecha v6',
                    sizeable=True, resizeToFitChildren=False,
                    minimizeButton=True, maximizeButton=False,
                    width=380, height=720)

    # formLayout raiz — es el unico layout que permite attachForm 'bottom'
    root_form = mc.formLayout()

    # ── Header (columnLayout dentro del form) ────────────────────────────────
    # Se mide por su contenido; el form lo ancla arriba.
    header = mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mc.separator(h=8, style='none')
    mc.text(label='RETROMECHA - GENERADOR PROCEDURAL',
            font='boldLabelFont', align='center', h=28,
            backgroundColor=[0.10, 0.30, 0.48])
    mc.separator(h=6, style='in')

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

    mc.setParent('..')  # cierra header (columnLayout) → vuelve a root_form

    # ── tabLayout — ocupa todo el espacio bajo el header ─────────────────────
    tabs = mc.tabLayout(innerMarginWidth=4, innerMarginHeight=4)

    # Tab 1: ESCENA
    escena_scroll = mc.scrollLayout(childResizable=True)
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mecha_panel.build()
    terrain_panel.build()
    animation_panel.build()
    material_panel.build()

    # botones globales
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
    mc.setParent('..')  # cierra columnLayout interno
    mc.setParent('..')  # cierra escena_scroll → vuelve a tabs

    # Tab 2: RENDERING
    rendering_scroll = mc.scrollLayout(childResizable=True)
    rendering_panel.build()
    mc.setParent('..')  # cierra rendering_scroll → vuelve a tabs

    # etiquetas de pestañas
    mc.tabLayout(tabs, edit=True,
                 tabLabel=((escena_scroll, 'Escena'),
                           (rendering_scroll, 'Rendering')))

    mc.setParent('..')  # cierra tabs → vuelve a root_form

    # ── Anclar con formLayout ─────────────────────────────────────────────────
    # header: pegado arriba, izquierda y derecha.
    # tabs:   pegado a izquierda, derecha y ABAJO; su borde superior toca header.
    # Resultado: tabs ocupa TODO el espacio restante — scrollLayout funciona.
    mc.formLayout(root_form, edit=True,
        attachForm=[
            (header, 'top',    0),
            (header, 'left',   0),
            (header, 'right',  0),
            (tabs,   'left',   0),
            (tabs,   'right',  0),
            (tabs,   'bottom', 0),
        ],
        attachControl=[(tabs, 'top', 0, header)],
    )

    state._UI_BUILDING[0] = False
    _toggle_symmetry_ui()

    try:
        from utils.camera import create_default_camera
        create_default_camera(frame_mecha=True, look_through=True)
    except Exception as e:
        print(f'[RetroMecha] Camera: {e}')

    mc.showWindow(win)
    print('[RetroMecha] UI v6 abierta (Escena | Rendering)')
