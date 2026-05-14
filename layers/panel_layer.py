"""
RetroMecha — layers/panel_layer.py
Capa de post-proceso: añade paneles mecánicos decorativos encima de la geometría generada.

Esta capa corre DESPUÉS de que todos los módulos han sido creados.
Lee los grupos existentes y añade paneles flotantes sobre ellos.
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

import random


class PanelLayer:
    """
    Post-procesador que detecta las piezas del mecha y añade
    paneles mecánicos planos sobre sus superficies.

    Probabilidad de panel configurable (50-70% según documento técnico).
    """

    PANEL_PROBABILITY = 0.60  # 60% chance por pieza

    def __init__(self, params: dict, root_group: str):
        self.params = params
        self.root   = root_group
        self._rng   = random.Random(params.get('_seed', 42))

    def apply(self):
        """Aplica paneles al grupo raíz del mecha."""
        if not MAYA_AVAILABLE:
            return

        panel_grp = mc.group(empty=True, name='rm_panels_#')

        # Buscar grupos de torso y brazos para añadir paneles
        targets = mc.listRelatives(self.root, children=True, type='transform') or []

        panels_created = 0
        for target in targets:
            if self._rng.random() < self.PANEL_PROBABILITY:
                panel = self._create_panel(target)
                if panel:
                    mc.parent(panel, panel_grp)
                    panels_created += 1

        if panels_created > 0:
            mc.parent(panel_grp, self.root)
            print(f'[RetroMecha][PanelLayer] {panels_created} paneles creados')
        else:
            mc.delete(panel_grp)

    def _create_panel(self, target: str) -> str | None:
        """Crea un panel plano posicionado cerca del target."""
        try:
            bb = mc.exactWorldBoundingBox(target)
            # bb = [xmin, ymin, zmin, xmax, ymax, zmax]
            cx = (bb[0] + bb[3]) * 0.5
            cy = (bb[1] + bb[4]) * 0.5
            cz = (bb[5])  # cara frontal

            # Variación aleatoria de tamaño
            pw = self._rng.uniform(0.25, 0.55)
            ph = self._rng.uniform(0.15, 0.35)

            panel = mc.polyCube(w=pw, h=ph, d=0.04,
                                name='rm_panel_#')[0]

            # Offset aleatorio sobre la superficie frontal
            ox = self._rng.uniform(-0.2, 0.2)
            oy = self._rng.uniform(-0.15, 0.15)
            mc.move(cx + ox, cy + oy, cz + 0.03, panel)

            return panel
        except Exception:
            return None
