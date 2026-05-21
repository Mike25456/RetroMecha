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
from utils.hard_surface import apply_support_edges
from utils.maya_materials import assign_material


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
            if self.params.get('use_support_edges', True):
                count = apply_support_edges(self._root_group, offset=0.010,
                                            max_faces=90)
                print(f'[RetroMecha] Support edges aplicados: {count}')
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
        use_head   = self.params.get('use_head',         True)
        use_arms   = self.params.get('use_arms',         True)
        use_wings  = self.params.get('use_wings',        True)

        # ── TORSO primero (la cabeza se apoya en su bbox, no en separation) ───
        torso = self._spawn('TORSO', position=(0, 0, 0), scale=h_scale)

        head_y = 1.15 * h_scale
        if torso and mc.objExists(torso):
            bb = mc.exactWorldBoundingBox(torso)
            # Pivot de cabeza ≈ centro; subir media altura de cabeza + hueco cuello
            head_y = bb[4] + 0.06 + 0.48 * h_scale

        if use_head:
            self._spawn('HEAD', position=(0, head_y, 0))

        # ── ARMS ──────────────────────────────────────────────────────────────
        arm_x = 1.18 + sep * 0.35
        arm_y = 0.5 * h_scale
        if use_arms:
            self._spawn('ARM',
                        position=(-arm_x, arm_y, 0.16),
                        rotation=(0, 0, angle * 0.18),
                        scale=decay)

        if use_arms and symmetry:
            self._spawn('ARM',
                        position=( arm_x, arm_y, 0.16),
                        rotation=(0, 0, -angle * 0.18),
                        scale=decay)

        # ── WINGS: alta en la espalda; separation aleja del torso en Z ─────────
        wing_x = 0.40
        wing_y = 1.05 * h_scale
        wing_z = -0.50 - sep * 0.55
        if torso and mc.objExists(torso):
            bb = mc.exactWorldBoundingBox(torso)
            wing_y = bb[1] + (bb[4] - bb[1]) * 0.86
            wing_z = bb[2] - 0.32 - sep * 1.55
            wing_x = (bb[3] - bb[0]) * 0.24

        if use_wings:
            self._spawn('WING',
                        position=(-wing_x, wing_y, wing_z),
                        rotation=(-4, -16, 0))

        if use_wings and symmetry:
            self._spawn('WING',
                        position=(wing_x, wing_y, wing_z),
                        rotation=(-4, 16, 0))

        self._build_energy_fields(arm_x, arm_y, head_y, h_scale, symmetry,
                                  use_head, use_arms)

    # ── Capa de paneles ────────────────────────────────────────────────────────

    def _apply_panel_layer(self):
        """Post-proceso: añade paneles decorativos sobre el torso y brazos."""
        try:
            from layers.panel_layer import PanelLayer
            PanelLayer(self.params, self._root_group).apply()
        except ImportError:
            print('[RetroMecha] panel_layer no disponible, omitiendo')

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _build_energy_fields(self, arm_x: float, arm_y: float, head_y: float,
                             h_scale: float, symmetry: bool,
                             use_head: bool, use_arms: bool) -> None:
        """Cyan connector rings for the separated, floating mecha parts."""
        if not MAYA_AVAILABLE or not self._root_group:
            return

        grp = mc.group(empty=True, name='rm_energy_fields_#')
        rings = [
            self._energy_ring((0, -0.98 * h_scale, 0), 0.30, (0, 0, 0)),
        ]
        if use_head:
            rings.append(self._energy_ring((0, head_y - 0.52, 0), 0.24, (0, 0, 0)))
        if use_arms:
            rings.append(self._energy_ring((-arm_x * 0.58, arm_y + 0.22, 0),
                                           0.22, (0, 90, 0)))
        if use_arms and symmetry:
            rings.append(self._energy_ring((arm_x * 0.58, arm_y + 0.22, 0),
                                           0.22, (0, 90, 0)))

        rings = [r for r in rings if r and mc.objExists(r)]
        if rings:
            mc.parent(rings, grp)
            mc.parent(grp, self._root_group)
        else:
            mc.delete(grp)

    def _energy_ring(self, position: tuple, radius: float,
                     rotation: tuple) -> str | None:
        try:
            ring = mc.polyTorus(r=radius, sr=0.011, sa=32, sh=4,
                                name='rm_energy_ring_#')[0]
            mc.move(position[0], position[1], position[2], ring)
            mc.rotate(rotation[0], rotation[1], rotation[2], ring)
            assign_material(ring, "rm_cyan_glow_mat")
            if mc.objExists(ring):
                mc.delete(ring, ch=True)
            return ring
        except Exception:
            return None

    def _spawn(self, module_name: str,
               position=(0, 0, 0),
               scale=1.0,
               rotation=(0, 0, 0)) -> str | None:
        """Instancia un módulo y lo parenta al grupo raíz.

        Los errores dentro de generate() se aíslan aquí para que un módulo
        roto no cancele el build completo. Los nodos huérfanos que pudiera
        haber creado el módulo antes de fallar se eliminan automáticamente.
        """
        cls = get_module(module_name)
        if cls is None:
            print(f'[RetroMecha] Módulo "{module_name}" no registrado, omitiendo')
            return None

        # Snapshot de nodos antes de intentar el generate, para poder
        # limpiar cualquier nodo huérfano si el módulo lanza una excepción.
        nodes_before = set(mc.ls(dag=True) or [])

        instance = cls(self.params)
        try:
            node = instance.generate(position=position,
                                     scale=scale,
                                     rotation=rotation)
        except Exception as e:
            print(f'[RetroMecha] ERROR en módulo "{module_name}": {e}')
            import traceback
            traceback.print_exc()

            # Limpia nodos huérfanos creados durante el generate() fallido
            nodes_after = set(mc.ls(dag=True) or [])
            orphans = list(nodes_after - nodes_before)
            if orphans:
                try:
                    mc.delete(orphans)
                    print(f'[RetroMecha] Limpiados {len(orphans)} nodo(s) huérfano(s) '
                          f'de "{module_name}"')
                except Exception:
                    pass
            return None

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
