"""
RetroMecha — modules/wing.py
Módulo de ala: placas superpuestas (composición laminar, ref. Takayuki Yanase).
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('WING')
class WingModule(BaseModule):
    MODULE_NAME = 'WING'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_wing_DEBUG'

        grp = mc.group(empty=True, name='rm_wing_#')

        aggr  = self._get('aggressiveness', 0.5)
        decay = self._get('decay', 0.85)

        wing_h = 1.1 + aggr * 0.3

        # ── Placa principal ───────────────────────────────────────────────────
        main = mc.polyCube(w=0.14, h=wing_h, d=0.75,
                           name='rm_wing_main_#')[0]

        # ── Sub-placa (estratificación Yanase) ────────────────────────────────
        sub = mc.polyCube(w=0.10, h=wing_h * 0.80, d=0.52,
                          name='rm_wing_sub_#')[0]
        mc.move(0.13, 0.08, 0, sub, relative=True)

        # ── Placa terciaria (solo si alta agresividad) ────────────────────────
        if aggr > 0.5:
            sub2 = mc.polyCube(w=0.08, h=wing_h * 0.55, d=0.35,
                               name='rm_wing_sub2_#')[0]
            mc.move(0.24, 0.15, 0, sub2, relative=True)
            mc.parent(sub2, grp)

        # ── Punta / spike ─────────────────────────────────────────────────────
        tip_h = 0.30 + aggr * 0.25
        tip = mc.polyCone(r=0.07, h=tip_h, sa=4,
                          name='rm_wing_tip_#')[0]
        mc.move(0, wing_h * 0.5 + tip_h * 0.5 - 0.05, 0, tip, relative=True)

        # ── Conector base (une con el torso) ──────────────────────────────────
        base = mc.polyCube(w=0.22, h=0.18, d=0.3,
                           name='rm_wing_base_#')[0]
        mc.move(-0.04, -(wing_h * 0.5 - 0.09), 0, base, relative=True)

        mc.parent(main, sub, tip, base, grp)

        return self._finalize_group(grp, position, rotation, scale)
