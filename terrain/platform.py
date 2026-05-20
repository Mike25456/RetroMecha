"""
RetroMecha — terrain/platform.py  v2
Plataforma industrial elevada con columnas de soporte.
Alturas reales positivas — estilo Syd Mead.
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('PLATFORM')
class PlatformModule(BaseModule):
    MODULE_NAME = 'PLATFORM'

    def generate(self, position=(0,0,0), scale=1.0, rotation=(0,0,0)) -> str:
        if mc is None:
            return 'rm_platform_DEBUG'

        grp = mc.group(empty=True, name='rm_platform_#')

        aggr = self._get('aggressiveness', 0.5)
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + hash(str(position)) % 9999)

        # ── Dimensiones del tablero ───────────────────────────────────────────
        # Tamaños generosos — la escala del terrain_builder los reduce si hace falta
        bw = rng.uniform(3.5, 6.5)
        bd = rng.uniform(2.5, 5.0)
        bh = rng.uniform(0.22, 0.40)

        # ── Tablero principal ─────────────────────────────────────────────────
        surface = mc.polyCube(w=bw, h=bh, d=bd,
                              name='rm_plat_surface_#')[0]
        # Centrar en Y=0 local — _finalize_group lo lleva a position
        # El tablero queda arriba, las columnas cuelgan hacia abajo

        # ── Borde perimetral ──────────────────────────────────────────────────
        lip = mc.polyCube(w=bw + 0.12, h=bh*0.4, d=bd + 0.12,
                          name='rm_plat_lip_#')[0]
        mc.move(0, -(bh*0.5 + bh*0.2), 0, lip, relative=True)

        # ── Ranura decorativa en superficie ──────────────────────────────────
        slot = mc.polyCube(w=bw*0.7, h=0.03, d=0.06,
                           name='rm_plat_slot_#')[0]
        slot_z = rng.uniform(-bd*0.25, bd*0.25)
        mc.move(0, bh*0.5 + 0.015, slot_z, slot, relative=True)

        parts = [surface, lip, slot]

        # ── Columnas de soporte ───────────────────────────────────────────────
        # Van desde la base del tablero hasta el suelo (position[1] arriba, 0 abajo)
        col_h = position[1]          # altura real sobre el suelo
        if col_h > 0.15:
            col_r  = rng.uniform(0.10, 0.18)
            col_sa = rng.choice([4, 6, 8])
            offsets = [
                (-bw*0.38,  bd*0.38),
                ( bw*0.38,  bd*0.38),
                (-bw*0.38, -bd*0.38),
                ( bw*0.38, -bd*0.38),
            ]
            for cx, cz in offsets:
                col = mc.polyCylinder(r=col_r, h=col_h, sa=col_sa,
                                      name='rm_plat_col_#')[0]
                # posición local: la mitad de la columna está en -col_h/2 desde
                # el centro del tablero (que luego _finalize_group sube a position[1])
                mc.move(cx, -(bh*0.5 + col_h*0.5), cz, col, relative=True)
                parts.append(col)

            # Anillo de refuerzo a media columna
            for cx, cz in offsets[:2]:
                ring = mc.polyTorus(r=col_r*2.2, sr=col_r*0.28, sa=8, sh=4,
                                    name='rm_plat_ring_#')[0]
                mc.move(cx, -(bh*0.5 + col_h*0.5), cz, ring, relative=True)
                parts.append(ring)

        # ── Deformación de bordes (alta agresividad) ──────────────────────────
        if aggr > 0.45:
            try:
                vtx_n = mc.polyEvaluate(surface, vertex=True)
                for _ in range(2):
                    vi = rng.randint(0, vtx_n - 1)
                    mc.polyMoveVertex(f'{surface}.vtx[{vi}]',
                                      translateX=rng.uniform(-0.12, 0.12)*aggr,
                                      translateY=rng.uniform(-0.06, 0.0)*aggr,
                                      localTranslate=True)
            except Exception:
                pass

        mc.parent(*parts, grp)
        return self._finalize_group(grp, position, rotation, scale)
