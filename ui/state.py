"""Shared state and control registry for the RetroMecha UI."""

CTRLS = {}

_SEED = [None]
_APPLYING_MECHA_PRESET = [False]
_APPLYING_TERRAIN_VALUES = [False]
_UI_BUILDING = [False]


def reg(name, ctrl):
    CTRLS[name] = ctrl


def get(name):
    return CTRLS.get(name)
