"""TERRENO section of the RetroMecha UI."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl, isl
from ui.build_actions import rebuild_terrain_only, random_terrain


def build():
    mc.frameLayout(
        label='  >  TERRENO',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.12, 0.22, 0.48],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    # ── preset ──
    mc.rowLayout(nc=2, cw2=[130, 178],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset escena', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(changeCommand=lambda *_: rebuild_terrain_only())
    for label in ('Avanzada', 'Hangar', 'Campo de batalla', 'Centinela'):
        mc.menuItem(label=label)
    mc.setParent('..')
    state.reg('t_preset_menu', menu)

    mc.separator(h=4)

    state.reg('t_mon_sl', fsl('Escala monumento', 3.0, 9.0, 5.5,
                               step=0.1, on_cc=rebuild_terrain_only,
                               annotation='Tamaño del monumento central'))
    state.reg('t_plat_sl', isl('N. plataformas', 3, 16, 8, on_cc=rebuild_terrain_only,
                                annotation='Cantidad de plataformas dispersas'))
    state.reg('t_frag_sl', isl('N. fragmentos', 2, 24, 12, on_cc=rebuild_terrain_only,
                                annotation='Fragmentos de terreno rotos'))
    state.reg('t_deb_sl', isl('Debris (piezas)', 20, 150, 80, on_cc=rebuild_terrain_only,
                               annotation='Escombros pequeños esparcidos'))
    state.reg('t_pil_sl', isl('Pilares', 2, 16, 8, on_cc=rebuild_terrain_only,
                               annotation='Columnas/pilares decorativos'))
    state.reg('t_ramp_sl', fsl('Prob. rampas', 0.0, 1.0, 0.55, on_cc=rebuild_terrain_only,
                                annotation='Probabilidad de generar rampas'))
    state.reg('t_ring_sl', fsl('Radio máx.', 8.0, 35.0, 22.0,
                                step=0.5, on_cc=rebuild_terrain_only,
                                annotation='Radio máximo de dispersion del terreno'))

    # ── skyline avanzado ──
    mc.separator(h=4)
    mc.frameLayout(label='  Skyline avanzado',
                   collapsable=True, collapse=True,
                   borderStyle='etchedIn', marginHeight=3, marginWidth=4)
    mc.columnLayout(adjustableColumn=True, rowSpacing=2)
    state.reg('t_sky_n_sl',  isl('N skylines', 1, 6, 3, on_cc=rebuild_terrain_only,
                                  annotation='Cantidad de franjas skyline al fondo'))
    state.reg('t_sky_z_sl',  fsl('Distancia Z', -80.0, -30.0, -55.0,
                                  step=1.0, on_cc=rebuild_terrain_only,
                                  annotation='Profundidad del skyline (mas negativo = mas lejos)'))
    state.reg('t_sky_sp_sl', fsl('Expansion X', 10.0, 80.0, 40.0,
                                  step=1.0, on_cc=rebuild_terrain_only,
                                  annotation='Ancho lateral del skyline'))
    mc.setParent('..')
    mc.setParent('..')

    mc.separator(h=6)
    mc.button(label='Aleatorio Terreno', h=28,
              backgroundColor=[0.22, 0.36, 0.60],
              command=lambda *_: _random_terrain(),
              annotation='Genera valores aleatorios para el terreno')

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')


def _random_terrain(*_):
    random_terrain()
