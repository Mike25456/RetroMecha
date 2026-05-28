"""
RetroMecha — terrain/terrain_builder.py  v5

COMPOSICIÓN EN PERSPECTIVA CENTRAL (boceto del usuario):
  - Cámara en Z+ mirando hacia Z-
  - Monumento SIEMPRE centrado en X=0, lejos en Z-
  - FRENTE (Z+): ZONA PROHIBIDA — nada se genera ahí
  - LATERALES (X+ y X-): alta densidad — elementos guían la vista al mecha
  - FONDO (Z-): densidad media — espacio para el monumento

  Ángulos (0=X+, π/2=Z+FRENTE, π=X-, 3π/2=Z-FONDO):
  ┌─────────────────────────────────────────────────────────┐
  │  Lateral dcho  │  FRENTE      │  Lateral izq           │
  │  ████████████  │  ░░ VACÍO ░░ │  ████████████          │
  │  -60° → +40°   │  40° → 140°  │  140° → 240°           │
  │  peso: 40%     │  PROHIBIDO   │  peso: 40%             │
  └─────────────────────────────────────────────────────────┘
  Fondo (240°→300°, Z-): peso 20% — skylines y fragmentos lejanos
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
from utils.hard_surface import apply_support_edges
from utils.maya_scene import force_preview_one

GROUND_Y = 0.0


class TerrainBuilder:

    DEFAULT_PRESET = {
        'ground_plane_y':       -0.05,
        'safe_radius':           6.0,
        'front_exclusion_deg':  50.0,   # grados excluidos alrededor de Z+

        # Monumento SIEMPRE centrado X=0
        'monument_scale':        5.5,
        'monument_distance_z': -45.0,

        # Skylines a los lados del monumento (pero en Z-)
        'skyline_count':          3,
        'skyline_distance_z':  -55.0,
        'skyline_spread_x':     40.0,

        # Plataformas
        'platform_count':        8,
        'platform_y_levels':  [0.6, 1.4, 2.5, 4.0],
        'platform_scale_range': [1.0, 1.8],

        # Fragmentos
        'fragment_count':       12,
        'fragment_scale_range': [0.8, 2.0],

        # Pilares, rampas, debris
        'pillar_count':          8,
        'ramp_probability':      0.55,
        'debris_count':         80,
        'tower_probability':     0.65,

        # Radios del anillo
        'ring_min_r':           10.0,
        'ring_max_r':           35.0,
    }

    # Zonas de distribución angular (en radianes, 0=X+, π/2=Z+FRENTE PROHIBIDO)
    # Definidas como (angle_start, angle_end, weight)
    ZONES = [
        (math.radians(-60), math.radians(40),  0.44),  # lateral derecho
        (math.radians(140), math.radians(240), 0.44),  # lateral izquierdo
        (math.radians(240), math.radians(300), 0.12),  # fondo (Z-)
    ]

    def __init__(self, params, seed, preset_name='avanzada', mecha_bbox=None):
        self.params    = params
        self.seed      = seed
        self._rng      = random.Random(seed)
        self.preset    = self._load_preset(preset_name)
        self.mecha_bbox = mecha_bbox or (-2, 0.5, -1.5, 2, 5, 1.5)
        self._root     = None
        self._plat_pos = []

    # ─────────────────────────────────────────────────────────────────────────
    #  PUNTO DE ENTRADA
    # ─────────────────────────────────────────────────────────────────────────

    def build(self):
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
            if self.params.get('use_support_edges', True):
                count = apply_support_edges(self._root, offset=0.018,
                                             fraction=0.045, segments=2,
                                             max_faces=500)
                print(f'[RetroMecha][Terrain] Support edges aplicados: {count}')
            force_preview_one(self._root)
            n = len(mc.listRelatives(self._root,
                    allDescendents=True, type='transform') or [])
            print(f'[RetroMecha][Terrain] OK: {self._root} ({n} objs)')
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERROR: {e}')
            import traceback; traceback.print_exc()
        return self._root

    # ─────────────────────────────────────────────────────────────────────────
    #  DISTRIBUCIÓN ANGULAR — perspectiva central
    # ─────────────────────────────────────────────────────────────────────────

    def _composition_pos(self, n, r_min=None, r_max=None):
        """
        Genera n posiciones (x, z) respetando la composición en perspectiva
        central: laterales con alta densidad, frente prohibido.
        """
        safe  = self.preset.get('safe_radius', 6.0)
        r_lo  = max(safe, r_min or self.preset.get('ring_min_r', 10.0))
        r_hi  = r_max or self.preset.get('ring_max_r', 35.0)
        zones = self.ZONES

        # Excluir frente dinámicamente si el preset lo ajusta
        excl_deg = self.preset.get('front_exclusion_deg', 50.0)
        excl     = math.radians(excl_deg)
        front    = math.pi / 2   # Z+ (frente cámara)
        dyn_zones = [
            (front - excl - math.radians(70), front - excl, 0.40),  # lateral dcho
            (front + excl,                    front + excl + math.radians(100), 0.40),  # lateral izq
            (front + excl + math.radians(100),front + excl + math.radians(160), 0.20),  # fondo
        ]

        result = []
        for _ in range(n):
            # Elegir zona con su peso
            rv = self._rng.random()
            cumul = 0.0
            chosen = dyn_zones[-1]
            for z in dyn_zones:
                cumul += z[2]
                if rv <= cumul:
                    chosen = z
                    break

            angle  = self._rng.uniform(chosen[0], chosen[1])
            radius = self._rng.uniform(r_lo, r_hi)
            px = math.cos(angle) * radius
            pz = math.sin(angle) * radius
            result.append((px, pz))

        return result

    def _random_lateral_pos(self, r_lo, r_hi):
        """Posición aleatoria en zona lateral (no frente) para debris."""
        excl_deg = self.preset.get('front_exclusion_deg', 50.0)
        excl     = math.radians(excl_deg)
        front    = math.pi / 2

        # Elegir entre lateral derecho, izquierdo o fondo
        choice = self._rng.random()
        if choice < 0.40:
            angle = self._rng.uniform(front - excl - math.radians(70), front - excl)
        elif choice < 0.80:
            angle = self._rng.uniform(front + excl, front + excl + math.radians(100))
        else:
            angle = self._rng.uniform(math.radians(240), math.radians(310))

        r  = self._rng.uniform(r_lo, r_hi)
        return math.cos(angle) * r, math.sin(angle) * r

    # ─────────────────────────────────────────────────────────────────────────
    #  GROUND
    # ─────────────────────────────────────────────────────────────────────────

    def _ground(self):
        gp_y = self.preset.get('ground_plane_y', -0.05)
        self._spawn('GROUND_PLANE', position=(0, gp_y, 0), scale=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    #  BACKGROUND — monumento CENTRADO + skylines laterales
    # ─────────────────────────────────────────────────────────────────────────

    def _background(self):
        p    = self.preset
        gp_y = p.get('ground_plane_y', -0.05)

        # ── Monumento: SIEMPRE X=0, centrado en el eje de perspectiva ─────────
        ms = p.get('monument_scale', 5.5)
        mz = p.get('monument_distance_z', -45.0)

        self._spawn('MONUMENT', position=(0, gp_y, mz), scale=ms)

        # Torres ornamentales a los lados del monumento (simétricas)
        for side in [-1, 1]:
            if self._rng.random() < 0.7:
                self._spawn('TOWER',
                            position=(side * ms * 1.5, gp_y, mz + 2.0),
                            scale=ms * 0.5)

        # ── Skylines: distribuidos lateralmente DETRÁS del monumento ──────────
        sky_n    = p.get('skyline_count', 3)
        sky_z    = p.get('skyline_distance_z', -55.0)
        spread_x = p.get('skyline_spread_x', 40.0)

        for i in range(sky_n):
            if sky_n == 1:
                sx = 0.0
            else:
                sx = -spread_x*0.5 + (spread_x / (sky_n-1)) * i
            sx += self._rng.uniform(-2.0, 2.0)
            sz  = sky_z + self._rng.uniform(-4.0, 4.0)
            ss  = self._rng.uniform(1.6, 2.8)
            self._spawn('SKYLINE', position=(sx, gp_y, sz), scale=ss)

    # ─────────────────────────────────────────────────────────────────────────
    #  PLATAFORMAS — distribuidas en laterales
    # ─────────────────────────────────────────────────────────────────────────

    def _platforms(self):
        p      = self.preset
        aggr   = self.params.get('aggressiveness', 0.5)
        y_lvls = p.get('platform_y_levels', [0.6, 1.4, 2.5, 4.0])
        sc_rng = p.get('platform_scale_range', [1.0, 1.8])
        n      = max(4, int(p.get('platform_count', 8) * (1.4 - 0.5 * 1.2)))

        positions = self._composition_pos(n)

        for (px, pz) in positions:
            py = GROUND_Y + self._rng.choice(y_lvls)
            ps = self._rng.uniform(*sc_rng)

            self._spawn('PLATFORM', position=(px, py, pz), scale=ps)
            self._plat_pos.append((px, py, pz))

            # Torre encima
            if self._rng.random() < p.get('tower_probability', 0.65):
                self._spawn('TOWER',
                            position=(px, py, pz),
                            scale=ps * self._rng.uniform(0.5, 0.9))

            # Sub-plataformas adyacentes (2 intentos para más densidad)
            for _sp in range(2):
             if self._rng.random() < 0.80:
                ox = px + self._rng.uniform(-3.0, 3.0)
                oz = pz + self._rng.uniform(-3.0, 3.0)
                safe = p.get('safe_radius', 6.0)
                dist = math.sqrt(ox*ox + oz*oz)
                if dist > safe:
                    oy = GROUND_Y + self._rng.choice(y_lvls) * 0.65
                    ss = ps * self._rng.uniform(0.4, 0.7)
                    self._spawn('PLATFORM', position=(ox, oy, oz), scale=ss)
                    self._plat_pos.append((ox, oy, oz))

        # Landing pad central bajo el mecha (siempre)
        self._spawn('PLATFORM', position=(0, GROUND_Y, 0), scale=1.4)
        self._plat_pos.append((0, GROUND_Y, 0))

    # ─────────────────────────────────────────────────────────────────────────
    #  RAMPAS
    # ─────────────────────────────────────────────────────────────────────────

    def _ramps(self):
        prob = self.preset.get('ramp_probability', 0.55)
        MAX_D = 18.0
        grp = mc.group(empty=True, name='rm_ramps_#')
        created = 0

        for i, p1 in enumerate(self._plat_pos):
            if self._rng.random() > prob:
                continue
            best_d, best = float('inf'), None
            for j, p2 in enumerate(self._plat_pos):
                if i == j: continue
                d = math.dist(p1, p2)
                if d < best_d and d < MAX_D:
                    best_d, best = d, p2
            if best is None:
                continue
            mx = (p1[0]+best[0])*0.5
            my = (p1[1]+best[1])*0.5
            mz = (p1[2]+best[2])*0.5
            ramp = mc.polyCube(w=0.5, h=0.10, d=best_d, name='rm_ramp_#')[0]
            mc.move(mx, my+0.06, mz, ramp)
            ay = math.degrees(math.atan2(best[0]-p1[0], best[2]-p1[2]))
            ax = -math.degrees(math.atan2(best[1]-p1[1], best_d))
            mc.rotate(ax, ay, 0, ramp)
            mc.parent(ramp, grp)
            created += 1

        if created:
            mc.parent(grp, self._root)
            print(f'[RetroMecha][Terrain] {created} rampas')
        else:
            mc.delete(grp)

    # ─────────────────────────────────────────────────────────────────────────
    #  PILARES — laterales
    # ─────────────────────────────────────────────────────────────────────────

    def _pillars(self):
        n   = self.preset.get('pillar_count', 8)
        grp = mc.group(empty=True, name='rm_pillars_#')

        positions = self._composition_pos(n)
        for (px, pz) in positions:
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

    # ─────────────────────────────────────────────────────────────────────────
    #  FRAGMENTOS — laterales + fondo, respetando safe_radius
    # ─────────────────────────────────────────────────────────────────────────

    def _fragments(self):
        p    = self.preset
        aggr = self.params.get('aggressiveness', 0.5)
        sr   = p.get('fragment_scale_range', [0.8, 2.0])
        n    = max(4, int(p.get('fragment_count', 12) * (0.5 + aggr)))

        positions = self._composition_pos(n)
        safe = p.get('safe_radius', 6.0)

        for (fx, fz) in positions:
            fs = self._rng.uniform(*sr)
            self._spawn('FRAGMENT', position=(fx, GROUND_Y, fz), scale=fs)

            # Satélites
            for _ in range(self._rng.randint(2, 4)):
                sx = fx + self._rng.uniform(-4.0, 4.0)
                sz = fz + self._rng.uniform(-4.0, 4.0)
                if math.sqrt(sx*sx + sz*sz) > safe:
                    self._spawn('FRAGMENT',
                                position=(sx, GROUND_Y, sz),
                                scale=fs * self._rng.uniform(0.2, 0.5))

    # ─────────────────────────────────────────────────────────────────────────
    #  DEBRIS — solo en laterales y fondo, respeta frente vacío
    # ─────────────────────────────────────────────────────────────────────────

    def _debris(self):
        n     = self.preset.get('debris_count', 80)
        gp_y  = self.preset.get('ground_plane_y', -0.05)
        safe  = self.preset.get('safe_radius', 6.0)
        r_lo  = self.preset.get('ring_min_r', 10.0)
        r_hi  = self.preset.get('ring_max_r', 35.0)

        mash_ok = False
        try:
            mc.loadPlugin('MASH', quiet=True)
            mash_ok = True
        except Exception:
            pass

        # MASH no respeta la zona frontal — siempre usar scatter manual
        self._debris_manual(n, gp_y, safe, r_lo, r_hi)

    def _debris_manual(self, count, gp_y, safe, r_lo, r_hi):
        grp = mc.group(empty=True, name='rm_debris_scatter_#')
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 4:
            attempts += 1
            px, pz = self._random_lateral_pos(r_lo, r_hi)
            if math.sqrt(px*px + pz*pz) < safe:
                continue

            s  = self._rng.uniform(0.06, 0.25)
            sw = s * self._rng.uniform(0.5, 2.2)
            sh = s * self._rng.uniform(0.3, 1.6)
            sd = s * self._rng.uniform(0.4, 1.9)
            piece = mc.polyCube(w=sw, h=sh, d=sd,
                                name=f'rm_deb_{placed}_#')[0]
            mc.move(px, gp_y + sh*0.5, pz, piece)
            mc.rotate(self._rng.uniform(0,360),
                      self._rng.uniform(0,360),
                      self._rng.uniform(0,360), piece)
            mc.parent(piece, grp)
            placed += 1

        mc.parent(grp, self._root)
        print(f'[RetroMecha][Terrain] Debris: {placed}')

    # ─────────────────────────────────────────────────────────────────────────
    #  SPAWN / LOAD
    # ─────────────────────────────────────────────────────────────────────────

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

    def _load_preset(self, name):
        path = os.path.join(os.path.dirname(__file__),
                            '..', 'config', 'terrain_presets.json')
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                if name in data:
                    merged = dict(self.DEFAULT_PRESET)
                    merged.update(data[name])
                    print(f'[RetroMecha][Terrain] Preset: {name}')
                    return merged
            except Exception as e:
                print(f'[RetroMecha][Terrain] Error JSON: {e}')
        return dict(self.DEFAULT_PRESET)
