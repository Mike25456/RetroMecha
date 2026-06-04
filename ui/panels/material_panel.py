"""Panel MATERIALES (pestaña Escena / panel Pro).

Gestiona los shaders aiStandardSurface del mecha y terreno (requiere Arnold).

Estructura:
  - Paleta (preset de colores)
  - Selector de shader individual (Armadura, Estructura, ...) + sliders
  - Boton 'Aplicar materiales al mecha' al final (full width, estilo terreno)

Tambien expone apply_palette_quick(palette_key) para que el modo Rapido
aplique una paleta aiToon directamente sin tocar la UI.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.widgets import fsl

from materials.presets import SHADER_NAMES, list_presets, apply_preset
from utils.maya_materials import (
    ensure_material, set_semantic_attr, get_semantic_attr,
)

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
        label='  >  MATERIALES',
        collapsable=True, collapse=True,
        backgroundColor=[0.40, 0.24, 0.06],
        marginHeight=8, marginWidth=6,
    )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)

    for shader_name in SHADER_NAMES:
        ensure_material(shader_name)

    presets_list = list_presets()
    _current_shader[0] = 'rm_white_armor_mat'

    # ── Paleta (preset de colores) ────────────────────────────────
    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Paleta', align='right', font='smallPlainLabelFont')
    if presets_list:
        preset_menu = mc.optionMenu(
            changeCommand=lambda *_: _on_preset_changed(),
            annotation='Preset de colores aplicado a los 6 shaders del mecha y terreno')
        for p in presets_list:
            mc.menuItem(label=p)
        state.reg('materials_preset_menu', preset_menu)
    else:
        mc.text(label='(sin presets)', align='left', font='smallPlainLabelFont')
        state.reg('materials_preset_menu', None)
    mc.setParent('..')

    # ── Editor individual de shader ───────────────────────────────
    mc.separator(h=6)
    mc.rowLayout(nc=2, cw2=[128, 180],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[0, 4])
    mc.text(label='Editar shader', align='right', font='smallPlainLabelFont',
            annotation='Selecciona un material para editar sus propiedades')
    mc.optionMenu(changeCommand=_on_shader_sel,
                  annotation='Cada shader se aplica a multiples piezas del mecha o terreno')
    for label in _SHADER_LABELS:
        mc.menuItem(label=label)
    mc.setParent('..')

    state.reg('color_sl', mc.colorSliderGrp(
        label='Color', rgb=(0.86, 0.84, 0.78),
        columnWidth3=[60, 180, 52],
        changeCommand=_set_shader_color,
        annotation='Color principal del shader (baseColor de aiStandardSurface)',
    ))
    state.reg('d_sl', fsl('Difuso', 0.0, 1.0, 0.82, on_cc=_set_shader_diffuse,
                          annotation='Peso difuso (base de aiStandardSurface)'))
    state.reg('i_sl', fsl('Brillo', 0.0, 1.0, 0.0, on_cc=_set_shader_incandescence,
                          annotation='Emision auto (emissionColor, solo shader Brillo)'))
    mc.control(state.get('i_sl'), e=True, visible=False)

    _update_shader_sliders()

    # ── Aplicar materiales (estilo terreno, full width al final) ──
    mc.separator(h=8)
    mc.button(
        label='Aplicar materiales al mecha', h=28,
        backgroundColor=[0.62, 0.36, 0.10],
        command=lambda *_: _apply_materials(),
        annotation='Aplica la paleta actual y reasigna los shaders al mecha y terreno',
    )

    mc.separator(h=4, style='none')
    mc.setParent('..')
    mc.setParent('..')


# ── helpers ──────────────────────────────────────────────────

def _find_mecha_group():
    from ui import scene_utils as sc
    return sc.find_mecha_group()


def _find_scene_group():
    from ui import scene_utils as sc
    return sc.find_scene_group()


# ── callbacks ─────────────────────────────────────────────────

def _on_preset_changed(*_):
    """Al cambiar la paleta, actualizar los shaders en memoria + sliders + sky."""
    preset_menu = state.get('materials_preset_menu')
    if not preset_menu or not mc.optionMenu(preset_menu, exists=True):
        return
    label = mc.optionMenu(preset_menu, q=True, value=True)
    apply_preset(label)
    _update_shader_sliders()
    # Recolorear el sky si existe (composicion armonica con la paleta)
    try:
        from materials.sky_material import update_sky_ramp, has_sky_material
        if has_sky_material():
            update_sky_ramp(label)
    except Exception:
        pass
    # Recolorear las luces palette-aware (luz_ambiente + veam_light_*)
    try:
        from utils import lighting
        if lighting.has_rm_lights():
            lighting.set_palette(label)
    except Exception:
        pass


def _apply_materials(*_):
    """Aplica la paleta + reasigna shaders al mecha, terreno y sky."""
    palette_label = current_palette_label()
    preset_menu = state.get('materials_preset_menu')
    if preset_menu and mc.optionMenu(preset_menu, exists=True):
        apply_preset(palette_label)
        _update_shader_sliders()

    mecha_grp = _find_mecha_group()
    scene_grp = _find_scene_group()
    target = scene_grp or mecha_grp
    if not target:
        print('[RetroMecha][Mat] No hay mecha en escena')
        return

    try:
        from materials.materializer import materialize_mecha, materialize_terrain
        if mecha_grp:
            materialize_mecha(mecha_grp)
        if scene_grp:
            for child in (mc.listRelatives(scene_grp, children=True, type='transform') or []):
                if child.startswith('rm_terrain_'):
                    materialize_terrain(child)
        print('[RetroMecha][Mat] Materiales aplicados')
    except Exception as e:
        print(f'[RetroMecha][Mat] Error: {e}')

    # Sky material acorde a la paleta (composicion armonica)
    try:
        from materials.sky_material import (
            create_sky_material, update_sky_ramp, has_sky_material,
        )
        if mc.objExists('sky'):
            if has_sky_material():
                update_sky_ramp(palette_label)
            else:
                create_sky_material(palette_label)
    except Exception as e:
        print(f'[RetroMecha][Mat] Sky: {e}')


def current_palette_label() -> str:
    """Devuelve el label del preset seleccionado en el menu (Default si no hay)."""
    preset_menu = state.get('materials_preset_menu')
    if preset_menu and mc.optionMenu(preset_menu, exists=True):
        try:
            return mc.optionMenu(preset_menu, q=True, value=True) or 'Default'
        except Exception:
            pass
    return 'Default'


def _set_shader_color(*_):
    if _APPLYING_SHADER[0]:
        return
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    rgb = mc.colorSliderGrp(state.get('color_sl'), q=True, rgb=True)
    set_semantic_attr(sh, 'color', tuple(float(c) for c in rgb))


def _set_shader_diffuse(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh):
        set_semantic_attr(sh, 'diffuse', float(val))


def _set_shader_incandescence(val):
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh) and sh == 'rm_cyan_glow_mat':
        v = float(val)
        set_semantic_attr(sh, 'incandescence', (v, v, v))


def _update_shader_sliders():
    sh = _current_shader[0]
    if not sh:
        return
    ensure_material(sh)
    if not mc.objExists(sh):
        return
    _APPLYING_SHADER[0] = True
    try:
        col = get_semantic_attr(sh, 'color')
        if col is not None:
            mc.colorSliderGrp(state.get('color_sl'), e=True, rgb=tuple(col))
        d = get_semantic_attr(sh, 'diffuse')
        if d is not None:
            mc.floatSliderGrp(state.get('d_sl'), e=True, value=float(d))
        is_glow = (sh == 'rm_cyan_glow_mat')
        mc.control(state.get('i_sl'), e=True, visible=is_glow)
        if is_glow:
            inc = get_semantic_attr(sh, 'incandescence')
            if inc is not None:
                mc.floatSliderGrp(state.get('i_sl'), e=True, value=float(inc[0]))
    except Exception:
        pass
    finally:
        _APPLYING_SHADER[0] = False


def _on_shader_sel(label):
    sh = _SHADER_LABELS.get(label)
    if sh:
        _current_shader[0] = sh
        _update_shader_sliders()


# ══════════════════════════════════════════════════════════════
#  API publica para Modo Rapido (quick_panel)
# ══════════════════════════════════════════════════════════════

def apply_palette_quick(palette_key):
    """Aplica una paleta aiToon directamente por key (modo Rapido).

    Usada por quick_panel para asignar paletas sin pasar por la UI del panel.
    """
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


def apply_color_preset_quick(preset_name):
    """Aplica un preset de colores (Default/Atardecer/...) por nombre.

    Usada por quick_panel/build_actions para sincronizar el preset
    sin pasar por el menu de la UI.
    """
    apply_preset(preset_name)
    preset_menu = state.get('materials_preset_menu')
    if preset_menu and mc.optionMenu(preset_menu, exists=True):
        try:
            mc.optionMenu(preset_menu, e=True, value=preset_name)
        except Exception:
            pass
    _update_shader_sliders()
