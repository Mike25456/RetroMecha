"""
RetroMecha — terrain/terrain_builder.py  v6

COMPOSICIÓN EN PERSPECTIVA CENTRAL (boceto del usuario):
  - Cámara en Z+ mirando hacia Z-
  - Monumento SIEMPRE centrado en X=0, lejos en Z-
  - FRENTE (Z+): ZONA PROHIBIDA — nada se genera ahí
  - LATERALES (X+ y X-): alta densidad — elementos guían la vista al mecha
  - FONDO (Z-): densidad media — espacio para el monumento

MEJORAS v6 sobre v5:
  ① Nuevo paso _greebles(): bloques de detalle pequeños sobre plataformas
     (cajas de máquinas, conductos, barreras) — rellena el vacío visual
  ② Nuevo paso _barriers(): muros de contención industriales a lo largo
     de los bordes de zonas laterales — encuadran la composición
  ③ _pillars() mejorado: pilares ahora pueden ser "rotos" (inclinados)
     y tener cables entre ellos (polyCube muy delgado entre dos posiciones)
  ④ _platforms() corregido: platform_count se lee correctamente del preset
     (el cálculo anterior ignoraba el slider del panel)
  ⑤ _debris() más denso cerca de fragmentos (debris_anchor_mode)
  ⑥ Optimización: los debris usan ch=False en polyCube (ya estaba),
     y el batch-parent se hace una sola vez al final del build()
  ⑦ Posición de torres ornamentales del monumento corregida (ya no flotan)
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
from materials.materializer import materialize_terrain

GROUND_Y = 0.0

COMPONENT_CLEAN = {
    'monument':  ['rm_monument_*', 'rm_bg_tower_*'],
    'skyline':   ['rm_skyline_*'],
    'platforms': ['rm_platform_*', 'rm_plat_tower_*'],
    'pillars':   ['rm_pillar_*'],
    'fragments': ['rm_fragment_*'],
    'debris':    ['rm_debris_*', 'rm_deb_*'],
    'ramps':     ['rm_ramps_*', 'rm_ramp_*'],
    'ground':    ['rm_ground_*'],
    'greebles':  ['rm_greeble_*'],
    'barriers':  ['rm_barrier_*'],
}


def _clean_patterns(patterns):
    for pat in patterns:
        for node in (mc.ls(pat, type='transform') or []):
            try:
                mc.delete(node)
            except Exception:
                pass


class TerrainBuilder:

    DEFAULT_PRESET = {
        'ground_plane_y':       -0.05,
        'safe_radius':           6.0,
        'front_exclusion_deg':  50.0,

        'monument_scale':        5.5,
        'monument_distance_z': -45.0,

        'skyline_count':          3,
        'skyline_distance_z':  -55.0,
        'skyline_spread_x':     40.0,

        'platform_count':        8,
        'platform_y_levels':  [0.6, 1.4, 2.5, 4.0],
        'platform_scale_range': [1.0, 1.8],

        'fragment_count':       12,
        'fragment_scale_range': [0.8, 2.0],

        'pillar_count':          8,
        'ramp_probability':      0.55,
        'debris_count':         50,
        'tower_probability':     0.65,

        # Nuevos en v6
        'greeble_count':        30,   # bloques de detalle sobre plataformas
        'barrier_count':         6,   # muros de contención

        'ring_min_r':           10.0,
        'ring_max_r':           35.0,
    }

    ZONES = [
        (math.radians(-60), math.radians(40),  0.44),
        (math.radians(140), math.radians(240), 0.44),
        (math.radians(240), math.radians(300), 0.12),
    ]

    def __init__(self, params, seed, preset_name='avanzada', mecha_bbox=None):
        self.params     = params
        self.seed       = seed
        self._rng       = random.Random(seed)
        self.preset     = self._load_preset(preset_name)
        self.mecha_bbox = mecha_bbox or (-2, 0.5, -1.5, 2, 5, 1.5)
        self._root      = None
        self._plat_pos  = []

    # ─────────────────────────────────────────────────────────────────────────
    #  PUNTO DE ENTRADA
    # ─────────────────────────────────────────────────────────────────────────

    def build(self):
        print(f'[RetroMecha][Terrain] Build v6 | Seed:{self.seed}')
        if not MAYA_AVAILABLE:
            return 'rm_terrain_DEBUG'

        self._all_pieces = []
        self._root = mc.group(empty=True, name='rm_terrain_#')
        try:
            self._ground()
            self._monument_bg()
            self._skyline_bg()
            self._platforms()
            self._ramps()
            self._pillars()
            self._barriers()       # ← nuevo v6
            self._fragments()
            self._greebles()       # ← nuevo v6
            self._debris()

            if self._all_pieces:
                mc.parent(self._all_pieces, self._root)

            if self.params.get('use_support_edges', True):
                count = apply_support_edges(self._root, offset=0.018,
                                            fraction=0.045, segments=2,
                                            max_faces=80, min_faces=20)
                print(f'[RetroMecha][Terrain] Support edges: {count}')
            materialize_terrain(self._root)
            force_preview_one(self._root)
            n = len(mc.listRelatives(self._root,
                    allDescendents=True, type='transform') or [])
            print(f'[RetroMecha][Terrain] OK: {self._root} ({n} objs)')
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERROR: {e}')
            import traceback; traceback.print_exc()
        return self._root

    def rebuild_component(self, component, terrain_root, overrides=None):
        if not MAYA_AVAILABLE or not mc.objExists(terrain_root):
            return False
        if overrides:
            self.preset.update(overrides)

        self._root = terrain_root
        self._all_pieces = []
        self._plat_pos = None

        _clean_patterns(COMPONENT_CLEAN.get(component, []))

        if component == 'platforms':
            _clean_patterns(COMPONENT_CLEAN.get('ramps', []))
            _clean_patterns(COMPONENT_CLEAN.get('greebles', []))
            self._plat_pos = []

        if component == 'ramps':
            self._plat_pos = self._restore_plat_pos(terrain_root)

        try:
            _FN = {
                'ground':    self._ground,
                'monument':  self._monument_bg,
                'skyline':   self._skyline_bg,
                'platforms': self._platforms,
                'pillars':   self._pillars,
                'fragments': self._fragments,
                'debris':    self._debris,
                'ramps':     self._ramps,
                'greebles':  self._greebles,
                'barriers':  self._barriers,
            }
            fn = _FN.get(component)
            if fn:
                fn()

            if component == 'platforms':
                self._ramps()
                self._greebles()

            if self._all_pieces:
                mc.parent(self._all_pieces, terrain_root)

            materialize_terrain(terrain_root)
            if self.params.get('use_support_edges', True):
                count = apply_support_edges(terrain_root, max_faces=80, min_faces=20)
                print(f'[RetroMecha][Terrain] SE({component}): {count}')
            force_preview_one(terrain_root)
        except Exception as e:
            print(f'[RetroMecha][Terrain] rebuild_component({component}): {e}')
            import traceback; traceback.print_exc()
            return False
        return True

    def _restore_plat_pos(self, terrain_root):
        positions = []
        for plat in (mc.ls('rm_platform_*', type='transform') or []):
            try:
                p = mc.xform(plat, q=True, t=True, ws=True)
                positions.append(tuple(p))
            except Exception:
                pass
        return positions

    # ─────────────────────────────────────────────────────────────────────────
    #  DISTRIBUCIÓN ANGULAR
    # ─────────────────────────────────────────────────────────────────────────

    def _composition_pos(self, n, r_min=None, r_max=None):
        safe  = self.preset.get('safe_radius', 6.0)
        r_lo  = max(safe, r_min or self.preset.get('ring_min_r', 10.0))
        r_hi  = r_max or self.preset.get('ring_max_r', 35.0)

        excl_deg = self.preset.get('front_exclusion_deg', 50.0)
        excl     = math.radians(excl_deg)
        front    = math.pi / 2
        dyn_zones = [
            (front - excl - math.radians(70), front - excl, 0.40),
            (front + excl,                    front + excl + math.radians(100), 0.40),
            (front + excl + math.radians(100),front + excl + math.radians(160), 0.20),
        ]

        result = []
        for _ in range(n):
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
            result.append((math.cos(angle) * radius, math.sin(angle) * radius))
        return result

    def _random_lateral_pos(self, r_lo, r_hi):
        excl_deg = self.preset.get('front_exclusion_deg', 50.0)
        excl     = math.radians(excl_deg)
        front    = math.pi / 2
        choice   = self._rng.random()
        if choice < 0.40:
            angle = self._rng.uniform(front - excl - math.radians(70), front - excl)
        elif choice < 0.80:
            angle = self._rng.uniform(front + excl, front + excl + math.radians(100))
        else:
            angle = self._rng.uniform(math.radians(240), math.radians(310))
        r = self._rng.uniform(r_lo, r_hi)
        return math.cos(angle) * r, math.sin(angle) * r

    # ─────────────────────────────────────────────────────────────────────────
    #  GROUND
    # ─────────────────────────────────────────────────────────────────────────

    def _ground(self):
        gp_y = self.preset.get('ground_plane_y', -0.05)
        self._spawn('GROUND_PLANE', position=(0, gp_y, 0), scale=1.0)

    # ─────────────────────────────────────────────────────────────────────────
    #  MONUMENTO
    # ─────────────────────────────────────────────────────────────────────────

    def _monument_bg(self):
        p    = self.preset
        gp_y = p.get('ground_plane_y', -0.05)
        ms   = p.get('monument_scale', 5.5)
        mz   = p.get('monument_distance_z', -45.0)

        self._spawn('MONUMENT', position=(0, gp_y, mz), scale=ms)

        # Torres ornamentales — posición corregida (antes flotaban)
        for side in [-1, 1]:
            if self._rng.random() < 0.7:
                node = self._spawn(
                    'TOWER',
                    position=(side * ms * 1.6, gp_y, mz + self._rng.uniform(-3.0, 3.0)),
                    scale=ms * self._rng.uniform(0.4, 0.65)
                )
                if node:
                    try: mc.rename(node, 'rm_bg_tower_#')
                    except: pass

    # ─────────────────────────────────────────────────────────────────────────
    #  SKYLINE
    # ─────────────────────────────────────────────────────────────────────────

    def _skyline_bg(self):
        p        = self.preset
        gp_y     = p.get('ground_plane_y', -0.05)
        sky_n    = p.get('skyline_count', 3)
        sky_z    = p.get('skyline_distance_z', -55.0)
        spread_x = p.get('skyline_spread_x', 40.0)

        for i in range(sky_n):
            sx = 0.0 if sky_n == 1 else -spread_x * 0.5 + (spread_x / (sky_n - 1)) * i
            sx += self._rng.uniform(-2.0, 2.0)
            sz  = sky_z + self._rng.uniform(-4.0, 4.0)
            ss  = self._rng.uniform(1.6, 2.8)
            self._spawn('SKYLINE', position=(sx, gp_y, sz), scale=ss)

    # ─────────────────────────────────────────────────────────────────────────
    #  PLATAFORMAS — FIX v6: usa platform_count del preset correctamente
    # ─────────────────────────────────────────────────────────────────────────

    def _platforms(self):
        p      = self.preset
        y_lvls = p.get('platform_y_levels', [0.6, 1.4, 2.5, 4.0])
        sc_rng = p.get('platform_scale_range', [1.0, 1.8])
        # FIX: antes multiplicaba por (1.4 - 0.5*1.2) = 0.8 siempre.
        # Ahora usa el valor directo del preset (ya modificado por el slider).
        n = max(4, int(p.get('platform_count', 8)))

        positions = self._composition_pos(n)

        for (px, pz) in positions:
            py = GROUND_Y + self._rng.choice(y_lvls)
            ps = self._rng.uniform(*sc_rng)

            self._spawn('PLATFORM', position=(px, py, pz), scale=ps)
            self._plat_pos.append((px, py, pz))

            if self._rng.random() < p.get('tower_probability', 0.65):
                node = self._spawn('TOWER',
                                   position=(px, py, pz),
                                   scale=ps * self._rng.uniform(0.5, 0.9))
                if node:
                    try: mc.rename(node, 'rm_plat_tower_#')
                    except: pass

            for _sp in range(2):
                if self._rng.random() < 0.75:
                    ox = px + self._rng.uniform(-3.0, 3.0)
                    oz = pz + self._rng.uniform(-3.0, 3.0)
                    safe = p.get('safe_radius', 6.0)
                    if math.sqrt(ox * ox + oz * oz) > safe:
                        oy = GROUND_Y + self._rng.choice(y_lvls) * 0.65
                        ss = ps * self._rng.uniform(0.4, 0.7)
                        self._spawn('PLATFORM', position=(ox, oy, oz), scale=ss)
                        self._plat_pos.append((ox, oy, oz))

        # Landing pad central
        self._spawn('PLATFORM', position=(0, GROUND_Y, 0), scale=1.4)
        self._plat_pos.append((0, GROUND_Y, 0))

    # ─────────────────────────────────────────────────────────────────────────
    #  RAMPAS
    # ─────────────────────────────────────────────────────────────────────────

    def _ramps(self):
        prob  = self.preset.get('ramp_probability', 0.55)
        MAX_D = 18.0
        grp   = mc.group(empty=True, name='rm_ramps_#')
        ramps = []

        for i, p1 in enumerate(self._plat_pos):
            if self._rng.random() > prob:
                continue
            best_d, best = float('inf'), None
            for j in range(i + 1, len(self._plat_pos)):
                p2 = self._plat_pos[j]
                d  = math.dist(p1, p2)
                if d < best_d and d < MAX_D:
                    best_d, best = d, p2
            if best is None:
                continue
            mx = (p1[0] + best[0]) * 0.5
            my = (p1[1] + best[1]) * 0.5
            mz = (p1[2] + best[2]) * 0.5
            ramp = mc.polyCube(w=0.5, h=0.10, d=best_d, ch=False, name='rm_ramp_#')[0]
            mc.move(mx, my + 0.06, mz, ramp)
            ay = math.degrees(math.atan2(best[0] - p1[0], best[2] - p1[2]))
            ax = -math.degrees(math.atan2(best[1] - p1[1], best_d))
            mc.rotate(ax, ay, 0, ramp)
            ramps.append(ramp)

        if ramps:
            mc.parent(*ramps, grp)
            mc.parent(grp, self._root)
            print(f'[RetroMecha][Terrain] {len(ramps)} rampas')
        else:
            mc.delete(grp)

    # ─────────────────────────────────────────────────────────────────────────
    #  PILARES — v6: pilares dañados + cables
    # ─────────────────────────────────────────────────────────────────────────

    def _pillars(self):
        n         = self.preset.get('pillar_count', 8)
        positions = self._composition_pos(n)
        pillar_world_pos = []   # para cables

        for (px, pz) in positions:
            ph  = self._rng.uniform(3.0, 9.0)
            pr  = self._rng.uniform(0.15, 0.35)
            psa = self._rng.choice([4, 6, 8])

            shaft = mc.polyCylinder(r=pr, h=ph, sa=psa, name='rm_pillar_#')[0]
            mc.move(px, GROUND_Y + ph * 0.5, pz, shaft)

            # Pilar dañado: leve inclinación aleatoria
            tilt = self._rng.uniform(0, 6.0)
            tilt_dir = self._rng.uniform(0, 360)
            mc.rotate(tilt * math.cos(math.radians(tilt_dir)),
                      0,
                      tilt * math.sin(math.radians(tilt_dir)),
                      shaft, relative=True)

            ring = mc.polyTorus(r=pr * 2.5, sr=pr * 0.35, sa=8, sh=4,
                                name='rm_pillar_ring_#')[0]
            mc.move(px, GROUND_Y + ph * 0.65, pz, ring)

            cap = mc.polyCylinder(r=pr * 1.8, h=0.12, sa=psa,
                                  name='rm_pillar_cap_#')[0]
            mc.move(px, GROUND_Y + ph, pz, cap)

            # Segundo anillo a media altura
            ring2 = mc.polyTorus(r=pr * 1.8, sr=pr * 0.25, sa=6, sh=4,
                                 name='rm_pillar_ring_#')[0]
            mc.move(px, GROUND_Y + ph * 0.30, pz, ring2)

            pillar_grp = mc.group(shaft, ring, ring2, cap, name='rm_pillar_grp_#')
            self._all_pieces.append(pillar_grp)
            pillar_world_pos.append((px, GROUND_Y + ph * 0.75, pz))

        # Cables entre pilares vecinos (muy delgados, tienen acento visual)
        if len(pillar_world_pos) >= 2:
            cable_grp = mc.group(empty=True, name='rm_pillar_cable_#')
            cables = []
            for i, pa in enumerate(pillar_world_pos):
                # Conectar al pilar más cercano
                best_d, best_b = float('inf'), None
                for j, pb in enumerate(pillar_world_pos):
                    if j == i:
                        continue
                    d = math.dist(pa, pb)
                    if d < best_d and d < 22.0:
                        best_d, best_b = d, pb
                if best_b is None:
                    continue
                if self._rng.random() > 0.55:
                    continue
                cable_len = best_d
                cable = mc.polyCube(
                    w=0.04, h=0.04, d=cable_len, ch=False,
                    name='rm_pillar_ring_cable_#'
                )[0]
                mx = (pa[0] + best_b[0]) * 0.5
                my = (pa[1] + best_b[1]) * 0.5 + self._rng.uniform(-0.3, 0.3)
                mz = (pa[2] + best_b[2]) * 0.5
                mc.move(mx, my, mz, cable)
                ay = math.degrees(math.atan2(best_b[0] - pa[0], best_b[2] - pa[2]))
                mc.rotate(0, ay, 0, cable)
                cables.append(cable)
            if cables:
                mc.parent(*cables, cable_grp)
                self._all_pieces.append(cable_grp)
            else:
                mc.delete(cable_grp)

    # ─────────────────────────────────────────────────────────────────────────
    #  BARRIERS — nuevo v6
    #  Muros de contención / barreras industriales
    # ─────────────────────────────────────────────────────────────────────────

    def _barriers(self):
        n         = self.preset.get('barrier_count', 6)
        positions = self._composition_pos(n, r_min=8.0, r_max=28.0)
        grp       = mc.group(empty=True, name='rm_barrier_#')
        pieces    = []

        for (bx, bz) in positions:
            # Orientación de la barrera (perpendicular a la dirección del mecha)
            angle_to_center = math.degrees(math.atan2(-bx, -bz))
            bw = self._rng.uniform(2.5, 6.0)
            bh = self._rng.uniform(0.6, 1.6)
            bd = self._rng.uniform(0.25, 0.45)

            # Cuerpo principal
            body = mc.polyCube(w=bw, h=bh, d=bd, name='rm_barrier_body_#')[0]
            mc.move(bx, GROUND_Y + bh * 0.5, bz, body)
            mc.rotate(0, angle_to_center + self._rng.uniform(-25, 25), 0, body)

            # Tapa superior con acento
            cap = mc.polyCube(
                w=bw + 0.08, h=bh * 0.12, d=bd + 0.06,
                name='rm_barrier_cap_#'
            )[0]
            mc.move(bx, GROUND_Y + bh + bh * 0.06, bz, cap)
            mc.rotate(0, angle_to_center + self._rng.uniform(-25, 25), 0, cap)

            # Patas de soporte en los extremos
            for side in [-1, 1]:
                leg_w = self._rng.uniform(0.15, 0.28)
                leg_h = GROUND_Y + bh
                leg = mc.polyCylinder(r=leg_w, h=leg_h, sa=4, name='rm_barrier_base_#')[0]
                ox = side * bw * 0.42 * math.cos(math.radians(angle_to_center))
                oz = side * bw * 0.42 * math.sin(math.radians(angle_to_center))
                mc.move(bx + ox, GROUND_Y + leg_h * 0.5, bz + oz, leg)

            # Franja de acento (ranura horizontal)
            slot = mc.polyCube(
                w=bw * 0.8, h=bh * 0.08, d=bd + 0.02,
                name='rm_barrier_slot_#'
            )[0]
            mc.move(bx, GROUND_Y + bh * 0.55, bz, slot)
            mc.rotate(0, angle_to_center + self._rng.uniform(-25, 25), 0, slot)

            pieces.extend([body, cap, slot])

        if pieces:
            mc.parent(*pieces, grp)
            self._all_pieces.append(grp)
        else:
            mc.delete(grp)

    # ─────────────────────────────────────────────────────────────────────────
    #  FRAGMENTS
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

            for _ in range(self._rng.randint(2, 4)):
                sx = fx + self._rng.uniform(-4.0, 4.0)
                sz = fz + self._rng.uniform(-4.0, 4.0)
                if math.sqrt(sx * sx + sz * sz) > safe:
                    self._spawn('FRAGMENT',
                                position=(sx, GROUND_Y, sz),
                                scale=fs * self._rng.uniform(0.2, 0.5))

    # ─────────────────────────────────────────────────────────────────────────
    #  GREEBLES — nuevo v6
    #  Cajas de maquinaria, conductos y bloques pequeños encima de plataformas
    # ─────────────────────────────────────────────────────────────────────────

    def _greebles(self):
        """Coloca detalles industriales sobre las plataformas existentes."""
        if not self._plat_pos:
            return

        n_total = self.preset.get('greeble_count', 30)
        grp     = mc.group(empty=True, name='rm_greeble_#')
        pieces  = []

        for i in range(n_total):
            # Elegir una plataforma al azar como punto de referencia
            base = self._plat_pos[self._rng.randint(0, len(self._plat_pos) - 1)]
            px = base[0] + self._rng.uniform(-2.0, 2.0)
            py = base[1] + 0.22   # encima del tablero de plataforma
            pz = base[2] + self._rng.uniform(-2.0, 2.0)

            gtype = self._rng.choices(
                ['box', 'conduit', 'vent', 'tank'],
                weights=[0.40, 0.25, 0.20, 0.15]
            )[0]

            if gtype == 'box':
                gw = self._rng.uniform(0.20, 0.60)
                gh = self._rng.uniform(0.15, 0.45)
                gd = self._rng.uniform(0.18, 0.55)
                obj = mc.polyCube(w=gw, h=gh, d=gd,
                                  name='rm_greeble_box_#')[0]
                mc.move(px, py + gh * 0.5, pz, obj)
                mc.rotate(0, self._rng.uniform(0, 90), 0, obj)
                # Ranura/tapa de acento
                lid = mc.polyCube(w=gw + 0.02, h=0.03, d=gd + 0.02,
                                  name='rm_greeble_cap_#')[0]
                mc.move(px, py + gh + 0.015, pz, lid)
                mc.rotate(0, self._rng.uniform(0, 90), 0, lid)
                pieces.extend([obj, lid])

            elif gtype == 'conduit':
                clen = self._rng.uniform(0.8, 2.5)
                crad = self._rng.uniform(0.04, 0.10)
                obj  = mc.polyCylinder(r=crad, h=clen, sa=6,
                                       name='rm_greeble_cap_conduit_#')[0]
                mc.rotate(0, 0, 90, obj, relative=True)   # horizontal
                ry = self._rng.uniform(0, 180)
                mc.rotate(0, ry, 0, obj, relative=True)
                mc.move(px, py + crad + 0.01, pz, obj)
                # Anillos de sujeción
                for frac in (0.25, 0.75):
                    ring = mc.polyTorus(r=crad * 1.8, sr=crad * 0.28, sa=6, sh=4,
                                        name='rm_greeble_ring_#')[0]
                    dx = math.cos(math.radians(ry)) * clen * (frac - 0.5)
                    dz = math.sin(math.radians(ry)) * clen * (frac - 0.5)
                    mc.move(px + dx, py + crad + 0.01, pz + dz, ring)
                    pieces.append(ring)
                pieces.append(obj)

            elif gtype == 'vent':
                vw = self._rng.uniform(0.3, 0.65)
                vh = self._rng.uniform(0.05, 0.14)
                vd = self._rng.uniform(0.25, 0.55)
                obj = mc.polyCube(w=vw, h=vh, d=vd,
                                  name='rm_greeble_cap_vent_#')[0]
                mc.move(px, py + vh * 0.5, pz, obj)
                mc.rotate(0, self._rng.uniform(0, 90), 0, obj)
                # Lamas del vent (2-3 tiras)
                n_lamas = self._rng.randint(2, 4)
                for li in range(n_lamas):
                    lama = mc.polyCube(w=vw * 0.85, h=0.015, d=0.025,
                                       name='rm_greeble_slot_vent_lama_#')[0]
                    lz = vd * (-0.35 + 0.7 * li / max(1, n_lamas - 1))
                    mc.move(px, py + vh * 0.6, pz + lz, lama)
                    pieces.append(lama)
                pieces.append(obj)

            else:   # tank
                tr = self._rng.uniform(0.15, 0.30)
                th = self._rng.uniform(0.40, 0.90)
                obj = mc.polyCylinder(r=tr, h=th, sa=8,
                                      name='rm_greeble_cap_tank_#')[0]
                mc.move(px, py + th * 0.5, pz, obj)
                ring = mc.polyTorus(r=tr * 1.6, sr=tr * 0.20, sa=8, sh=4,
                                    name='rm_greeble_ring_#')[0]
                mc.move(px, py + th * 0.75, pz, ring)
                pieces.extend([obj, ring])

        if pieces:
            mc.parent(*pieces, grp)
            self._all_pieces.append(grp)
        else:
            mc.delete(grp)

        print(f'[RetroMecha][Terrain] Greebles: {len(pieces)} piezas')

    # ─────────────────────────────────────────────────────────────────────────
    #  DEBRIS
    # ─────────────────────────────────────────────────────────────────────────

    def _debris(self):
        n    = self.preset.get('debris_count', 80)
        gp_y = self.preset.get('ground_plane_y', -0.05)
        safe = self.preset.get('safe_radius', 6.0)
        r_lo = self.preset.get('ring_min_r', 10.0)
        r_hi = self.preset.get('ring_max_r', 35.0)
        self._debris_manual(n, gp_y, safe, r_lo, r_hi)

    def _debris_manual(self, count, gp_y, safe, r_lo, r_hi):
        grp      = mc.group(empty=True, name='rm_debris_scatter_#')
        placed   = 0
        pieces   = []
        attempts = 0
        while placed < count and attempts < count * 4:
            attempts += 1
            px, pz = self._random_lateral_pos(r_lo, r_hi)
            if math.sqrt(px * px + pz * pz) < safe:
                continue
            s  = self._rng.uniform(0.06, 0.25)
            sw = s * self._rng.uniform(0.5, 2.2)
            sh = s * self._rng.uniform(0.3, 1.6)
            sd = s * self._rng.uniform(0.4, 1.9)
            piece = mc.polyCube(w=sw, h=sh, d=sd, ch=False,
                                name=f'rm_deb_{placed}_#')[0]
            mc.move(px, gp_y + sh * 0.5, pz, piece)
            mc.rotate(self._rng.uniform(0, 360),
                      self._rng.uniform(0, 360),
                      self._rng.uniform(0, 360), piece)
            pieces.append(piece)
            placed += 1

        mc.parent(*pieces, grp)
        self._all_pieces.append(grp)
        print(f'[RetroMecha][Terrain] Debris: {placed}')

    # ─────────────────────────────────────────────────────────────────────────
    #  SPAWN / LOAD
    # ─────────────────────────────────────────────────────────────────────────

    def _spawn(self, name, position=(0, 0, 0), scale=1.0, rotation=(0, 0, 0)):
        cls = get_module(name)
        if cls is None:
            return None
        instance = cls(self.params)
        try:
            node = instance.generate(position=position, scale=scale, rotation=rotation)
        except Exception as e:
            print(f'[RetroMecha][Terrain] ERR "{name}": {e}')
            import traceback; traceback.print_exc()
            return None
        if node and mc.objExists(node):
            self._all_pieces.append(node)
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