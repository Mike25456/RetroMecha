"""Paleta y helpers visuales compartidos — sin dependencias de UI."""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

# ── Paleta ──────────────────────────────────────────────
BG       = (0.055, 0.067, 0.086)   # #0e1116  fondo ventana (ligeramente más claro)
PANEL    = (0.075, 0.090, 0.110)   # #13171c  frameLayout / sub-paneles
LINE     = (0.133, 0.165, 0.200)   # #222a33  separadores / hover
STRUCT   = (0.910, 0.918, 0.929)   # #e8eaed  texto principal
CYAN     = (0.176, 0.831, 0.867)   # #2dd4dd  acento principal
SLATE    = (0.357, 0.392, 0.439)   # #5b6470  botón secundario
DIM      = (0.604, 0.639, 0.678)   # #9aa3ad  dim text
MUTE     = (0.420, 0.455, 0.502)   # #6b7480  muted
DARK     = (0.043, 0.051, 0.063)   # #0b0d10  sub-panel profundo (el más oscuro)

# ── Colores de estado ───────────────────────────────────
OK       = (0.176, 0.831, 0.467)   # verde
WARN     = (0.960, 0.690, 0.220)   # amber
ERR      = (0.870, 0.270, 0.270)   # rojo


# ── Helpers ─────────────────────────────────────────────

def frame(label='', collapsable=False, **kwargs):
    """frameLayout estilizado con borde PANEL (sin backgroundColorMode)."""
    return mc.frameLayout(
        label=label,
        collapsable=collapsable,
        backgroundColor=PANEL,
        marginWidth=8,
        marginHeight=6,
        **kwargs,
    )


def sep():
    """Separador delgado del color LINE."""
    mc.separator(height=1, style='in', backgroundColor=LINE)


def label(text, dim=False, cyan=False, small=False):
    """Label de texto. Sin backgroundColor (no confiable en mc.text)."""
    fn = 'smallBoldLabelFont' if small else 'boldLabelFont'
    mc.text(label=text, font=fn)
