"""MATERIALES section — shaders aiStandardSurface con paleta.

Gestiona los shaders del mecha y terreno:
  - Paleta (preset de colores)
  - Selector de shader + sliders (color, difuso, brillo)
  - Boton 'Aplicar materiales al mecha'
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.build_actions import _safe_ctrl_exists
from ui.widgets import fsl, button_grid
import ui.theme as T

from materials.presets import SHADER_NAMES, PRESETS, apply_preset
from utils.maya_materials import (
    DEFAULT_DIFFUSE_ROUGHNESS,
    ensure_material,
    get_semantic_attr,
    has_arnold,
    set_semantic_attr,
)

_SHADER_LABELS = {
    'Armadura': 'rm_white_armor_mat',
    'Estructura': 'rm_graphite_mat',
    'Brillo': 'rm_cyan_glow_mat',
    'Terreno base': 'rm_terrain_base_mat',
    'Terreno oscuro': 'rm_terrain_dark_mat',
    'Terreno acento': 'rm_terrain_accent_mat',
    'Terreno estr.': 'rm_terrain_accent2_mat',   # ← nuevo v2
}

_current_shader = ['rm_white_armor_mat']
_APPLYING_SHADER = [False]


def build(wrapped=True):
    if wrapped:
        mc.frameLayout(
            label='  >  MATERIALES',
            collapsable=True, collapse=True,
            borderStyle='etchedIn',
            backgroundColor=T.PANEL,
            marginHeight=8, marginWidth=6,
        )
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)

    for shader_name in SHADER_NAMES:
        ensure_material(shader_name)

    _current_shader[0] = 'rm_white_armor_mat'

    # Swatches de paleta (como en modo Rápido)
    _build_palette_swatches()

    mc.separator(h=4)
    _build_shader_tabs()

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

    mc.separator(h=4)
    mc.setParent('..')
    if wrapped:
        mc.setParent('..')


def _build_palette_swatches():
    """Swatches de paleta como en modo Rápido."""
    from ui.constants import PALETTE_SWATCH_COLORS
    items = list(PALETTE_SWATCH_COLORS.items())

    def _swatch_row(chunk):
        n = len(chunk)
        mc.rowLayout(nc=n, columnWidth=[(i + 1, 80) for i in range(n)],
                     columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for name, (color, key) in chunk:
            is_active = (state._QUICK_PALETTE[0] == key)
            btn = mc.button(
                label='',
                width=80, height=30,
                backgroundColor=color,
                command=lambda *_, k=key: _on_swatch_click(k),
            )
            if is_active:
                state.reg('_active_swatch_btn', btn)
        mc.setParent('..')

        mc.rowLayout(nc=n, columnWidth=[(i + 1, 80) for i in range(n)],
                     columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for name, _ in chunk:
            mc.text(label=name, align='center', font='smallPlainLabelFont')
        mc.setParent('..')

    for i in range(0, len(items), 4):
        _swatch_row(items[i:i + 4])


def _on_swatch_click(preset_name):
    state._QUICK_PALETTE[0] = preset_name
    _apply_palette_to_scene(preset_name)
    _update_shader_sliders()


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
        color = tuple(float(c) for c in rgb)
        set_semantic_attr(sh, 'color', color)
        _sync_terrain_swaps(sh, 'color', color)
    except Exception:
        pass


def _set_shader_diffuse(val):
    if _APPLYING_SHADER[0]:
        return
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh):
        val = float(val)
        set_semantic_attr(sh, 'diffuse', val)
        _sync_terrain_swaps(sh, 'diffuse', val)


def _set_shader_incandescence(val):
    if _APPLYING_SHADER[0]:
        return
    sh = _current_shader[0]
    if sh:
        ensure_material(sh)
    if sh and mc.objExists(sh) and sh == 'rm_cyan_glow_mat':
        v = float(val)
        color = (v, v, v)
        set_semantic_attr(sh, 'incandescence', color)
        _sync_terrain_swaps(sh, 'incandescence', color)


def _sync_terrain_swaps(master_shader, semantic, value):
    """Copia el cambio a los ping-pong swaps si es un shader de terreno."""
    if master_shader not in _TERRAIN_SHADER_NAMES_SET:
        return
    for store in (_TERRAIN_SWAP_SETS['A'], _TERRAIN_SWAP_SETS['B']):
        data = store.get(master_shader)
        if not data:
            continue
        target = data.get('shader')
        if target and mc.objExists(target):
            set_semantic_attr(target, semantic, value)


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


def _build_shader_tabs():
    labels = list(_SHADER_LABELS.keys())

    def _select(idx):
        label = labels[idx]
        sh = _SHADER_LABELS.get(label)
        if sh:
            _current_shader[0] = sh
            _update_shader_sliders()
        for j, lbl in enumerate(labels):
            btn = state.get(f'shader_tab_{lbl}')
            if btn:
                try:
                    mc.button(btn, e=True, backgroundColor=T.CYAN if j == idx else T.PANEL)
                except Exception:
                    pass

    def _shader_btn(item, col_idx, row_start):
        idx = row_start + col_idx
        label = item
        is_active = (_SHADER_LABELS.get(label) == _current_shader[0])
        btn = mc.button(label=label, height=24,
                        backgroundColor=T.CYAN if is_active else T.PANEL,
                        command=lambda *_, idx=idx: _select(idx))
        state.reg(f'shader_tab_{label}', btn)

    button_grid(labels, cols=3, btn_width=110, btn_height=24, on_build=_shader_btn)


def current_palette_label() -> str:
    """Devuelve el label del preset activo."""
    return state._QUICK_PALETTE[0] or 'Predeterminado'


def _apply_palette_to_scene(palette_key: str):
    """Aplica paleta a shaders, cielo, luces y reasigna materiales del terreno."""
    was_playing = False
    refresh_suspended = False

    try:
        was_playing = bool(mc.play(q=True, state=True))
        if was_playing:
            mc.play(state=False)
    except Exception:
        was_playing = False

    try:
        mc.refresh(suspend=True)
        refresh_suspended = True
    except Exception:
        refresh_suspended = False

    try:
        # 1. Asegurar que los swaps existen (una sola vez)
        _ensure_terrain_swaps()

        # 2. Colorear AMBOS sets de swap con la nueva paleta
        _color_terrain_swaps(palette_key)

        # 3. Sincronizar paleta a shaders maestros + sky_ramp + luces
        try:
            from materials.sync import apply_palette_full
            if not apply_palette_full(palette_key):
                print(f'[RetroMecha][Material] Paleta "{palette_key}" no disponible')
                return
        except Exception as e:
            print(f'[RetroMecha][Material] Sync: {e}')
            apply_preset(palette_key)

        # 4. Sky temp shader (pre-creado cada vez, es efimero)
        sky_data = _create_viewport_fresh_sky_material(palette_key)

        # 5. Asignar set opuesto al terreno + sky bounce
        _swap_terrain_to_opposite()
        if sky_data:
            _rematerialize_sky(sky_data)
        try:
            mc.dgdirty(allPlugs=True)
        except Exception:
            pass
    finally:
        if refresh_suspended:
            try:
                mc.refresh(suspend=False)
                mc.refresh(force=True)
            except Exception:
                pass
        if was_playing:
            try:
                mc.play(forward=True)
            except Exception:
                pass

    # 4. Cleanup fuera del bloque suspendido (solo sky — terreno usa ping-pong fijo)
    if sky_data:
        _cleanup_old_sky_swaps(sky_data)


_TERRAIN_SHADER_NAMES = (
    'rm_terrain_base_mat',
    'rm_terrain_dark_mat',
    'rm_terrain_accent_mat',
    'rm_terrain_accent2_mat',
)
_TERRAIN_SHADER_NAMES_SET = set(_TERRAIN_SHADER_NAMES)

# Ping-pong swap sets para terreno — pre-creados una sola vez
_TERRAIN_SWAP_SETS = {'A': {}, 'B': {}}
_TERRAIN_SWAP_ACTIVE = ['A']
_TERRAIN_SWAPS_READY = [False]


def _ensure_terrain_swaps():
    """Crea los dos sets de swap shaders para el terreno (una sola vez)."""
    if _TERRAIN_SWAPS_READY[0] or not has_arnold():
        return
    for label in ('A', 'B'):
        store = _TERRAIN_SWAP_SETS[label]
        for shader in _TERRAIN_SHADER_NAMES:
            try:
                tag = f'_ping{label}'
                temp_shader = mc.shadingNode(
                    'aiStandardSurface', asShader=True,
                    name=f'{shader}{tag}')
                temp_sg = mc.sets(
                    renderable=True, noSurfaceShader=True, empty=True,
                    name=f'{shader}SG{tag}')
                mc.connectAttr(f'{temp_shader}.outColor',
                               f'{temp_sg}.surfaceShader', force=True)
                set_semantic_attr(temp_shader, 'diffuseRoughness',
                                  DEFAULT_DIFFUSE_ROUGHNESS)
                store[shader] = {'shader': temp_shader, 'sg': temp_sg}
            except Exception as e:
                print(f'[RetroMecha][Material] ping init {shader}_{label}: {e}')
    _TERRAIN_SWAPS_READY[0] = True
    print('[RetroMecha][Material] Swap sets A/B listos')


def _color_terrain_swaps(palette_key: str):
    """Colorea ambos sets de swap con los valores del preset."""
    preset = PRESETS.get(palette_key, PRESETS.get('Predeterminado', {}))
    for store in (_TERRAIN_SWAP_SETS['A'], _TERRAIN_SWAP_SETS['B']):
        for shader, data in store.items():
            shd = data.get('shader')
            if not shd or not mc.objExists(shd):
                continue
            for semantic, value in preset.get(shader, {}).items():
                set_semantic_attr(shd, semantic, value)


def _swap_terrain_to_opposite():
    """Asigna el set de swap opuesto al terreno (invalida GPU cache)."""
    active = _TERRAIN_SWAP_ACTIVE[0]
    target_label = 'B' if active == 'A' else 'A'
    target = _TERRAIN_SWAP_SETS[target_label]
    # Asignar target al terreno
    shapes = _terrain_mesh_shapes()
    count = 0
    for shape in shapes:
        parents = mc.listRelatives(shape, parent=True) or []
        transform = parents[0] if parents else shape
        from materials.materializer import _resolve_terrain_material
        mat = _resolve_terrain_material(transform)
        sg = target.get(mat, {}).get('sg')
        if not sg:
            continue
        mc.sets(transform, edit=True, forceElement=sg)
        mc.sets(shape, edit=True, forceElement=sg)
        try:
            face_count = mc.polyEvaluate(shape, face=True)
            if face_count:
                mc.sets(f'{shape}.f[0:{int(face_count) - 1}]',
                        edit=True, forceElement=sg)
        except Exception:
            pass
        count += 1
        try:
            mc.dgdirty(shape)
        except Exception:
            pass
    if count:
        print(f'[RetroMecha][Material] Terreno swap → {target_label}: {count} mesh(es)')
    _TERRAIN_SWAP_ACTIVE[0] = target_label


def _create_viewport_fresh_sky_material(palette_key: str) -> dict | None:
    """Crea shader temporal para el sky con colores planos derivados de la paleta."""
    if not has_arnold() or not mc.objExists('sky'):
        return None
    preset = PRESETS.get(palette_key, PRESETS.get('Predeterminado', {}))
    top_rgb = preset.get('rm_cyan_glow_mat', {}).get('color', (0.04, 0.75, 1.0))
    bottom_rgb = tuple(round(c * 0.10, 4) for c in top_rgb)
    try:
        temp_shader = mc.shadingNode(
            'aiStandardSurface', asShader=True, name='sky_material_swap#')
        temp_sg = mc.sets(
            renderable=True, noSurfaceShader=True, empty=True,
            name='sky_materialSG_swap#')
        mc.connectAttr(f'{temp_shader}.outColor',
                       f'{temp_sg}.surfaceShader', force=True)
        set_semantic_attr(temp_shader, 'color', bottom_rgb)
        set_semantic_attr(temp_shader, 'diffuseRoughness', DEFAULT_DIFFUSE_ROUGHNESS)
        set_semantic_attr(temp_shader, 'emission', 0.5)
        set_semantic_attr(temp_shader, 'incandescence', top_rgb)
        return {'shader': temp_shader, 'sg': temp_sg}
    except Exception as e:
        print(f'[RetroMecha][Material] temp sky: {e}')
        return None


def _rematerialize_sky(sky_data: dict):
    """Asigna el SG temporal al sky (invalida GPU cache) y restaura el real con ramp."""
    sg = sky_data.get('sg')
    if not sg or not mc.objExists('sky'):
        return
    real_sg = 'sky_materialSG'
    try:
        mc.sets('sky', edit=True, forceElement=sg)
        for shape in (mc.listRelatives('sky', shapes=True, type='mesh') or []):
            mc.sets(shape, edit=True, forceElement=sg)
            try:
                face_count = mc.polyEvaluate(shape, face=True)
                if face_count:
                    mc.sets(f'{shape}.f[0:{int(face_count) - 1}]',
                            edit=True, forceElement=sg)
            except Exception:
                pass

        # Restaurar el material real con ramp
        if mc.objExists(real_sg):
            mc.sets('sky', edit=True, forceElement=real_sg)
            for shape in (mc.listRelatives('sky', shapes=True, type='mesh') or []):
                mc.sets(shape, edit=True, forceElement=real_sg)
                try:
                    face_count = mc.polyEvaluate(shape, face=True)
                    if face_count:
                        mc.sets(f'{shape}.f[0:{int(face_count) - 1}]',
                                edit=True, forceElement=real_sg)
                except Exception:
                    pass
    except Exception as e:
        print(f'[RetroMecha][Material] Sky remat: {e}')


def _cleanup_old_sky_swaps(current: dict | None):
    """Elimina swaps antiguos del sky."""
    if not current:
        return
    keep = {current.get('shader'), current.get('sg')}
    for pattern in ('sky_material_swap*', 'sky_materialSG_swap*'):
        for node in (mc.ls(pattern) or []):
            if not node or node in keep or not mc.objExists(node):
                continue
            try:
                mc.delete(node)
            except Exception:
                pass


def _terrain_mesh_shapes():
    """Devuelve shapes unicos de terreno sin recorrer el mismo arbol repetido."""
    from ui.scene_utils import TERRAIN_PATTERNS
    shapes = []
    seen = set()
    for pattern in TERRAIN_PATTERNS:
        for node in (mc.ls(pattern, type='transform') or []):
            if not node or not mc.objExists(node):
                continue
            direct = mc.listRelatives(node, shapes=True, type='mesh') or []
            nested = mc.listRelatives(node, allDescendents=True, type='mesh') or []
            for shape in direct + nested:
                if shape and mc.objExists(shape) and shape not in seen:
                    seen.add(shape)
                    shapes.append(shape)
    return shapes


def apply_color_preset_quick(preset_name):
    """Aplica un preset de colores por nombre (modo Rapido)."""
    state._QUICK_PALETTE[0] = preset_name
    _apply_palette_to_scene(preset_name)
    _update_shader_sliders()