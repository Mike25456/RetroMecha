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
from ui.widgets import fsl
import ui.theme as T

from materials.presets import SHADER_NAMES, PRESETS, list_presets, apply_preset
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

    presets_list = list_presets()
    _current_shader[0] = 'rm_white_armor_mat'

    if presets_list:
        mc.rowLayout(nc=2, cw2=[128, 180],
                     columnAttach2=['both', 'both'],
                     columnOffset2=[0, 4])
        mc.text(label='Paleta', align='right', font='smallPlainLabelFont')
        preset_menu = mc.optionMenu(
            changeCommand=lambda *_: _on_preset_changed(),
            backgroundColor=T.LINE,
            annotation='Preset de colores aplicado a los 6 shaders del mecha y terreno')
        for p in presets_list:
            mc.menuItem(label=p)
        state.reg('materials_preset_menu', preset_menu)
        mc.setParent('..')
    else:
        mc.text(label='(sin presets)', align='left', font='smallPlainLabelFont')
        state.reg('materials_preset_menu', None)

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
        set_semantic_attr(sh, 'color', tuple(float(c) for c in rgb))
    except Exception:
        pass


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

    for row_ofs in (0, 3):
        row_labels = labels[row_ofs:row_ofs + 3]
        n = len(row_labels)
        mc.rowLayout(nc=n,
            columnWidth=[(i + 1, 110) for i in range(n)],
            columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for i, label in enumerate(row_labels):
            idx = row_ofs + i
            is_active = (label == 'Armadura')
            btn = mc.button(label=label, height=24,
                            backgroundColor=T.CYAN if is_active else T.PANEL,
                            command=lambda *_, idx=idx: _select(idx))
            state.reg(f'shader_tab_{label}', btn)
        mc.setParent('..')


def _on_preset_changed(*_):
    """Al cambiar la paleta, actualizar los shaders en memoria + sky + luces."""
    preset_menu = state.get('materials_preset_menu')
    if not _safe_ctrl_exists(preset_menu):
        return
    try:
        label = mc.optionMenu(preset_menu, q=True, value=True)
    except Exception:
        return
    state._QUICK_PALETTE[0] = label
    _apply_palette_to_scene(label)
    _update_shader_sliders()


def current_palette_label() -> str:
    """Devuelve el label del preset activo (Quick o Pro)."""
    if state._QUICK_PALETTE[0]:
        return state._QUICK_PALETTE[0]
    preset_menu = state.get('materials_preset_menu')
    if _safe_ctrl_exists(preset_menu):
        try:
            return mc.optionMenu(preset_menu, q=True, value=True) or 'Predeterminado'
        except Exception:
            pass
    return 'Predeterminado'


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
        try:
            mc.refresh(suspend=True)
            refresh_suspended = True
        except Exception:
            refresh_suspended = False

        try:
            from materials.sync import apply_palette_full
            if not apply_palette_full(palette_key):
                print(f'[RetroMecha][Material] Paleta "{palette_key}" no disponible')
                return
        except Exception as e:
            print(f'[RetroMecha][Material] Sync: {e}')
            apply_preset(palette_key)

        terrain_sgs = _create_viewport_fresh_terrain_materials(palette_key)
        _rematerialize_terrain_shapes(terrain_sgs)
        _cleanup_old_terrain_swaps(terrain_sgs)
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


_TERRAIN_SHADER_NAMES = (
    'rm_terrain_base_mat',
    'rm_terrain_dark_mat',
    'rm_terrain_accent_mat',
)


def _create_viewport_fresh_terrain_materials(palette_key: str) -> dict:
    """Crea shaders temporales ya coloreados para evitar el frame sin material."""
    if not has_arnold():
        return {}
    preset = PRESETS.get(palette_key, PRESETS.get('Predeterminado', {}))
    result = {}
    for shader in _TERRAIN_SHADER_NAMES:
        try:
            temp_shader = mc.shadingNode(
                'aiStandardSurface',
                asShader=True,
                name=f'{shader}_swap#',
            )
            temp_sg = mc.sets(
                renderable=True,
                noSurfaceShader=True,
                empty=True,
                name=f'{shader}SG_swap#',
            )
            mc.connectAttr(f'{temp_shader}.outColor',
                           f'{temp_sg}.surfaceShader',
                           force=True)
            set_semantic_attr(temp_shader, 'diffuseRoughness',
                              DEFAULT_DIFFUSE_ROUGHNESS)
            for semantic, value in preset.get(shader, {}).items():
                set_semantic_attr(temp_shader, semantic, value)
            result[shader] = {
                'shader': temp_shader,
                'sg': temp_sg,
            }
        except Exception as e:
            print(f'[RetroMecha][Material] temp terrain {shader}: {e}')
    return result


def _cleanup_old_terrain_swaps(current: dict):
    """Elimina swaps antiguos despues de asignar los nuevos."""
    keep = set()
    for data in current.values():
        keep.add(data.get('shader'))
        keep.add(data.get('sg'))
    patterns = []
    for shader in _TERRAIN_SHADER_NAMES:
        patterns.append(f'{shader}_swap*')
        patterns.append(f'{shader}SG_swap*')
    for pattern in patterns:
        for node in (mc.ls(pattern) or []):
            if not node or node in keep or not mc.objExists(node):
                continue
            try:
                mc.delete(node)
            except Exception as e:
                print(f'[RetroMecha][Material] cleanup swap {node}: {e}')


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


def _rematerialize_terrain_shapes(replacements=None):
    """Fuerza los shaders del terreno directamente sobre cada mesh shape."""
    try:
        from materials.materializer import _resolve_terrain_material
        replacements = replacements or {}
        shapes = _terrain_mesh_shapes()
        count = 0
        for shape in shapes:
            parents = mc.listRelatives(shape, parent=True) or []
            transform = parents[0] if parents else shape
            mat = _resolve_terrain_material(transform)
            sg = replacements.get(mat, {}).get('sg') or ensure_material(mat)
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
            try:
                mc.dgdirty(shape)
            except Exception:
                pass
            count += 1
        if count:
            print(f'[RetroMecha][Material] Terreno rematerializado: {count} mesh(es)')
    except Exception as e:
        print(f'[RetroMecha][Material] Terrain remat: {e}')


def _force_sky_material(palette_key: str):
    """Recrea y reasigna el sky material tambien sobre el shape."""
    try:
        from materials.sky_material import create_sky_material
        sg = create_sky_material(palette_key)
        if not sg or not mc.objExists('sky'):
            return
        shapes = mc.listRelatives('sky', shapes=True, type='mesh') or []
        mc.sets('sky', edit=True, forceElement=sg)
        for shape in shapes:
            mc.sets(shape, edit=True, forceElement=sg)
            try:
                mc.dgdirty(shape)
            except Exception:
                pass
    except Exception as e:
        print(f'[RetroMecha][Material] Sky force: {e}')


def apply_color_preset_quick(preset_name):
    """Aplica un preset de colores por nombre (modo Rapido)."""
    state._QUICK_PALETTE[0] = preset_name
    _apply_palette_to_scene(preset_name)
    preset_menu = state.get('materials_preset_menu')
    if _safe_ctrl_exists(preset_menu):
        try:
            mc.optionMenu(preset_menu, e=True, value=preset_name)
        except Exception:
            pass
    _update_shader_sliders()


def debug_material_state(palette_key=None, sample_limit=5):
    """Imprime una muestra de conexiones reales de terreno y cielo."""
    if not MAYA_AVAILABLE:
        return
    palette = palette_key or current_palette_label()
    print(f'[RetroMecha][DebugMat] ===== palette={palette} =====')
    _debug_shader('rm_terrain_base_mat')
    _debug_shader('rm_terrain_dark_mat')
    _debug_shader('rm_terrain_accent_mat')
    _debug_terrain_samples(sample_limit=sample_limit)
    _debug_sky_state()


def _debug_shader(shader):
    exists = mc.objExists(shader)
    sg = f'{shader}SG'
    sg_exists = mc.objExists(sg)
    base = None
    emission = None
    sg_src = None
    try:
        if exists:
            base = mc.getAttr(f'{shader}.baseColor')[0]
            emission = mc.getAttr(f'{shader}.emission')
    except Exception:
        pass
    try:
        if sg_exists:
            sg_src = mc.connectionInfo(f'{sg}.surfaceShader',
                                       sourceFromDestination=True)
    except Exception:
        pass
    print(
        f'[RetroMecha][DebugMat] shader {shader}: '
        f'exists={exists} sg={sg_exists} sgSrc={sg_src} '
        f'base={base} emission={emission}'
    )


def _debug_terrain_samples(sample_limit=5):
    try:
        from materials.materializer import _resolve_terrain_material
        shapes = _terrain_mesh_shapes()
        print(f'[RetroMecha][DebugMat] terrainShapes={len(shapes)}')
        for shape in shapes[:sample_limit]:
            parents = mc.listRelatives(shape, parent=True) or []
            transform = parents[0] if parents else shape
            expected = _resolve_terrain_material(transform)
            sgs = mc.listSets(type=1, object=shape) or []
            face_sg = []
            try:
                face_sg = mc.listSets(type=1, object=f'{shape}.f[0]') or []
            except Exception:
                pass
            shader_src = []
            for sg in sgs:
                try:
                    shader_src.append(
                        (sg, mc.connectionInfo(f'{sg}.surfaceShader',
                                               sourceFromDestination=True))
                    )
                except Exception:
                    shader_src.append((sg, None))
            print(
                f'[RetroMecha][DebugMat] terrain sample '
                f'{transform}/{shape}: expected={expected} '
                f'sgs={sgs} face0={face_sg} shaderSrc={shader_src}'
            )
    except Exception as e:
        print(f'[RetroMecha][DebugMat] terrain sample error: {e}')


def _debug_sky_state():
    sky_exists = mc.objExists('sky')
    sky_shapes = mc.listRelatives('sky', shapes=True, type='mesh') if sky_exists else []
    sky_shape = sky_shapes[0] if sky_shapes else None
    sky_sgs = mc.listSets(type=1, object=sky_shape) if sky_shape else []
    print(
        f'[RetroMecha][DebugMat] sky: exists={sky_exists} '
        f'shape={sky_shape} sgs={sky_sgs}'
    )
    for node in ('sky_material', 'sky_materialSG', 'rm_sky_ramp'):
        print(f'[RetroMecha][DebugMat] sky node {node}: exists={mc.objExists(node)}')
    try:
        src = mc.connectionInfo('sky_materialSG.surfaceShader',
                                sourceFromDestination=True)
        base_src = mc.connectionInfo('sky_material.baseColor',
                                     sourceFromDestination=True)
        emit_src = mc.connectionInfo('sky_material.emissionColor',
                                     sourceFromDestination=True)
        print(
            f'[RetroMecha][DebugMat] sky connections: '
            f'sgSrc={src} baseSrc={base_src} emissionSrc={emit_src}'
        )
    except Exception as e:
        print(f'[RetroMecha][DebugMat] sky connections error: {e}')
    try:
        indices = mc.getAttr('rm_sky_ramp.colorEntryList',
                             multiIndices=True) or []
        entries = []
        for i in indices:
            pos = mc.getAttr(f'rm_sky_ramp.colorEntryList[{i}].position')
            col = mc.getAttr(f'rm_sky_ramp.colorEntryList[{i}].color')[0]
            entries.append((i, pos, col))
        print(f'[RetroMecha][DebugMat] sky ramp entries={entries}')
    except Exception as e:
        print(f'[RetroMecha][DebugMat] sky ramp error: {e}')
