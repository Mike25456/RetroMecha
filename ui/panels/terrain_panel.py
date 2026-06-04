"""TERRENO section of the RetroMecha UI."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl, isl
from ui.build_actions import rebuild_terrain_only


def build(wrapped=True):
    if wrapped:
        mc.frameLayout(
            label='  >  TERRENO',
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            backgroundColor=[0.12, 0.22, 0.48],
            marginHeight=6, marginWidth=6,
        )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    params = state._TERRAIN_PARAMS

    mc.rowLayout(nc=2, cw2=[110, 210],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset escena', align='right', font='smallPlainLabelFont')
    menu = mc.optionMenu(changeCommand=lambda *_: rebuild_terrain_only())
    for label in ('Avanzada', 'Hangar', 'Campo de batalla', 'Centinela'):
        mc.menuItem(label=label)
    mc.setParent('..')
    state.reg('t_preset_menu', menu)

    mc.separator(h=4)
    state.reg('t_mon_sl', fsl(
        'Monumento', 3.0, 9.0, params.get('monument_scale', 5.5),
        step=0.1, on_cc=rebuild_terrain_only,
    ))
    state.reg('t_plat_sl', isl(
        'Plataformas', 3, 16, params.get('platform_count', 8),
        on_cc=rebuild_terrain_only,
    ))
    state.reg('t_frag_sl', isl(
        'Fragmentos', 2, 24, params.get('fragment_count', 12),
        on_cc=rebuild_terrain_only,
    ))
    state.reg('t_deb_sl', isl(
        'Debris', 20, 150, params.get('debris_count', 80),
        on_cc=rebuild_terrain_only,
    ))
    state.reg('t_pil_sl', isl(
        'Pilares', 2, 16, params.get('pillar_count', 8),
        on_cc=rebuild_terrain_only,
    ))
    state.reg('t_ramp_sl', fsl(
        'Rampas', 0.0, 1.0, params.get('ramp_probability', 0.55),
        on_cc=rebuild_terrain_only,
    ))
    state.reg('t_ring_sl', fsl(
        'Radio', 8.0, 35.0, params.get('ring_max_r', 22.0),
        step=0.5, on_cc=rebuild_terrain_only,
    ))

    mc.separator(h=4)
    mc.text(label='SKYLINE', align='left', font='smallPlainLabelFont')
    state.reg('t_sky_n_sl', isl(
        'Skylines', 1, 6, params.get('skyline_count', 3),
        on_cc=rebuild_terrain_only,
    ))
    state.reg('t_sky_z_sl', fsl(
        'Distancia Z', -80.0, -30.0, params.get('skyline_distance_z', -55.0),
        step=1.0, on_cc=rebuild_terrain_only,
    ))
    state.reg('t_sky_sp_sl', fsl(
        'Expansion X', 10.0, 80.0, params.get('skyline_spread_x', 40.0),
        step=1.0, on_cc=rebuild_terrain_only,
    ))

    mc.separator(h=4, style='none')
    mc.setParent('..')
    if wrapped:
        mc.setParent('..')
