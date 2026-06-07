"""Reusable Maya UI widgets for RetroMecha — Modern Dark."""
import ui.theme as T

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

# ── Paleta (alias a theme — backward compat) ─────────────
BG_DARK      = T.BG
BG_PANEL     = T.PANEL
BG_HOVER     = T.LINE
ACCENT_QUICK = T.CYAN
ACCENT_PRO   = T.CYAN
ACCENT_ACTION= T.CYAN
ACCENT_RAND  = T.SLATE
ACCENT_DANGER= T.PURPLE
TEXT_MUTED   = T.DIM


def fsl(label, mn, mx, val, step=0.01, prec=2, on_cc=None, on_drag=None, annotation=''):
    ctrl = mc.floatSliderGrp(
        label=label, field=True,
        min=mn, max=mx, value=val, step=step, precision=prec,
        columnWidth3=[90, 44, 170],
        columnAlign3=['right', 'left', 'left'],
        annotation=annotation,
    )
    if on_cc:
        mc.floatSliderGrp(ctrl, e=True, changeCommand=on_cc)
    if on_drag:
        mc.floatSliderGrp(ctrl, e=True, dragCommand=on_drag)
    return ctrl


def isl(label, mn, mx, val, on_cc=None, on_drag=None, annotation=''):
    ctrl = mc.intSliderGrp(
        label=label, field=True,
        min=mn, max=mx, value=val,
        columnWidth3=[90, 44, 170],
        columnAlign3=['right', 'left', 'left'],
        annotation=annotation,
    )
    if on_cc:
        mc.intSliderGrp(ctrl, e=True, changeCommand=on_cc)
    if on_drag:
        mc.intSliderGrp(ctrl, e=True, dragCommand=on_drag)
    return ctrl


def big_button(label, color, command, height=42, annotation=''):
    """Botón grande de acción principal."""
    return mc.button(
        label=label, height=height,
        backgroundColor=color,
        command=command,
        annotation=annotation,
    )


def secondary_button(label, color, command, height=28, annotation=''):
    """Botón secundario más pequeño."""
    return mc.button(
        label=label, height=height,
        backgroundColor=color,
        command=command,
        annotation=annotation,
    )


def swatch_button(color, command, size=32, annotation=''):
    """Botón cuadrado de color para paletas."""
    return mc.button(
        label='', height=size, width=size,
        backgroundColor=color,
        command=command,
        annotation=annotation,
    )


def section_title(text):
    """Título de sección: texto + separador LINE."""
    mc.text(label=f'  {text.upper()}', align='left', font='smallBoldLabelFont')
    T.sep()


def tab_bar(tab_ids, labels, colors, change_command, width=320, height=24):
    """Fila de botones tipo tabs. Solo uno activo (coloreado) a la vez."""
    n = len(tab_ids)
    cw = width // n
    row = mc.rowLayout(
        nc=n,
        columnWidth=[(i+1, cw) for i in range(n)],
        columnAttach=[(i+1, 'both', 2) for i in range(n)]
    )
    btns = {}
    def _make_callback(idx):
        def _cb(*_):
            for j, tid in enumerate(tab_ids):
                mc.button(btns[tid], e=True, backgroundColor=T.PANEL if j != idx else colors[j])
            change_command(tab_ids[idx])
        return _cb

    for i, (tid, lbl, col) in enumerate(zip(tab_ids, labels, colors)):
        btns[tid] = mc.button(
            label=lbl, height=height,
            backgroundColor=col if i == 0 else T.PANEL,
            command=_make_callback(i)
        )
    mc.setParent('..')
    return btns


def mode_switch(change_command, active_mode='quick'):
    """
    Switch grande Rápido / Pro.
    Activo en CYAN, inactivo en PANEL.
    """
    mc.rowLayout(nc=2, cw2=[172, 172],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])

    q_active = active_mode == 'quick'
    q_bg = T.CYAN if q_active else T.PANEL
    p_bg = T.CYAN if not q_active else T.PANEL

    def _quick(*_):
        mc.button(q_btn, e=True, backgroundColor=T.CYAN)
        mc.button(p_btn, e=True, backgroundColor=T.PANEL)
        change_command('quick')

    def _pro(*_):
        mc.button(p_btn, e=True, backgroundColor=T.CYAN)
        mc.button(q_btn, e=True, backgroundColor=T.PANEL)
        change_command('pro')

    q_btn = mc.button(
        label='◈  RÁPIDO', h=32,
        backgroundColor=q_bg,
        command=_quick,
        annotation='Modo simplificado: pocas decisiones, resultado inmediato',
    )
    p_btn = mc.button(
        label='●  PRO', h=32,
        backgroundColor=p_bg,
        command=_pro,
        annotation='Modo avanzado: control total de cada parámetro',
    )
    mc.setParent('..')
    return q_btn, p_btn


def button_grid(items, cols, btn_width, btn_height, on_build):
    """Iterate items in rows of `cols`, creating rowLayout + button per item.
    
    `on_build(item, col_idx, row_start)` is called per item to create the button.
    """
    for i in range(0, len(items), cols):
        chunk = items[i:i + cols]
        n = len(chunk)
        mc.rowLayout(nc=n, columnWidth=[(j + 1, btn_width) for j in range(n)],
                     columnAttach=[(j + 1, 'both', 2) for j in range(n)])
        for j, item in enumerate(chunk):
            on_build(item, j, i)
        mc.setParent('..')