"""
RetroMecha — terrain/fragment.py
Fragmento angular emergente del suelo.
Estilo Yoji Shinkawa: poliedros irregulares, rotaciones pronunciadas,
alto contraste, espacio negativo dramático.
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
    """
    Poliedro irregular emergiendo del suelo con ángulo pronunciado.
    Se construye deformando un polyCube con polyMoveVertex.

    Parámetros usados:
        aggressiveness → intensidad de deformación y ángulo
        height_scale   → estira la verticalidad del fragmento
        _seed          → forma única por fragmento
    """
    MODULE_NAME = 'FRAGMENT'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_fragment_DEBUG'

        grp = mc.group(empty=True, name='rm_fragment_#')

        aggr = self._get('aggressiveness', 0.5)
        h_sc = self._get('height_scale', 1.0)
        seed = self._get('_seed', 42)
        rng = random.Random(seed + hash(str(position)) % 10000)

        # Proporciones base: alto y delgado (losa fracturada)
        frag_w = rng.uniform(0.3, 0.7)
        frag_h = rng.uniform(1.2, 2.5) * h_sc
        frag_d = rng.uniform(0.15, 0.4)

        # ── Geometría base ────────────────────────────────────────────────────
        slab = mc.polyCube(
            w=frag_w, h=frag_h, d=frag_d,
            sx=1, sy=2, sz=1,
            name='rm_fragment_slab_#'
        )[0]

        # Centrar la base del fragmento en Y=0 (emerge del suelo)
        mc.move(0, frag_h * 0.5, 0, slab, relative=True)

        # ── Deformación de vértices (forma irregular) ─────────────────────────
        # Mover 3-5 vértices para romper la regularidad del cubo
        try:
            vtx_count = mc.polyEvaluate(slab, vertex=True)
            deform_count = rng.randint(3, min(5, vtx_count))
            deform_intensity = 0.08 + aggr * 0.15

            for _ in range(deform_count):
                vi = rng.randint(0, vtx_count - 1)
                ox = rng.uniform(-1, 1) * deform_intensity
                oy = rng.uniform(-0.5, 1) * deform_intensity * 0.5
                oz = rng.uniform(-1, 1) * deform_intensity
                mc.polyMoveVertex(
                    f'{slab}.vtx[{vi}]',
                    translateX=ox, translateY=oy, translateZ=oz,
                    localTranslate=True
                )
        except Exception:
            pass  # Si falla, fragmento queda como cubo — aceptable

        # ── Rotación angular (marca Shinkawa) ─────────────────────────────────
        # Siempre inclinado, nunca plano
        rot_range_min = 15.0 + aggr * 5.0
        rot_range_max = 30.0 + aggr * 15.0

        rx = rng.uniform(rot_range_min, rot_range_max) * rng.choice([-1, 1])
        rz = rng.uniform(rot_range_min * 0.3, rot_range_max * 0.5) * rng.choice([-1, 1])
        mc.rotate(rx, 0, rz, slab, relative=True)

        # ── Punta afilada (cono superior, opcional con alta aggr) ─────────────
        if aggr > 0.35:
            tip_h = rng.uniform(0.15, 0.35) * h_sc
            tip = mc.polyCone(
                r=frag_w * 0.35, h=tip_h, sa=rng.choice([3, 4, 5]),
                name='rm_fragment_tip_#'
            )[0]
            mc.move(0, frag_h * 0.85, 0, tip, relative=True)
            mc.rotate(rx * 0.8, 0, rz * 0.8, tip, relative=True)
            mc.parent(tip, grp)

        mc.parent(slab, grp)

        return self._finalize_group(grp, position, rotation, scale)
