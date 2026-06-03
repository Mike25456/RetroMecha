"""Build orchestration for RetroMecha UI — generar, random, presets, reset."""

import json
import random
from pathlib import Path

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, scene_utils as sc
from ui.constants import (
    HEAD_STYLE_LABELS, ARM_STYLE_LABELS, WING_STYLE_LABELS,
    TORSO_STYLE_LABELS, NUCLEUS_STYLE_LABELS, TERRAIN_PRESET_MAP,
)
from ui.module_advanced import get_slider_specs


# ── helpers ──────────────────────────────────────────────────

def _resolve_seed():
    txt = mc.textField(state.get('seed_field'), q=True, text=True).strip()
    if txt.isdigit():
        seed = int(txt)
    else:
        seed = random.randint(0, 99999)
        mc.textField(state.get('seed_field'), e=True, text=str(seed))
    state._SEED[0] = seed
    return seed


# ── collect ──────────────────────────────────────────────────

def _collect_mecha():
    def _val(name):
        return mc.floatSliderGrp(state.get(name), q=True, value=True)

    def _ival(name):
        return mc.intSliderGrp(state.get(name), q=True, value=True)

    def _opt(ctrl_name):
        return mc.optionMenu(state.get(ctrl_name), q=True, value=True)

    def _cb(name):
        return mc.checkBox(state.get(name), q=True, value=True)

    adv = {}
    for module in ('head', 'arm', 'wing', 'torso', 'nucleus'):
        for spec in get_slider_specs(module):
            key = f'{module}.{spec["key"]}'
            ctrl = state.get(key)
            if ctrl:
                adv[spec['key']] = mc.floatSliderGrp(ctrl, q=True, value=True)

    return {
        'height_scale': _val('height_sl'),
        'symmetry': _cb('sym_cb'),
        'use_head': True,
        'use_arms': _cb('arms_cb'),
        'use_wings': _cb('wings_cb'),
        'use_energy_fields': _cb('energy_cb'),
        'head_style': HEAD_STYLE_LABELS.get(_opt('head_style_menu'), 'helmet'),
        'arm_style': ARM_STYLE_LABELS.get(_opt('arm_style_menu'), 'standard'),
        'arm_style_right': ARM_STYLE_LABELS.get(_opt('arm_style_right_menu')),
        'wing_style': WING_STYLE_LABELS.get(_opt('wing_style_menu'), 'needle'),
        'wing_style_right': WING_STYLE_LABELS.get(_opt('wing_style_right_menu')),
        'torso_style': TORSO_STYLE_LABELS.get(_opt('torso_style_menu'), 'core'),
        'nucleus_style': NUCLEUS_STYLE_LABELS.get(_opt('nucleus_style_menu'), 'ring'),
        **adv,
    }


def _collect_terrain():
    result = {
        'monument_scale': mc.floatSliderGrp(state.get('t_mon_sl'), q=True, value=True),
        'platform_count': mc.intSliderGrp(state.get('t_plat_sl'), q=True, value=True),
        'fragment_count': mc.intSliderGrp(state.get('t_frag_sl'), q=True, value=True),
        'debris_count': mc.intSliderGrp(state.get('t_deb_sl'), q=True, value=True),
        'pillar_count': mc.intSliderGrp(state.get('t_pil_sl'), q=True, value=True),
        'ramp_probability': mc.floatSliderGrp(state.get('t_ramp_sl'), q=True, value=True),
        'ring_max_r': mc.floatSliderGrp(state.get('t_ring_sl'), q=True, value=True),
    }
    if state.get('t_sky_n_sl'):
        result['skyline_count'] = mc.intSliderGrp(state.get('t_sky_n_sl'), q=True, value=True)
    if state.get('t_sky_z_sl'):
        result['skyline_distance_z'] = mc.floatSliderGrp(state.get('t_sky_z_sl'), q=True, value=True)
    if state.get('t_sky_sp_sl'):
        result['skyline_spread_x'] = mc.floatSliderGrp(state.get('t_sky_sp_sl'), q=True, value=True)
    return result


