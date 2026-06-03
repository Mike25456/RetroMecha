"""Panel MATERIALES (pestaña Escena) — solo Viewport 2.0 / Lambert.

Los materiales Arnold y la iluminación se gestionan desde la pestaña Rendering.
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

_current_shader = ['rm_white_armor_mat']
_APPLYING_SHADER = [False]


def build():
    mc.frameLayout(
        label='  >  MATERIALES  (Viewport 2.0)',
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

    # ── Preset Lambert + botón aplicar ──────────────────────────
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

    # ── Editor individual de shader ─────────────────────────────
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
        annotation='Color principal del shader',
    ))
    state.reg('d_sl', fsl('Difuso', 0.0, 1.0, 0.82, on_cc=_set_shader_diffuse,
                          annotation='Intensidad difusa'))
    state.reg('i_sl', fsl('Brillo', 0.0, 1.0, 0.0, on_cc=_set_shader_incandescence,
                          annotation='Brillo auto-emitido (solo shader Brillo)'))
    mc.control(state.get('i_sl'), e=True, visible=False)

    _update_shader_sliders()

    mc.setParent('..')
    mc.setParent('..')


# ── helpers ──────────────────────────────────────────────────

def _find_mecha_group():
    from ui import scene_utils as sc
    return sc.find_mecha_group()


# ── VP2.0 callbacks ───────────────────────────────────────────

def _apply_vp2(*_):
    """Aplica el preset Lambert seleccionado y reasigna shaders VP2.0 al mecha."""
    preset_menu = state.get('lambert_preset_menu')
    if preset_menu and mc.optionMenu(preset_menu, exists=True):
        label = mc.optionMenu(preset_menu, q=True, value=True)
        apply_preset(label)
        _update_shader_sliders()

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
