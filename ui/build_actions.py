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

# ── safe control access (mode-agnostic) ──────────────────────

def _safe_val(name, default=1.0):
    ctrl = state.get(name)
    if not ctrl:
        return default
    try:
        if mc.control(ctrl, exists=True):
            return mc.floatSliderGrp(ctrl, q=True, value=True)
    except Exception:
        pass
    return default


def _safe_int(name, default=8):
    ctrl = state.get(name)
    if not ctrl:
        return default
    try:
        if mc.control(ctrl, exists=True):
            return mc.intSliderGrp(ctrl, q=True, value=True)
    except Exception:
        pass
    return default


def _safe_opt(name, default_label=None):
    ctrl = state.get(name)
    if not ctrl:
        return default_label
    try:
        if mc.control(ctrl, exists=True):
            return mc.optionMenu(ctrl, q=True, value=True)
    except Exception:
        pass
    return default_label


def _safe_cb(name, default=True):
    ctrl = state.get(name)
    if not ctrl:
        return default
    try:
        if mc.control(ctrl, exists=True):
            return mc.checkBox(ctrl, q=True, value=True)
    except Exception:
        pass
    return default


def _safe_set_opt(name, value):
    ctrl = state.get(name)
    if not ctrl:
        return
    try:
        if mc.control(ctrl, exists=True):
            mc.optionMenu(ctrl, e=True, value=value)
    except Exception:
        pass


def _safe_set_val(name, value):
    ctrl = state.get(name)
    if not ctrl:
        return
    try:
        if mc.control(ctrl, exists=True):
            mc.floatSliderGrp(ctrl, e=True, value=value)
    except Exception:
        pass


def _safe_set_int(name, value):
    ctrl = state.get(name)
    if not ctrl:
        return
    try:
        if mc.control(ctrl, exists=True):
            mc.intSliderGrp(ctrl, e=True, value=value)
    except Exception:
        pass


def _safe_set_cb(name, value):
    ctrl = state.get(name)
    if not ctrl:
        return
    try:
        if mc.control(ctrl, exists=True):
            mc.checkBox(ctrl, e=True, value=value)
    except Exception:
        pass


def _safe_set_txt(name, value):
    ctrl = state.get(name)
    if not ctrl:
        return
    try:
        if mc.control(ctrl, exists=True):
            mc.textField(ctrl, e=True, text=str(value))
    except Exception:
        pass


# ── centralized control existence check ──────────────────────

def _safe_ctrl_exists(ctrl):
    """Check if a raw Maya control handle exists. Never raises."""
    if not ctrl:
        return False
    try:
        return mc.control(ctrl, exists=True)
    except Exception:
        return False


def _safe_exists(name):
    """Check a state-registered control by name. Never raises."""
    return _safe_ctrl_exists(state.get(name))


# ── helpers ──────────────────────────────────────────────────

def _resolve_seed():
    ctrl = state.get('seed_field')
    if _safe_ctrl_exists(ctrl):
        txt = mc.textField(ctrl, q=True, text=True).strip()
        if txt.isdigit():
            seed = int(txt)
        else:
            seed = random.randint(0, 99999)
            mc.textField(ctrl, e=True, text=str(seed))
    else:
        seed = random.randint(0, 99999)
    state._SEED[0] = seed
    return seed


# ── collect ──────────────────────────────────────────────────

def _collect_mecha():
    params = {
        'height_scale': 1.0,
        'symmetry': True,
        'use_head': True,
        'use_arms': True,
        'use_wings': True,
        'use_energy_fields': True,
        'head_style': 'helmet',
        'arm_style': 'standard',
        'arm_style_right': None,
        'wing_style': 'needle',
        'wing_style_right': None,
        'torso_style': 'core',
        'nucleus_style': 'ring',
    }
    params.update(state._MECHA_PARAMS)

    adv = {}
    for module in ('head', 'arm', 'wing', 'torso', 'nucleus'):
        for spec in get_slider_specs(module):
            key = f'{module}.{spec["key"]}'
            ctrl = state.get(key)
            if _safe_ctrl_exists(ctrl):
                adv[spec['key']] = mc.floatSliderGrp(ctrl, q=True, value=True)

    params.update({
        'height_scale': _safe_val('height_sl', params.get('height_scale', 1.0)),
        'symmetry': params.get('symmetry', True),
        'use_head': True,
        'use_arms': params.get('use_arms', True),
        'use_wings': params.get('use_wings', True),
        'use_energy_fields': params.get('use_energy_fields', True),
        'head_style': params.get('head_style', 'helmet'),
        'arm_style': params.get('arm_style', 'standard'),
        'arm_style_right': params.get('arm_style_right'),
        'wing_style': params.get('wing_style', 'needle'),
        'wing_style_right': params.get('wing_style_right'),
        'torso_style': params.get('torso_style', 'core'),
        'nucleus_style': params.get('nucleus_style', 'ring'),
        **adv,
    })
    if state._MODE[0] == 'quick':
        params.update(state._QUICK_MECHA_OVERRIDES)
    state._MECHA_PARAMS.clear()
    state._MECHA_PARAMS.update(params)
    return params


