"""MATERIALES section of the RetroMecha UI."""

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

_current_shader = ['rm_white_armor_mat']
_APPLYING_SHADER = [False]


def build():
    mc.frameLayout(
        label='  >  MATERIALES',
        collapsable=True, collapse=True,
        borderStyle='etchedIn',
        backgroundColor=[0.22, 0.20, 0.10],
        marginHeight=8, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)

    # ensure all shaders exist
    for shader_name in SHADER_NAMES:
        ensure_material(shader_name)

    presets_list = list_presets()
    _current_shader[0] = 'rm_white_armor_mat'

    # ── preset dropdown ──
    if presets_list:
        _preset_labels = {p: p for p in presets_list}
        mc.rowLayout(nc=2, cw2=[128, 140],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label='Paleta', align='right', font='smallPlainLabelFont',
                annotation='Aplica una paleta de colores predefinida')
        mc.optionMenu(changeCommand=lambda label: _apply_material_preset(label, _preset_labels))
        for p in presets_list:
            mc.menuItem(label=p)
        mc.setParent('..')
    else:
        mc.text(label='(sin presets)', align='left', font='smallPlainLabelFont')

    # ── shader selector ──
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

    # ── color slider ──
    state.reg('color_sl', mc.colorSliderGrp(
        label='Color', rgb=(0.86, 0.84, 0.78),
        columnWidth3=[60, 180, 52],
        changeCommand=_set_shader_color,
        annotation='Color principal del shader (click para abrir selector)',
    ))

    # ── diffuse slider ──
    state.reg('d_sl', fsl('Difuso', 0.0, 1.0, 0.82, on_cc=_set_shader_diffuse,
                           annotation='Intensidad de luz difusa del material'))

    # ── glow slider ──
    state.reg('i_sl', fsl('Brillo', 0.0, 1.0, 0.0, on_cc=_set_shader_incandescence,
                           annotation='Brillo auto-emitido (solo para shader Brillo)'))
    mc.control(state.get('i_sl'), e=True, visible=False)

    _update_shader_sliders()

    mc.setParent('..')
    mc.setParent('..')


# ── callbacks ────────────────────────────────────────────────

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
