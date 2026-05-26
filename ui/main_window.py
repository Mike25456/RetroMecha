"""RetroMecha - ui/main_window.py v4
Single Maya UI with independent MECHA and TERRAIN rebuild controls.
"""

import json
import random
from pathlib import Path

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui.module_advanced import get_module_spec, get_slider_specs

WIN_ID = 'RetroMechaWindow'
_SEED = [None]
_APPLYING_MECHA_PRESET = [False]
_APPLYING_TERRAIN_VALUES = [False]
_UI_BUILDING = [False]

HEAD_STYLE_LABELS = {
    'Casco': 'helmet',
    'Drone': 'drone',
    'Centinela': 'sentinel',
}
ARM_STYLE_LABELS = {
    'Estandar': 'standard',
    'Pesado': 'heavy',
    'Cuchilla': 'blade',
    'Cañon': 'cannon',
}
WING_STYLE_LABELS = {
    'Agujas': 'needle',
    'Compactas': 'compact',
    'Abanico': 'fan',
}
TORSO_STYLE_LABELS = {
    'Base': 'core',
    'Pesado': 'heavy',
    'Delgado': 'slim',
    'Compacto': 'compact',
}
NUCLEUS_STYLE_LABELS = {
    'Anillo': 'ring',
    'Columna': 'column',
    'Orbe': 'orb',
}

PRESET_MAP = {
    'Avanzada': 'avanzada',
    'Hangar': 'hangar',
    'Campo de batalla': 'campo_de_batalla',
    'Centinela': 'centinela',
}

MECHA_PATTERNS = ['RetroMecha_*']
SCENE_PATTERNS = ['RetroMecha_Scene_*']
TERRAIN_PATTERNS = [
    'rm_terrain_*', 'rm_ground_*', 'rm_monument_*',
    'rm_platform_*', 'rm_fragment_*', 'rm_debris_*',
    'rm_ramps_*', 'rm_pillars_*', 'rm_tower_*', 'rm_skyline_*',
]