def _collect_terrain():
    result = {
        'monument_scale': 5.5,
        'platform_count': 8,
        'fragment_count': 12,
        'debris_count': 80,
        'pillar_count': 8,
        'ramp_probability': 0.55,
        'ring_max_r': 22.0,
        'skyline_count': 3,
        'skyline_distance_z': -55.0,
        'skyline_spread_x': 40.0,
    }
    result.update(state._TERRAIN_PARAMS)
    result = {
        'monument_scale': _safe_val('t_mon_sl', result['monument_scale']),
        'platform_count': _safe_int('t_plat_sl', result['platform_count']),
        'fragment_count': _safe_int('t_frag_sl', result['fragment_count']),
        'debris_count': _safe_int('t_deb_sl', result['debris_count']),
        'pillar_count': _safe_int('t_pil_sl', result['pillar_count']),
        'ramp_probability': _safe_val('t_ramp_sl', result['ramp_probability']),
        'ring_max_r': _safe_val('t_ring_sl', result['ring_max_r']),
        'skyline_count': result['skyline_count'],
        'skyline_distance_z': result['skyline_distance_z'],
        'skyline_spread_x': result['skyline_spread_x'],
    }
    if state.get('t_sky_n_sl'):
        result['skyline_count'] = _safe_int('t_sky_n_sl', result['skyline_count'])
    if state.get('t_sky_z_sl'):
        result['skyline_distance_z'] = _safe_val('t_sky_z_sl', result['skyline_distance_z'])
    if state.get('t_sky_sp_sl'):
        result['skyline_spread_x'] = _safe_val('t_sky_sp_sl', result['skyline_spread_x'])
    if state._MODE[0] == 'quick':
        result.update(state._QUICK_TERRAIN_OVERRIDES)
    state._TERRAIN_PARAMS.clear()
    state._TERRAIN_PARAMS.update(result)
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
    preset_label = state._TERRAIN_PRESET[0] or 'Avanzada'
    if preset_label not in TERRAIN_PRESET_MAP:
        preset_label = 'Avanzada'
    state._TERRAIN_PRESET[0] = preset_label
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


# ── idle animation helper ────────────────────────────────────

def _apply_idle_to_mecha():
    """Aplica animacion idle + auto-play al mecha en escena."""
    mecha_root = sc.find_mecha_group()
    if not mecha_root:
        return
    try:
        from animations.registry import get_animation
        anim_cls = get_animation('idle')
        if anim_cls:
            anim = anim_cls(mecha_root)
            anim.apply()
            mc.currentTime(0)
            mc.play(forward=True)
            state._ACTIVE_ANIM[0] = 'idle'
    except Exception as e:
        print(f'[RetroMecha][Anim] No se pudo aplicar idle: {e}')
    _sync_anim_ui()


def _sync_anim_ui():
    coll = state.get('anim_rb_coll')
    rb_map = state.get('anim_rb_map')
    if coll and rb_map:
        active = state._ACTIVE_ANIM[0]
        if active in rb_map:
            try:
                mc.radioCollection(coll, e=True, select=rb_map[active])
            except Exception:
                pass


