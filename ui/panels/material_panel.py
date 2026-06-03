"""MATERIALES section of the RetroMecha UI.

Dos sistemas de materiales completamente independientes:
  - Viewport 2.0 (Lambert): rm_white_armor_mat, rm_graphite_mat, ...
  - Arnold (aiToon):        paletas industrial, oxidado, artico, carmesi
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl

from materials.presets import SHADER_NAMES, list_presets, apply_preset
from utils.maya_materials import ensure_material

_SHADER_LABELS = {
    'Armadura':      'rm_white_armor_mat',
    'Estructura':    'rm_graphite_mat',
    'Brillo':        'rm_cyan_glow_mat',
    'Terreno base':  'rm_terrain_base_mat',
    'Terreno oscuro':'rm_terrain_dark_mat',
    'Terreno acento':'rm_terrain_accent_mat',
}

_PALETTE_LABELS = {
    'Industrial': 'industrial',
    'Oxidado':    'oxidado',
    'Artico':     'artico',
    'Carmesi':    'carmesi',
}

_LIGHTING_LABELS = {
    'Estudio':   'studio',
    'Dramatico': 'dramatic',
    'Retro':     'retro',
}

_current_shader = ['rm_white_armor_mat']
_APPLYING_SHADER = [False]


def build():
    mc.frameLayout(
        label='  >  MATERIALES',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.40, 0.24, 0.06],
        marginHeight=8, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)

    for shader_name in SHADER_NAMES:
        ensure_material(shader_name)

    presets_list = list_presets()
    _current_shader[0] = 'rm_white_armor_mat'

    # ── VIEWPORT 2.0 (Lambert) ─────────────────────────────────
    mc.text(
        label='  VIEWPORT 2.0  (Lambert)',
        align='left', font='boldLabelFont',
        backgroundColor=[0.22, 0.18, 0.10],
    )

    # Preset dropdown + botón aplicar
    mc.rowLayout(nc=3, cw3=[100, 130, 72],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[0, 4, 4])
    mc.text(label='Paleta', align='right', font='smallPlainLabelFont')
    if presets_list:
        lambert_menu = mc.optionMenu(
            annotation='Preset Lambert: colores base de los 6 shaders')
        for p in presets_list:
            mc.menuItem(label=p)
        state.reg('lambert_preset_menu', lambert_menu)
    else:
        mc.text(label='(sin presets)', align='left', font='smallPlainLabelFont')
        state.reg('lambert_preset_menu', None)
    mc.button(
        label='Aplicar VP2.0', h=22,
        backgroundColor=[0.30, 0.44, 0.22],
        command=lambda *_: _apply_vp2(),
        annotation='Aplica el preset Lambert y reasigna shaders VP2.0 al mecha',
    )
    mc.setParent('..')

    # Editor individual de shader
    mc.separator(h=4)
    mc.rowLayout(nc=2, cw2=[128, 140],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Editar shader', align='right', font='smallPlainLabelFont',
            annotation='Selecciona un material para editar sus propiedades')
    mc.optionMenu(changeCommand=_on_shader_sel,
                  annotation='Cada shader se aplica a múltiples piezas del mecha')
    for label in _SHADER_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    state.reg('color_sl', mc.colorSliderGrp(
        label='Color', rgb=(0.86, 0.84, 0.78),
        columnWidth3=[60, 180, 52],
        changeCommand=_set_shader_color,
        annotation='Color principal del shader (click para abrir selector)',
    ))
    state.reg('d_sl', fsl('Difuso', 0.0, 1.0, 0.82, on_cc=_set_shader_diffuse,
                          annotation='Intensidad de luz difusa del material'))
    state.reg('i_sl', fsl('Brillo', 0.0, 1.0, 0.0, on_cc=_set_shader_incandescence,
                          annotation='Brillo auto-emitido (solo shader Brillo)'))
    mc.control(state.get('i_sl'), e=True, visible=False)

    _update_shader_sliders()

    # ── ARNOLD (aiToon) ────────────────────────────────────────
    mc.separator(h=6)
    mc.text(
        label='  ARNOLD  (aiToon)',
        align='left', font='boldLabelFont',
        backgroundColor=[0.18, 0.18, 0.28],
    )

    # Indicador de disponibilidad de Arnold
    state.reg('arnold_status_text', mc.text(
        label=_arnold_status_label(),
        align='left', font='smallPlainLabelFont',
        annotation='Estado del renderer Arnold en la sesión actual',
    ))

    mc.rowLayout(nc=3, cw3=[100, 130, 72],
                 columnAttach3=['both', 'both', 'both'],
                 columnOffset3=[0, 4, 4])
    mc.text(label='Paleta', align='right', font='smallPlainLabelFont')
    aitoon_menu = mc.optionMenu(
        annotation='Paleta aiToon con ramps y silhouette (requiere Arnold)')
    mc.menuItem(label='(ninguna)')
    for lbl in _PALETTE_LABELS:
        mc.menuItem(label=lbl)
    state.reg('aitoon_menu', aitoon_menu)
    mc.button(
        label='Aplicar Arnold', h=22,
        backgroundColor=[0.58, 0.38, 0.12],
        command=lambda *_: _apply_aitoon_palette(),
        annotation='Aplica la paleta aiToon al mecha (requiere Arnold/MtoA)',
    )
    mc.setParent('..')

    # ── ILUMINACIÓN ────────────────────────────────────────────
    mc.separator(h=6)
    mc.text(
        label='  ILUMINACION',
        align='left', font='boldLabelFont',
        backgroundColor=[0.20, 0.20, 0.14],
    )
    lighting_menu = mc.optionMenu(width=308,
                                  annotation='Preset de iluminación (incluye aiSkyDomeLight)')
    for lbl in _LIGHTING_LABELS:
        mc.menuItem(label=lbl)
    state.reg('lighting_menu', lighting_menu)

    mc.rowLayout(nc=2, cw2=[152, 152],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.button(label='Crear iluminacion', h=24,
              backgroundColor=[0.60, 0.40, 0.14],
              command=lambda *_: _apply_lighting(),
              annotation='Crea luces direccionales + aiSkyDomeLight si hay Arnold')
    mc.button(label='Eliminar luces', h=24,
              backgroundColor=[0.46, 0.16, 0.12],
              command=lambda *_: _remove_lighting(),
              annotation='Elimina luces y sky dome creados por RetroMecha')
    mc.setParent('..')

    mc.setParent('..')
    mc.setParent('..')


# ── helpers ──────────────────────────────────────────────────

def _find_mecha_group():
    from ui import scene_utils as sc
    return sc.find_mecha_group()


def _arnold_status_label() -> str:
    try:
        from utils.material_assigner import _has_arnold
        available = _has_arnold()
    except Exception:
        available = False
    if available:
        return '  Arnold disponible — se usará aiToon'
    return '  Arnold no detectado — se usará Lambert como fallback'


# ── VP2.0 callbacks ───────────────────────────────────────────

def _apply_vp2(*_):
    """Aplica el preset Lambert seleccionado y reasigna shaders VP2.0 al mecha."""
    # 1. Aplicar colores del preset al conjunto de shaders Lambert
    preset_menu = state.get('lambert_preset_menu')
    if preset_menu and mc.optionMenu(preset_menu, exists=True):
        label = mc.optionMenu(preset_menu, q=True, value=True)
        apply_preset(label)
        _update_shader_sliders()

    # 2. Reasignar shaders Lambert a todos los meshes del mecha
    mecha_grp = _find_mecha_group()
    if not mecha_grp:
        print('[RetroMecha][VP2.0] No hay mecha en escena')
        return
    try:
        from materials.materializer import materialize_mecha
        materialize_mecha(mecha_grp)
        print('[RetroMecha][VP2.0] Materiales Lambert aplicados al mecha')
    except Exception as e:
        print(f'[RetroMecha][VP2.0] Error: {e}')


def _set_shader_color(*_):
    if _APPLYING_SHADER[0]:
        return
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    try:
        rgb = mc.colorSliderGrp(state.get('color_sl'), q=True, rgb=True)
        mc.setAttr(f'{sh}.color',
                   float(rgb[0]), float(rgb[1]), float(rgb[2]),
                   type='double3')
    except Exception:
        pass


def _set_shader_diffuse(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh):
        try:
            mc.setAttr(f'{sh}.diffuse', val)
        except Exception:
            pass


def _set_shader_incandescence(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh) and sh == 'rm_cyan_glow_mat':
        try:
            mc.setAttr(f'{sh}.incandescence', val, val, val, type='double3')
        except Exception:
            pass


def _update_shader_sliders():
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    _APPLYING_SHADER[0] = True
    try:
        col = mc.getAttr(f'{sh}.color')[0]
        mc.colorSliderGrp(state.get('color_sl'), e=True, rgb=col)
        d = mc.getAttr(f'{sh}.diffuse')
        mc.floatSliderGrp(state.get('d_sl'), e=True, value=d)
        is_glow = (sh == 'rm_cyan_glow_mat')
        mc.control(state.get('i_sl'), e=True, visible=is_glow)
        if is_glow:
            inc = mc.getAttr(f'{sh}.incandescence')[0]
            mc.floatSliderGrp(state.get('i_sl'), e=True, value=inc[0])
    except Exception:
        pass
    finally:
        _APPLYING_SHADER[0] = False


def _on_shader_sel(label):
    sh = _SHADER_LABELS.get(label)
    if sh:
        _current_shader[0] = sh
        _update_shader_sliders()


# ── Arnold callbacks ──────────────────────────────────────────

def _apply_aitoon_palette(*_):
    label = mc.optionMenu(state.get('aitoon_menu'), q=True, value=True)
    palette = _PALETTE_LABELS.get(label)
    if not palette:
        print('[RetroMecha][Arnold] Selecciona una paleta antes de aplicar')
        return
    grp = _find_mecha_group()
    if not grp:
        print('[RetroMecha][Arnold] No hay mecha en escena')
        return
    try:
        from utils.material_assigner import assign_palette_to_group, clear_material_cache
        clear_material_cache()
        assign_palette_to_group(grp, palette)
        # Refrescar indicador de Arnold tras aplicar
        status = state.get('arnold_status_text')
        if status and mc.text(status, exists=True):
            mc.text(status, e=True, label=_arnold_status_label())
    except ImportError as e:
        print(f'[RetroMecha][Arnold] material_assigner no disponible: {e}')
    except Exception as e:
        print(f'[RetroMecha][Arnold] Error aplicando paleta: {e}')


# ── Iluminación callbacks ─────────────────────────────────────

def _apply_lighting(*_):
    label = mc.optionMenu(state.get('lighting_menu'), q=True, value=True)
    preset = _LIGHTING_LABELS.get(label, 'studio')
    try:
        from utils.lighting import apply_lighting
        apply_lighting(preset, sky_dome=True)
    except Exception as e:
        print(f'[RetroMecha][Lighting] {e}')


def _remove_lighting(*_):
    try:
        from utils.lighting import remove_lighting
        remove_lighting()
        print('[RetroMecha][Lighting] Luces eliminadas')
    except Exception as e:
        print(f'[RetroMecha][Lighting] {e}')
