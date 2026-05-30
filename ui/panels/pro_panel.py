"""Modo Pro — todos los controles organizados en secciones colapsables."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from ui import state
from ui.build_actions import rebuild_mecha, rebuild_terrain_only, \
    random_mecha, random_terrain, random_all, on_reset, on_generar
from ui.panels import mecha_panel, terrain_panel, material_panel, animation_panel


def build():
    mc.columnLayout(adjustableColumn=True, rowSpacing=4)

    # ── MECHA ────────────────────────────────────────────────
    _section_header('MECHA', [0.06, 0.25, 0.14],
                    '↺', random_mecha, '▶', rebuild_mecha)
    mecha_panel.build()
    mc.setParent('..')

    # ── TERRENO ──────────────────────────────────────────────
    _section_header('TERRENO', [0.08, 0.16, 0.35],
                    '↺', lambda *_: random_terrain(),
                    '▶', lambda *_: rebuild_terrain_only())
    terrain_panel.build()
    mc.setParent('..')

    # ── MATERIALES ───────────────────────────────────────────
    _section_header('MATERIALES', [0.30, 0.18, 0.06], None, None, None, None)
    material_panel.build()
    mc.setParent('..')

    # ── ANIMACIONES ──────────────────────────────────────────
    _section_header('ANIMACIONES', [0.18, 0.08, 0.32], None, None, None, None)
    animation_panel.build()
    mc.setParent('..')

    # ── Botones globales ─────────────────────────────────────
    mc.separator(h=8, style='in')
    mc.button(label='▶ Generar todo', h=36,
              backgroundColor=[0.14, 0.56, 0.28],
              command=on_generar,
              annotation='Genera mecha + terreno con configuración actual')

    mc.rowLayout(nc=2, cw2=[170, 170],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[3, 3])
    mc.button(label='↺ Aleatorio', h=32,
              backgroundColor=[0.50, 0.20, 0.54],
              command=random_all,
              annotation='Valores aleatorios + genera escena completa')
    mc.button(label='✕ Reset', h=32,
              backgroundColor=[0.58, 0.16, 0.16],
              command=on_reset,
              annotation='Elimina todo de la escena')
    mc.setParent('..')

    mc.separator(h=4, style='none')
    mc.setParent('..')


def _section_header(label, accent_color, btn1_label, btn1_cmd, btn2_label, btn2_cmd):
    """FrameLayout colapsable con mini-botones en fila previa."""
    if btn1_label or btn2_label:
        mc.rowLayout(nc=4, cw4=[50, 58, 58, 180],
                     columnAttach4=['left', 'both', 'both', 'right'],
                     columnOffset4=[4, 2, 2, 4])
        mc.text(label='', width=50)
        if btn1_label and btn1_cmd:
            mc.button(label=btn1_label, h=20, width=54,
                      backgroundColor=[0.20, 0.52, 0.34],
                      command=btn1_cmd)
        if btn2_label and btn2_cmd:
            mc.button(label=btn2_label, h=20, width=54,
                      backgroundColor=[0.30, 0.38, 0.50],
                      command=btn2_cmd)
        mc.text(label=label, align='right', font='smallPlainLabelFont')
        mc.setParent('..')
    mc.frameLayout(
        label=f'  {label}',
        collapsable=True, collapse=False,
        borderStyle='etchedIn',
        backgroundColor=accent_color,
        marginHeight=2, marginWidth=6,
    )
    # inner columnLayout is created by panel's build()
