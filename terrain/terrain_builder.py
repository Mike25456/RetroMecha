"""
RetroMecha — terrain/terrain_builder.py  v4

Composición basada en el boceto del usuario:
  SIDE: monumento izq, plataformas elevadas con pilares, rampas, debris
  TOP:  monumento arriba-derecha lejos, mecha al centro con RADIO DE SEGURIDAD,
        plataformas y fragmentos distribuidos FUERA del radio, bien espaciados.

RADIO DE SEGURIDAD: nada se genera dentro de safe_radius del centro (0,0,0).
Esto evita que los elementos choquen con el mecha.
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

GROUND_Y = 0.0


class TerrainBuilder:

    DEFAULT_PRESET = {
        'ground_plane_y':       -0.05,
        'safe_radius':           6.0,     # NADA dentro de este radio
        'monument_scale':        5.5,
        'monument_distance_z': -45.0,     # muy lejos atrás
        'monument_offset_x':    12.0,     # lateral (boceto: arriba-derecha)
        'platform_count':        8,
        'platform_y_levels':  [0.6, 1.4, 2.5, 4.0],
        'platform_scale_range': [1.0, 1.8],
        'fragment_count':       12,
        'fragment_scale_range': [0.8, 2.0],
        'pillar_count':          8,
        'ramp_probability':      0.55,
        'debris_count':         80,
        'tower_probability':     0.65,
        'skyline_count':          3,
        'skyline_distance_z':  -55.0,     # detrás del monumento
        'skyline_spread_x':     40.0,     # ancho de distribución skylines
        'ring_min_r':           10.0,     # mínimo desde centro
        'ring_max_r':           35.0,     # máximo desde centro
    }

    def __init__(self, params, seed, preset_name='avanzada', mecha_bbox=None):
        self.params     = params
        self.seed       = seed
        self._rng       = random.Random(seed)
        self.preset     = self._load_preset(preset_name)
        self.mecha_bbox = mecha_bbox or (-2, 0.5, -1.5, 2, 5, 1.5)
        self._root      = None
        self._plat_pos  = []

    # ── Build ─────────────────────────────────────────────────────────────────

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
            n = len(mc.listRelatives(self._root,
                    allDescendents=True, type='transform') or [])
            print(f'[RetroMecha][Terrain] OK: {self._root} ({n} objs)')
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERROR: {e}')
            import traceback; traceback.print_exc()
        return self._root

    # ── Helpers de posición ───────────────────────────────────────────────────

    def _safe_pos(self, r_min=None, r_max=None):
        """Genera (x, z) fuera del radio de seguridad del mecha."""
        safe  = self.preset.get('safe_radius', 6.0)
        r_lo  = max(safe, r_min or self.preset.get('ring_min_r', 10.0))
        r_hi  = r_max or self.preset.get('ring_max_r', 35.0)
        r     = self._rng.uniform(r_lo, r_hi)
        angle = self._rng.uniform(0, math.tau)
        return (math.cos(angle) * r, math.sin(angle) * r)

    def _safe_angles(self, n, r_min=None, r_max=None):
        """N posiciones en anillo fuera del radio seguro."""
        safe = self.preset.get('safe_radius', 6.0)
        r_lo = max(safe, r_min or self.preset.get('ring_min_r', 10.0))
        r_hi = r_max or self.preset.get('ring_max_r', 35.0)
        step = math.tau / max(n, 1)
        result = []
        for i in range(n):
            angle = step * i + self._rng.uniform(-step*0.3, step*0.3)
            r = self._rng.uniform(r_lo, r_hi)
            result.append((math.cos(angle)*r, math.sin(angle)*r))
        return result

    # ── Ground ────────────────────────────────────────────────────────────────

    def _ground(self):
        gp_y = self.preset.get('ground_plane_y', -0.05)
        self._spawn('GROUND_PLANE', position=(0, gp_y, 0), scale=1.0)

    # ── Background: monumento + skylines ──────────────────────────────────────

    def _background(self):
        p    = self.preset
        gp_y = p.get('ground_plane_y', -0.05)

        # Monumento: lejos en Z negativo, con offset lateral (boceto: arriba-derecha)
        ms = p.get('monument_scale', 5.5)
        mz = p.get('monument_distance_z', -45.0)
        mx = p.get('monument_offset_x', 12.0) * self._rng.choice([-1, 1])

        self._spawn('MONUMENT', position=(mx, gp_y, mz), scale=ms)

        # Torres del monumento
        for side in [-1, 1]:
            if self._rng.random() < 0.7:
                self._spawn('TOWER',
                            position=(mx + side * ms * 1.5, gp_y, mz + 2.0),
                            scale=ms * 0.5)

        # Skylines: distribuidos a lo ancho DETRÁS del monumento
        sky_n    = p.get('skyline_count', 3)
        sky_z    = p.get('skyline_distance_z', -55.0)
        spread_x = p.get('skyline_spread_x', 40.0)

        for i in range(sky_n):
            # Distribuir equidistantes en X con jitter
            sx = -spread_x*0.5 + (spread_x / max(sky_n-1, 1)) * i
            sx += self._rng.uniform(-3.0, 3.0)
            sz = sky_z + self._rng.uniform(-3.0, 3.0)
            ss = self._rng.uniform(1.5, 2.5)
            self._spawn('SKYLINE', position=(sx, gp_y, sz), scale=ss)

    # ── Plataformas ───────────────────────────────────────────────────────────

    def _platforms(self):
        p      = self.preset
        aggr   = self.params.get('aggressiveness', 0.5)
        y_lvls = p.get('platform_y_levels', [0.6, 1.4, 2.5, 4.0])
        sc_rng = p.get('platform_scale_range', [1.0, 1.8])

        n = p.get('platform_count', 8)
        n = max(4, int(n * (1.4 - aggr * 0.4)))

        positions = self._safe_angles(n)

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

            # Sub-plataforma adyacente (diferente Y)
            if self._rng.random() < 0.5:
                ox = px + self._rng.uniform(-3.0, 3.0)
                oz = pz + self._rng.uniform(-3.0, 3.0)
                # Verificar que sigue fuera del safe radius
                dist = math.sqrt(ox*ox + oz*oz)
                safe = p.get('safe_radius', 6.0)
                if dist > safe:
                    oy = GROUND_Y + self._rng.choice(y_lvls) * 0.65
                    ss = ps * self._rng.uniform(0.4, 0.7)
                    self._spawn('PLATFORM', position=(ox, oy, oz), scale=ss)
                    self._plat_pos.append((ox, oy, oz))

        # Landing pad central (justo bajo el mecha, a nivel de suelo)
        self._spawn('PLATFORM', position=(0, GROUND_Y, 0), scale=1.4)
        self._plat_pos.append((0, GROUND_Y, 0))

    # ── Rampas ────────────────────────────────────────────────────────────────

    def _ramps(self):
        prob = self.preset.get('ramp_probability', 0.55)
        MAX_DIST = 18.0
        grp = mc.group(empty=True, name='rm_ramps_#')
        created = 0

        for i, p1 in enumerate(self._plat_pos):
            if self._rng.random() > prob:
                continue
            best_d, best = float('inf'), None
            for j, p2 in enumerate(self._plat_pos):
                if i == j: continue
                d = math.dist(p1, p2)
                if d < best_d and d < MAX_DIST:
                    best_d, best = d, p2
            if best is None:
                continue

            mx = (p1[0]+best[0])*0.5
            my = (p1[1]+best[1])*0.5
            mz = (p1[2]+best[2])*0.5

            ramp = mc.polyCube(w=0.5, h=0.10, d=best_d,
                               name='rm_ramp_#')[0]
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

    # ── Pilares ───────────────────────────────────────────────────────────────

    def _pillars(self):
        n   = self.preset.get('pillar_count', 8)
        grp = mc.group(empty=True, name='rm_pillars_#')

        positions = self._safe_angles(n)
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

    # ── Fragmentos ────────────────────────────────────────────────────────────

    def _fragments(self):
        p    = self.preset
        aggr = self.params.get('aggressiveness', 0.5)
        sr   = p.get('fragment_scale_range', [0.8, 2.0])
        n    = max(4, int(p.get('fragment_count', 12) * (0.5 + aggr)))

        positions = self._safe_angles(n)
        for (fx, fz) in positions:
            fs = self._rng.uniform(*sr)
            self._spawn('FRAGMENT', position=(fx, GROUND_Y, fz), scale=fs)

            # 1-2 satélites
            for _ in range(self._rng.randint(1, 2)):
                sx = fx + self._rng.uniform(-4.0, 4.0)
                sz = fz + self._rng.uniform(-4.0, 4.0)
                dist = math.sqrt(sx*sx + sz*sz)
                safe = p.get('safe_radius', 6.0)
                if dist > safe:
                    self._spawn('FRAGMENT',
                                position=(sx, GROUND_Y, sz),
                                scale=fs * self._rng.uniform(0.2, 0.5))

    # ── Debris ────────────────────────────────────────────────────────────────

    def _debris(self):
        n      = self.preset.get('debris_count', 80)
        gp_y   = self.preset.get('ground_plane_y', -0.05)
        r_max  = self.preset.get('ring_max_r', 35.0)
        safe   = self.preset.get('safe_radius', 6.0)
        spread = r_max * 1.2

        mash_ok = False
        try:
            mc.loadPlugin('MASH', quiet=True)
            mash_ok = True
        except Exception:
            pass

        if mash_ok:
            self._debris_mash(n, spread, gp_y)
        else:
            self._debris_manual(n, spread, gp_y, safe)

    def _debris_mash(self, count, spread, gp_y):
        try:
            import MASH.api as mapi
            base = mc.polyCube(w=0.18, h=0.12, d=0.14,
                               name='rm_debris_base_#')[0]
            mc.move(0, gp_y+0.06, 0, base)
            net = mapi.Network()
            net.createNetwork(base, count=count)
            rnd = net.addNode('MASH_Random')
            mc.setAttr(rnd+'.positionX', spread)
            mc.setAttr(rnd+'.positionY', 0.4)
            mc.setAttr(rnd+'.positionZ', spread)
            mc.setAttr(rnd+'.rotationX', 180)
            mc.setAttr(rnd+'.rotationY', 180)
            mc.setAttr(rnd+'.rotationZ', 180)
            mc.setAttr(rnd+'.scaleX', 0.8)
            mc.setAttr(rnd+'.scaleY', 0.8)
            mc.setAttr(rnd+'.scaleZ', 0.8)
            mc.setAttr(rnd+'.randomSeed', self.seed)
            print(f'[RetroMecha][Terrain] MASH debris: {count}')
        except Exception as e:
            print(f'[RetroMecha][Terrain] MASH falló ({e}), manual')
            safe = self.preset.get('safe_radius', 6.0)
            self._debris_manual(count, spread,
                                self.preset.get('ground_plane_y', -0.05), safe)

    def _debris_manual(self, count, spread, gp_y, safe):
        grp = mc.group(empty=True, name='rm_debris_scatter_#')
        placed = 0
        attempts = 0
        while placed < count and attempts < count * 3:
            attempts += 1
            s  = self._rng.uniform(0.06, 0.25)
            sw = s * self._rng.uniform(0.5, 2.2)
            sh = s * self._rng.uniform(0.3, 1.6)
            sd = s * self._rng.uniform(0.4, 1.9)
            px = self._rng.uniform(-spread, spread)
            pz = self._rng.uniform(-spread, spread)

            # Respetar radio de seguridad
            if math.sqrt(px*px + pz*pz) < safe:
                continue

            p = mc.polyCube(w=sw, h=sh, d=sd,
                            name=f'rm_deb_{placed}_#')[0]
            mc.move(px, gp_y + sh*0.5, pz, p)
            mc.rotate(self._rng.uniform(0,360),
                      self._rng.uniform(0,360),
                      self._rng.uniform(0,360), p)
            mc.parent(p, grp)
            placed += 1

        mc.parent(grp, self._root)
        print(f'[RetroMecha][Terrain] Debris manual: {placed}')

    # ── Spawn / Load ──────────────────────────────────────────────────────────

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