def _apply_terrain_visuals(palette: str):
    """Crea sky + sky_material + luces y sincroniza paleta completa.

    Flujo: paleta a shaders PRIMERO (como on_generar), luego sky + luces.
    """
    # 0. Sincronizar shaders ANTES de crear sky/luces
    try:
        from materials.sync import apply_palette_full
        apply_palette_full(palette)
    except Exception as e:
        print(f'[RetroMecha][Terrain] Sync: {e}')

    # 1. Sky geometry
    try:
        from utils.sky import create_sky
        create_sky()
    except Exception as e:
        print(f'[RetroMecha][Terrain] Cielo: {e}')

    # 2. Sky material
    try:
        from materials.sky_material import create_sky_material
        create_sky_material(palette)
    except Exception as e:
        print(f'[RetroMecha][Terrain] Sky material: {e}')

    # 3. Luces (crear si no existen, sino re-colorear)
    try:
        from utils import lighting
        if not lighting.has_rm_lights():
            lighting.apply_lighting(palette)
        else:
            lighting.set_palette(palette)
    except Exception as e:
        print(f'[RetroMecha][Terrain] Luces: {e}')


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
        _apply_idle_to_mecha()
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

        # Paleta actual (para sky_material y lights)
        try:
            from ui.panels.material_panel import current_palette_label
            palette = current_palette_label()
        except Exception:
            palette = 'Predeterminado'

        _apply_terrain_visuals(palette)

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
        if state._QUICK_PALETTE[0]:
            try:
                from ui.panels.material_panel import apply_color_preset_quick
                apply_color_preset_quick(state._QUICK_PALETTE[0])
            except Exception as e:
                print(f'[RetroMecha][Quick] No se pudo aplicar paleta: {e}')

        # Lift default +6 en Y al mecha (replica el ajuste manual del setup)
        try:
            from utils.camera import lift_mecha_default
            lift_mecha_default()
        except Exception as e:
            print(f'[RetroMecha][Generar] Lift: {e}')

        # Camara default compo (se reposiciona contra el bbox actualizado)
        try:
            from utils.camera import create_default_camera
            create_default_camera(frame_mecha=False, look_through=True)
        except Exception as e:
            print(f'[RetroMecha][Generar] Camara: {e}')

        # Sky + luces siempre desde el terreno
        try:
            from ui.panels.material_panel import current_palette_label
            palette = current_palette_label()
        except Exception:
            palette = 'Default'
        _apply_terrain_visuals(palette)

        # Animacion idle + auto-play
        _apply_idle_to_mecha()
        mc.select(scene_grp)
    return sc.scene_update(_work)


# ── random ───────────────────────────────────────────────────

def _random_module_adv(module):
    for spec in get_slider_specs(module):
        key = f'{module}.{spec["key"]}'
        ctrl = state.get(key)
        if not ctrl:
            continue
        if _safe_ctrl_exists(ctrl):
            try:
                mc.floatSliderGrp(
                    ctrl, e=True,
                    value=random.uniform(float(spec['min']), float(spec['max'])),
                )
            except Exception:
                pass


def _set_random_mecha_controls():
    quick_values = {
        'height_scale': random.uniform(0.50, 2.0),
        'symmetry': random.choice([True, False]),
        'use_arms': random.random() > 0.18,
        'use_wings': random.random() > 0.28,
        'use_energy_fields': random.random() > 0.25,
        'head_style': random.choice(list(HEAD_STYLE_LABELS.values())),
        'arm_style': random.choice(list(ARM_STYLE_LABELS.values())),
        'arm_style_right': random.choice(list(ARM_STYLE_LABELS.values())),
        'wing_style': random.choice(list(WING_STYLE_LABELS.values())),
        'wing_style_right': random.choice(list(WING_STYLE_LABELS.values())),
        'torso_style': random.choice(list(TORSO_STYLE_LABELS.values())),
        'nucleus_style': random.choice(list(NUCLEUS_STYLE_LABELS.values())),
    }
    if state._MODE[0] == 'quick':
        state._QUICK_MECHA_OVERRIDES.update(quick_values)
    state._MECHA_PARAMS.update(quick_values)

    _safe_set_opt('mecha_preset_menu', 'Custom')
    _safe_set_val('height_sl', quick_values['height_scale'])
    state._MECHA_PARAMS['head_style'] = quick_values['head_style']
    state._MECHA_PARAMS['arm_style'] = quick_values['arm_style']
    state._MECHA_PARAMS['arm_style_right'] = quick_values['arm_style_right']
    state._MECHA_PARAMS['wing_style'] = quick_values['wing_style']
    state._MECHA_PARAMS['wing_style_right'] = quick_values['wing_style_right']
    state._MECHA_PARAMS['torso_style'] = quick_values['torso_style']
    state._MECHA_PARAMS['nucleus_style'] = quick_values['nucleus_style']
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
    _safe_set_txt('seed_field', str(state._SEED[0]))
    rebuild_mecha()


