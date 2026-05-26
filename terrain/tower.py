"""
RetroMecha — terrain/tower.py
Torre hexagonal vertical que emerge de plataformas.
Puente visual entre Mead (industrial) y Shinkawa (verticalidad).
Referencia directa al núcleo pectoral hexagonal del torso del mecha.
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('TOWER')
class TowerModule(BaseModule):
    """
    Cilindro hexagonal vertical con disco o anillo en la punta.

    Parámetros usados:
        height_scale   → altura de la torre
        aggressiveness → si alta, la torre puede estar inclinada (dañada)
        _seed          → variación de altura y detalles
    """
    MODULE_NAME = 'TOWER'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_tower_DEBUG'

        grp = mc.group(empty=True, name='rm_tower_#')

        aggr = 0.5
        h_sc = self._get('height_scale', 1.0)
        seed = self._get('_seed', 42)
        rng = random.Random(seed + hash(str(position)) % 10000)

        # Dimensiones
        tower_r = rng.uniform(0.08, 0.14)
        tower_h = rng.uniform(1.0, 2.2) * h_sc

        # ── Columna hexagonal ─────────────────────────────────────────────────
        shaft = mc.polyCylinder(
            r=tower_r, h=tower_h, sa=6,
            name='rm_tower_shaft_#'
        )[0]
        mc.move(0, tower_h * 0.5, 0, shaft, relative=True)

        # ── Disco/anillo superior (ref. núcleo pectoral del mecha) ────────────
        cap_type = rng.choice(['disc', 'ring'])

        if cap_type == 'disc':
            cap = mc.polyCylinder(
                r=tower_r * 2.2, h=0.04, sa=8,
                name='rm_tower_cap_#'
            )[0]
        else:
            cap = mc.polyTorus(
                r=tower_r * 2.0, sr=tower_r * 0.35,
                sa=8, sh=6,
                name='rm_tower_cap_#'
            )[0]

        mc.move(0, tower_h, 0, cap, relative=True)

        # ── Base de anclaje ───────────────────────────────────────────────────
        base = mc.polyCylinder(
            r=tower_r * 1.5, h=0.08, sa=6,
            name='rm_tower_base_#'
        )[0]
        mc.move(0, 0.04, 0, base, relative=True)

        # ── Inclinación por daño ──────────────────────────────────────────────
        if aggr > 0.5:
            tilt = rng.uniform(3, 12) * aggr
            tilt_dir = rng.choice([-1, 1])
            mc.rotate(tilt * tilt_dir, 0, tilt * tilt_dir * 0.5,
                      grp, relative=True)

        mc.parent(shaft, cap, base, grp)

        return self._finalize_group(grp, position, rotation, scale)
