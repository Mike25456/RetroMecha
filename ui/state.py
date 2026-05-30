"""Shared state and control registry for the RetroMecha UI."""

CTRLS = {}

_SEED = [None]
_APPLYING_MECHA_PRESET = [False]
_APPLYING_TERRAIN_VALUES = [False]
_UI_BUILDING = [False]
_MODE = ['quick']

_QUICK_PROFILE_BTNS = {}  # registered by quick_panel for active highlight


def clear():
    CTRLS.clear()
    _SEED[0] = None
    _APPLYING_MECHA_PRESET[0] = False
    _APPLYING_TERRAIN_VALUES[0] = False
    _UI_BUILDING[0] = False
    _QUICK_PROFILE_BTNS.clear()


def reg(name, ctrl):
    CTRLS[name] = ctrl


def get(name):
    return CTRLS.get(name)
