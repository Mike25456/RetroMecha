"""
RetroMecha — terrain/skyline.py
Silueta genérica de fondo lejano. Rectángulos simples de distintas alturas.
Estilo genérico e invariable — no distrae del monumento ni del mecha.
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('SKYLINE')
class SkylineModule(BaseModule):
    """
    Fila de rectángulos verticales de distintas alturas.
    Siempre el mismo estilo genérico.

    Parámetros usados:
        _seed → variación de alturas
    """
    MODULE_NAME = 'SKYLINE'

    # Cantidad fija de bloques por skyline
    BLOCK_COUNT = 8

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_skyline_DEBUG'

        grp = mc.group(empty=True, name='rm_skyline_#')

        seed = self._get('_seed', 42)
        rng = random.Random(seed + hash(str(position)) % 10000)

        total_width = 12.0
        block_w = total_width / self.BLOCK_COUNT
        start_x = -(total_width * 0.5) + block_w * 0.5

        blocks = []
        for i in range(self.BLOCK_COUNT):
            # Altura variada pero contenida
            bh = rng.uniform(0.8, 3.5)
            bw = block_w * rng.uniform(0.6, 0.95)
            bd = rng.uniform(0.3, 0.8)

            block = mc.polyCube(
                w=bw, h=bh, d=bd,
                name=f'rm_skyline_block_{i}_#'
            )[0]

            bx = start_x + i * block_w + rng.uniform(-0.15, 0.15)
            mc.move(bx, bh * 0.5, 0, block, relative=True)
            blocks.append(block)

        if blocks:
            mc.parent(*blocks, grp)

        return self._finalize_group(grp, position, rotation, scale)