def _collect_terrain_params(seed, support_edges=True):
    return {
        '_seed': seed + 1000,
        'height_scale': 1.0,
        'use_support_edges': support_edges,
    }


# ── build ────────────────────────────────────────────────────

def _build_mecha(seed, support_edges=True):
    params = _collect_mecha()
    params['_seed'] = seed
    params['use_support_edges'] = support_edges
    from core.mecha_builder import MechaBuilder
    grp = MechaBuilder(params, seed=seed).build()
    if grp and mc.objExists(grp):
        sc.lift_mecha(grp)
        mc.makeIdentity(grp, apply=True, translate=True, rotate=True, scale=True,
                        normal=False, preserveNormals=True)
    return grp


def _build_terrain(seed, support_edges=True):
    preset_label = mc.optionMenu(state.get('t_preset_menu'), q=True, value=True)
    preset_name = TERRAIN_PRESET_MAP.get(preset_label, 'avanzada')
    overrides = _collect_terrain()
    from terrain.terrain_builder import TerrainBuilder
    tb = TerrainBuilder(
        params=_collect_terrain_params(seed, support_edges=support_edges),
        seed=seed + 1000,
        preset_name=preset_name,
        mecha_bbox=sc.mecha_bbox(),
    )
    tb.preset.update(overrides)
    return tb.build()


# ── rebuild ──────────────────────────────────────────────────

def rebuild_mecha(*_):
    def _work():
        seed = state._SEED[0] if isinstance(state._SEED[0], int) else _resolve_seed()
        state._SEED[0] = seed
        sc.clean_mecha()
        grp = _build_mecha(seed, support_edges=False)
        if grp and mc.objExists(grp):
            sc.parent_to_scene(grp)
            sc.mark_undelimited(sc.find_scene_group() or grp)
            mc.select(grp)
    return sc.scene_update(_work)


def rebuild_terrain_only(*_):
    def _work():
        seed = state._SEED[0] if isinstance(state._SEED[0], int) else _resolve_seed()
        state._SEED[0] = seed
        sc.clean_terrain()
        grp = _build_terrain(seed, support_edges=False)
        if grp and mc.objExists(grp):
            sc.parent_to_scene(grp)
            sc.mark_undelimited(sc.find_scene_group() or grp)
            mc.select(grp)
    return sc.scene_update(_work)


# ── generar ──────────────────────────────────────────────────

def on_generar(*_):
    def _work():
        seed = _resolve_seed()
        sc.clean_scene()
        scene_grp = mc.group(empty=True, name='RetroMecha_Scene_#')
        mecha_grp = _build_mecha(seed, support_edges=False)
        if mecha_grp and mc.objExists(mecha_grp):
            mc.parent(mecha_grp, scene_grp)
        terrain_grp = _build_terrain(seed, support_edges=False)
        if terrain_grp and mc.objExists(terrain_grp):
            mc.parent(terrain_grp, scene_grp)

        # Lift default +6 en Y al mecha (replica el ajuste manual del setup)
        try:
            from utils.camera import lift_mecha_default
            lift_mecha_default()
        except Exception as e:
            print(f'[RetroMecha][Generar] Lift: {e}')

        # Camara default compo (se reposiciona contra el bbox actualizado)
        try:
            from utils.camera import create_default_camera
            create_default_camera(frame_mecha=True, look_through=True)
        except Exception as e:
            print(f'[RetroMecha][Generar] Camara: {e}')

        mc.select(scene_grp)
    return sc.scene_update(_work)


# ── random ───────────────────────────────────────────────────

def _random_module_adv(module):
    for spec in get_slider_specs(module):
        ctrl = state.get(f'{module}.{spec["key"]}')
        if ctrl:
            mc.floatSliderGrp(
                ctrl, e=True,
                value=random.uniform(float(spec['min']), float(spec['max'])),
            )


