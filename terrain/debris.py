"""
RetroMecha — terrain/debris.py
Escombros diminutos esparcidos en clusters.
Dan peso visual al suelo y contexto de destrucción alrededor de los fragmentos.
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('DEBRIS')
class DebrisModule(BaseModule):
    """
    Cluster de cubos diminutos con rotaciones caóticas.

    Parámetros usados:
        aggressiveness → densidad y dispersión del cluster
        _seed          → posiciones únicas por cluster
    """
    MODULE_NAME = 'DEBRIS'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_debris_DEBUG'

        grp = mc.group(empty=True, name='rm_debris_#')

        aggr = self._get('aggressiveness', 0.5)
        seed = self._get('_seed', 42)
        rng = random.Random(seed + hash(str(position)) % 10000)

        # Cantidad de piezas por cluster: 3-8 según agresividad
        count = rng.randint(3, max(3, int(4 + aggr * 4)))

        # Radio de dispersión del cluster
        spread = 0.3 + aggr * 0.4

        pieces = []
        for i in range(count):
            # Tamaño diminuto con variación
            s = rng.uniform(0.04, 0.14)
            # Proporciones irregulares (no cubos perfectos)
            sw = s * rng.uniform(0.6, 1.5)
            sh = s * rng.uniform(0.4, 1.2)
            sd = s * rng.uniform(0.5, 1.4)

            piece = mc.polyCube(
                w=sw, h=sh, d=sd,
                name=f'rm_debris_piece_{i}_#'
            )[0]

            # Posición dentro del cluster
            px = rng.uniform(-spread, spread)
            py = sh * 0.5  # apoyado en el suelo
            pz = rng.uniform(-spread, spread)
            mc.move(px, py, pz, piece, relative=True)

            # Rotación completamente aleatoria
            mc.rotate(
                rng.uniform(0, 360),
                rng.uniform(0, 360),
                rng.uniform(0, 360),
                piece, relative=True
            )

            pieces.append(piece)

        if pieces:
            mc.parent(*pieces, grp)

        return self._finalize_group(grp, position, rotation, scale)
