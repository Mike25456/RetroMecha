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
from utils.maya_scene import force_preview_one
from materials.materializer import materialize_mecha

# Altura del anclaje del hombro dentro del módulo ARM (espacio local, pre-escala).
_ARM_SHOULDER_JOINT_Y = 0.60


def _find_shoulder_pad(torso: str, side: str):
    """Busca rm_torso_shoulder_l o rm_torso_shoulder_r bajo el grupo torso."""
    if not torso or not mc.objExists(torso):
        return None
    token = f"rm_torso_shoulder_{side}"
    for node in mc.listRelatives(torso, allDescendents=True,
                                 type='transform', fullPath=True) or []:
        short = node.rsplit('|', 1)[-1]
        if short.startswith(token):
            return node
    return None


def _arm_attach_from_torso(torso: str | None, h_scale: float) -> tuple:
    """
    Punto de anclaje del brazo (x, y, z) y escala uniforme.
    x > 0 = lado derecho; el izquierdo usa -x.
    """
    arm_scale = 0.75 * h_scale
    joint_y = _ARM_SHOULDER_JOINT_Y * arm_scale

    pad = _find_shoulder_pad(torso, 'r') or _find_shoulder_pad(torso, 'l')
    if pad and mc.objExists(pad):
        bb = mc.exactWorldBoundingBox(pad)
        arm_x = abs((bb[0] + bb[3]) * 0.5)
        # El joint del brazo (y≈0.60 local) queda al borde inferior de la hombrera.
        arm_y = bb[1] - joint_y
        arm_z = (bb[2] + bb[5]) * 0.5
        return arm_x, arm_y, arm_z, arm_scale

    spread = 1.06
    torso_h = 2.0 * h_scale
    pad_y = torso_h * 0.30 + 0.08 * h_scale
    return (
        spread * h_scale,
        pad_y - joint_y,
        -0.06 * h_scale,
        arm_scale,
    )


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
            if self.params.get('use_support_edges', True):
                count = apply_support_edges(
                    self._root_group, max_faces=500,
                )
                print(f'[RetroMecha] Support edges aplicados: {count}')
            materialize_mecha(self._root_group)
            force_preview_one(self._root_group)
            mc.select(self._root_group)
            print(f'[RetroMecha] Build completo: {self._root_group}')
        except Exception as e:
            print(f'[RetroMecha] ERROR durante build: {e}')
            import traceback
            traceback.print_exc()

        return self._root_group

    # ── Construcción del cuerpo ───────────────────────────────────────────────

    def _build_body(self):
        symmetry   = self.params.get('symmetry',         True)

        h_scale    = self.params.get('height_scale',     1.0)
        use_head   = self.params.get('use_head',         True)
        use_arms   = self.params.get('use_arms',         True)
        use_wings  = self.params.get('use_wings',        True)
        use_energy = self.params.get('use_energy_fields', True)

        torso = self._spawn('TORSO', position=(0, 0, 0), scale=h_scale)

        head_y = 1.15 * h_scale
        arm_x, arm_y, arm_z, arm_scale = _arm_attach_from_torso(torso, h_scale)
        wing_x = 0.40 * h_scale
        wing_y = 1.05 * h_scale
        wing_z = -0.50

        if torso and mc.objExists(torso):
            bb = mc.exactWorldBoundingBox(torso)
            half_w = (bb[3] - bb[0]) * 0.5
            height = bb[4] - bb[1]

            head_y = bb[4] + 0.06 + 0.48 * h_scale
            wing_x = half_w * 0.48
            wing_y = bb[1] + height * 0.86
            wing_z = bb[2] - 0.32

        head_grp = None
        if use_head:
            head_grp = self._spawn('HEAD', position=(0, head_y, 0))

        wing_left = wing_right = None

        if use_arms:
            self._spawn('ARM',
                        position=(-arm_x, arm_y, arm_z),
                        rotation=(0, 0, 2.7),
                        scale=arm_scale)

            if symmetry:
                self._spawn('ARM',
                            position=(arm_x, arm_y, arm_z),
                            rotation=(0, 0, -2.7),
                            scale=arm_scale)
            else:
                right_overrides = {'_side_seed': self.seed + 1}
                right_style = self.params.get('arm_style_right')
                if right_style:
                    right_overrides['arm_style'] = right_style
                self._spawn('ARM',
                            position=(arm_x, arm_y, arm_z),
                            rotation=(0, 0, -2.7),
                            scale=arm_scale,
                            overrides=right_overrides)

        if use_wings:
            wing_left = self._spawn('WING',
                                    position=(-wing_x, wing_y, wing_z),
                                    rotation=(-4, -16, 0))

            if symmetry:
                wing_right = self._spawn('WING',
                                         position=(wing_x, wing_y, wing_z),
                                         rotation=(-4, 16, 0))
            else:
                right_overrides = {'_side_seed': self.seed + 1}
                right_style = self.params.get('wing_style_right')
                if right_style:
                    right_overrides['wing_style'] = right_style
                wing_right = self._spawn('WING',
                                         position=(wing_x, wing_y, wing_z),
                                         rotation=(-4, 16, 0),
                                         overrides=right_overrides)

        if use_energy:
            self._build_energy_fields(h_scale, torso, head_grp,
                                      wing_left, wing_right)

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _build_energy_fields(self, h_scale: float,
                             torso_grp: str | None,
                             head_grp: str | None,
                             wing_left: str | None = None,
                             wing_right: str | None = None) -> None:
        """Cyan connector rings anchored to actual bbox of torso/head/stub/wings."""
        if not MAYA_AVAILABLE or not self._root_group:
            return

        grp = mc.group(empty=True, name='rm_energy_fields_#')
        rings = []

        def _bbox_bot(node):
            return mc.exactWorldBoundingBox(node)[1]

        def _bbox_top(node):
            return mc.exactWorldBoundingBox(node)[4]

        def _ring_at(pos, r, rot=(0, 0, 0)):
            rings.append(self._energy_ring(pos, r, rot))

        # ── Neck ring: entre cabeza y torso (tamaño fijo)
        if head_grp and mc.objExists(head_grp) and torso_grp and mc.objExists(torso_grp):
            try:
                neck_y = (_bbox_bot(head_grp) + _bbox_top(torso_grp)) * 0.5
                _ring_at((0, neck_y, 0), 0.20)
            except Exception:
                pass

        # ── Hip ring: justo debajo del stub (tamaño fijo)
        if torso_grp and mc.objExists(torso_grp):
            try:
                stub = [n for n in (mc.listRelatives(torso_grp, allDescendents=True,
                                                     type='transform') or [])
                        if 'stub' in n]
                ref = stub[0] if stub else torso_grp
                bot_y = _bbox_bot(ref) - 0.04
                _ring_at((0, bot_y, 0), 0.28)
            except Exception:
                _ring_at((0, -0.98 * h_scale, 0), 0.28)

        # ── Wing root rings: centrados en el hub de cada ala (tamaño fijo)
        for wing in (wing_left, wing_right):
            if not wing or not mc.objExists(wing):
                continue
            try:
                hub = [n for n in (mc.listRelatives(wing, allDescendents=True,
                                                    type='transform') or [])
                       if 'hub' in n and 'glow' not in n]
                if hub:
                    bb = mc.exactWorldBoundingBox(hub[0])
                    cx = (bb[0] + bb[3]) * 0.5
                    cy = (bb[1] + bb[4]) * 0.5
                    cz = (bb[2] + bb[5]) * 0.5
                    _ring_at((cx, cy, cz), 0.15, (-4, 0, 0))
            except Exception:
                pass

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
            if mc.objExists(ring):
                mc.delete(ring, ch=True)
            return ring
        except Exception:
            return None

    def _spawn(self, module_name: str,
               position=(0, 0, 0),
               scale=1.0,
               rotation=(0, 0, 0),
               overrides: dict | None = None) -> str | None:
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

        mod_params = dict(self.params)
        if overrides:
            mod_params.update(overrides)
        instance = cls(mod_params)
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
