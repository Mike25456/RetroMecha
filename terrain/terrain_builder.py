"""
RetroMecha — terrain/terrain_builder.py  v3
Orquestador completo: escala corregida, plataformas ELEVADAS con columnas,
más densidad de elementos, MASH/scatter debris, rampas, pilares.

CORRECCIONES PRINCIPALES vs v1:
  - ground_plane_y = -0.05 (el top queda en 0.0)
  - platform_y_levels POSITIVOS [0.6, 1.4, 2.5, 4.0] — plataformas SOBRE el suelo
  - platform_scale_range [1.0, 1.8] — PlatformModule ya tiene dims grandes internamente
  - fragment_scale_range [0.8, 2.0] — fragmentos visibles
  - ring_r mínimo 8 unidades — no pega encima del mecha
  - monument más lejos y más grande
  - MASH scatter debris con fallback manual
  - rampas entre plataformas cercanas
  - pilares independientes
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

# Y del top del ground plane — debe coincidir con scene_composer.GROUND_TOP_Y
GROUND_Y = 0.0


class TerrainBuilder:

    DEFAULT_PRESET = {
        'ground_plane_y':        -0.05,   # top queda en 0.0
        'monument_scale':         5.5,
        'monument_distance_z':   -30.0,
        'monument_damage':         0.3,
        'platform_count':          8,
        'platform_y_levels':  [0.6, 1.4, 2.5, 4.0],   # POSITIVOS
        'platform_scale_range': [1.0, 1.8],
        'fragment_count':         12,
        'fragment_scale_range': [0.8, 2.0],
        'pillar_count':            8,
        'ramp_probability':        0.55,
        'debris_count':           80,
        'tower_probability':       0.65,
        'skyline_count':            3,
        'skyline_distance_z':    -42.0,
        'ring_min_r':              8.0,    # radio mínimo absoluto
        'ring_max_r':             22.0,    # radio máximo absoluto
    }

    def __init__(self, params: dict, seed: int,
                 preset_name: str = 'avanzada',
                 mecha_bbox: tuple = None):
        self.params   = params
        self.seed     = seed
        self._rng     = random.Random(seed)
        self.preset   = self._load_preset(preset_name)
        # bbox del mecha ya elevado: (xmin,ymin,zmin, xmax,ymax,zmax)
        self.mecha_bbox = mecha_bbox or (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)
        self._root    = None
        self._plat_positions = []   # (x, y, z) surface — para rampas

    # ── Punto de entrada ──────────────────────────────────────────────────────

    def build(self) -> str:
        print(f'[RetroMecha][Terrain] Build | Seed:{self.seed}')
        if not MAYA_AVAILABLE:
            return 'rm_terrain_DEBUG'

        self._root = mc.group(empty=True, name='rm_terrain_#')
        try:
            self._ground()
            self._background()
            self._platforms()
            self._ramps()
            self._pillars()
            self._fragments()
            self._debris()
            n = len(mc.listRelatives(self._root,
                    allDescendents=True, type='transform') or [])
            print(f'[RetroMecha][Terrain] Completo: {self._root} ({n} objs)')
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERROR: {e}')
            import traceback; traceback.print_exc()
        return self._root

    # ── Ground ────────────────────────────────────────────────────────────────

    def _ground(self):
        gp_y = self.preset.get('ground_plane_y', -0.05)
        # scale=1 porque el módulo ya tiene tamaño fijo (60u)
        self._spawn('GROUND_PLANE', position=(0, gp_y, 0), scale=1.0)

    # ── Background ────────────────────────────────────────────────────────────

    def _background(self):
        p    = self.preset
        gp_y = p.get('ground_plane_y', -0.05)
        ms   = p.get('monument_scale', 5.5)
        mz   = p.get('monument_distance_z', -30.0)
        mx   = self._rng.uniform(-3.0, 3.0)

        self._spawn('MONUMENT', position=(mx, gp_y, mz), scale=ms)

        # Torres flanqueando el monumento
        for side in [-1, 1]:
            if self._rng.random() < 0.7:
                self._spawn('TOWER',
                            position=(mx + side * ms * 1.3, gp_y, mz + 1.5),
                            scale=ms * 0.55)

        # Skylines más lejos aún
        sky_n = p.get('skyline_count', 3)
        sky_z = p.get('skyline_distance_z', -42.0)
        for i in range(sky_n):
            sx = (i - (sky_n-1)*0.5) * 14.0 + self._rng.uniform(-2, 2)
            self._spawn('SKYLINE',
                        position=(sx, gp_y, sky_z),
                        scale=1.5 + self._rng.uniform(0, 0.8))

    # ── Plataformas ───────────────────────────────────────────────────────────

    def _platforms(self):
        p      = self.preset
        aggr   = self.params.get('aggressiveness', 0.5)
        gp_y   = p.get('ground_plane_y', -0.05)
        r_min  = p.get('ring_min_r', 8.0)
        r_max  = p.get('ring_max_r', 22.0)

        y_levels    = p.get('platform_y_levels',  [0.6, 1.4, 2.5, 4.0])
        scale_range = p.get('platform_scale_range',[1.0, 1.8])
        n_plat      = p.get('platform_count', 8)
        n_plat      = max(4, int(n_plat * (1.4 - aggr * 0.4)))

        angles = self._spread_angles(n_plat)

        for i, angle in enumerate(angles):
            r   = self._rng.uniform(r_min, r_max)
            px  = math.cos(angle) * r
            pz  = math.sin(angle) * r
            py  = GROUND_Y + self._rng.choice(y_levels)
            ps  = self._rng.uniform(*scale_range)

            self._spawn('PLATFORM', position=(px, py, pz), scale=ps)
            self._plat_positions.append((px, py, pz))

            # Torre sobre la plataforma
            if self._rng.random() < p.get('tower_probability', 0.65):
                self._spawn('TOWER',
                            position=(px, py, pz),
                            scale=ps * self._rng.uniform(0.6, 1.0))

            # Sub-plataforma adyacente a distinto nivel
            if self._rng.random() < 0.55:
                ox = px + self._rng.uniform(-2.5, 2.5)
                oz = pz + self._rng.uniform(-2.5, 2.5)
                oy = GROUND_Y + self._rng.choice(y_levels) * 0.7
                ss = ps * self._rng.uniform(0.45, 0.70)
                self._spawn('PLATFORM', position=(ox, oy, oz), scale=ss)
                self._plat_positions.append((ox, oy, oz))

        # Landing pad central debajo del mecha
        self._spawn('PLATFORM', position=(0.0, GROUND_Y, 0.0), scale=1.6)
        self._plat_positions.append((0.0, GROUND_Y, 0.0))

    # ── Rampas ────────────────────────────────────────────────────────────────

    def _ramps(self):
        prob = self.preset.get('ramp_probability', 0.55)
        MAX_DIST = 14.0
        ramp_grp = mc.group(empty=True, name='rm_ramps_#')
        created  = 0

        for i, p1 in enumerate(self._plat_positions):
            if self._rng.random() > prob:
                continue
            # Vecino más cercano
            best_dist, best_p = float('inf'), None
            for j, p2 in enumerate(self._plat_positions):
                if i == j:
                    continue
                d = math.dist(p1, p2)
                if d < best_dist and d < MAX_DIST:
                    best_dist, best_p = d, p2

            if best_p is None:
                continue

            mx = (p1[0] + best_p[0]) * 0.5
            my = (p1[1] + best_p[1]) * 0.5
            mz = (p1[2] + best_p[2]) * 0.5
            ramp_len = best_dist

            ramp = mc.polyCube(w=0.45, h=0.10, d=ramp_len,
                               name='rm_ramp_#')[0]
            mc.move(mx, my + 0.06, mz, ramp)

            ay = math.degrees(math.atan2(best_p[0]-p1[0], best_p[2]-p1[2]))
            dy = best_p[1] - p1[1]
            ax = -math.degrees(math.atan2(dy, ramp_len))
            mc.rotate(ax, ay, 0, ramp)

            mc.parent(ramp, ramp_grp)
            created += 1

        if created:
            mc.parent(ramp_grp, self._root)
            print(f'[RetroMecha][Terrain] {created} rampas')
        else:
            mc.delete(ramp_grp)

    # ── Pilares ───────────────────────────────────────────────────────────────

    def _pillars(self):
        n     = self.preset.get('pillar_count', 8)
        gp_y  = self.preset.get('ground_plane_y', -0.05)
        r_min = self.preset.get('ring_min_r', 8.0)
        r_max = self.preset.get('ring_max_r', 22.0)
        grp   = mc.group(empty=True, name='rm_pillars_#')

        for _ in range(n):
            r   = self._rng.uniform(r_min * 0.5, r_max * 0.9)
            ang = self._rng.uniform(0, math.tau)
            px  = math.cos(ang) * r
            pz  = math.sin(ang) * r
            ph  = self._rng.uniform(3.0, 9.0)
            pr  = self._rng.uniform(0.15, 0.35)
            psa = self._rng.choice([4, 6, 8])

            shaft = mc.polyCylinder(r=pr, h=ph, sa=psa,
                                    name='rm_pillar_#')[0]
            mc.move(px, GROUND_Y + ph*0.5, pz, shaft)

            ring = mc.polyTorus(r=pr*2.5, sr=pr*0.35, sa=8, sh=4,
                                name='rm_pillar_ring_#')[0]
            mc.move(px, GROUND_Y + ph*0.65, pz, ring)

            cap = mc.polyCylinder(r=pr*1.8, h=0.12, sa=psa,
                                  name='rm_pillar_cap_#')[0]
            mc.move(px, GROUND_Y + ph, pz, cap)

            mc.parent(shaft, ring, cap, grp)

        mc.parent(grp, self._root)

    # ── Fragmentos ────────────────────────────────────────────────────────────

    def _fragments(self):
        p     = self.preset
        aggr  = self.params.get('aggressiveness', 0.5)
        gp_y  = p.get('ground_plane_y', -0.05)
        r_min = p.get('ring_min_r', 8.0)
        r_max = p.get('ring_max_r', 22.0)
        sr    = p.get('fragment_scale_range', [0.8, 2.0])
        n_fr  = p.get('fragment_count', 12)
        n_fr  = max(4, int(n_fr * (0.5 + aggr)))

        angles = self._spread_angles(n_fr)
        for angle in angles:
            r  = self._rng.uniform(r_min * 0.4, r_max * 1.1)
            fx = math.cos(angle) * r
            fz = math.sin(angle) * r
            fs = self._rng.uniform(*sr)
            self._spawn('FRAGMENT', position=(fx, GROUND_Y, fz), scale=fs)

            # 1-3 fragmentos satélite más pequeños
            for _ in range(self._rng.randint(1, 3)):
                sx = fx + self._rng.uniform(-3.0, 3.0)
                sz = fz + self._rng.uniform(-3.0, 3.0)
                self._spawn('FRAGMENT',
                            position=(sx, GROUND_Y, sz),
                            scale=fs * self._rng.uniform(0.2, 0.5))

    # ── Debris ────────────────────────────────────────────────────────────────

    def _debris(self):
        n    = self.preset.get('debris_count', 80)
        gp_y = self.preset.get('ground_plane_y', -0.05)
        r_max = self.preset.get('ring_max_r', 22.0)
        spread = r_max * 1.3

        mash_ok = False
        try:
            mc.loadPlugin('MASH', quiet=True)
            mash_ok = True
        except Exception:
            pass

        if mash_ok:
            self._debris_mash(n, spread, gp_y)
        else:
            self._debris_manual(n, spread, gp_y)

    def _debris_mash(self, count, spread, gp_y):
        try:
            import MASH.api as mapi

            base = mc.polyCube(w=0.18, h=0.12, d=0.14,
                               name='rm_debris_base_#')[0]
            mc.move(0, gp_y + 0.06, 0, base)

            net = mapi.Network()
            net.createNetwork(base, count=count)

            rnd = net.addNode('MASH_Random')
            mc.setAttr(rnd + '.positionX', spread)
            mc.setAttr(rnd + '.positionY', 0.4)
            mc.setAttr(rnd + '.positionZ', spread)
            mc.setAttr(rnd + '.rotationX', 180)
            mc.setAttr(rnd + '.rotationY', 180)
            mc.setAttr(rnd + '.rotationZ', 180)
            mc.setAttr(rnd + '.scaleX',    0.8)
            mc.setAttr(rnd + '.scaleY',    0.8)
            mc.setAttr(rnd + '.scaleZ',    0.8)
            mc.setAttr(rnd + '.randomSeed', self.seed)

            # Parent la red al grupo raíz
            waiter = mc.ls(type='MASH_Waiter') or []
            if waiter:
                mc.parent(waiter[-1], self._root)

            print(f'[RetroMecha][Terrain] MASH debris: {count} instancias')
        except Exception as e:
            print(f'[RetroMecha][Terrain] MASH falló ({e}), scatter manual')
            self._debris_manual(count, spread, gp_y)

    def _debris_manual(self, count, spread, gp_y):
        grp = mc.group(empty=True, name='rm_debris_scatter_#')
        for i in range(count):
            s  = self._rng.uniform(0.06, 0.25)
            sw = s * self._rng.uniform(0.5, 2.2)
            sh = s * self._rng.uniform(0.3, 1.6)
            sd = s * self._rng.uniform(0.4, 1.9)
            p  = mc.polyCube(w=sw, h=sh, d=sd,
                             name=f'rm_deb_{i}_#')[0]
            px = self._rng.uniform(-spread, spread)
            pz = self._rng.uniform(-spread, spread)
            mc.move(px, gp_y + sh*0.5, pz, p)
            mc.rotate(self._rng.uniform(0,360),
                      self._rng.uniform(0,360),
                      self._rng.uniform(0,360), p)
            mc.parent(p, grp)
        mc.parent(grp, self._root)
        print(f'[RetroMecha][Terrain] Debris manual: {count} piezas')

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _spawn(self, name, position=(0,0,0), scale=1.0, rotation=(0,0,0)):
        cls = get_module(name)
        if cls is None:
            return None

        nodes_before = set(mc.ls(dag=True) or [])
        instance = cls(self.params)
        try:
            node = instance.generate(position=position, scale=scale,
                                     rotation=rotation)
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERR "{name}": {e}')
            import traceback; traceback.print_exc()
            orphans = list(set(mc.ls(dag=True) or []) - nodes_before)
            if orphans:
                try: mc.delete(orphans)
                except: pass
            return None

        if node and mc.objExists(node):
            mc.parent(node, self._root)
        return node

    def _spread_angles(self, n: int) -> list:
        """Distribuye n ángulos en 360° con jitter."""
        if n <= 0:
            return []
        step = math.tau / n
        return [step*i + self._rng.uniform(-step*0.3, step*0.3)
                for i in range(n)]

    def _load_preset(self, name: str) -> dict:
        path = os.path.join(os.path.dirname(__file__),
                            '..', 'config', 'terrain_presets.json')
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                if name in data:
                    # Mezclar defaults con el preset (preset tiene precedencia)
                    merged = dict(self.DEFAULT_PRESET)
                    merged.update(data[name])
                    print(f'[RetroMecha][Terrain] Preset: {name}')
                    return merged
            except Exception as e:
                print(f'[RetroMecha][Terrain] Error JSON presets: {e}')
        return dict(self.DEFAULT_PRESET)
