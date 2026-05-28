"""
RetroMecha — terrain/fragment.py  v2
Fragmento angular emergente. Escalas corregidas (más grandes).
Estilo Yoji Shinkawa.
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('FRAGMENT')
class FragmentModule(BaseModule):
    MODULE_NAME = 'FRAGMENT'

    def generate(self, position=(0,0,0), scale=1.0, rotation=(0,0,0)) -> str:
        if mc is None:
            return 'rm_fragment_DEBUG'

        grp = mc.group(empty=True, name='rm_fragment_#')

        aggr = 0.5
        h_sc = self._get('height_scale', 1.0)
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + hash(str(position)) % 9999)

        # ── Dimensiones amplias ───────────────────────────────────────────────
        # La escala que llega del terrain_builder (0.8-2.5) multiplica esto
        fw = rng.uniform(0.6, 1.2)
        fh = rng.uniform(2.0, 4.5) * h_sc
        fd = rng.uniform(0.25, 0.7)

        # ── Losa principal ────────────────────────────────────────────────────
        slab = mc.polyCube(w=fw, h=fh, d=fd, sx=1, sy=2, sz=1,
                           name='rm_frag_slab_#')[0]
        # Emerge del suelo — base en Y=0 local
        mc.move(0, fh*0.5, 0, slab, relative=True)

        # ── Deformación de vértices ───────────────────────────────────────────
        try:
            vn = mc.polyEvaluate(slab, vertex=True)
            intensity = 0.10 + aggr * 0.54
            for _ in range(rng.randint(3, min(5, vn))):
                vi = rng.randint(0, vn-1)
                mc.polyMoveVertex(f'{slab}.vtx[{vi}]',
                                  translateX=rng.uniform(-1,1)*intensity,
                                  translateY=rng.uniform(-0.5,1)*intensity*0.4,
                                  translateZ=rng.uniform(-1,1)*intensity,
                                  localTranslate=True)
        except Exception:
            pass

        # ── Rotación angular Shinkawa ─────────────────────────────────────────
        rmin = 15.0 + aggr * 15.0
        rmax = 32.0 + aggr * 39.0
        rx = rng.uniform(rmin, rmax) * rng.choice([-1, 1])
        rz = rng.uniform(rmin*0.3, rmax*0.5) * rng.choice([-1, 1])
        mc.rotate(rx, 0, rz, slab, relative=True)

        parts = [slab]

        # ── Losa secundaria adosada ───────────────────────────────────────────
        if rng.random() < 0.55:
            fw2 = fw * rng.uniform(0.4, 0.75)
            fh2 = fh * rng.uniform(0.5, 0.8)
            fd2 = fd * rng.uniform(0.6, 1.0)
            slab2 = mc.polyCube(w=fw2, h=fh2, d=fd2,
                                name='rm_frag_slab2_#')[0]
            ox = rng.uniform(-fw*0.6, fw*0.6)
            mc.move(ox, fh2*0.5, 0, slab2, relative=True)
            rx2 = rx * rng.uniform(0.6, 1.4)
            rz2 = rz * rng.uniform(0.6, 1.4)
            mc.rotate(rx2, 0, rz2, slab2, relative=True)
            parts.append(slab2)

        # ── Punta/spike (alta aggr) ───────────────────────────────────────────
        if aggr > 0.30:
            tip_h = rng.uniform(0.4, 0.9) * h_sc
            tip = mc.polyCone(r=fw*0.3, h=tip_h,
                              sa=rng.choice([3, 4, 5]),
                              name='rm_frag_tip_#')[0]
            mc.move(0, fh*0.85, 0, tip, relative=True)
            mc.rotate(rx*0.7, 0, rz*0.7, tip, relative=True)
            parts.append(tip)

        mc.parent(*parts, grp)
        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)
