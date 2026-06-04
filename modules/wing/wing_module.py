"""
RetroMecha — modules/wing/wing_module.py
Clase principal WingModule. Delega geometría a style_*.py
"""
from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from modules.wing._shared import build_root
import modules.wing.style_needle  as needle_mod
import modules.wing.style_compact as compact_mod
import modules.wing.style_fan     as fan_mod

_STYLES = {
    'needle':  needle_mod,
    'compact': compact_mod,
    'fan':     fan_mod,
}


@dataclass(frozen=True)
class WingTune:
    width: float  = 1.0
    length: float = 1.0
    detail: float = 1.0
    spread: float = 1.0

    @classmethod
    def from_params(cls, getter):
        return cls(
            width =float(getter('wing_width_mul',  1.0)),
            length=float(getter('wing_length_mul', 1.0)),
            detail=float(getter('wing_detail_mul', 1.0)),
            spread=float(getter('wing_spread_mul', 1.0)),
        )


@register('WING')
class WingModule(BaseModule):
    MODULE_NAME = 'WING'

    def generate(self, position=(0,0,0), scale=1.0, rotation=(0,0,0)) -> str:
        if mc is None:
            return 'rm_wing_DEBUG'

        grp   = mc.group(empty=True, name='rm_wing_#')
        aggr  = self._get('aggressiveness', 0.5)
        style = self._get('wing_style', 'needle')
        side  = -1.0 if position[0] < 0 else 1.0
        tune  = WingTune.from_params(self._get)
        s     = 1.0 + aggr * 0.75

        # Variación por seed lateral
        w_mul, l_mul, d_mul, s_mul = tune.width, tune.length, tune.detail, tune.spread
        side_seed = self._get('_side_seed')
        if side_seed is not None:
            import random as _r
            rng = _r.Random(side_seed + (1 if side > 0 else 0))
            w_mul *= 1.0 + (rng.random()-0.5)*0.30
            l_mul *= 1.0 + (rng.random()-0.5)*0.30
            d_mul *= 1.0 + (rng.random()-0.5)*0.20
            s_mul *= 1.0 + (rng.random()-0.5)*0.20

        root = build_root(side, s, aggr, d_mul)

        mod = _STYLES.get(style, needle_mod)
        blades, extras = mod.build(side, s, l_mul, w_mul, s_mul, d_mul)

        mc.parent(root, *blades, *extras, grp)

        # Aplicar materiales si hay paleta activa
        self._assign_materials(grp)

        return self._finalize_group(grp, position, rotation, scale)
