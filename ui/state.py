"""Shared state and control registry for the RetroMecha UI."""

CTRLS = {}

_SEED = [None]
_APPLYING_MECHA_PRESET = [False]
_APPLYING_TERRAIN_VALUES = [False]
_UI_BUILDING = [False]


def clear():
    CTRLS.clear()
    _SEED[0] = None
    _APPLYING_MECHA_PRESET[0] = False
    _APPLYING_TERRAIN_VALUES[0] = False
    _UI_BUILDING[0] = False


def reg(name, ctrl):
    CTRLS[name] = ctrl


def get(name):
    return CTRLS.get(name)
