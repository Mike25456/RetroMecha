"""
RetroMecha — terrain/fragment.py  v3
Fragmento angular emergente con formación en cluster — estilo Yoji Shinkawa.

MEJORAS sobre v2:
  - Losa base de anclaje (base enterrada, da peso visual al suelo)
  - Hasta 3 losas satélite adicionales formando una "grieta" coherente
  - Chips angulares de borde (polyCube muy delgados, adosados a la losa)
  - Eje de rotación base variado: ahora puede inclinarse en Y (giro en planta)
  - Geometría de la punta más variada: cone 3-4 lados O pirámide plana
  - Losa secundaria puede tener offset negativo en Y (semi-enterrada)
  - Sin cambios en la interfaz pública (mismos args/returns)
"""

import random
import math

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('FRAGMENT')
class FragmentModule(BaseModule):
    MODULE_NAME = 'FRAGMENT'

    def generate(self, position=(0, 0, 0), scale=1.0, rotation=(0, 0, 0)) -> str:
        if mc is None:
            return 'rm_fragment_DEBUG'

        grp = mc.group(empty=True, name='rm_fragment_#')

        aggr = self._get('aggressiveness', 0.5)
        h_sc = self._get('height_scale', 1.0)
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + hash(str(position)) % 99991)

        # ── Dimensiones ───────────────────────────────────────────────────────
        fw = rng.uniform(0.6, 1.3)
        fh = rng.uniform(2.0, 5.0) * h_sc
        fd = rng.uniform(0.25, 0.75)

        # Rotaciones angulares Shinkawa
        rmin = 12.0 + aggr * 12.0
        rmax = 28.0 + aggr * 35.0
        rx   = rng.uniform(rmin, rmax) * rng.choice([-1, 1])
        rz   = rng.uniform(rmin * 0.3, rmax * 0.5) * rng.choice([-1, 1])
        ry   = rng.uniform(-25.0, 25.0)   # giro en planta — novedad v3

        # ── 1. Losa base de anclaje (enterrada) ──────────────────────────────
        #       Ancla el fragmento al suelo, elimina el efecto de "flotando"
        base_w = fw * rng.uniform(1.4, 2.2)
        base_d = fd * rng.uniform(1.4, 2.2)
        base_h = rng.uniform(0.18, 0.40)
        base_slab = mc.polyCube(
            w=base_w, h=base_h, d=base_d,
            name='rm_frag_slab_base_#'
        )[0]
        # La losa base queda levemente por encima del suelo
        mc.move(0, base_h * 0.35, 0, base_slab, relative=True)
        # Leve rotación en planta para seguir el giro de la losa principal
        mc.rotate(0, ry * 0.6, 0, base_slab, relative=True)

        # ── 2. Losa principal emergente ───────────────────────────────────────
        slab = mc.polyCube(w=fw, h=fh, d=fd, sx=1, sy=2, sz=1,
                           name='rm_frag_slab_#')[0]
        mc.move(0, fh * 0.5, 0, slab, relative=True)

        # Deformación de vértices
        try:
            vn = mc.polyEvaluate(slab, vertex=True)
            intensity = 0.08 + aggr * 0.48
            for _ in range(rng.randint(3, min(6, vn))):
                vi = rng.randint(0, vn - 1)
                mc.polyMoveVertex(
                    f'{slab}.vtx[{vi}]',
                    translateX=rng.uniform(-1, 1) * intensity,
                    translateY=rng.uniform(-0.4, 0.8) * intensity * 0.4,
                    translateZ=rng.uniform(-1, 1) * intensity,
                    localTranslate=True
                )
        except Exception:
            pass

        mc.rotate(rx, ry, rz, slab, relative=True)

        parts = [base_slab, slab]

        # ── 3. Chips de borde (fragmentos angulares adosados) ─────────────────
        n_chips = rng.randint(1, 3)
        for _ in range(n_chips):
            cw = fw * rng.uniform(0.15, 0.45)
            ch = fh * rng.uniform(0.08, 0.25)
            cd = fd * rng.uniform(0.5, 1.4)
            chip = mc.polyCube(w=cw, h=ch, d=cd, name='rm_frag_slab_chip_#')[0]
            side_x = rng.choice([-1, 1]) * (fw * 0.5 + cw * 0.4)
            off_y  = rng.uniform(fh * 0.1, fh * 0.7)
            mc.move(side_x, off_y, rng.uniform(-fd * 0.3, fd * 0.3), chip, relative=True)
            mc.rotate(rx * rng.uniform(0.5, 1.3),
                      rng.uniform(-35, 35),
                      rz * rng.uniform(0.5, 1.3), chip, relative=True)
            parts.append(chip)

        # ── 4. Losa secundaria adosada ────────────────────────────────────────
        if rng.random() < 0.60:
            fw2 = fw * rng.uniform(0.4, 0.80)
            fh2 = fh * rng.uniform(0.45, 0.85)
            fd2 = fd * rng.uniform(0.55, 1.1)
            slab2 = mc.polyCube(w=fw2, h=fh2, d=fd2, name='rm_frag_slab2_#')[0]
            ox  = rng.uniform(-fw * 0.7, fw * 0.7)
            oy2 = fh2 * rng.uniform(0.3, 0.6)   # puede quedar semi-baja
            mc.move(ox, oy2, 0, slab2, relative=True)
            mc.rotate(rx * rng.uniform(0.55, 1.45),
                      ry + rng.uniform(-20, 20),
                      rz * rng.uniform(0.55, 1.45), slab2, relative=True)
            parts.append(slab2)

        # ── 5. Losa terciaria en clúster (novedad v3) ─────────────────────────
        if rng.random() < 0.40:
            fw3 = fw * rng.uniform(0.25, 0.55)
            fh3 = fh * rng.uniform(0.30, 0.60)
            fd3 = fd * rng.uniform(0.4, 0.9)
            slab3 = mc.polyCube(w=fw3, h=fh3, d=fd3, name='rm_frag_slab2_#')[0]
            ox3 = rng.uniform(-fw * 1.1, fw * 1.1)
            oy3 = fh3 * rng.uniform(0.2, 0.5)
            oz3 = rng.uniform(-fd * 0.8, fd * 0.8)
            mc.move(ox3, oy3, oz3, slab3, relative=True)
            mc.rotate(rx * rng.uniform(0.4, 1.6),
                      ry + rng.uniform(-40, 40),
                      rz * rng.uniform(0.4, 1.6), slab3, relative=True)
            parts.append(slab3)

        # ── 6. Punta / spike ──────────────────────────────────────────────────
        if aggr > 0.25:
            tip_h = rng.uniform(0.35, 1.0) * h_sc
            tip_type = rng.choice(['cone3', 'cone4', 'flat'])
            if tip_type == 'flat':
                tip = mc.polyCube(
                    w=fw * 0.18, h=tip_h, d=fd * 0.18,
                    name='rm_frag_tip_#'
                )[0]
            else:
                sa = 3 if tip_type == 'cone3' else 4
                tip = mc.polyCone(r=fw * 0.25, h=tip_h, sa=sa,
                                  name='rm_frag_tip_#')[0]
            mc.move(rng.uniform(-fw * 0.2, fw * 0.2),
                    fh * rng.uniform(0.75, 0.95),
                    rng.uniform(-fd * 0.2, fd * 0.2),
                    tip, relative=True)
            mc.rotate(rx * 0.65, ry * 0.4, rz * 0.65, tip, relative=True)
            parts.append(tip)

        mc.parent(*parts, grp)
        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)