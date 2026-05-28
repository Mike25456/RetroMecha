"""
RetroMecha — terrain/skyline.py  v2
Silueta de fondo lejano. Bloques más grandes y anchos para ser visibles.
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
    MODULE_NAME = 'SKYLINE'

    BLOCK_COUNT = 12

    def generate(self, position=(0,0,0), scale=1.0, rotation=(0,0,0)) -> str:
        if mc is None:
            return 'rm_skyline_DEBUG'

        grp  = mc.group(empty=True, name='rm_skyline_#')
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + hash(str(position)) % 9999)

        total_w = 30.0    # franja ancha
        block_w = total_w / self.BLOCK_COUNT
        start_x = -(total_w * 0.5) + block_w * 0.5

        blocks = []
        for i in range(self.BLOCK_COUNT):
            bh = rng.uniform(2.0, 8.0)
            bw = block_w * rng.uniform(0.65, 0.95)
            bd = rng.uniform(0.6, 1.8)

            block = mc.polyCube(w=bw, h=bh, d=bd,
                                name=f'rm_skyline_blk_{i}_#')[0]
            bx = start_x + i * block_w + rng.uniform(-0.3, 0.3)
            mc.move(bx, bh * 0.5, 0, block, relative=True)
            blocks.append(block)

        if blocks:
            mc.parent(*blocks, grp)
        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)