def _load_mecha_presets() -> dict:
    path = Path(__file__).resolve().parent.parent / 'config' / 'presets.json'
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith('_')}
    except Exception as e:
        print(f'[RetroMecha] No se pudieron cargar presets de mecha: {e}')
        return {}


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

    _UI_BUILDING[0] = True

    win = mc.window(WIN_ID, title='RetroMecha v4',
                    sizeable=True, resizeToFitChildren=True,
                    minimizeButton=True, maximizeButton=False,
                    width=340)

    mc.scrollLayout(childResizable=True)
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mc.separator(h=8, style='none')
    mc.text(label='RETROMECHA - GENERADOR PROCEDURAL',
            font='boldLabelFont', align='center', h=28,
            backgroundColor=[0.12, 0.22, 0.30])
    mc.separator(h=6, style='in')

    mc.rowLayout(nc=2, cw2=[60, 260],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
    seed_field = mc.textField(placeholderText='dejar vacio = aleatoria',
                              editable=True)
    mc.setParent('..')
    mc.separator(h=8, style='none')

    def fsl(label, mn, mx, val, step=0.01, prec=2, on_cc=None):
        ctrl = mc.floatSliderGrp(
            label=label, field=True,
            min=mn, max=mx, value=val, step=step, precision=prec,
            columnWidth3=[128, 52, 128],
            columnAlign3=['right', 'left', 'left'],
        )
        if on_cc:
            mc.floatSliderGrp(ctrl, e=True, changeCommand=on_cc)
        return ctrl

    def isl(label, mn, mx, val, on_cc=None):
        ctrl = mc.intSliderGrp(
            label=label, field=True,
            min=mn, max=mx, value=val,
            columnWidth3=[128, 52, 128],
            columnAlign3=['right', 'left', 'left'],
        )
        if on_cc:
            mc.intSliderGrp(ctrl, e=True, changeCommand=on_cc)
        return ctrl

    def resolve_seed() -> int:
        txt = mc.textField(seed_field, q=True, text=True).strip()
        if txt.isdigit():
            seed = int(txt)
        else:
            seed = random.randint(0, 99999)
            mc.textField(seed_field, e=True, text=str(seed))
        _SEED[0] = seed
        return seed

    mecha_presets = _load_mecha_presets()
    mecha_preset_labels = {
        data.get('_name', key): key
        for key, data in mecha_presets.items()
    }

    # MECHA
    mc.frameLayout(
        label='  >  MECHA',
        collapsable=True, collapse=False,
        borderStyle='etchedIn',
        backgroundColor=[0.12, 0.22, 0.18],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    def _on_mecha_cc(*_):
        if _UI_BUILDING[0] or _APPLYING_MECHA_PRESET[0]:
            return
        _rebuild_mecha()

    def _on_mecha_preset(label):
        _apply_mecha_preset(mecha_preset_labels.get(label, label))

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset mecha', align='right',
            font='smallPlainLabelFont')
    mecha_preset_menu = mc.optionMenu()
    mc.menuItem(label='Custom')
    if mecha_preset_labels:
        for label in mecha_preset_labels:
            mc.menuItem(label=label)
    mc.setParent('..')

    mc.separator(h=4)

    height_sl = fsl('Altura', 0.50, 2.0, 1.0, step=0.05)

    mc.separator(h=4)
    _asym_rows = []

    def _toggle_symmetry_ui(*_):
        if _UI_BUILDING[0]:
            return
        on = mc.checkBox(sym_cb, q=True, value=True)
        for row in _asym_rows:
            if mc.control(row, exists=True):
                mc.control(row, e=True, visible=not on)

    sym_cb = mc.checkBox(label='Simetria', value=True, changeCommand=_toggle_symmetry_ui)
    arms_cb = mc.checkBox(label='Modulo Brazos', value=True)
    wings_cb = mc.checkBox(label='Modulo Alas', value=True)
    energy_cb = mc.checkBox(label='Anillos de energia', value=True)

    mc.separator(h=4)
    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Cabeza', align='right', font='smallPlainLabelFont')
    head_style_menu = mc.optionMenu()
    for label in HEAD_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    head_adv_sliders = {}
    head_adv_spec = get_module_spec('head')
    if head_adv_spec:
        mc.frameLayout(
            label=f"  {head_adv_spec.get('frame_label', 'Cabeza — avanzado')}",
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            marginHeight=4, marginWidth=4,
        )
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for spec in get_slider_specs('head'):
            head_adv_sliders[spec['key']] = fsl(
                spec['label'],
                float(spec['min']), float(spec['max']), float(spec['default']),
                step=float(spec.get('step', 0.02)),
            )
        mc.setParent('..')
        mc.setParent('..')

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Brazos', align='right', font='smallPlainLabelFont')
    arm_style_menu = mc.optionMenu()
    for label in ARM_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    arm_style_right_row = mc.rowLayout(nc=2, cw2=[128, 180],
                                       columnAttach2=['both', 'both'],
                                       columnOffset2=[0, 4])
    _asym_rows.append(arm_style_right_row)
    mc.text(label='Brazo der', align='right', font='smallPlainLabelFont')
    arm_style_right_menu = mc.optionMenu()
    for label in ARM_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    arm_adv_sliders = {}
    arm_adv_spec = get_module_spec('arm')
    if arm_adv_spec:
        mc.frameLayout(
            label=f"  {arm_adv_spec.get('frame_label', 'Brazos — avanzado')}",
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            marginHeight=4, marginWidth=4,
        )
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for spec in get_slider_specs('arm'):
            arm_adv_sliders[spec['key']] = fsl(
                spec['label'],
                float(spec['min']), float(spec['max']), float(spec['default']),
                step=float(spec.get('step', 0.02)),
            )
        mc.setParent('..')
        mc.setParent('..')

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Alas', align='right', font='smallPlainLabelFont')
    wing_style_menu = mc.optionMenu()
    for label in WING_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    wing_style_right_row = mc.rowLayout(nc=2, cw2=[128, 180],
                                        columnAttach2=['both', 'both'],
                                        columnOffset2=[0, 4])
    _asym_rows.append(wing_style_right_row)
    mc.text(label='Ala der', align='right', font='smallPlainLabelFont')
    wing_style_right_menu = mc.optionMenu()
    for label in WING_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    wing_adv_sliders = {}
    wing_adv_spec = get_module_spec('wing')
    if wing_adv_spec:
        mc.frameLayout(
            label=f"  {wing_adv_spec.get('frame_label', 'Alas — avanzado')}",
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            marginHeight=4, marginWidth=4,
        )
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for spec in get_slider_specs('wing'):
            wing_adv_sliders[spec['key']] = fsl(
                spec['label'],
                float(spec['min']), float(spec['max']), float(spec['default']),
                step=float(spec.get('step', 0.02)),
            )
        mc.setParent('..')
        mc.setParent('..')

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Torso', align='right', font='smallPlainLabelFont')
    torso_style_menu = mc.optionMenu()
    for label in TORSO_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    torso_adv_sliders = {}
    torso_adv_spec = get_module_spec('torso')
    if torso_adv_spec:
        mc.frameLayout(
            label=f"  {torso_adv_spec.get('frame_label', 'Torso — avanzado')}",
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            marginHeight=4, marginWidth=4,
        )
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for spec in get_slider_specs('torso'):
            torso_adv_sliders[spec['key']] = fsl(
                spec['label'],
                float(spec['min']), float(spec['max']), float(spec['default']),
                step=float(spec.get('step', 0.02)),
            )
        mc.setParent('..')
        mc.setParent('..')

    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Nucleo', align='right', font='smallPlainLabelFont')
    nucleus_style_menu = mc.optionMenu()
    for label in NUCLEUS_STYLE_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    nucleus_adv_sliders = {}
    nucleus_adv_spec = get_module_spec('nucleus')
    if nucleus_adv_spec:
        mc.frameLayout(
            label=f"  {nucleus_adv_spec.get('frame_label', 'Núcleo — avanzado')}",
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            marginHeight=4, marginWidth=4,
        )
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for spec in get_slider_specs('nucleus'):
            nucleus_adv_sliders[spec['key']] = fsl(
                spec['label'],
                float(spec['min']), float(spec['max']), float(spec['default']),
                step=float(spec.get('step', 0.02)),
            )
        mc.setParent('..')
        mc.setParent('..')

    mc.separator(h=6)
    mc.button(label='Aleatorio Mecha', h=28,
              backgroundColor=[0.32, 0.18, 0.32],
              command=lambda *_: _random_mecha())

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    # ANIMATIONS
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  >  ANIMACIONES',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.28, 0.18, 0.14],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    from animations.registry import list_animations, get_animation

    def _apply_animation(*_):
        mecha_root = _find_mecha_group()
        if not mecha_root:
            print('[RetroMecha][Anim] No hay mecha en escena')
            return
        anim_cls = get_animation(_current_anim[0])
        if not anim_cls:
            print(f'[RetroMecha][Anim] Animacion "{_current_anim[0]}" no encontrada')
            return
        anim = anim_cls(mecha_root)
        anim.apply()

    def _remove_animation(*_):
        mecha_root = _find_mecha_group()
        if not mecha_root:
            print('[RetroMecha][Anim] No hay mecha en escena')
            return
        anim_cls = get_animation(_current_anim[0])
        if not anim_cls:
            return
        anim = anim_cls(mecha_root)
        anim.remove()

    anims = list_animations()
    _current_anim = [anims[0] if anims else None]

    if anims:
        mc.rowLayout(nc=2, cw2=[128, 140],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label='Animacion', align='right', font='smallPlainLabelFont')
        anim_menu = mc.optionMenu(
            changeCommand=lambda val: _current_anim.__setitem__(0, val))
        for name in anims:
            mc.menuItem(label=name)
        mc.setParent('..')

        mc.rowLayout(nc=2, cw2=[134, 134],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[3, 3])
        mc.button(label='Aplicar', h=28,
                  backgroundColor=[0.28, 0.38, 0.18],
                  command=_apply_animation)
        mc.button(label='Remover', h=28,
                  backgroundColor=[0.38, 0.18, 0.18],
                  command=_remove_animation)
        mc.setParent('..')
    else:
        mc.text(label='(no hay animaciones registradas)',
                align='left', font='smallPlainLabelFont')

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    # TERRAIN
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  >  TERRENO',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.14, 0.18, 0.28],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    def _on_terrain_cc(*_):
        if _APPLYING_TERRAIN_VALUES[0]:
            return
        _rebuild_terrain_only()

    mc.rowLayout(nc=2, cw2=[130, 178],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset de escena', align='right',
            font='smallPlainLabelFont')
    preset_menu = mc.optionMenu(changeCommand=_on_terrain_cc)
    mc.menuItem(label='Avanzada')
    mc.menuItem(label='Hangar')
    mc.menuItem(label='Campo de batalla')
    mc.menuItem(label='Centinela')
    mc.setParent('..')

    mc.separator(h=4)
    t_mon_sl = fsl('Escala monumento', 3.0, 9.0, 5.5,
                   step=0.1, on_cc=_on_terrain_cc)
    t_plat_sl = isl('N plataformas', 3, 16, 8, on_cc=_on_terrain_cc)
    t_frag_sl = isl('N fragmentos', 2, 24, 12, on_cc=_on_terrain_cc)
    t_deb_sl = isl('Debris (piezas)', 20, 150, 80, on_cc=_on_terrain_cc)
    t_pil_sl = isl('Pilares', 2, 16, 8, on_cc=_on_terrain_cc)
    t_ramp_sl = fsl('Prob. rampas', 0.0, 1.0, 0.55, on_cc=_on_terrain_cc)
    t_ring_sl = fsl('Radio max. terreno', 8.0, 35.0, 22.0,
                    step=0.5, on_cc=_on_terrain_cc)

    mc.separator(h=6)
    mc.button(label='Aleatorio Terreno', h=28,
              backgroundColor=[0.18, 0.22, 0.36],
              command=lambda *_: _random_terrain())

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    # GLOBAL BUTTONS
    mc.separator(h=8, style='in')
    mc.rowLayout(nc=3, cw3=[107, 107, 107],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[3, 3, 3])
    mc.button(label='Generar', h=38,
              backgroundColor=[0.18, 0.42, 0.22],
              command=lambda *_: _on_generar())
    mc.button(label='Aleatorio', h=38,
              backgroundColor=[0.40, 0.20, 0.38],
              command=lambda *_: _random_all())
    mc.button(label='Resetear', h=38,
              backgroundColor=[0.40, 0.16, 0.16],
              command=lambda *_: _on_reset())
    mc.setParent('..')

    mc.separator(h=4, style='none')
    mc.button(label='Delimitar escena', h=32,
              backgroundColor=[0.18, 0.34, 0.42],
              command=lambda *_: _on_delimitar())

    mc.separator(h=6, style='none')

    # MATERIALS PLACEHOLDER
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  >  MATERIALES - proxima fase',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.22, 0.18, 0.12],
        marginHeight=8, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)
    mc.text(label='Shaders retro-futuristas (Lambert / Blinn / PBR)',
            align='left', font='smallPlainLabelFont')
    mc.text(label='Paleta por preset: oxidado / pulido / mate',
            align='left', font='smallPlainLabelFont')
    mc.text(label='Asignacion automatica por modulo',
            align='left', font='smallPlainLabelFont')
    mc.setParent('..')
    mc.setParent('..')

    mc.separator(h=8, style='none')

    def _collect_mecha() -> dict:
        head_label = mc.optionMenu(head_style_menu, q=True, value=True)
        arm_label = mc.optionMenu(arm_style_menu, q=True, value=True)
        arm_right_label = mc.optionMenu(arm_style_right_menu, q=True, value=True)
        wing_label = mc.optionMenu(wing_style_menu, q=True, value=True)
        wing_right_label = mc.optionMenu(wing_style_right_menu, q=True, value=True)
        torso_label = mc.optionMenu(torso_style_menu, q=True, value=True)
        nucleus_label = mc.optionMenu(nucleus_style_menu, q=True, value=True)
        params = {
            'height_scale': mc.floatSliderGrp(height_sl, q=True, value=True),
            'symmetry': mc.checkBox(sym_cb, q=True, value=True),
            'use_head': True,
            'use_arms': mc.checkBox(arms_cb, q=True, value=True),
            'use_wings': mc.checkBox(wings_cb, q=True, value=True),
            'use_energy_fields': mc.checkBox(energy_cb, q=True, value=True),
            'head_style': HEAD_STYLE_LABELS.get(head_label, 'helmet'),
            'arm_style': ARM_STYLE_LABELS.get(arm_label, 'standard'),
            'arm_style_right': ARM_STYLE_LABELS.get(arm_right_label),
            'wing_style': WING_STYLE_LABELS.get(wing_label, 'needle'),
            'wing_style_right': WING_STYLE_LABELS.get(wing_right_label),
            'torso_style': TORSO_STYLE_LABELS.get(torso_label, 'core'),
            'nucleus_style': NUCLEUS_STYLE_LABELS.get(nucleus_label, 'ring'),
        }
        for key, ctrl in head_adv_sliders.items():
            params[key] = mc.floatSliderGrp(ctrl, q=True, value=True)
        for key, ctrl in arm_adv_sliders.items():
            params[key] = mc.floatSliderGrp(ctrl, q=True, value=True)
        for key, ctrl in wing_adv_sliders.items():
            params[key] = mc.floatSliderGrp(ctrl, q=True, value=True)
        for key, ctrl in torso_adv_sliders.items():
            params[key] = mc.floatSliderGrp(ctrl, q=True, value=True)
        for key, ctrl in nucleus_adv_sliders.items():
            params[key] = mc.floatSliderGrp(ctrl, q=True, value=True)
        return params

    def _collect_terrain() -> dict:
        return {
            'monument_scale': mc.floatSliderGrp(t_mon_sl, q=True, value=True),
            'platform_count': mc.intSliderGrp(t_plat_sl, q=True, value=True),
            'fragment_count': mc.intSliderGrp(t_frag_sl, q=True, value=True),
            'debris_count': mc.intSliderGrp(t_deb_sl, q=True, value=True),
            'pillar_count': mc.intSliderGrp(t_pil_sl, q=True, value=True),
            'ramp_probability': mc.floatSliderGrp(t_ramp_sl, q=True, value=True),
            'ring_max_r': mc.floatSliderGrp(t_ring_sl, q=True, value=True),
        }

    def _collect_terrain_params(seed: int, support_edges: bool = True) -> dict:
        return {
            '_seed': seed + 1000,
            'height_scale': 1.0,
            'use_support_edges': support_edges,
        }

    def _find_scene_group():
        return next((n for n in (mc.ls('RetroMecha_Scene_*', type='transform') or [])
                     if mc.objExists(n)), None)

    def _find_mecha_group():
        return next((n for n in (mc.ls('RetroMecha_*', type='transform') or [])
                     if 'Scene' not in n and mc.objExists(n)), None)

    def _mecha_bbox():
        mecha_grp = _find_mecha_group()
        if mecha_grp and mc.objExists(mecha_grp):
            try:
                return tuple(mc.exactWorldBoundingBox(mecha_grp))
            except Exception:
                pass
        return (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)

    def _parent_to_scene(node: str):
        scene = _find_scene_group()
        if scene and node and mc.objExists(node):
            try:
                mc.parent(node, scene)
            except Exception:
                pass

    def _delete_nodes(nodes: list):
        nodes = [node for node in nodes if node and mc.objExists(node)]
        if not nodes:
            return
        try:
            mc.delete(nodes)
        except Exception:
            for node in nodes:
                try:
                    mc.delete(node)
                except Exception:
                    pass

    def _clean_scene():
        nodes = []
        for pat in SCENE_PATTERNS:
            nodes.extend(mc.ls(pat, type='transform') or [])
        _delete_nodes(nodes)

    def _clean_mecha():
        nodes = []
        for pat in MECHA_PATTERNS:
            for node in (mc.ls(pat, type='transform') or []):
                if 'Scene' in node:
                    continue
                nodes.append(node)
        _delete_nodes(nodes)

    def _clean_terrain():
        nodes = []
        for pat in TERRAIN_PATTERNS:
            nodes.extend(mc.ls(pat, type='transform') or [])
        _delete_nodes(nodes)

    def _lift_mecha(group: str):
        try:
            bb = mc.exactWorldBoundingBox(group)
            lift = 0.5 - bb[1]
            if abs(lift) > 0.01:
                mc.move(0, lift, 0, group, relative=True, worldSpace=True)
        except Exception:
            pass

    def _scene_update(fn):
        try:
            mc.undoInfo(openChunk=True)
        except Exception:
            pass
        try:
            mc.refresh(suspend=True)
        except Exception:
            pass
        try:
            return fn()
        finally:
            try:
                mc.refresh(suspend=False)
                mc.refresh(force=True)
            except Exception:
                pass
            try:
                mc.undoInfo(closeChunk=True)
            except Exception:
                pass

    def _set_option_by_value(menu, mapping: dict, value: str):
        for label, mapped in mapping.items():
            if mapped == value:
                mc.optionMenu(menu, e=True, value=label)
                return

    def _apply_mecha_preset(key: str):
        preset = mecha_presets.get(key)
        if not preset:
            return

        _APPLYING_MECHA_PRESET[0] = True
        try:
            mc.floatSliderGrp(height_sl, e=True,
                              value=preset.get('height_scale', 1.0))
            mc.checkBox(sym_cb, e=True,
                        value=preset.get('symmetry', True))
            mc.checkBox(arms_cb, e=True,
                        value=preset.get('use_arms', True))
            mc.checkBox(wings_cb, e=True,
                        value=preset.get('use_wings', True))
            mc.checkBox(energy_cb, e=True,
                        value=preset.get('use_energy_fields', True))
            _set_option_by_value(head_style_menu, HEAD_STYLE_LABELS,
                                 preset.get('head_style', 'helmet'))
            _set_option_by_value(arm_style_menu, ARM_STYLE_LABELS,
                                 preset.get('arm_style', 'standard'))
            arm_right = preset.get('arm_style_right')
            if arm_right:
                _set_option_by_value(arm_style_right_menu, ARM_STYLE_LABELS, arm_right)
            _set_option_by_value(wing_style_menu, WING_STYLE_LABELS,
                                 preset.get('wing_style', 'needle'))
            wing_right = preset.get('wing_style_right')
            if wing_right:
                _set_option_by_value(wing_style_right_menu, WING_STYLE_LABELS, wing_right)
            _set_option_by_value(torso_style_menu, TORSO_STYLE_LABELS,
                                 preset.get('torso_style', 'core'))
            _set_option_by_value(nucleus_style_menu, NUCLEUS_STYLE_LABELS,
                                 preset.get('nucleus_style', 'ring'))
            for spec in get_slider_specs('head'):
                ctrl = head_adv_sliders.get(spec['key'])
                if ctrl and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
            for spec in get_slider_specs('arm'):
                ctrl = arm_adv_sliders.get(spec['key'])
                if ctrl and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
            for spec in get_slider_specs('wing'):
                ctrl = wing_adv_sliders.get(spec['key'])
                if ctrl and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
            for spec in get_slider_specs('torso'):
                ctrl = torso_adv_sliders.get(spec['key'])
                if ctrl and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
            for spec in get_slider_specs('nucleus'):
                ctrl = nucleus_adv_sliders.get(spec['key'])
                if ctrl and spec['key'] in preset:
                    mc.floatSliderGrp(ctrl, e=True, value=preset[spec['key']])
        finally:
            _APPLYING_MECHA_PRESET[0] = False

        _rebuild_mecha()

    def _build_mecha(seed: int, support_edges: bool = True):
        params = _collect_mecha()
        params['_seed'] = seed
        params['use_support_edges'] = support_edges
        from core.mecha_builder import MechaBuilder
        grp = MechaBuilder(params, seed=seed).build()
        if grp and mc.objExists(grp):
            _lift_mecha(grp)
            mc.makeIdentity(grp, apply=True, translate=True, rotate=True, scale=True,
                            normal=False, preserveNormals=True)
        return grp

    def _build_terrain(seed: int, support_edges: bool = True):
        preset_label = mc.optionMenu(preset_menu, q=True, value=True)
        preset_name = PRESET_MAP.get(preset_label, 'avanzada')
        overrides = _collect_terrain()

        from terrain.terrain_builder import TerrainBuilder
        tb = TerrainBuilder(
            params=_collect_terrain_params(seed, support_edges=support_edges),
            seed=seed + 1000,
            preset_name=preset_name,
            mecha_bbox=_mecha_bbox(),
        )
        tb.preset.update(overrides)
        return tb.build()

    def _rebuild_mecha(*_):
        def _work():
            seed = _SEED[0] if isinstance(_SEED[0], int) else resolve_seed()
            _SEED[0] = seed
            _clean_mecha()
            grp = _build_mecha(seed, support_edges=False)
            if grp and mc.objExists(grp):
                _parent_to_scene(grp)
                _mark_undelimited(_find_scene_group() or grp)
                mc.select(grp)
        return _scene_update(_work)

    def _rebuild_terrain_only(*_):
        def _work():
            seed = _SEED[0] if isinstance(_SEED[0], int) else resolve_seed()
            _SEED[0] = seed
            _clean_terrain()
            grp = _build_terrain(seed, support_edges=False)
            if grp and mc.objExists(grp):
                _parent_to_scene(grp)
                _mark_undelimited(_find_scene_group() or grp)
                mc.select(grp)
        return _scene_update(_work)

    def _on_generar(*_):
        def _work():
            seed = resolve_seed()
            _clean_scene()
            _clean_mecha()
            _clean_terrain()

            scene_grp = mc.group(empty=True, name='RetroMecha_Scene_#')

            mecha_grp = _build_mecha(seed, support_edges=False)
            if mecha_grp and mc.objExists(mecha_grp):
                mc.parent(mecha_grp, scene_grp)

            terrain_grp = _build_terrain(seed, support_edges=False)
            if terrain_grp and mc.objExists(terrain_grp):
                mc.parent(terrain_grp, scene_grp)

            mc.select(scene_grp)
        return _scene_update(_work)

    def _delimit_roots() -> list:
        scene = _find_scene_group()
        if scene:
            return [scene]

        roots = []
        mecha = _find_mecha_group()
        if mecha:
            roots.append(mecha)
        roots.extend([
            n for n in (mc.ls('rm_terrain_*', type='transform') or [])
            if mc.objExists(n)
        ])
        return roots

    def _is_delimited(root: str) -> bool:
        try:
            return (
                mc.attributeQuery('rm_delimited', node=root, exists=True)
                and mc.getAttr(f'{root}.rm_delimited')
            )
        except Exception:
            return False

    def _mark_delimited(root: str):
        try:
            if not mc.attributeQuery('rm_delimited', node=root, exists=True):
                mc.addAttr(root, longName='rm_delimited', attributeType='bool')
            mc.setAttr(f'{root}.rm_delimited', True)
        except Exception:
            pass

    def _mark_undelimited(root: str):
        if not root or not mc.objExists(root):
            return
        try:
            if not mc.attributeQuery('rm_delimited', node=root, exists=True):
                mc.addAttr(root, longName='rm_delimited', attributeType='bool')
            mc.setAttr(f'{root}.rm_delimited', False)
        except Exception:
            pass

    def _on_delimitar(*_):
        def _work():
            roots = [root for root in _delimit_roots() if not _is_delimited(root)]
            if not roots:
                print('[RetroMecha] No hay escena nueva por delimitar')
                return

            from utils.hard_surface import apply_support_edges
            from utils.maya_scene import force_preview_one

            total = 0
            for root in roots:
                total += apply_support_edges(
                    root, offset=0.018, fraction=0.045,
                    segments=2, max_faces=500,
                )
                force_preview_one(root)
                _mark_delimited(root)

            mc.select(roots)
            print(f'[RetroMecha] Delimitacion aplicada: {total} pieza(s)')
        return _scene_update(_work)

    def _random_mecha(*_):
        _APPLYING_MECHA_PRESET[0] = True
        try:
            mc.optionMenu(mecha_preset_menu, e=True, value='Custom')
            mc.floatSliderGrp(height_sl, e=True, value=random.uniform(0.50, 2.0))
            mc.checkBox(sym_cb, e=True, value=random.choice([True, False]))
            mc.checkBox(arms_cb, e=True, value=random.random() > 0.18)
            mc.checkBox(wings_cb, e=True, value=random.random() > 0.28)
            mc.checkBox(energy_cb, e=True, value=random.random() > 0.25)
            mc.optionMenu(head_style_menu, e=True,
                          value=random.choice(list(HEAD_STYLE_LABELS.keys())))
            mc.optionMenu(arm_style_menu, e=True,
                          value=random.choice(list(ARM_STYLE_LABELS.keys())))
            mc.optionMenu(arm_style_right_menu, e=True,
                          value=random.choice(list(ARM_STYLE_LABELS.keys())))
            mc.optionMenu(wing_style_menu, e=True,
                          value=random.choice(list(WING_STYLE_LABELS.keys())))
            mc.optionMenu(wing_style_right_menu, e=True,
                          value=random.choice(list(WING_STYLE_LABELS.keys())))
            mc.optionMenu(torso_style_menu, e=True,
                          value=random.choice(list(TORSO_STYLE_LABELS.keys())))
            mc.optionMenu(nucleus_style_menu, e=True,
                          value=random.choice(list(NUCLEUS_STYLE_LABELS.keys())))
            _toggle_symmetry_ui()
            for spec in get_slider_specs('head'):
                ctrl = head_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('arm'):
                ctrl = arm_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('wing'):
                ctrl = wing_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('torso'):
                ctrl = torso_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('nucleus'):
                ctrl = nucleus_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
        finally:
            _APPLYING_MECHA_PRESET[0] = False
        _SEED[0] = random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(_SEED[0]))
        _rebuild_mecha()

    def _randomize_terrain_controls():
        _APPLYING_TERRAIN_VALUES[0] = True
        try:
            mc.floatSliderGrp(t_mon_sl, e=True, value=random.uniform(3.0, 9.0))
            mc.intSliderGrp(t_plat_sl, e=True, value=random.randint(3, 16))
            mc.intSliderGrp(t_frag_sl, e=True, value=random.randint(2, 24))
            mc.intSliderGrp(t_deb_sl, e=True, value=random.randint(20, 150))
            mc.intSliderGrp(t_pil_sl, e=True, value=random.randint(2, 16))
            mc.floatSliderGrp(t_ramp_sl, e=True, value=random.uniform(0.0, 1.0))
            mc.floatSliderGrp(t_ring_sl, e=True, value=random.uniform(10.0, 35.0))
        finally:
            _APPLYING_TERRAIN_VALUES[0] = False

    def _random_terrain(*_):
        _randomize_terrain_controls()
        _rebuild_terrain_only()

    def _random_all(*_):
        _APPLYING_MECHA_PRESET[0] = True
        try:
            mc.optionMenu(mecha_preset_menu, e=True, value='Custom')
            mc.floatSliderGrp(height_sl, e=True, value=random.uniform(0.50, 2.0))
            mc.checkBox(sym_cb, e=True, value=random.choice([True, False]))
            mc.checkBox(arms_cb, e=True, value=random.random() > 0.18)
            mc.checkBox(wings_cb, e=True, value=random.random() > 0.28)
            mc.checkBox(energy_cb, e=True, value=random.random() > 0.25)
            mc.optionMenu(head_style_menu, e=True,
                          value=random.choice(list(HEAD_STYLE_LABELS.keys())))
            mc.optionMenu(arm_style_menu, e=True,
                          value=random.choice(list(ARM_STYLE_LABELS.keys())))
            mc.optionMenu(arm_style_right_menu, e=True,
                          value=random.choice(list(ARM_STYLE_LABELS.keys())))
            mc.optionMenu(wing_style_menu, e=True,
                          value=random.choice(list(WING_STYLE_LABELS.keys())))
            mc.optionMenu(wing_style_right_menu, e=True,
                          value=random.choice(list(WING_STYLE_LABELS.keys())))
            mc.optionMenu(torso_style_menu, e=True,
                          value=random.choice(list(TORSO_STYLE_LABELS.keys())))
            mc.optionMenu(nucleus_style_menu, e=True,
                          value=random.choice(list(NUCLEUS_STYLE_LABELS.keys())))
            _toggle_symmetry_ui()
            for spec in get_slider_specs('head'):
                ctrl = head_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('arm'):
                ctrl = arm_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('wing'):
                ctrl = wing_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('torso'):
                ctrl = torso_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            for spec in get_slider_specs('nucleus'):
                ctrl = nucleus_adv_sliders.get(spec['key'])
                if ctrl:
                    mc.floatSliderGrp(
                        ctrl, e=True,
                        value=random.uniform(float(spec['min']), float(spec['max'])),
                    )
            _randomize_terrain_controls()
        finally:
            _APPLYING_MECHA_PRESET[0] = False
        _SEED[0] = random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(_SEED[0]))
        _on_generar()

    def _on_reset(*_):
        def _work():
            _clean_scene()
            _clean_mecha()
            _clean_terrain()
            mc.textField(seed_field, e=True, text='')
            _SEED[0] = None
            print('[RetroMecha] Escena limpiada')
        return _scene_update(_work)

    def _bind_mecha_live_callbacks():
        for slider in (height_sl,):
            mc.floatSliderGrp(slider, e=True,
                              changeCommand=_on_mecha_cc,
                              dragCommand=_on_mecha_cc)
        for checkbox in (sym_cb, arms_cb, wings_cb, energy_cb):
            mc.checkBox(checkbox, e=True, changeCommand=_on_mecha_cc)
        for menu in (head_style_menu, arm_style_menu, arm_style_right_menu,
                     wing_style_menu, wing_style_right_menu,
                     torso_style_menu, nucleus_style_menu):
            mc.optionMenu(menu, e=True, changeCommand=_on_mecha_cc)
        for ctrl in head_adv_sliders.values():
            mc.floatSliderGrp(ctrl, e=True,
                              changeCommand=_on_mecha_cc,
                              dragCommand=_on_mecha_cc)
        for ctrl in arm_adv_sliders.values():
            mc.floatSliderGrp(ctrl, e=True,
                              changeCommand=_on_mecha_cc,
                              dragCommand=_on_mecha_cc)
        for ctrl in wing_adv_sliders.values():
            mc.floatSliderGrp(ctrl, e=True,
                              changeCommand=_on_mecha_cc,
                              dragCommand=_on_mecha_cc)
        for ctrl in torso_adv_sliders.values():
            mc.floatSliderGrp(ctrl, e=True,
                              changeCommand=_on_mecha_cc,
                              dragCommand=_on_mecha_cc)
        for ctrl in nucleus_adv_sliders.values():
            mc.floatSliderGrp(ctrl, e=True,
                              changeCommand=_on_mecha_cc,
                              dragCommand=_on_mecha_cc)

    mc.optionMenu(mecha_preset_menu, e=True, changeCommand=_on_mecha_preset)
    _bind_mecha_live_callbacks()
    _UI_BUILDING[0] = False
    _toggle_symmetry_ui()
    mc.showWindow(win)
    print('[RetroMecha] UI v4 abierta')