def _set_random_mecha_controls():
    """Set all mecha controls to random values (no rebuild triggered)."""
    mc.optionMenu(state.get('mecha_preset_menu'), e=True, value='Custom')
    mc.floatSliderGrp(state.get('height_sl'), e=True, value=random.uniform(0.50, 2.0))
    mc.checkBox(state.get('sym_cb'), e=True, value=random.choice([True, False]))
    mc.checkBox(state.get('arms_cb'), e=True, value=random.random() > 0.18)
    mc.checkBox(state.get('wings_cb'), e=True, value=random.random() > 0.28)
    mc.checkBox(state.get('energy_cb'), e=True, value=random.random() > 0.25)
    mc.optionMenu(state.get('head_style_menu'), e=True,
                  value=random.choice(list(HEAD_STYLE_LABELS.keys())))
    mc.optionMenu(state.get('arm_style_menu'), e=True,
                  value=random.choice(list(ARM_STYLE_LABELS.keys())))
    mc.optionMenu(state.get('arm_style_right_menu'), e=True,
                  value=random.choice(list(ARM_STYLE_LABELS.keys())))
    mc.optionMenu(state.get('wing_style_menu'), e=True,
                  value=random.choice(list(WING_STYLE_LABELS.keys())))
    mc.optionMenu(state.get('wing_style_right_menu'), e=True,
                  value=random.choice(list(WING_STYLE_LABELS.keys())))
    mc.optionMenu(state.get('torso_style_menu'), e=True,
                  value=random.choice(list(TORSO_STYLE_LABELS.keys())))
    mc.optionMenu(state.get('nucleus_style_menu'), e=True,
                  value=random.choice(list(NUCLEUS_STYLE_LABELS.keys())))
    for m in ('head', 'arm', 'wing', 'torso', 'nucleus'):
        _random_module_adv(m)


def random_mecha(*_):
    state._APPLYING_MECHA_PRESET[0] = True
    try:
        _set_random_mecha_controls()
    finally:
        state._APPLYING_MECHA_PRESET[0] = False
    _toggle_symmetry_ui()
    state._SEED[0] = random.randint(0, 99999)
    mc.textField(state.get('seed_field'), e=True, text=str(state._SEED[0]))
    rebuild_mecha()


def randomize_terrain_controls():
    state._APPLYING_TERRAIN_VALUES[0] = True
    try:
        mc.floatSliderGrp(state.get('t_mon_sl'), e=True, value=random.uniform(3.0, 9.0))
        mc.intSliderGrp(state.get('t_plat_sl'), e=True, value=random.randint(3, 16))
        mc.intSliderGrp(state.get('t_frag_sl'), e=True, value=random.randint(2, 24))
        mc.intSliderGrp(state.get('t_deb_sl'), e=True, value=random.randint(20, 150))
        mc.intSliderGrp(state.get('t_pil_sl'), e=True, value=random.randint(2, 16))
        mc.floatSliderGrp(state.get('t_ramp_sl'), e=True, value=random.uniform(0.0, 1.0))
        mc.floatSliderGrp(state.get('t_ring_sl'), e=True, value=random.uniform(10.0, 35.0))
        if state.get('t_sky_n_sl'):
            mc.intSliderGrp(state.get('t_sky_n_sl'), e=True, value=random.randint(1, 6))
        if state.get('t_sky_z_sl'):
            mc.floatSliderGrp(state.get('t_sky_z_sl'), e=True, value=random.uniform(-80.0, -30.0))
        if state.get('t_sky_sp_sl'):
            mc.floatSliderGrp(state.get('t_sky_sp_sl'), e=True, value=random.uniform(20.0, 70.0))
    finally:
        state._APPLYING_TERRAIN_VALUES[0] = False


def random_terrain(*_):
    randomize_terrain_controls()
    rebuild_terrain_only()


