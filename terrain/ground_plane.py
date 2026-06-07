"""
RetroMecha — terrain/ground_plane.py  v5
Suelo industrial con paneles de rejilla, franjas elevadas y variación tonal.

MEJORAS sobre v4:
  - Paneles de rejilla en cuadrícula (sx/sz elevados → subdivided grid look)
  - Franja central elevada bajo el mecha (landing grid)
  - 4 franjas perimetrales de acento (rm_terrain_accent_mat)
  - Borde exterior achaflanado en dos niveles
  - Ranuras radiales cruzadas (decoración ground-level)
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('GROUND_PLANE')
class GroundPlaneModule(BaseModule):
    MODULE_NAME = 'GROUND_PLANE'

    def generate(self, position=(0, 0, 0), scale=1.0, rotation=(0, 0, 0)) -> str:
        if mc is None:
            return 'rm_ground_DEBUG'

        grp = mc.group(empty=True, name='rm_ground_#')
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + 7777)

        gs = 150.0   # tamaño total del suelo

        # ── 1. Superficie principal (subdividida — rejilla visible con materiales)
        surface = mc.polyCube(
            w=gs, h=0.10, d=gs,
            sx=20, sz=20,          # 20×20 → paneles de 7.5u cada uno
            name='rm_ground_surface_#'
        )[0]

        # ── 2. Borde exterior nivel-1 (plano, ligeramente más bajo)
        border1 = mc.polyCube(
            w=gs + 1.2, h=0.06, d=gs + 1.2,
            name='rm_ground_border_#'
        )[0]
        mc.move(0, -0.07, 0, border1, relative=True)

        # ── 3. Borde exterior nivel-2 (acento, muy delgado)
        border2 = mc.polyCube(
            w=gs + 2.2, h=0.03, d=gs + 2.2,
            name='rm_ground_border_#'
        )[0]
        mc.move(0, -0.12, 0, border2, relative=True)

        parts = [surface, border1, border2]

        # ── 4. Landing grid central (plataforma baja bajo el mecha)
        #       rm_terrain_accent_mat por token 'slot'
        landing = mc.polyCube(
            w=12.0, h=0.04, d=10.0,
            sx=4, sz=4,
            name='rm_ground_slot_landing_#'
        )[0]
        mc.move(0, 0.07, 0, landing, relative=True)
        parts.append(landing)

        # ── 5. Franjas de acento cruzadas (X y Z) sobre el suelo
        #       Usamos 'slot' en el nombre → rm_terrain_accent_mat
        strip_configs = [
            # (ancho, profundidad, posX, posZ, es_X_orientado)
            (gs * 0.85, 0.35, 0.0,   0.0,   True),   # franja X larga
            (0.35, gs * 0.85, 0.0,   0.0,   False),  # franja Z larga
            (gs * 0.55, 0.20, 0.0,   8.0,   True),   # franja X media
            (gs * 0.55, 0.20, 0.0,  -8.0,   True),   # franja X media
            (0.20, gs * 0.55, 8.0,   0.0,   False),  # franja Z media
            (0.20, gs * 0.55, -8.0,  0.0,   False),  # franja Z media
        ]
        for sw, sd, sx, sz, _ in strip_configs:
            strip = mc.polyCube(
                w=sw, h=0.03, d=sd,
                name='rm_ground_slot_strip_#'
            )[0]
            mc.move(sx, 0.065, sz, strip, relative=True)
            parts.append(strip)

        # ── 6. Paneles de acento en las cuatro esquinas del suelo
        corner_size = rng.uniform(14.0, 20.0)
        for cx, cz in [(-1, -1), (1, -1), (-1, 1), (1, 1)]:
            corner = mc.polyCube(
                w=corner_size, h=0.025, d=corner_size,
                sx=2, sz=2,
                name='rm_ground_slot_corner_#'
            )[0]
            mc.move(
                cx * (gs * 0.5 - corner_size * 0.5 - 1.0),
                0.06,
                cz * (gs * 0.5 - corner_size * 0.5 - 1.0),
                corner, relative=True
            )
            parts.append(corner)

        # ── 7. Micro-relieves: pequeñas losas dispersas (escombros integrados al suelo)
        #       Usadas para que el suelo no sea completamente plano
        n_slabs = rng.randint(12, 20)
        for i in range(n_slabs):
            sw = rng.uniform(1.5, 4.5)
            sd = rng.uniform(1.0, 3.5)
            sh = rng.uniform(0.02, 0.06)
            px = rng.uniform(-gs * 0.38, gs * 0.38)
            pz = rng.uniform(-gs * 0.38, gs * 0.38)
            # Evitar zona central del mecha
            if abs(px) < 7.0 and abs(pz) < 7.0:
                continue
            ry = rng.uniform(0, 90)
            slab = mc.polyCube(
                w=sw, h=sh, d=sd,
                name='rm_ground_surface_slab_#'
            )[0]
            mc.move(px, sh * 0.5 + 0.055, pz, slab, relative=True)
            mc.rotate(0, ry, 0, slab, relative=True)
            parts.append(slab)

        mc.parent(*parts, grp)
        return self._finalize_group(grp, position, rotation, scale)