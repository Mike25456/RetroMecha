"""Reusable Maya UI widgets for RetroMecha — Modern Dark."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

# ── Paleta moderna oscura ───────────────────────────────────
BG_DARK      = [0.07, 0.07, 0.08]
BG_PANEL     = [0.10, 0.10, 0.11]
BG_HOVER     = [0.14, 0.14, 0.16]
ACCENT_QUICK = [0.90, 0.55, 0.15]   # ámbar/dorado
ACCENT_PRO   = [0.25, 0.65, 0.90]   # cian eléctrico
ACCENT_ACTION= [0.12, 0.52, 0.32]   # verde oscuro elegante
ACCENT_RAND  = [0.22, 0.24, 0.28]   # gris azulado
ACCENT_DANGER= [0.55, 0.16, 0.16]   # rojo oscuro
TEXT_MUTED   = [0.55, 0.55, 0.60]


def fsl(label, mn, mx, val, step=0.01, prec=2, on_cc=None, annotation=''):
    ctrl = mc.floatSliderGrp(
        label=label, field=True,
        min=mn, max=mx, value=val, step=step, precision=prec,
        columnWidth3=[90, 44, 170],
        columnAlign3=['right', 'left', 'left'],
        annotation=annotation,
    )
    if on_cc:
        mc.floatSliderGrp(ctrl, e=True, changeCommand=on_cc)
    return ctrl


def isl(label, mn, mx, val, on_cc=None, annotation=''):
    ctrl = mc.intSliderGrp(
        label=label, field=True,
        min=mn, max=mx, value=val,
        columnWidth3=[90, 44, 170],
        columnAlign3=['right', 'left', 'left'],
        annotation=annotation,
    )
    if on_cc:
        mc.intSliderGrp(ctrl, e=True, changeCommand=on_cc)
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
    """Título de sección moderno: texto + línea sutil."""
    mc.text(label=text.upper(), align='left', font='smallBoldLabelFont')
    mc.separator(h=4, style='none')
    mc.separator(h=1, style='single')
    mc.separator(h=6, style='none')


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
                mc.button(btns[tid], e=True, backgroundColor=[0.12, 0.12, 0.14] if j != idx else colors[j])
            change_command(tab_ids[idx])
        return _cb

    for i, (tid, lbl, col) in enumerate(zip(tab_ids, labels, colors)):
        btns[tid] = mc.button(
            label=lbl, height=height,
            backgroundColor=col if i == 0 else [0.12, 0.12, 0.14],
            command=_make_callback(i)
        )
    mc.setParent('..')
    return btns


def mode_switch(change_command, active_mode='quick'):
    """
    Switch grande Rápido / Pro. Es imposible de no ver.
    Ocupa todo el ancho disponible.
    """
    mc.rowLayout(nc=2, cw2=[172, 172],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[4, 4])

    q_active = active_mode == 'quick'
    q_bg = ACCENT_QUICK if q_active else BG_HOVER
    p_bg = ACCENT_PRO if not q_active else BG_HOVER

    def _quick(*_):
        mc.button(q_btn, e=True, backgroundColor=ACCENT_QUICK)
        mc.button(p_btn, e=True, backgroundColor=BG_HOVER)
        change_command('quick')

    def _pro(*_):
        mc.button(p_btn, e=True, backgroundColor=ACCENT_PRO)
        mc.button(q_btn, e=True, backgroundColor=BG_HOVER)
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