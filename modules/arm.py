"""
RetroMecha — modules/arm.py
Módulo de brazo: segmentos articulados con decrecimiento paramétrico.
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('ARM')
class ArmModule(BaseModule):
    MODULE_NAME = 'ARM'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_arm_DEBUG'

        grp = mc.group(empty=True, name='rm_arm_#')

        decay  = self._get('decay',          0.85)
        aggr   = self._get('aggressiveness', 0.5)

        # ── Brazo superior ────────────────────────────────────────────────────
        upper_w = 0.48
        upper_h = 1.0
        upper = mc.polyCube(w=upper_w, h=upper_h, d=0.44,
                            name='rm_arm_upper_#')[0]
        # centrado en origen

        # Detalle lateral brazo superior
        detail = mc.polyCube(w=0.08, h=0.6, d=0.3,
                             name='rm_arm_upper_detail_#')[0]
        mc.move(upper_w * 0.5 + 0.04, 0.1, 0, detail, relative=True)

        # ── Articulación codo (esfera hexagonal) ──────────────────────────────
        elbow = mc.polySphere(r=0.20, sa=6, se=4,
                              name='rm_arm_elbow_#')[0]
        mc.move(0, -(upper_h * 0.5 + 0.12), 0, elbow, relative=True)

        # ── Antebrazo (escalado por decay) ───────────────────────────────────
        fore_h = 0.85 * decay
        forearm = mc.polyCube(w=upper_w * decay, h=fore_h, d=0.38 * decay,
                              name='rm_arm_forearm_#')[0]
        mc.move(0, -(upper_h * 0.5 + 0.28 + fore_h * 0.5), 0,
                forearm, relative=True)

        # ── Placa de antebrazo (si agresividad alta) ──────────────────────────
        if aggr > 0.4:
            spike_h = 0.25 + aggr * 0.2
            spike = mc.polyCone(r=0.08, h=spike_h, sa=4,
                                name='rm_arm_spike_#')[0]
            mc.move(0, -(upper_h * 0.5 + 0.30 + fore_h * 0.5 + spike_h * 0.3),
                    0.22, spike, relative=True)
            mc.parent(spike, grp)

        # ── Mano/garra ────────────────────────────────────────────────────────
        hand_y = -(upper_h * 0.5 + 0.28 + fore_h + 0.25)
        hand = mc.polyCube(w=0.45 * decay, h=0.28 * decay, d=0.40 * decay,
                           name='rm_arm_hand_#')[0]
        mc.move(0, hand_y, 0, hand, relative=True)

        mc.parent(upper, detail, elbow, forearm, hand, grp)

        return self._finalize_group(grp, position, rotation, scale)
