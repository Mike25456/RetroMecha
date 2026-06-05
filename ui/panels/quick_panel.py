"""Modo Rapido: compact scene generation controls."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state, widgets
from ui.constants import PALETTE_SWATCH_COLORS
import ui.theme as T
from ui.build_actions import (
    random_all, on_reset, random_mecha, rebuild_terrain_only,
)
from ui.panels.material_panel import apply_color_preset_quick
from ui.panels.animation_panel import apply_animation_quick

_ACTIVE_SWATCH = [None]


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=0)

    mc.rowLayout(nc=2, cw2=[165, 165],
                 columnAttach2=['both', 'both'])
    widgets.secondary_button('Ensamblar escena', widgets.ACCENT_ACTION, random_all, height=32)
    widgets.secondary_button('Limpiar', widgets.ACCENT_DANGER, on_reset, height=32)
    mc.setParent('..')
    mc.separator(h=8, style='none')

    widgets.section_title('Mecha')
    widgets.big_button(
        'Ensamblar Mecha',
        widgets.ACCENT_RAND,
        lambda *_: random_mecha(),
        height=42,
    )
    mc.separator(h=6, style='none')

    widgets.section_title('Escenario')
    widgets.big_button(
        'Ensamblar Escenario',
        widgets.ACCENT_RAND,
        lambda *_: _random_terrain_and_build(),
        height=42,
    )
    mc.separator(h=8, style='none')

    widgets.section_title('Estilo')
    swatch_btns = {}
    items = list(PALETTE_SWATCH_COLORS.items())

    def _swatch_row(chunk):
        n = len(chunk)
        mc.rowLayout(nc=n, columnWidth=[(i + 1, 80) for i in range(n)],
                     columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for name, (color, key) in chunk:
            btn = widgets.swatch_button(
                color,
                lambda *_, k=key, n=name: _select_swatch(n, k, swatch_btns),
                size=30,
            )
            swatch_btns[name] = (btn, color)
        mc.setParent('..')

        mc.rowLayout(nc=n, columnWidth=[(i + 1, 80) for i in range(n)],
                     columnAttach=[(i + 1, 'both', 2) for i in range(n)])
        for name, _ in chunk:
            mc.text(label=name, align='center', font='smallPlainLabelFont')
        mc.setParent('..')

    for i in range(0, len(items), 4):
        _swatch_row(items[i:i + 4])

    mc.separator(h=8, style='none')

    mc.text(label='Movimiento', align='left', font='smallPlainLabelFont')
    coll = mc.radioCollection()
    mc.rowLayout(nc=4, cw4=[80, 80, 80, 80])
    rb_map = {}
    for key, label in [('idle', 'Reposo'), ('flight', 'Vuelo'), ('spin', 'Giro'), ('charge', 'Carga')]:
        rb = mc.radioButton(label=label,
                            onCommand=lambda *_, k=key: apply_animation_quick(k))
        rb_map[key] = rb
    mc.setParent('..')
    state.reg('anim_rb_coll', coll)
    state.reg('anim_rb_map', rb_map)
    from ui.build_actions import _sync_anim_ui
    _sync_anim_ui()

    mc.separator(h=8, style='none')

    widgets.section_title('Renderizar')
    widgets.big_button(
        'Ensamblar Render',
        widgets.ACCENT_ACTION,
        lambda *_: _quick_render(),
        height=42,
    )
    mc.button(
        label='Eliminar cámara', h=24,
        backgroundColor=T.PANEL,
        command=lambda *_: _remove_render_camera(),
        annotation='Elimina Camara_for_render para volver a la navegación libre',
    )
    mc.separator(h=6, style='none')
    mc.setParent('..')


def _select_swatch(name, preset_name, btns_map):
    for _name, (btn, original_color) in btns_map.items():
        mc.button(btn, e=True, backgroundColor=original_color)

    btn, original = btns_map[name]
    mc.button(btn, e=True, backgroundColor=[max(0.05, c - 0.18) for c in original])
    _ACTIVE_SWATCH[0] = name
    state._QUICK_PALETTE[0] = preset_name
    apply_color_preset_quick(preset_name)
    try:
        mc.refresh(force=True)
    except Exception:
        pass


def _random_terrain_and_build(*_):
    from ui.build_actions import randomize_terrain_controls
    randomize_terrain_controls()
    rebuild_terrain_only()


def _quick_render(*_):
    try:
        mc.play(state=False)
    except Exception:
        pass
    from ui.panels.material_panel import current_palette_label
    palette = current_palette_label()
    try:
        from utils import lighting
        if not lighting.has_rm_lights():
            lighting.apply_lighting(palette)
    except Exception as e:
        print(f'[RetroMecha][Quick] Luces: {e}')
    try:
        from utils.sky import create_sky, has_sky
        if not has_sky():
            create_sky()
    except Exception as e:
        print(f'[RetroMecha][Quick] Cielo: {e}')
    try:
        from materials.sky_material import create_sky_material, has_sky_material
        if not has_sky_material():
            create_sky_material(palette)
    except Exception as e:
        print(f'[RetroMecha][Quick] Sky material: {e}')
    try:
        from utils.render import render_now
        render_now()
    except Exception as e:
        print(f'[RetroMecha][Quick] Render: {e}')


def _remove_render_camera(*_):
    try:
        from utils.camera import remove_camera
        remove_camera()
        print('[RetroMecha][Quick] Cámara de render eliminada')
    except Exception as e:
        print(f'[RetroMecha][Quick] Eliminar cámara: {e}')