def randomize_terrain_controls():
    quick_values = {
        'monument_scale': random.uniform(3.0, 9.0),
        'platform_count': random.randint(3, 16),
        'fragment_count': random.randint(2, 24),
        'debris_count': random.randint(20, 150),
        'pillar_count': random.randint(2, 16),
        'ramp_probability': random.uniform(0.0, 1.0),
        'ring_max_r': random.uniform(10.0, 35.0),
        'skyline_count': random.randint(1, 6),
        'skyline_distance_z': random.uniform(-80.0, -30.0),
        'skyline_spread_x': random.uniform(20.0, 70.0),
    }
    if state._MODE[0] == 'quick':
        state._QUICK_TERRAIN_OVERRIDES.update(quick_values)
    state._TERRAIN_PARAMS.update(quick_values)

    state._APPLYING_TERRAIN_VALUES[0] = True
    try:
        _safe_set_val('t_mon_sl', quick_values['monument_scale'])
        _safe_set_int('t_plat_sl', quick_values['platform_count'])
        _safe_set_int('t_frag_sl', quick_values['fragment_count'])
        _safe_set_int('t_deb_sl', quick_values['debris_count'])
        _safe_set_int('t_pil_sl', quick_values['pillar_count'])
        _safe_set_val('t_ramp_sl', quick_values['ramp_probability'])
        _safe_set_val('t_ring_sl', quick_values['ring_max_r'])
        if state.get('t_sky_n_sl'):
            _safe_set_int('t_sky_n_sl', quick_values['skyline_count'])
        if state.get('t_sky_z_sl'):
            _safe_set_val('t_sky_z_sl', quick_values['skyline_distance_z'])
        if state.get('t_sky_sp_sl'):
            _safe_set_val('t_sky_sp_sl', quick_values['skyline_spread_x'])
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
    _safe_set_txt('seed_field', str(state._SEED[0]))
    on_generar()

    # Apply random color preset (aiStandardSurface) and sync UI
    from materials.presets import list_presets, apply_preset
    presets = list_presets()
    rand_preset = random.choice(presets) if presets else None
    if rand_preset:
        apply_preset(rand_preset)
        from ui.panels.material_panel import apply_color_preset_quick
        apply_color_preset_quick(rand_preset)

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

    # Camera setup — solo si no existe (render_now la reposiciona si hace falta)
    try:
        from utils.camera import create_default_camera, has_rm_camera
        if not has_rm_camera():
            create_default_camera(frame_mecha=True, look_through=True)
    except Exception as e:
        print(f'[RetroMecha][Random] Camara: {e}')


# ── reset ────────────────────────────────────────────────────

def on_reset(*_):
    def _work():
        sc.clean_scene()
        _safe_set_txt('seed_field', '')
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
        if state._MODE[0] == 'quick':
            state._QUICK_MECHA_OVERRIDES.update({
                k: v for k, v in preset.items()
                if not k.startswith('_')
            })
        state._MECHA_PARAMS.update({
            k: v for k, v in preset.items()
            if not k.startswith('_')
        })
        _safe_set_val('height_sl', preset.get('height_scale', 1.0))
        state._MECHA_PARAMS['head_style'] = preset.get('head_style', 'helmet')
        state._MECHA_PARAMS['arm_style'] = preset.get('arm_style', 'standard')
        arm_right = preset.get('arm_style_right')
        if arm_right:
            state._MECHA_PARAMS['arm_style_right'] = arm_right
        state._MECHA_PARAMS['wing_style'] = preset.get('wing_style', 'needle')
        wing_right = preset.get('wing_style_right')
        if wing_right:
            state._MECHA_PARAMS['wing_style_right'] = wing_right
        state._MECHA_PARAMS['torso_style'] = preset.get('torso_style', 'core')
        state._MECHA_PARAMS['nucleus_style'] = preset.get('nucleus_style', 'ring')
        for module in ('head', 'arm', 'wing', 'torso', 'nucleus'):
            for spec in get_slider_specs(module):
                ctrl = state.get(f'{module}.{spec["key"]}')
                if _safe_ctrl_exists(ctrl) and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
    finally:
        state._APPLYING_MECHA_PRESET[0] = False
    rebuild_mecha()


# ── symmetry toggle ──────────────────────────────────────────

def _toggle_symmetry_ui(*_):
    if state._UI_BUILDING[0]:
        return
    on = state._MECHA_PARAMS.get('symmetry', True)
    for row_name in ('arm_right_row', 'wing_right_row'):
        row = state.get(row_name)
        if _safe_ctrl_exists(row):
            try:
                mc.control(row, e=True, visible=not on)
            except Exception:
                pass
