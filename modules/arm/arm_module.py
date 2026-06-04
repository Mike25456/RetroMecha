"""
RetroMecha — modules/arm/arm_module.py
Clase principal ArmModule. Delega geometría a style_*.py
"""
from dataclasses import dataclass

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
import modules.arm.style_standard as standard_mod
import modules.arm.style_heavy    as heavy_mod
import modules.arm.style_blade    as blade_mod
import modules.arm.style_cannon   as cannon_mod
import modules.arm.style_shield   as shield_mod

_STYLES = {
    'standard': standard_mod,
    'heavy':    heavy_mod,
    'blade':    blade_mod,
    'cannon':   cannon_mod,
    'shield':   shield_mod,
}


@dataclass(frozen=True)
class ArmTune:
    width:  float = 1.0
    length: float = 1.0
    detail: float = 1.0
    hand:   float = 1.0

    @classmethod
    def from_params(cls, getter):
        return cls(
            width =float(getter('arm_width_mul',  1.0)),
            length=float(getter('arm_length_mul', 1.0)),
            detail=float(getter('arm_detail_mul', 1.0)),
            hand  =float(getter('arm_hand_mul',   1.0)),
        )


@register('ARM')
class ArmModule(BaseModule):
    MODULE_NAME = 'ARM'

    def generate(self, position=(0,0,0), scale=1.0, rotation=(0,0,0)) -> str:
        if mc is None:
            return 'rm_arm_DEBUG'

        grp   = mc.group(empty=True, name='rm_arm_#')
        aggr  = self._get('aggressiveness', 0.5)
        style = self._get('arm_style', 'standard')
        side  = -1.0 if position[0] < 0 else 1.0
        tune  = ArmTune.from_params(self._get)
        w, l, d_mul, hm = tune.width, tune.length, tune.detail, tune.hand

        # Variación lateral por seed
        side_seed = self._get('_side_seed')
        if side_seed is not None:
            import random as _r
            rng = _r.Random(side_seed + (1 if side > 0 else 0))
            w     *= 1.0 + (rng.random()-0.5)*0.30
            l     *= 1.0 + (rng.random()-0.5)*0.30
            hm    *= 1.0 + (rng.random()-0.5)*0.20
            d_mul *= 1.0 + (rng.random()-0.5)*0.20

        mod = _STYLES.get(style, standard_mod)
        mod.build(grp, w, l, d_mul, hm, side, aggr)

        # Aplicar materiales si hay paleta activa
        self._assign_materials(grp)

        return self._finalize_group(grp, position, rotation, scale)
