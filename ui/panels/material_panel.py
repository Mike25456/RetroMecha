"""MATERIALES section of the RetroMecha UI.

Coexisten dos sistemas de materiales:
  - Lambert presets (Mike): rm_white_armor_mat, rm_graphite_mat, ...
  - aiToon palettes (Ricardo): industrial, oxidado, artico, carmesi
y un bloque de iluminacion procedural con aiSkyDomeLight.
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
    'Armadura': 'rm_white_armor_mat',
    'Estructura': 'rm_graphite_mat',
    'Brillo': 'rm_cyan_glow_mat',
    'Terreno base': 'rm_terrain_base_mat',
    'Terreno oscuro': 'rm_terrain_dark_mat',
    'Terreno acento': 'rm_terrain_accent_mat',
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


def build(wrapped=True):
    if wrapped:
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

    if presets_list:
        _preset_labels = {p: p for p in presets_list}
        mc.rowLayout(nc=2, cw2=[128, 140],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label='Paleta Lambert', align='right', font='smallPlainLabelFont',
                annotation='Aplica una paleta Lambert predefinida')
        mc.optionMenu(changeCommand=lambda label: _apply_material_preset(label, _preset_labels))
        for p in presets_list:
            mc.menuItem(label=p)
        mc.setParent('..')
    else:
        mc.text(label='(sin presets Lambert)', align='left', font='smallPlainLabelFont')

    mc.separator(h=4)
    mc.rowLayout(nc=2, cw2=[128, 140],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Shader', align='right', font='smallPlainLabelFont',
            annotation='Selecciona un material para editar sus propiedades')
    mc.optionMenu(changeCommand=_on_shader_sel,
                  annotation='Cada shader se aplica a multiples piezas del mecha')
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
                           annotation='Brillo auto-emitido (solo para shader Brillo)'))
    mc.control(state.get('i_sl'), e=True, visible=False)

    _update_shader_sliders()

    mc.separator(h=8)
    mc.text(label='Paleta aiToon (Arnold)', align='left',
            font='smallPlainLabelFont')
    mc.rowLayout(nc=2, cw2=[152, 152],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    aitoon_menu = mc.optionMenu(
        annotation='Selecciona una paleta aiToon con ramps y silhouette')
    mc.menuItem(label='(ninguna)')
    for lbl in _PALETTE_LABELS:
        mc.menuItem(label=lbl)
    state.reg('aitoon_menu', aitoon_menu)
    mc.button(label='Aplicar aiToon', h=24,
              backgroundColor=[0.58, 0.38, 0.12],
              command=lambda *_: _apply_aitoon_palette(),
              annotation='Aplica la paleta aiToon al mecha en escena')
    mc.setParent('..')

    mc.separator(h=8)
    mc.text(label='Iluminacion procedural', align='left',
            font='smallPlainLabelFont')
    lighting_menu = mc.optionMenu(width=308,
                                   annotation='Preset de iluminacion (incluye aiSkyDomeLight)')
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
    if wrapped:
        mc.setParent('..')


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


def _apply_material_preset(label, preset_labels):
    key = preset_labels.get(label, label)
    apply_preset(key)
    _update_shader_sliders()


def _find_mecha_group():
    from ui import scene_utils as sc
    return sc.find_mecha_group()


def _apply_aitoon_palette(*_):
    label = mc.optionMenu(state.get('aitoon_menu'), q=True, value=True)
    palette = _PALETTE_LABELS.get(label)
    if not palette:
        print('[RetroMecha][aiToon] Selecciona una paleta antes de aplicar')
        return
    grp = _find_mecha_group()
    if not grp:
        print('[RetroMecha][aiToon] No hay mecha en escena')
        return
    try:
        from utils.material_assigner import assign_palette_to_group, clear_material_cache
        clear_material_cache()
        assign_palette_to_group(grp, palette)
    except ImportError as e:
        print(f'[RetroMecha][aiToon] material_assigner no disponible: {e}')
    except Exception as e:
        print(f'[RetroMecha][aiToon] Error aplicando paleta: {e}')


def apply_palette_quick(palette_key):
    """Aplica una paleta aiToon directamente por key (modo Rápido)."""
    grp = _find_mecha_group()
    if not grp:
        print('[RetroMecha][aiToon] No hay mecha en escena')
        return
    try:
        from utils.material_assigner import assign_palette_to_group, clear_material_cache
        clear_material_cache()
        assign_palette_to_group(grp, palette_key)
        print(f'[RetroMecha][aiToon] Paleta {palette_key} aplicada')
    except ImportError as e:
        print(f'[RetroMecha][aiToon] material_assigner no disponible: {e}')
    except Exception as e:
        print(f'[RetroMecha][aiToon] Error aplicando paleta: {e}')


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
