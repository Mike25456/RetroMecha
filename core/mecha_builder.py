"""
RetroMecha — core/mecha_builder.py
Orquestador central: interpreta el L-System y ensambla los módulos en Maya.

Este es el único archivo que conoce la estructura global del mecha.
Los módulos solo saben crear su propia geometría local.
"""

import random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False
    print('[RetroMecha] maya.cmds no disponible — modo debug')

from core.l_system import LSystem
from core.module_registry import get as get_module, is_registered


class MechaBuilder:
    """
    Ensambla un mecha completo a partir de parámetros de UI y una semilla.

    Flujo:
        1. LSystem.expand()     → cadena de símbolos
        2. LSystem.to_build_plan() → lista de módulos a instanciar
        3. Por cada módulo: Registry.get() → instancia → generate()
        4. parent() de todos los grupos bajo el grupo raíz
        5. Layers post-proceso (paneles, etc.)
    """

    def __init__(self, params: dict, seed: int = None):
        self.params = params
        self.seed = seed or random.randint(0, 99999)
        self.l_system = LSystem(seed=self.seed)
        self._root_group = None

    # ── Punto de entrada principal ────────────────────────────────────────────

    def build(self) -> str:
        """
        Construye el mecha completo.

        Returns:
            Nombre del grupo raíz en Maya
        """
        print(f'[RetroMecha] Build iniciado | Seed: {self.seed}')

        if not MAYA_AVAILABLE:
            print('[RetroMecha] Maya no disponible, mostrando plan en consola')
            self._debug_build()
            return 'RetroMecha_DEBUG'

        self._root_group = mc.group(empty=True, name='RetroMecha_#')

        try:
            self._build_body()
            if self.params.get('use_panels', True):
                self._apply_panel_layer()
            mc.select(self._root_group)
            print(f'[RetroMecha] Build completo: {self._root_group}')
        except Exception as e:
            print(f'[RetroMecha] ERROR durante build: {e}')
            import traceback
            traceback.print_exc()

        return self._root_group

    # ── Construcción del cuerpo ───────────────────────────────────────────────

    def _build_body(self):
        sep        = self.params.get('separation',       0.35)
        decay      = self.params.get('decay',            0.85)
        symmetry   = self.params.get('symmetry',         True)
        angle      = self.params.get('connector_angle',  15.0)
        h_scale    = self.params.get('height_scale',     1.0)

        # ── HEAD ─────────────────────────────────────────────────────────────
        self._spawn('HEAD',
                    position=(0, (2.6 + sep) * h_scale, 0))

        # ── TORSO (núcleo) ────────────────────────────────────────────────────
        self._spawn('TORSO',
                    position=(0, 0, 0),
                    scale=h_scale)

        # ── ARMS ──────────────────────────────────────────────────────────────
        arm_x = 1.25 + sep
        arm_y = 0.5 * h_scale
        self._spawn('ARM',
                    position=(-arm_x, arm_y, 0),
                    rotation=(0, 0,  angle),
                    scale=decay)

        if symmetry:
            self._spawn('ARM',
                        position=( arm_x, arm_y, 0),
                        rotation=(0, 0, -angle),
                        scale=decay)

        # ── WINGS ─────────────────────────────────────────────────────────────
        wing_x = 0.9 + sep
        wing_y = 1.1 * h_scale
        self._spawn('WING',
                    position=(-wing_x, wing_y, -0.3),
                    rotation=(0, 0,  angle * 1.5))

        if symmetry:
            self._spawn('WING',
                        position=( wing_x, wing_y, -0.3),
                        rotation=(0, 0, -angle * 1.5))

    # ── Capa de paneles ────────────────────────────────────────────────────────

    def _apply_panel_layer(self):
        """Post-proceso: añade paneles decorativos sobre el torso y brazos."""
        try:
            from layers.panel_layer import PanelLayer
            PanelLayer(self.params, self._root_group).apply()
        except ImportError:
            print('[RetroMecha] panel_layer no disponible, omitiendo')

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _spawn(self, module_name: str,
               position=(0, 0, 0),
               scale=1.0,
               rotation=(0, 0, 0)) -> str | None:
        """Instancia un módulo y lo parenta al grupo raíz."""
        cls = get_module(module_name)
        if cls is None:
            print(f'[RetroMecha] Módulo "{module_name}" no registrado, omitiendo')
            return None

        instance = cls(self.params)
        node = instance.generate(position=position,
                                 scale=scale,
                                 rotation=rotation)
        if node and mc.objExists(node):
            mc.parent(node, self._root_group)
        return node

    def _debug_build(self):
        """Modo sin Maya: imprime el plan de construcción."""
        string = self.l_system.expand('T', iterations=2)
        plan = self.l_system.to_build_plan(string)
        print(f'[LSystem] Cadena: {string}')
        print('[LSystem] Plan:')
        for step in plan:
            indent = '  ' * step['depth']
            print(f'  {indent}→ {step["module"]} (rama: {step["branch"]})')
