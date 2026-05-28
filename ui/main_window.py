"""
RetroMecha — ui/main_window.py  v5
UI completa con:
  - Estilos por módulo (head/arm/wing/torso/nucleus)
  - Sliders avanzados por módulo
  - Simetría con brazo/ala independiente
  - Presets de mecha desde presets.json
  - Animaciones
  - Terreno con presets y sliders
  - Materiales aiToon (paletas + verificación)
  - Iluminación procedural (3 presets)
"""

import json
import random
from pathlib import Path

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

WIN_ID = 'RetroMechaWindow'
_SEED  = [None]
_APPLYING_PRESET  = [False]
_UI_BUILDING      = [False]

# ── Diccionarios de estilos ───────────────────────────────────────────────────
HEAD_STYLE_LABELS = {
    'Casco':     'helmet',
    'Drone':     'drone',
    'Centinela': 'sentinel',
}
ARM_STYLE_LABELS = {
    'Estandar': 'standard',
    'Pesado':   'heavy',
    'Cuchilla': 'blade',
    'Canon':    'cannon',
}
WING_STYLE_LABELS = {
    'Agujas':    'needle',
    'Compactas': 'compact',
    'Abanico':   'fan',
}
TORSO_STYLE_LABELS = {
    'Base':     'core',
    'Pesado':   'heavy',
    'Delgado':  'slim',
    'Compacto': 'compact',
}
NUCLEUS_STYLE_LABELS = {
    'Anillo':  'ring',
    'Columna': 'column',
    'Orbe':    'orb',
}
PRESET_MAP = {
    'Avanzada':         'avanzada',
    'Hangar':           'hangar',
    'Campo de batalla': 'campo_de_batalla',
    'Centinela':        'centinela',
}
PALETTE_LABELS = {
    'Industrial': 'industrial',
    'Oxidado':    'oxidado',
    'Artico':     'artico',
    'Carmesi':    'carmesi',
}
LIGHTING_LABELS = {
    'Estudio':   'studio',
    'Dramatico': 'dramatic',
    'Retro':     'retro',
}

MECHA_PATTERNS = ['RetroMecha_*']
SCENE_PATTERNS = ['RetroMecha_Scene_*']
TERRAIN_PATTERNS = [
    'rm_terrain_*', 'rm_ground_*', 'rm_monument_*',
    'rm_platform_*', 'rm_fragment_*', 'rm_debris_*',
    'rm_ramps_*', 'rm_pillars_*', 'rm_tower_*', 'rm_skyline_*',
]


# ── Helpers de config ─────────────────────────────────────────────────────────

def _load_mecha_presets() -> dict:
    path = Path(__file__).resolve().parent.parent / 'config' / 'presets.json'
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        return {k: v for k, v in data.items() if not k.startswith('_')}
    except Exception:
        return {}


def _load_module_advanced() -> dict:
    """Carga config de sliders avanzados por módulo desde module_advanced.json."""
    path = Path(__file__).resolve().parent.parent / 'config' / 'module_advanced.json'
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


# =============================================================================
#  PUNTO DE ENTRADA
# =============================================================================

