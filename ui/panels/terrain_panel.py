"""TERRENO section of the RetroMecha UI."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

import ui.theme as T
from ui import state
from ui.constants import TERRAIN_PRESET_MAP
from ui.widgets import fsl, isl, ACCENT_ACTION, BG_HOVER, button_grid
from ui.build_actions import (
    rebuild_terrain_only, rebuild_monument, rebuild_skyline,
    rebuild_platforms, rebuild_pillars, rebuild_fragments,
    rebuild_debris, rebuild_ramps,
)


def _on_terrain_preset_click(label):
    state._TERRAIN_PRESET[0] = label
    _update_terrain_btn_colors()
    rebuild_terrain_only()


def _update_terrain_btn_colors():
    active = state._TERRAIN_PRESET[0]
    for label in TERRAIN_PRESET_MAP:
        ctrl = state.get(f't_preset_btn_{label}')
        if ctrl and mc.control(ctrl, q=True, exists=True):
            mc.button(ctrl, e=True,
                      backgroundColor=ACCENT_ACTION if label == active else BG_HOVER)


def build(wrapped=True):
    if wrapped:
        mc.frameLayout(
            label='  >  TERRENO',
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            backgroundColor=T.PANEL,
            marginHeight=6, marginWidth=6,
        )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)
    params = state._TERRAIN_PARAMS

    mc.text(label='Preset escena', align='left', font='smallPlainLabelFont')
    active = state._TERRAIN_PRESET[0]
    presets = list(TERRAIN_PRESET_MAP.keys())

    def _tpreset_btn(item, _j, _i):
        lbl = item
        is_active = (lbl == active)
        btn = mc.button(
            label=lbl, height=24,
            backgroundColor=ACCENT_ACTION if is_active else BG_HOVER,
            command=lambda *_, l=lbl: _on_terrain_preset_click(l),
        )
        state.reg(f't_preset_btn_{lbl}', btn)

    button_grid(presets, cols=4, btn_width=80, btn_height=24, on_build=_tpreset_btn)

    mc.separator(h=4)
    state.reg('t_mon_sl', fsl(
        'Monumento', 3.0, 9.0, params.get('monument_scale', 5.5),
        step=0.1, on_cc=rebuild_monument, on_drag=lambda *_: None,
    ))
    state.reg('t_plat_sl', isl(
        'Plataformas', 3, 16, params.get('platform_count', 8),
        on_cc=rebuild_platforms, on_drag=lambda *_: None,
    ))
    state.reg('t_frag_sl', isl(
        'Fragmentos', 2, 24, params.get('fragment_count', 12),
        on_cc=rebuild_fragments, on_drag=lambda *_: None,
    ))
    state.reg('t_deb_sl', isl(
        'Escombros', 20, 150, params.get('debris_count', 80),
        on_cc=rebuild_debris, on_drag=lambda *_: None,
    ))
    state.reg('t_pil_sl', isl(
        'Pilares', 2, 16, params.get('pillar_count', 8),
        on_cc=rebuild_pillars, on_drag=lambda *_: None,
    ))
    state.reg('t_ramp_sl', fsl(
        'Rampas', 0.0, 1.0, params.get('ramp_probability', 0.55),
        on_cc=rebuild_ramps, on_drag=lambda *_: None,
    ))
    state.reg('t_ring_sl', fsl(
        'Radio', 8.0, 35.0, params.get('ring_max_r', 22.0),
        step=0.5, on_cc=rebuild_terrain_only, on_drag=lambda *_: None,
    ))

    mc.separator(h=4)
    mc.text(label='Horizonte', align='left', font='smallPlainLabelFont')
    state.reg('t_sky_n_sl', isl(
        'Edificios', 1, 6, params.get('skyline_count', 3),
        on_cc=rebuild_skyline, on_drag=lambda *_: None,
    ))
    state.reg('t_sky_z_sl', fsl(
        'Distancia Z', -80.0, -30.0, params.get('skyline_distance_z', -55.0),
        step=1.0, on_cc=rebuild_skyline, on_drag=lambda *_: None,
    ))
    state.reg('t_sky_sp_sl', fsl(
        'Expansión X', 10.0, 80.0, params.get('skyline_spread_x', 40.0),
        step=1.0, on_cc=rebuild_skyline, on_drag=lambda *_: None,
    ))

    mc.separator(h=4, style='none')
    mc.setParent('..')
    if wrapped:
        mc.setParent('..')
