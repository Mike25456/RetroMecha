"""
RetroMecha — terrain/terrain_builder.py
Orquestador de terreno: genera y distribuye los elementos de la escena
alrededor del mecha usando el L-System de terreno y los presets de composición.

Paralelo a core/mecha_builder.py — misma interfaz, distinta responsabilidad.
"""

import random
import json
import os
import math

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from core.module_registry import get as get_module


class TerrainBuilder:
    """
    Ensambla el terreno completo a partir de parámetros del mecha y un preset.

    Flujo:
        1. Crea ground plane
        2. Posiciona monumento y skylines en el fondo
        3. Distribuye plataformas, fragmentos, debris y torres en anillo
        4. Parent todo bajo un grupo raíz de terreno
    """

    # Presets por defecto si no se carga el JSON
    DEFAULT_PRESET = {
        'terrain_iterations': 2,
        'ground_plane_scale': 5.0,
        'ground_plane_y': -0.15,
        'monument_scale': 3.5,
        'monument_distance_z': -14.0,
        'monument_damage': 0.3,
        'platform_count_bias': 2,
        'platform_y_levels': [0.0, -0.3, -0.6],
        'platform_scale_range': [0.6, 1.0],
        'fragment_count_bias': 3,
        'fragment_rotation_range': [15, 35],
        'fragment_scale_range': [0.4, 0.8],
        'debris_density': 0.5,
        'debris_cluster_size': [3, 6],
        'tower_probability': 0.5,
        'skyline_count': 2,
        'skyline_distance_z': -16.0,
        'ring_radius_multiplier': 1.5,
        'ring_distribution': 'full_ring',
    }

    def __init__(self, params: dict, seed: int, preset_name: str = 'avanzada',
                 mecha_bbox: tuple = None):
        """
        Args:
            params:      diccionario de parámetros de la UI del mecha
            seed:        seed del terreno (derivado del seed del mecha)
            preset_name: nombre del preset de composición
            mecha_bbox:  (xmin, ymin, zmin, xmax, ymax, zmax) del mecha generado
        """
        self.params = params
        self.seed = seed
        self._rng = random.Random(seed)
        self.preset = self._load_preset(preset_name)
        self.mecha_bbox = mecha_bbox or (-1.5, -1.5, -1, 1.5, 3.5, 1)
        self._root_group = None

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def build(self) -> str:
        """
        Construye el terreno completo.

        Returns:
            Nombre del grupo raíz del terreno en Maya
        """
        print(f'[RetroMecha][Terrain] Build iniciado | Seed: {self.seed}')

        if not MAYA_AVAILABLE:
            print('[RetroMecha][Terrain] Maya no disponible')
            return 'RetroMecha_Terrain_DEBUG'

        self._root_group = mc.group(empty=True, name='rm_terrain_#')

        try:
            self._build_ground_plane()
            self._build_background()
            self._build_ring_elements()
            mc.select(self._root_group)
            obj_count = len(mc.listRelatives(
                self._root_group, allDescendents=True, type='transform') or [])
            print(f'[RetroMecha][Terrain] Build completo: {self._root_group} '
                  f'({obj_count} objetos)')
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERROR: {e}')
            import traceback
            traceback.print_exc()

        return self._root_group

    # ── Ground Plane ──────────────────────────────────────────────────────────

    def _build_ground_plane(self):
        """Crea el plano de suelo."""
        gp_y = self.preset.get('ground_plane_y', -0.15)
        gp_scale = self.preset.get('ground_plane_scale', 5.0)

        node = self._spawn('GROUND_PLANE',
                           position=(0, gp_y, 0),
                           scale=gp_scale)
        return node

    # ── Background (monumento + skylines) ─────────────────────────────────────

    def _build_background(self):
        """Posiciona el monumento y los skylines en el fondo."""
        p = self.preset

        # ── Monumento ─────────────────────────────────────────────────────────
        m_scale = p.get('monument_scale', 3.5)
        m_z = p.get('monument_distance_z', -14.0)
        # Offset X sutil para composición asimétrica
        m_x = self._rng.uniform(-1.5, 1.5)

        node = self._spawn('MONUMENT',
                           position=(m_x, p.get('ground_plane_y', -0.15), m_z),
                           scale=m_scale)

        # Torres ornamentales del monumento (si el preset lo permite)
        if self._rng.random() < p.get('tower_probability', 0.5):
            for side in [-1, 1]:
                self._spawn('TOWER',
                            position=(m_x + side * m_scale * 0.8,
                                      p.get('ground_plane_y', -0.15),
                                      m_z + 0.5),
                            scale=m_scale * 0.3)

        # ── Skylines ─────────────────────────────────────────────────────────
        sky_count = p.get('skyline_count', 2)
        sky_z = p.get('skyline_distance_z', -18.0)

        for i in range(sky_count):
            sx = (i - (sky_count - 1) * 0.5) * 8.0
            sx += self._rng.uniform(-1.0, 1.0)
            self._spawn('SKYLINE',
                        position=(sx, p.get('ground_plane_y', -0.15), sky_z),
                        scale=0.7 + self._rng.uniform(0, 0.3))

    # ── Ring Elements (plataformas, fragmentos, debris, torres) ───────────────

    def _build_ring_elements(self):
        """Distribuye elementos en un anillo alrededor del mecha."""
        p = self.preset
        aggr = self.params.get('aggressiveness', 0.5)
        symmetry = self.params.get('symmetry', True)

        # Radio del anillo basado en el bounding box del mecha
        bb = self.mecha_bbox
        mecha_radius = max(abs(bb[3] - bb[0]), abs(bb[5] - bb[2])) * 0.5
        ring_r = (mecha_radius + 1.5) * p.get('ring_radius_multiplier', 1.5)

        # Distribución angular
        distribution = p.get('ring_distribution', 'full_ring')
        if distribution == 'semicircle_back':
            angle_start = math.radians(150)
            angle_end = math.radians(390)
        else:
            angle_start = 0
            angle_end = math.radians(360)

        # ── Plataformas ───────────────────────────────────────────────────────
        plat_count = p.get('platform_count_bias', 2)
        # Más plataformas con baja agresividad
        plat_count = max(1, int(plat_count * (1.5 - aggr)))
        y_levels = p.get('platform_y_levels', [0.0, -0.3, -0.6])
        plat_scale_range = p.get('platform_scale_range', [0.6, 1.0])

        plat_angles = self._distribute_angles(plat_count,
                                              angle_start, angle_end,
                                              zone='back')
        for angle in plat_angles:
            r_var = ring_r * self._rng.uniform(0.7, 1.1)
            px = math.cos(angle) * r_var
            pz = math.sin(angle) * r_var
            py = self._rng.choice(y_levels)
            ps = self._rng.uniform(*plat_scale_range)

            self._spawn('PLATFORM', position=(px, py, pz), scale=ps)

            # Torre sobre la plataforma (probabilidad del preset)
            if self._rng.random() < p.get('tower_probability', 0.5):
                self._spawn('TOWER',
                            position=(px, py, pz),
                            scale=ps * 0.6)

        # ── Fragmentos ────────────────────────────────────────────────────────
        frag_count = p.get('fragment_count_bias', 3)
        # Más fragmentos con alta agresividad
        frag_count = max(1, int(frag_count * (0.5 + aggr)))
        frag_scale_range = p.get('fragment_scale_range', [0.4, 0.8])

        frag_angles = self._distribute_angles(frag_count,
                                              angle_start, angle_end,
                                              zone='scattered')
        for angle in frag_angles:
            r_var = ring_r * self._rng.uniform(0.5, 1.4)
            fx = math.cos(angle) * r_var
            fz = math.sin(angle) * r_var
            fs = self._rng.uniform(*frag_scale_range)
            gp_y = p.get('ground_plane_y', -0.15)

            self._spawn('FRAGMENT', position=(fx, gp_y, fz), scale=fs)

            # Cluster de debris alrededor de cada fragmento
            if self._rng.random() < p.get('debris_density', 0.5):
                # Offset cercano al fragmento
                dx = fx + self._rng.uniform(-0.4, 0.4)
                dz = fz + self._rng.uniform(-0.4, 0.4)
                self._spawn('DEBRIS',
                            position=(dx, gp_y, dz),
                            scale=fs * 0.6)

        # ── Debris suelto en foreground ───────────────────────────────────────
        # Algunos clusters de debris en primer plano (Z positivo)
        fg_debris = max(1, int(3 * p.get('debris_density', 0.5)))
        for _ in range(fg_debris):
            dx = self._rng.uniform(-ring_r * 0.8, ring_r * 0.8)
            dz = self._rng.uniform(ring_r * 0.3, ring_r * 0.8)
            gp_y = p.get('ground_plane_y', -0.15)
            self._spawn('DEBRIS',
                        position=(dx, gp_y, dz),
                        scale=self._rng.uniform(0.3, 0.6))

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _spawn(self, module_name: str,
               position=(0, 0, 0),
               scale=1.0,
               rotation=(0, 0, 0)) -> str:
        """Instancia un módulo de terreno y lo parenta al grupo raíz."""
        cls = get_module(module_name)
        if cls is None:
            return None

        nodes_before = set(mc.ls(dag=True) or [])

        instance = cls(self.params)
        try:
            node = instance.generate(position=position,
                                     scale=scale,
                                     rotation=rotation)
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERROR en "{module_name}": {e}')
            import traceback
            traceback.print_exc()
            nodes_after = set(mc.ls(dag=True) or [])
            orphans = list(nodes_after - nodes_before)
            if orphans:
                try:
                    mc.delete(orphans)
                except Exception:
                    pass
            return None

        if node and mc.objExists(node):
            mc.parent(node, self._root_group)
        return node

    def _distribute_angles(self, count: int,
                           start: float, end: float,
                           zone: str = 'scattered') -> list:
        """
        Distribuye ángulos dentro de un rango con variación.

        Args:
            count: cantidad de elementos
            start: ángulo inicial en radianes
            end:   ángulo final en radianes
            zone:  'back' (agrupa atrás), 'scattered' (disperso)
        """
        if count <= 0:
            return []

        span = end - start
        step = span / max(count, 1)
        angles = []

        for i in range(count):
            base = start + step * (i + 0.5)
            jitter = step * 0.35 * self._rng.uniform(-1, 1)
            angles.append(base + jitter)

        return angles

    def _load_preset(self, name: str) -> dict:
        """Carga un preset de terreno desde JSON."""
        presets_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'terrain_presets.json'
        )
        if os.path.exists(presets_path):
            try:
                with open(presets_path, 'r') as f:
                    data = json.load(f)
                if name in data:
                    print(f'[RetroMecha][Terrain] Preset cargado: {name}')
                    return data[name]
                else:
                    print(f'[RetroMecha][Terrain] Preset "{name}" no encontrado, '
                          f'usando defaults')
            except Exception as e:
                print(f'[RetroMecha][Terrain] Error cargando presets: {e}')
        return self.DEFAULT_PRESET.copy()