def build_ui(recreate: bool = True):
    if not MAYA_AVAILABLE:
        print('[RetroMecha] Ejecutar dentro de Maya')
        return

    if mc.window(WIN_ID, exists=True):
        if not recreate:
            mc.showWindow(WIN_ID)
            return
        mc.deleteUI(WIN_ID, window=True)

    _UI_BUILDING[0] = True

    win = mc.window(WIN_ID, title='RetroMecha v5',
                    sizeable=True, resizeToFitChildren=True,
                    minimizeButton=True, maximizeButton=False,
                    width=345)

    mc.scrollLayout(childResizable=True)
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    # ── Header ────────────────────────────────────────────────────────────────
    mc.separator(h=8, style='none')
    mc.text(label='RETROMECHA  —  GENERADOR PROCEDURAL',
            font='boldLabelFont', align='center', h=28,
            backgroundColor=[0.10, 0.30, 0.48])
    mc.separator(h=6, style='in')

    mc.rowLayout(nc=2, cw2=[62, 264],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])
    mc.text(label='Semilla', align='right', font='smallPlainLabelFont')
    seed_field = mc.textField(placeholderText='dejar vacio = aleatoria',
                              editable=True)
    mc.setParent('..')
    mc.separator(h=8, style='none')

    # ── Helpers de widget ─────────────────────────────────────────────────────
    def fsl(label, mn, mx, val, step=0.01, prec=2, cc=None):
        ctrl = mc.floatSliderGrp(
            label=label, field=True,
            min=mn, max=mx, value=val, step=step, precision=prec,
            columnWidth3=[128, 52, 128],
            columnAlign3=['right', 'left', 'left'],
        )
        if cc:
            mc.floatSliderGrp(ctrl, e=True, changeCommand=cc)
        return ctrl

    def isl(label, mn, mx, val, cc=None):
        ctrl = mc.intSliderGrp(
            label=label, field=True,
            min=mn, max=mx, value=val,
            columnWidth3=[128, 52, 128],
            columnAlign3=['right', 'left', 'left'],
        )
        if cc:
            mc.intSliderGrp(ctrl, e=True, changeCommand=cc)
        return ctrl

    def option_row(label, items):
        mc.rowLayout(nc=2, cw2=[128, 196],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label=label, align='right', font='smallPlainLabelFont')
        menu = mc.optionMenu()
        for item in items:
            mc.menuItem(label=item)
        mc.setParent('..')
        return menu

    def resolve_seed() -> int:
        txt = mc.textField(seed_field, q=True, text=True).strip()
        s = int(txt) if txt.isdigit() else random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(s))
        _SEED[0] = s
        return s

    # ── Presets de mecha ──────────────────────────────────────────────────────
    mecha_presets = _load_mecha_presets()
    preset_label_to_key = {
        v.get('_name', k): k for k, v in mecha_presets.items()
    }
    adv_cfg = _load_module_advanced()

    # =========================================================================
    #  SECCIÓN MECHA
    # =========================================================================
    mc.frameLayout(
        label='  >  MECHA',
        collapsable=True, collapse=False,
        borderStyle='etchedIn',
        backgroundColor=[0.10, 0.36, 0.24],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    def _on_mecha_cc(*_):
        if _UI_BUILDING[0] or _APPLYING_PRESET[0]:
            return
        _rebuild_mecha()

    # Preset de mecha
    mc.rowLayout(nc=2, cw2=[128, 196],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Preset mecha', align='right', font='smallPlainLabelFont')
    mecha_preset_menu = mc.optionMenu()
    mc.menuItem(label='Custom')
    for lbl in preset_label_to_key:
        mc.menuItem(label=lbl)
    mc.setParent('..')

    mc.separator(h=4)

    # Sliders principales
    sep_sl    = fsl('Separacion',         0.10, 0.80, 0.35, cc=_on_mecha_cc)
    angle_sl  = fsl('Angulos conectores', 0.0,  45.0, 15.0,
                    step=0.5, prec=1,     cc=_on_mecha_cc)
    aggr_sl   = fsl('Agresividad',        0.0,   1.0,  0.5, cc=_on_mecha_cc)
    decay_sl  = fsl('Decrecimiento',      0.50,  1.0,  0.85, cc=_on_mecha_cc)
    height_sl = fsl('Altura',             0.50,  2.0,  1.0,
                    step=0.05,            cc=_on_mecha_cc)

    mc.separator(h=4)
    sym_cb    = mc.checkBox(label='Simetria',        value=True,
                            changeCommand=_on_mecha_cc)
    panels_cb = mc.checkBox(label='Emplear Paneles', value=True,
                            changeCommand=_on_mecha_cc)
    arms_cb   = mc.checkBox(label='Modulo Brazos',   value=True,
                            changeCommand=_on_mecha_cc)
    wings_cb  = mc.checkBox(label='Modulo Alas',     value=True,
                            changeCommand=_on_mecha_cc)

    # Filas de asimetría (visibles solo cuando simetría=OFF)
    _asym_rows = []

    mc.separator(h=6)

    # ── Cabeza ────────────────────────────────────────────────────────────────
    head_style_menu = option_row('Cabeza', list(HEAD_STYLE_LABELS.keys()))

    # Sliders avanzados cabeza
    head_adv = {}
    head_adv_cfg = adv_cfg.get('head', {}).get('sliders', [])
    if head_adv_cfg:
        mc.frameLayout(label='  Cabeza avanzado',
                       collapsable=True, collapse=True,
                       borderStyle='etchedIn', marginHeight=3, marginWidth=4)
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for s in head_adv_cfg:
            head_adv[s['key']] = fsl(s['label'], float(s['min']),
                                     float(s['max']), float(s['default']),
                                     step=float(s.get('step', 0.02)))
        mc.setParent('..')
        mc.setParent('..')

    # ── Brazos ────────────────────────────────────────────────────────────────
    arm_style_menu = option_row('Brazos', list(ARM_STYLE_LABELS.keys()))

    arm_right_row = mc.rowLayout(nc=2, cw2=[128, 196],
                                 columnAttach2=['both', 'both'],
                                 columnOffset2=[0, 4])
    _asym_rows.append(arm_right_row)
    mc.text(label='Brazo derecho', align='right', font='smallPlainLabelFont')
    arm_style_right_menu = mc.optionMenu()
    for lbl in ARM_STYLE_LABELS:
        mc.menuItem(label=lbl)
    mc.setParent('..')

    arm_adv = {}
    arm_adv_cfg = adv_cfg.get('arm', {}).get('sliders', [])
    if arm_adv_cfg:
        mc.frameLayout(label='  Brazos avanzado',
                       collapsable=True, collapse=True,
                       borderStyle='etchedIn', marginHeight=3, marginWidth=4)
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for s in arm_adv_cfg:
            arm_adv[s['key']] = fsl(s['label'], float(s['min']),
                                    float(s['max']), float(s['default']),
                                    step=float(s.get('step', 0.02)))
        mc.setParent('..')
        mc.setParent('..')

    # ── Alas ──────────────────────────────────────────────────────────────────
    wing_style_menu = option_row('Alas', list(WING_STYLE_LABELS.keys()))

    wing_right_row = mc.rowLayout(nc=2, cw2=[128, 196],
                                  columnAttach2=['both', 'both'],
                                  columnOffset2=[0, 4])
    _asym_rows.append(wing_right_row)
    mc.text(label='Ala derecha', align='right', font='smallPlainLabelFont')
    wing_style_right_menu = mc.optionMenu()
    for lbl in WING_STYLE_LABELS:
        mc.menuItem(label=lbl)
    mc.setParent('..')

    wing_adv = {}
    wing_adv_cfg = adv_cfg.get('wing', {}).get('sliders', [])
    if wing_adv_cfg:
        mc.frameLayout(label='  Alas avanzado',
                       collapsable=True, collapse=True,
                       borderStyle='etchedIn', marginHeight=3, marginWidth=4)
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for s in wing_adv_cfg:
            wing_adv[s['key']] = fsl(s['label'], float(s['min']),
                                     float(s['max']), float(s['default']),
                                     step=float(s.get('step', 0.02)))
        mc.setParent('..')
        mc.setParent('..')

    # ── Torso ─────────────────────────────────────────────────────────────────
    torso_style_menu = option_row('Torso', list(TORSO_STYLE_LABELS.keys()))

    torso_adv = {}
    torso_adv_cfg = adv_cfg.get('torso', {}).get('sliders', [])
    if torso_adv_cfg:
        mc.frameLayout(label='  Torso avanzado',
                       collapsable=True, collapse=True,
                       borderStyle='etchedIn', marginHeight=3, marginWidth=4)
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for s in torso_adv_cfg:
            torso_adv[s['key']] = fsl(s['label'], float(s['min']),
                                      float(s['max']), float(s['default']),
                                      step=float(s.get('step', 0.02)))
        mc.setParent('..')
        mc.setParent('..')

    # ── Nucleo ────────────────────────────────────────────────────────────────
    nucleus_style_menu = option_row('Nucleo', list(NUCLEUS_STYLE_LABELS.keys()))

    nucleus_adv = {}
    nucleus_adv_cfg = adv_cfg.get('nucleus', {}).get('sliders', [])
    if nucleus_adv_cfg:
        mc.frameLayout(label='  Nucleo avanzado',
                       collapsable=True, collapse=True,
                       borderStyle='etchedIn', marginHeight=3, marginWidth=4)
        mc.columnLayout(adjustableColumn=True, rowSpacing=2)
        for s in nucleus_adv_cfg:
            nucleus_adv[s['key']] = fsl(s['label'], float(s['min']),
                                        float(s['max']), float(s['default']),
                                        step=float(s.get('step', 0.02)))
        mc.setParent('..')
        mc.setParent('..')

    mc.separator(h=6)
    mc.button(label='Aleatorio Mecha', h=28,
              backgroundColor=[0.20, 0.52, 0.34],
              command=lambda *_: _random_mecha())

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    # =========================================================================
    #  SECCIÓN ANIMACIONES
    # =========================================================================
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  >  ANIMACIONES',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.44, 0.18, 0.10],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    _current_anim = [None]
    try:
        from animations.registry import list_animations, get_animation
        anims = list_animations()
        _current_anim[0] = anims[0] if anims else None

        if anims:
            anim_menu = option_row('Animacion', anims)
            mc.optionMenu(anim_menu, e=True,
                          changeCommand=lambda v: _current_anim.__setitem__(0, v))

            def _find_mecha_for_anim():
                return next((n for n in (mc.ls('RetroMecha_*', type='transform') or [])
                             if 'Scene' not in n and mc.objExists(n)), None)

            def _apply_anim(*_):
                root = _find_mecha_for_anim()
                if not root:
                    print('[RetroMecha][Anim] No hay mecha en escena')
                    return
                cls = get_animation(_current_anim[0])
                if cls:
                    cls(root).apply()

            def _remove_anim(*_):
                root = _find_mecha_for_anim()
                if not root:
                    return
                cls = get_animation(_current_anim[0])
                if cls:
                    cls(root).remove()

            mc.rowLayout(nc=2, cw2=[134, 134],
                         columnAttach2=['both', 'both'],
                         columnOffset2=[3, 3])
            mc.button(label='Aplicar', h=28,
                      backgroundColor=[0.62, 0.30, 0.14],
                      command=_apply_anim)
            mc.button(label='Remover', h=28,
                      backgroundColor=[0.42, 0.14, 0.10],
                      command=_remove_anim)
            mc.setParent('..')
        else:
            mc.text(label='(sin animaciones registradas)',
                    align='left', font='smallPlainLabelFont')
    except ImportError:
        mc.text(label='(modulo animaciones no disponible)',
                align='left', font='smallPlainLabelFont')

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    # =========================================================================
    #  SECCIÓN TERRENO
    # =========================================================================
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  >  TERRENO',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.12, 0.22, 0.48],
        marginHeight=6, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=3)

    def _on_terrain_cc(*_):
        _rebuild_terrain_only()

    preset_menu = option_row('Preset de escena', list(PRESET_MAP.keys()))
    mc.optionMenu(preset_menu, e=True, changeCommand=_on_terrain_cc)

    mc.separator(h=4)
    t_mon_sl  = fsl('Escala monumento',   3.0,  9.0,  5.5,
                    step=0.1, cc=_on_terrain_cc)
    t_plat_sl = isl('N plataformas',      3,   16,    8,  cc=_on_terrain_cc)
    t_frag_sl = isl('N fragmentos',       2,   24,   12,  cc=_on_terrain_cc)
    t_deb_sl  = isl('Debris (piezas)',   20,  150,   80,  cc=_on_terrain_cc)
    t_pil_sl  = isl('Pilares',            2,   16,    8,  cc=_on_terrain_cc)
    t_ramp_sl = fsl('Prob. rampas',       0.0,  1.0,  0.55, cc=_on_terrain_cc)
    t_ring_sl = fsl('Radio max. terreno', 8.0, 35.0, 22.0,
                    step=0.5, cc=_on_terrain_cc)

    mc.separator(h=4)
    mc.frameLayout(label='  Skyline avanzado',
                   collapsable=True, collapse=True,
                   borderStyle='etchedIn', marginHeight=3, marginWidth=4)
    mc.columnLayout(adjustableColumn=True, rowSpacing=2)
    t_sky_n_sl   = isl('N skylines',          1,    6,    3,  cc=_on_terrain_cc)
    t_sky_z_sl   = fsl('Distancia Z',       -80.0, -30.0, -55.0,
                        step=1.0, cc=_on_terrain_cc)
    t_sky_sp_sl  = fsl('Expansion X',        10.0,  80.0,  40.0,
                        step=1.0, cc=_on_terrain_cc)
    mc.setParent('..')
    mc.setParent('..')

    mc.separator(h=6)
    mc.button(label='Aleatorio Terreno', h=28,
              backgroundColor=[0.22, 0.36, 0.60],
              command=lambda *_: _random_terrain())
    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    # =========================================================================
    #  BOTONES GLOBALES
    # =========================================================================
    mc.separator(h=8, style='in')
    mc.rowLayout(nc=3, cw3=[107, 107, 107],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[3, 3, 3])
    mc.button(label='Generar',   h=38, backgroundColor=[0.14, 0.56, 0.28],
              command=lambda *_: _on_generar())
    mc.button(label='Aleatorio', h=38, backgroundColor=[0.50, 0.20, 0.54],
              command=lambda *_: _random_all())
    mc.button(label='Resetear',  h=38, backgroundColor=[0.58, 0.16, 0.16],
              command=lambda *_: _on_reset())
    mc.setParent('..')
    mc.separator(h=6, style='none')

    # =========================================================================
    #  SECCIÓN MATERIALES
    # =========================================================================
    mc.separator(h=4, style='none')
    mc.frameLayout(
        label='  >  MATERIALES',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.40, 0.24, 0.06],
        marginHeight=8, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=6)

    mc.text(label='Paleta de color (aiToon / Lambert)',
            align='left', font='smallPlainLabelFont')
    palette_menu = mc.optionMenu(width=316)
    mc.menuItem(label='Lambert (sin paleta)')
    for lbl in PALETTE_LABELS:
        mc.menuItem(label=lbl)

    mc.separator(h=4)
    mc.rowLayout(nc=2, cw2=[152, 152],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Aplicar materiales', h=28,
              backgroundColor=[0.58, 0.38, 0.12],
              command=lambda *_: _apply_materials())
    mc.button(label='Verificar', h=28,
              backgroundColor=[0.44, 0.32, 0.18],
              command=lambda *_: _verify_materials())
    mc.setParent('..')

    mc.separator(h=8)
    mc.text(label='Iluminacion procedural',
            align='left', font='smallPlainLabelFont')
    lighting_menu = mc.optionMenu(width=316)
    for lbl in LIGHTING_LABELS:
        mc.menuItem(label=lbl)

    mc.rowLayout(nc=2, cw2=[152, 152],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Crear iluminacion', h=28,
              backgroundColor=[0.60, 0.40, 0.14],
              command=lambda *_: _apply_lighting())
    mc.button(label='Eliminar luces', h=28,
              backgroundColor=[0.46, 0.16, 0.12],
              command=lambda *_: _remove_lighting())
    mc.setParent('..')

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')

    mc.separator(h=8, style='none')

    # =========================================================================
    #  FUNCIONES INTERNAS
    # =========================================================================

    def _collect_mecha() -> dict:
        head_lbl  = mc.optionMenu(head_style_menu,  q=True, value=True)
        arm_lbl   = mc.optionMenu(arm_style_menu,   q=True, value=True)
        armr_lbl  = mc.optionMenu(arm_style_right_menu, q=True, value=True)
        wing_lbl  = mc.optionMenu(wing_style_menu,  q=True, value=True)
        wingr_lbl = mc.optionMenu(wing_style_right_menu, q=True, value=True)
        torso_lbl = mc.optionMenu(torso_style_menu, q=True, value=True)
        nuc_lbl   = mc.optionMenu(nucleus_style_menu, q=True, value=True)
        pal_lbl   = mc.optionMenu(palette_menu,     q=True, value=True)

        params = {
            'separation':      mc.floatSliderGrp(sep_sl,    q=True, value=True),
            'connector_angle': mc.floatSliderGrp(angle_sl,  q=True, value=True),
            'aggressiveness':  mc.floatSliderGrp(aggr_sl,   q=True, value=True),
            'decay':           mc.floatSliderGrp(decay_sl,  q=True, value=True),
            'height_scale':    mc.floatSliderGrp(height_sl, q=True, value=True),
            'symmetry':        mc.checkBox(sym_cb,    q=True, value=True),
            'use_panels':      mc.checkBox(panels_cb, q=True, value=True),
            'use_arms':        mc.checkBox(arms_cb,   q=True, value=True),
            'use_wings':       mc.checkBox(wings_cb,  q=True, value=True),
            'use_head':        True,
            'head_style':      HEAD_STYLE_LABELS.get(head_lbl,  'helmet'),
            'arm_style':       ARM_STYLE_LABELS.get(arm_lbl,    'standard'),
            'arm_style_right': ARM_STYLE_LABELS.get(armr_lbl,   'standard'),
            'wing_style':      WING_STYLE_LABELS.get(wing_lbl,  'needle'),
            'wing_style_right':WING_STYLE_LABELS.get(wingr_lbl, 'needle'),
            'torso_style':     TORSO_STYLE_LABELS.get(torso_lbl,'core'),
            'nucleus_style':   NUCLEUS_STYLE_LABELS.get(nuc_lbl,'ring'),
            'palette':         PALETTE_LABELS.get(pal_lbl),
        }
        for key, ctrl in {**head_adv, **arm_adv, **wing_adv,
                          **torso_adv, **nucleus_adv}.items():
            params[key] = mc.floatSliderGrp(ctrl, q=True, value=True)
        return params

    def _collect_terrain() -> dict:
        return {
            'monument_scale':    mc.floatSliderGrp(t_mon_sl,    q=True, value=True),
            'platform_count':    mc.intSliderGrp(t_plat_sl,     q=True, value=True),
            'fragment_count':    mc.intSliderGrp(t_frag_sl,     q=True, value=True),
            'debris_count':      mc.intSliderGrp(t_deb_sl,      q=True, value=True),
            'pillar_count':      mc.intSliderGrp(t_pil_sl,      q=True, value=True),
            'ramp_probability':  mc.floatSliderGrp(t_ramp_sl,   q=True, value=True),
            'ring_max_r':        mc.floatSliderGrp(t_ring_sl,   q=True, value=True),
            'skyline_count':     mc.intSliderGrp(t_sky_n_sl,    q=True, value=True),
            'skyline_distance_z':mc.floatSliderGrp(t_sky_z_sl,  q=True, value=True),
            'skyline_spread_x':  mc.floatSliderGrp(t_sky_sp_sl, q=True, value=True),
        }

    # ── Toggle asimetría ──────────────────────────────────────────────────────
    def _toggle_sym(*_):
        if _UI_BUILDING[0]:
            return
        on = mc.checkBox(sym_cb, q=True, value=True)
        for row in _asym_rows:
            if mc.control(row, exists=True):
                mc.control(row, e=True, visible=not on)
        if not _APPLYING_PRESET[0]:
            _rebuild_mecha()

    mc.checkBox(sym_cb, e=True, changeCommand=_toggle_sym)

    # ── Preset de mecha ───────────────────────────────────────────────────────
    def _set_option(menu, mapping, value):
        for lbl, val in mapping.items():
            if val == value:
                mc.optionMenu(menu, e=True, value=lbl)
                return

    def _apply_mecha_preset(lbl):
        key = preset_label_to_key.get(lbl, lbl)
        p = mecha_presets.get(key)
        if not p:
            return
        _APPLYING_PRESET[0] = True
        try:
            mc.floatSliderGrp(sep_sl,    e=True, value=p.get('separation',      0.35))
            mc.floatSliderGrp(angle_sl,  e=True, value=p.get('connector_angle', 15.0))
            mc.floatSliderGrp(aggr_sl,   e=True, value=p.get('aggressiveness',  0.5))
            mc.floatSliderGrp(decay_sl,  e=True, value=p.get('decay',           0.85))
            mc.floatSliderGrp(height_sl, e=True, value=p.get('height_scale',    1.0))
            mc.checkBox(sym_cb,    e=True, value=p.get('symmetry',   True))
            mc.checkBox(panels_cb, e=True, value=p.get('use_panels', True))
            mc.checkBox(arms_cb,   e=True, value=p.get('use_arms',   True))
            mc.checkBox(wings_cb,  e=True, value=p.get('use_wings',  True))
            _set_option(head_style_menu,  HEAD_STYLE_LABELS,
                        p.get('head_style',    'helmet'))
            _set_option(arm_style_menu,   ARM_STYLE_LABELS,
                        p.get('arm_style',     'standard'))
            _set_option(wing_style_menu,  WING_STYLE_LABELS,
                        p.get('wing_style',    'needle'))
            _set_option(torso_style_menu, TORSO_STYLE_LABELS,
                        p.get('torso_style',   'core'))
            _set_option(nucleus_style_menu, NUCLEUS_STYLE_LABELS,
                        p.get('nucleus_style', 'ring'))
            for key_p, ctrl in {**head_adv, **arm_adv, **wing_adv,
                                 **torso_adv, **nucleus_adv}.items():
                if key_p in p:
                    mc.floatSliderGrp(ctrl, e=True, value=p[key_p])
        finally:
            _APPLYING_PRESET[0] = False
        _rebuild_mecha()

    mc.optionMenu(mecha_preset_menu, e=True,
                  changeCommand=_apply_mecha_preset)

    # ── Limpieza de escena ────────────────────────────────────────────────────
    def _find_scene_group():
        return next((n for n in (mc.ls('RetroMecha_Scene_*',
                                       type='transform') or [])
                     if mc.objExists(n)), None)

    def _find_mecha_group():
        return next((n for n in (mc.ls('RetroMecha_*',
                                       type='transform') or [])
                     if 'Scene' not in n and mc.objExists(n)), None)

    def _del(*nodes):
        valid = [n for n in nodes if n and mc.objExists(n)]
        if valid:
            try: mc.delete(valid)
            except Exception:
                for n in valid:
                    try: mc.delete(n)
                    except: pass

    def _clean_scene():
        _del(*[n for pat in SCENE_PATTERNS
               for n in (mc.ls(pat, type='transform') or [])])

    def _clean_mecha():
        _del(*[n for pat in MECHA_PATTERNS
               for n in (mc.ls(pat, type='transform') or [])
               if 'Scene' not in n])

    def _clean_terrain():
        _del(*[n for pat in TERRAIN_PATTERNS
               for n in (mc.ls(pat, type='transform') or [])])

    def _lift(grp):
        try:
            bb = mc.exactWorldBoundingBox(grp)
            lift = 0.5 - bb[1]
            if abs(lift) > 0.01:
                mc.move(0, lift, 0, grp, relative=True, worldSpace=True)
        except Exception:
            pass

    def _mecha_bbox():
        g = _find_mecha_group()
        if g and mc.objExists(g):
            try: return tuple(mc.exactWorldBoundingBox(g))
            except: pass
        return (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)

    def _scene_wrap(fn):
        try: mc.undoInfo(openChunk=True)
        except: pass
        try: mc.refresh(suspend=True)
        except: pass
        try: return fn()
        finally:
            try: mc.refresh(suspend=False); mc.refresh(force=True)
            except: pass
            try: mc.undoInfo(closeChunk=True)
            except: pass

    def _auto_apply_materials(root):
        """Aplica la paleta activa si está configurada."""
        pal_lbl = mc.optionMenu(palette_menu, q=True, value=True)
        palette = PALETTE_LABELS.get(pal_lbl)
        if not palette:
            return
        try:
            from utils.material_assigner import assign_palette_to_group
            assign_palette_to_group(root, palette)
        except Exception as e:
            print(f'[RetroMecha][Materials] Auto-apply: {e}')

    # ── Rebuild ───────────────────────────────────────────────────────────────
    def _rebuild_mecha(*_):
        def _work():
            seed = _SEED[0] if isinstance(_SEED[0], int) else resolve_seed()
            _SEED[0] = seed
            params = _collect_mecha()
            params['_seed'] = seed
            _clean_mecha()
            from core.mecha_builder import MechaBuilder
            grp = MechaBuilder(params, seed=seed).build()
            if grp and mc.objExists(grp):
                _lift(grp)
                mc.select(grp)
                mc.viewFit()
        return _scene_wrap(_work)

    def _rebuild_terrain_only(*_):
        def _work():
            seed = _SEED[0] if isinstance(_SEED[0], int) else resolve_seed()
            _SEED[0] = seed
            params = _collect_mecha()
            params['_seed'] = seed
            preset_name = PRESET_MAP.get(
                mc.optionMenu(preset_menu, q=True, value=True), 'avanzada')
            overrides = _collect_terrain()
            _clean_terrain()
            from terrain.terrain_builder import TerrainBuilder
            tb = TerrainBuilder(params=params, seed=seed + 1000,
                                preset_name=preset_name,
                                mecha_bbox=_mecha_bbox())
            tb.preset.update(overrides)
            grp = tb.build()
            if grp and mc.objExists(grp):
                mc.select(grp)
                mc.viewFit()
        return _scene_wrap(_work)

    def _on_generar(*_):
        def _work():
            seed = resolve_seed()
            params = _collect_mecha()
            params['_seed'] = seed
            preset_name = PRESET_MAP.get(
                mc.optionMenu(preset_menu, q=True, value=True), 'avanzada')
            overrides = _collect_terrain()

            _clean_scene()
            _clean_mecha()
            _clean_terrain()

            scene_grp = mc.group(empty=True, name='RetroMecha_Scene_#')

            from core.mecha_builder import MechaBuilder
            mecha_grp = MechaBuilder(params, seed=seed).build()
            if mecha_grp and mc.objExists(mecha_grp):
                _lift(mecha_grp)
                mc.parent(mecha_grp, scene_grp)

            from terrain.terrain_builder import TerrainBuilder
            tb = TerrainBuilder(params=params, seed=seed + 1000,
                                preset_name=preset_name,
                                mecha_bbox=_mecha_bbox())
            tb.preset.update(overrides)
            terrain_grp = tb.build()
            if terrain_grp and mc.objExists(terrain_grp):
                mc.parent(terrain_grp, scene_grp)

            # Auto-aplicar materiales si hay paleta activa
            _auto_apply_materials(scene_grp)

            mc.select(scene_grp)
            mc.viewFit()
        return _scene_wrap(_work)

    # ── Materiales ────────────────────────────────────────────────────────────
    def _apply_materials(*_):
        from utils.maya_materials import set_active_palette
        from utils.material_assigner import assign_palette_to_group
        pal_lbl = mc.optionMenu(palette_menu, q=True, value=True)
        palette = PALETTE_LABELS.get(pal_lbl)
        set_active_palette(palette)
        scene = _find_scene_group()
        targets = ([scene] if scene else
                   ([g for g in [_find_mecha_group()] if g] +
                    (mc.ls('rm_terrain_*', type='transform') or [])))
        if not targets:
            print('[RetroMecha][Materials] No hay escena')
            return
        if palette:
            for t in targets:
                try:
                    assign_palette_to_group(t, palette)
                except Exception as e:
                    print(f'[RetroMecha][Materials] {t}: {e}')
            print(f'[RetroMecha][Materials] "{palette}" aplicado a '
                  f'{len(targets)} grupo(s)')
        else:
            print('[RetroMecha][Materials] Modo Lambert activo')

    def _verify_materials(*_):
        from utils.maya_materials import verify_materials_on_group
        scene = _find_scene_group()
        targets = ([scene] if scene else
                   ([g for g in [_find_mecha_group()] if g] +
                    (mc.ls('rm_terrain_*', type='transform') or [])))
        if not targets:
            print('[RetroMecha][Materials] No hay escena')
            return
        ok = sin = 0
        for t in targets:
            r = verify_materials_on_group(t)
            ok  += r['assigned']
            sin += r['unassigned']
            if r['unassigned']:
                print(f'  {t}: {r["assigned"]} OK / '
                      f'{r["unassigned"]} sin material')
        print(f'[RetroMecha][Materials] Total: {ok} con material, '
              f'{sin} sin material')

    # ── Iluminación ───────────────────────────────────────────────────────────
    def _apply_lighting(*_):
        from utils.lighting import apply_lighting
        lbl = mc.optionMenu(lighting_menu, q=True, value=True)
        apply_lighting(LIGHTING_LABELS.get(lbl, 'studio'), sky_dome=True)

    def _remove_lighting(*_):
        from utils.lighting import remove_lighting
        remove_lighting()
        print('[RetroMecha][Lighting] Luces eliminadas')

    # ── Aleatorio ─────────────────────────────────────────────────────────────
    def _random_mecha(*_):
        _APPLYING_PRESET[0] = True
        try:
            mc.optionMenu(mecha_preset_menu, e=True, value='Custom')
            mc.floatSliderGrp(sep_sl,    e=True, value=random.uniform(0.10, 0.80))
            mc.floatSliderGrp(angle_sl,  e=True, value=random.uniform(0.0,  45.0))
            mc.floatSliderGrp(aggr_sl,   e=True, value=random.uniform(0.0,   1.0))
            mc.floatSliderGrp(decay_sl,  e=True, value=random.uniform(0.50,  1.0))
            mc.floatSliderGrp(height_sl, e=True, value=random.uniform(0.50,  2.0))
            mc.checkBox(sym_cb,    e=True, value=random.choice([True, False]))
            mc.checkBox(panels_cb, e=True, value=random.random() > 0.2)
            mc.checkBox(arms_cb,   e=True, value=random.random() > 0.15)
            mc.checkBox(wings_cb,  e=True, value=random.random() > 0.25)
            mc.optionMenu(head_style_menu,  e=True,
                          value=random.choice(list(HEAD_STYLE_LABELS.keys())))
            mc.optionMenu(arm_style_menu,   e=True,
                          value=random.choice(list(ARM_STYLE_LABELS.keys())))
            mc.optionMenu(arm_style_right_menu, e=True,
                          value=random.choice(list(ARM_STYLE_LABELS.keys())))
            mc.optionMenu(wing_style_menu,  e=True,
                          value=random.choice(list(WING_STYLE_LABELS.keys())))
            mc.optionMenu(wing_style_right_menu, e=True,
                          value=random.choice(list(WING_STYLE_LABELS.keys())))
            mc.optionMenu(torso_style_menu, e=True,
                          value=random.choice(list(TORSO_STYLE_LABELS.keys())))
            mc.optionMenu(nucleus_style_menu, e=True,
                          value=random.choice(list(NUCLEUS_STYLE_LABELS.keys())))
            for ctrl_dict in (head_adv, arm_adv, wing_adv, torso_adv, nucleus_adv):
                for ctrl in ctrl_dict.values():
                    info = mc.floatSliderGrp(ctrl, q=True, min=True), \
                           mc.floatSliderGrp(ctrl, q=True, max=True)
                    mc.floatSliderGrp(ctrl, e=True,
                                      value=random.uniform(info[0], info[1]))
        finally:
            _APPLYING_PRESET[0] = False
        _SEED[0] = random.randint(0, 99999)
        mc.textField(seed_field, e=True, text=str(_SEED[0]))
        _rebuild_mecha()

    def _random_terrain(*_):
        mc.floatSliderGrp(t_mon_sl,  e=True, value=random.uniform(3.0,   9.0))
        mc.intSliderGrp(t_plat_sl,   e=True, value=random.randint(3,    16))
        mc.intSliderGrp(t_frag_sl,   e=True, value=random.randint(2,    24))
        mc.intSliderGrp(t_deb_sl,    e=True, value=random.randint(20,  150))
        mc.intSliderGrp(t_pil_sl,    e=True, value=random.randint(2,    16))
        mc.floatSliderGrp(t_ramp_sl, e=True, value=random.uniform(0.0,   1.0))
        mc.floatSliderGrp(t_ring_sl, e=True, value=random.uniform(10.0, 35.0))
        mc.intSliderGrp(t_sky_n_sl,  e=True, value=random.randint(1,     6))
        mc.floatSliderGrp(t_sky_z_sl,e=True, value=random.uniform(-80.0,-30.0))
        mc.floatSliderGrp(t_sky_sp_sl,e=True,value=random.uniform(20.0, 70.0))
        _rebuild_terrain_only()

    def _random_all(*_):
        _random_mecha()
        _random_terrain()

    def _on_reset(*_):
        def _work():
            _clean_scene()
            _clean_mecha()
            _clean_terrain()
            mc.textField(seed_field, e=True, text='')
            _SEED[0] = None
            print('[RetroMecha] Escena limpiada')
        _scene_wrap(_work)

    # ── Finalizar ─────────────────────────────────────────────────────────────
    _UI_BUILDING[0] = False
    _toggle_sym()       # estado inicial de filas asimétricas

    mc.showWindow(win)
    print('[RetroMecha] UI v5 abierta')