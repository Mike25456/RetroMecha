"""Reusable Maya UI widgets for RetroMecha."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


def fsl(label, mn, mx, val, step=0.01, prec=2, on_cc=None, annotation=''):
    ctrl = mc.floatSliderGrp(
        label=label, field=True,
        min=mn, max=mx, value=val, step=step, precision=prec,
        columnWidth3=[128, 52, 128],
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
        columnWidth3=[128, 52, 128],
        columnAlign3=['right', 'left', 'left'],
        annotation=annotation,
    )
    if on_cc:
        mc.intSliderGrp(ctrl, e=True, changeCommand=on_cc)
    return ctrl


def btn(label, w=140, h=28, bg=None, cmd=None, annotation=''):
    kwargs = dict(label=label, width=w, height=h, annotation=annotation)
    if bg:
        kwargs['backgroundColor'] = bg
    if cmd:
        kwargs['command'] = cmd
    return mc.button(**kwargs)


def row_label(label, width=128):
    mc.text(label=label, align='right', font='smallPlainLabelFont', width=width)


def section_header(label, dot_color, open=False):
    """Collapsable frameLayout with a colored dot prefix."""
    dot = f'  ●  {label}' if dot_color else f'  {label}'
    return mc.frameLayout(
        label=dot,
        collapsable=True, collapse=not open,
        borderStyle='etchedIn',
        backgroundColor=dot_color,
        marginHeight=6, marginWidth=6,
    )


def mode_toggle(change_command):
    """Pair of Rápido/Pro buttons that call change_command(mode)."""
    mc.rowLayout(nc=2, cw2=[52, 40],
                 columnAttach2=['both', 'both'],
                 columnOffset2=[2, 2])

    q_bg = [0.14, 0.40, 0.22]
    p_bg = [0.30, 0.18, 0.06]

    def _set_quick():
        mc.button(quick_btn, e=True, backgroundColor=q_bg)
        mc.button(pro_btn, e=True, backgroundColor=[0.12, 0.12, 0.14])
        change_command('quick')

    def _set_pro():
        mc.button(pro_btn, e=True, backgroundColor=p_bg)
        mc.button(quick_btn, e=True, backgroundColor=[0.12, 0.12, 0.14])
        change_command('pro')

    quick_btn = mc.button(label='Rápido', h=20, width=52,
                          backgroundColor=q_bg,
                          command=lambda *_: _set_quick())
    pro_btn = mc.button(label='Pro', h=20, width=40,
                        backgroundColor=[0.12, 0.12, 0.14],
                        command=lambda *_: _set_pro())
    mc.setParent('..')
    return quick_btn, pro_btn
