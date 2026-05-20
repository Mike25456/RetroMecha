"""
RetroMecha — terrain/scene_composer.py  v2
Combina MechaBuilder + TerrainBuilder.
Levanta el mecha sobre el suelo para evitar interpenetración.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from core.mecha_builder import MechaBuilder
from terrain.terrain_builder import TerrainBuilder

# Y del top del ground plane (surface.h=0.1 centrada en gp_y=-0.05 → top=0.0)
GROUND_TOP_Y = 0.0
# Distancia de flotación del mecha sobre el suelo
MECHA_FLOAT_Y = 0.5


class SceneComposer:
    TERRAIN_SEED_OFFSET = 1000

    def __init__(self, params: dict, seed: int,
                 terrain_preset: str = 'avanzada'):
        self.params = params
        self.seed = seed
        self.terrain_preset = terrain_preset

    def compose(self) -> str:
        if not MAYA_AVAILABLE:
            return 'RetroMecha_Scene_DEBUG'

        print(f'[RetroMecha][Scene] Composición | '
              f'Seed:{self.seed} Preset:{self.terrain_preset}')

        scene_group = mc.group(empty=True, name='RetroMecha_Scene_#')

        # ── 1. Generar mecha ──────────────────────────────────────────────────
        mecha_builder = MechaBuilder(self.params, seed=self.seed)
        mecha_group   = mecha_builder.build()

        if mecha_group and mc.objExists(mecha_group):
            # Levantar el mecha: su bounding box min Y debe quedar en GROUND_TOP_Y + FLOAT
            try:
                bb = mc.exactWorldBoundingBox(mecha_group)
                mecha_min_y = bb[1]
                lift = (GROUND_TOP_Y + MECHA_FLOAT_Y) - mecha_min_y
                if abs(lift) > 0.01:
                    mc.move(0, lift, 0, mecha_group, relative=True, worldSpace=True)
                    print(f'[RetroMecha][Scene] Mecha elevado {lift:.2f} u')
            except Exception as e:
                print(f'[RetroMecha][Scene] No se pudo elevar mecha: {e}')

            mc.parent(mecha_group, scene_group)

        # ── 2. Bounding box post-elevación ────────────────────────────────────
        mecha_bbox = self._get_bbox(mecha_group)

        # ── 3. Generar terreno ────────────────────────────────────────────────
        terrain_builder = TerrainBuilder(
            params=self.params,
            seed=self.seed + self.TERRAIN_SEED_OFFSET,
            preset_name=self.terrain_preset,
            mecha_bbox=mecha_bbox
        )
        terrain_group = terrain_builder.build()

        if terrain_group and mc.objExists(terrain_group):
            mc.parent(terrain_group, scene_group)

        # ── 4. Encuadrar ──────────────────────────────────────────────────────
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
