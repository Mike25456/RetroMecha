"""Shared state and control registry for the RetroMecha UI."""

CTRLS = {}

_SEED = [None]
_ACTIVE_ANIM = ['idle']
_APPLYING_MECHA_PRESET = [False]
_APPLYING_TERRAIN_VALUES = [False]
_UI_BUILDING = [False]
_MODE = ['quick']

_QUICK_PROFILE_BTNS = {}
_QUICK_MECHA_OVERRIDES = {}
_QUICK_TERRAIN_OVERRIDES = {}
_QUICK_PALETTE = [None]
_TERRAIN_PRESET = ['Avanzada']
_MECHA_PARAMS = {}
_TERRAIN_PARAMS = {}

# Controles que NUNCA se destruyen al cambiar de modo (seed, layouts raíz)
_PERMANENT = {'main_content', 'scene_menu'}


def clear():
    CTRLS.clear()
    _SEED[0] = None
    _APPLYING_MECHA_PRESET[0] = False
    _APPLYING_TERRAIN_VALUES[0] = False
    _UI_BUILDING[0] = False
    _QUICK_PROFILE_BTNS.clear()
    _QUICK_MECHA_OVERRIDES.clear()
    _QUICK_TERRAIN_OVERRIDES.clear()
    _QUICK_PALETTE[0] = None
    _TERRAIN_PRESET[0] = 'Avanzada'
    _MECHA_PARAMS.clear()
    _TERRAIN_PARAMS.clear()


def clear_dynamic():
    """Borra controles dinámicos preservando los permanentes."""
    to_remove = [k for k in list(CTRLS.keys()) if k not in _PERMANENT]
    for k in to_remove:
        del CTRLS[k]


def reg(name, ctrl):
    CTRLS[name] = ctrl


def get(name):
    return CTRLS.get(name)
