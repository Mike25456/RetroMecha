"""
RetroMecha — terrain/scene_composer.py  v3
FIX: seed nunca puede ser None cuando llega al TerrainBuilder.
"""

import random as _random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from core.mecha_builder import MechaBuilder
from terrain.terrain_builder import TerrainBuilder

GROUND_TOP_Y  = 0.0
MECHA_FLOAT_Y = 0.5


class SceneComposer:
    TERRAIN_SEED_OFFSET = 1000

    def __init__(self, params: dict, seed: int = None,
                 terrain_preset: str = 'avanzada'):
        self.params         = params
        # Garantizar que seed NUNCA sea None
        self.seed           = seed if isinstance(seed, int) else _random.randint(0, 99999)
        self.terrain_preset = terrain_preset

    def compose(self) -> str:
        if not MAYA_AVAILABLE:
            return 'RetroMecha_Scene_DEBUG'

        print(f'[RetroMecha][Scene] Seed:{self.seed} | Preset:{self.terrain_preset}')

        scene_group = mc.group(empty=True, name='RetroMecha_Scene_#')

        # ── 1. Mecha ──────────────────────────────────────────────────────────
        mecha_group = MechaBuilder(self.params, seed=self.seed).build()

        if mecha_group and mc.objExists(mecha_group):
            try:
                bb   = mc.exactWorldBoundingBox(mecha_group)
                lift = (GROUND_TOP_Y + MECHA_FLOAT_Y) - bb[1]
                if abs(lift) > 0.01:
                    mc.move(0, lift, 0, mecha_group,
                            relative=True, worldSpace=True)
                    print(f'[RetroMecha][Scene] Mecha elevado {lift:.2f} u')
            except Exception as e:
                print(f'[RetroMecha][Scene] Elevación: {e}')
            mc.parent(mecha_group, scene_group)

        # ── 2. Bbox post-elevación ────────────────────────────────────────────
        mecha_bbox = self._get_bbox(mecha_group)

        # ── 3. Terreno ────────────────────────────────────────────────────────
        terrain_seed = self.seed + self.TERRAIN_SEED_OFFSET   # siempre int + int
        tb = TerrainBuilder(
            params=self.params,
            seed=terrain_seed,
            preset_name=self.terrain_preset,
            mecha_bbox=mecha_bbox,
        )
        terrain_group = tb.build()

        if terrain_group and mc.objExists(terrain_group):
            mc.parent(terrain_group, scene_group)

        mc.select(scene_group)
        try:
            mc.viewFit(allObjects=False)
        except Exception:
            mc.viewFit()

        print(f'[RetroMecha][Scene] Completo: {scene_group}')
        return scene_group

    def _get_bbox(self, group: str) -> tuple:
        try:
            if group and mc.objExists(group):
                return tuple(mc.exactWorldBoundingBox(group))
        except Exception:
            pass
        return (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)