def random_all(*_):
    state._APPLYING_MECHA_PRESET[0] = True
    try:
        _set_random_mecha_controls()
        randomize_terrain_controls()
    finally:
        state._APPLYING_MECHA_PRESET[0] = False

    state._SEED[0] = random.randint(0, 99999)
    mc.textField(state.get('seed_field'), e=True, text=str(state._SEED[0]))
    on_generar()

    # Apply random color preset (aiStandardSurface) and sync UI
    from materials.presets import list_presets, apply_preset
    presets = list_presets()
    rand_preset = random.choice(presets) if presets else None
    if rand_preset:
        apply_preset(rand_preset)
        preset_menu = state.get('materials_preset_menu')
        if preset_menu and mc.optionMenu(preset_menu, exists=True):
            mc.optionMenu(preset_menu, e=True, value=rand_preset)

    mecha_grp = sc.find_mecha_group()

    # Reasignar shaders aiStandardSurface al mecha
    if mecha_grp:
        try:
            from materials.materializer import materialize_mecha
            materialize_mecha(mecha_grp)
        except Exception as e:
            print(f'[RetroMecha][Random] Materials: {e}')

    # Idle animation + playback
    if mecha_grp:
        from animations.registry import get_animation
        anim_cls = get_animation('idle')
        if anim_cls:
            try:
                anim_cls(mecha_grp).apply()
                mc.play(forward=True)
            except Exception as e:
                print(f'[RetroMecha][Random] Idle: {e}')


# ── reset ────────────────────────────────────────────────────

def on_reset(*_):
    def _work():
        sc.clean_scene()
        mc.textField(state.get('seed_field'), e=True, text='')
        state._SEED[0] = None
        print('[RetroMecha] Escena limpiada')
    return sc.scene_update(_work)


# ── preset ───────────────────────────────────────────────────

def _load_mecha_presets():
    path = Path(__file__).resolve().parent.parent / 'config' / 'presets.json'
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith('_')}
    except Exception as e:
        print(f'[RetroMecha] No se pudieron cargar presets de mecha: {e}')
        return {}


def apply_mecha_preset(key):
    preset = _load_mecha_presets().get(key)
    if not preset:
        return
    state._APPLYING_MECHA_PRESET[0] = True
    try:
        mc.floatSliderGrp(state.get('height_sl'), e=True,
                          value=preset.get('height_scale', 1.0))
        mc.checkBox(state.get('sym_cb'), e=True,
                    value=preset.get('symmetry', True))
        mc.checkBox(state.get('arms_cb'), e=True,
                    value=preset.get('use_arms', True))
        mc.checkBox(state.get('wings_cb'), e=True,
                    value=preset.get('use_wings', True))
        mc.checkBox(state.get('energy_cb'), e=True,
                    value=preset.get('use_energy_fields', True))
        sc.set_option_by_value(state.get('head_style_menu'), HEAD_STYLE_LABELS,
                               preset.get('head_style', 'helmet'))
        sc.set_option_by_value(state.get('arm_style_menu'), ARM_STYLE_LABELS,
                               preset.get('arm_style', 'standard'))
        arm_right = preset.get('arm_style_right')
        if arm_right:
            sc.set_option_by_value(state.get('arm_style_right_menu'), ARM_STYLE_LABELS, arm_right)
        sc.set_option_by_value(state.get('wing_style_menu'), WING_STYLE_LABELS,
                               preset.get('wing_style', 'needle'))
        wing_right = preset.get('wing_style_right')
        if wing_right:
            sc.set_option_by_value(state.get('wing_style_right_menu'), WING_STYLE_LABELS, wing_right)
        sc.set_option_by_value(state.get('torso_style_menu'), TORSO_STYLE_LABELS,
                               preset.get('torso_style', 'core'))
        sc.set_option_by_value(state.get('nucleus_style_menu'), NUCLEUS_STYLE_LABELS,
                               preset.get('nucleus_style', 'ring'))
        for module in ('head', 'arm', 'wing', 'torso', 'nucleus'):
            for spec in get_slider_specs(module):
                ctrl = state.get(f'{module}.{spec["key"]}')
                if ctrl and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
    finally:
        state._APPLYING_MECHA_PRESET[0] = False
    rebuild_mecha()


# ── symmetry toggle ──────────────────────────────────────────

def _toggle_symmetry_ui(*_):
    if state._UI_BUILDING[0]:
        return
    on = mc.checkBox(state.get('sym_cb'), q=True, value=True)
    for row_name in ('arm_right_row', 'wing_right_row'):
        row = state.get(row_name)
        if row and mc.control(row, exists=True):
            mc.control(row, e=True, visible=not on)
