"""
RetroMecha — modules/torso.py
Módulo de torso: cuerpo central con núcleo circular (referencia Syd Mead).
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('TORSO')
class TorsoModule(BaseModule):
    MODULE_NAME = 'TORSO'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_torso_DEBUG'

        grp = mc.group(empty=True, name='rm_torso_#')

        aggr   = self._get('aggressiveness', 0.5)
        h_sc   = self._get('height_scale',   1.0)
        sep    = self._get('separation',      0.35)

        torso_h = 2.0 * h_sc

        # ── Cuerpo principal ──────────────────────────────────────────────────
        main = mc.polyCube(w=1.75, h=torso_h, d=1.15,
                           name='rm_torso_main_#')[0]

        # ── Núcleo circular pectoral (Syd Mead) ───────────────────────────────
        nucleus = mc.polyCylinder(r=0.32, h=0.09, sa=16,
                                  name='rm_torso_nucleus_#')[0]
        mc.rotate(90, 0, 0, nucleus)
        mc.move(0, torso_h * 0.18, 0.60, nucleus, relative=True)

        # Anillo exterior del núcleo
        ring = mc.polyTorus(r=0.38, sr=0.04, sa=16, sh=8,
                            name='rm_torso_ring_#')[0]
        mc.rotate(90, 0, 0, ring)
        mc.move(0, torso_h * 0.18, 0.58, ring, relative=True)

        # ── Hombreras (tamaño crece con agresividad) ──────────────────────────
        pad_w = 0.28 + aggr * 0.22
        pad_h = 0.45 + aggr * 0.10

        pad_l = mc.polyCube(w=pad_w, h=pad_h, d=1.05,
                            name='rm_torso_pad_l_#')[0]
        mc.move(-(0.875 + pad_w * 0.5 + sep * 0.3),
                torso_h * 0.3, 0, pad_l, relative=True)

        pad_r = mc.polyCube(w=pad_w, h=pad_h, d=1.05,
                            name='rm_torso_pad_r_#')[0]
        mc.move( (0.875 + pad_w * 0.5 + sep * 0.3),
                torso_h * 0.3, 0, pad_r, relative=True)

        # ── Conector inferior (punto de unión flotante) ───────────────────────
        stub = mc.polyCylinder(r=0.18, h=0.25, sa=8,
                               name='rm_torso_stub_#')[0]
        mc.move(0, -(torso_h * 0.5 + 0.12), 0, stub, relative=True)

        # ── Panel abdominal ───────────────────────────────────────────────────
        abdomen = mc.polyCube(w=1.0, h=0.5, d=0.08,
                              name='rm_torso_abdomen_#')[0]
        mc.move(0, -(torso_h * 0.15), 0.58, abdomen, relative=True)

        mc.parent(main, nucleus, ring, pad_l, pad_r, stub, abdomen, grp)

        return self._finalize_group(grp, position, rotation, scale)
