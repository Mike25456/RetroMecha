"""
RetroMecha — terrain/scene_composer.py
Combina MechaBuilder + TerrainBuilder bajo un grupo raíz de escena unificado.
Punto de entrada cuando el usuario activa "Generar terreno" en la UI.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from core.mecha_builder import MechaBuilder
from terrain.terrain_builder import TerrainBuilder


class SceneComposer:
    """
    Orquesta la generación completa: mecha + terreno + composición.

    Flujo:
        1. MechaBuilder.build() → genera el robot
        2. Calcula bounding box del mecha
        3. TerrainBuilder.build() → genera terreno alrededor
        4. Parent ambos bajo grupo de escena
        5. viewFit() para encuadrar todo
    """

    TERRAIN_SEED_OFFSET = 1000

    def __init__(self, params: dict, seed: int,
                 terrain_preset: str = 'avanzada'):
        self.params = params
        self.seed = seed
        self.terrain_preset = terrain_preset

    def compose(self) -> str:
        """
        Genera mecha + terreno como escena completa.

        Returns:
            Nombre del grupo raíz de la escena
        """
        if not MAYA_AVAILABLE:
            print('[RetroMecha][Scene] Maya no disponible')
            return 'RetroMecha_Scene_DEBUG'

        print(f'[RetroMecha][Scene] Composición iniciada | '
              f'Seed: {self.seed} | Preset: {self.terrain_preset}')

        scene_group = mc.group(empty=True, name='RetroMecha_Scene_#')

        # ── Paso 1: Generar mecha ─────────────────────────────────────────────
        mecha_builder = MechaBuilder(self.params, seed=self.seed)
        mecha_group = mecha_builder.build()

        if mecha_group and mc.objExists(mecha_group):
            mc.parent(mecha_group, scene_group)

        # ── Paso 2: Calcular bounding box del mecha ──────────────────────────
        mecha_bbox = self._get_bbox(mecha_group)

        # ── Paso 3: Generar terreno ───────────────────────────────────────────
        terrain_seed = self.seed + self.TERRAIN_SEED_OFFSET
        terrain_builder = TerrainBuilder(
            params=self.params,
            seed=terrain_seed,
            preset_name=self.terrain_preset,
            mecha_bbox=mecha_bbox
        )
        terrain_group = terrain_builder.build()

        if terrain_group and mc.objExists(terrain_group):
            mc.parent(terrain_group, scene_group)

        # ── Paso 4: Encuadrar escena ──────────────────────────────────────────
        mc.select(scene_group)
        mc.viewFit(allObjects=False)

        print(f'[RetroMecha][Scene] Composición completa: {scene_group}')
        return scene_group

    def _get_bbox(self, group: str) -> tuple:
        """Calcula el bounding box de un grupo."""
        try:
            if group and mc.objExists(group):
                bb = mc.exactWorldBoundingBox(group)
                return tuple(bb)
        except Exception:
            pass
        # Fallback conservador
        return (-1.5, -1.5, -1.0, 1.5, 3.5, 1.0)
