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
