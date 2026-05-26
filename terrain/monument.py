"""
RetroMecha — terrain/monument.py
Mega-estructura de fondo inspirada en Syd Mead.

PRINCIPIO DE DISEÑO: ESTÉTICA SOBRE VARIACIÓN.
Composición FIJA de 5 planos intersectados. Solo monument_damage
desalinea las alas y la cuña. El plano central y la base NUNCA se mueven.

Referencia: imagen de arquitectura futurista angular del documento técnico.
"""

import random

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('MONUMENT')
class MonumentModule(BaseModule):
    """
    Mega-estructura de fondo. 5 piezas fijas con proporciones constantes.

    Parámetros usados:
        aggressiveness → monument_damage (desalineación de planos)
        height_scale   → escala vertical sutil
        _seed          → variación mínima de offset X
    """
    MODULE_NAME = 'MONUMENT'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_monument_DEBUG'

        grp = mc.group(empty=True, name='rm_monument_#')

        damage = 0.5
        h_sc = self._get('height_scale', 1.0)
        seed = self._get('_seed', 42)
        rng = random.Random(seed + 5000)

        # Variación de daño: rotaciones adicionales en alas y cuña
        # damage 0.0 = intacto, 1.0 = ±15° de desalineación
        dmg_max = 15.0

        # ── 1. Plano central (NUNCA se mueve) ─────────────────────────────────
        central = mc.polyCube(
            w=1.8, h=10.0 * h_sc, d=0.3,
            sx=1, sy=2, sz=1,
            name='rm_monument_central_#'
        )[0]
        mc.move(0, 5.0 * h_sc, 0, central, relative=True)

        # ── 2. Ala izquierda ──────────────────────────────────────────────────
        wing_l = mc.polyCube(
            w=1.2, h=7.5 * h_sc, d=0.25,
            sx=1, sy=2, sz=1,
            name='rm_monument_wing_l_#'
        )[0]
        # Rotación base + daño
        ry_l = -18.0 + rng.uniform(-1, 1) * damage * dmg_max
        rz_l = 3.0 + rng.uniform(-1, 1) * damage * dmg_max * 0.5
        mc.move(-0.9, 3.75 * h_sc, 0.15, wing_l, relative=True)
        mc.rotate(0, ry_l, rz_l, wing_l, relative=True)

        # ── 3. Ala derecha ────────────────────────────────────────────────────
        wing_r = mc.polyCube(
            w=1.2, h=7.5 * h_sc, d=0.25,
            sx=1, sy=2, sz=1,
            name='rm_monument_wing_r_#'
        )[0]
        ry_r = 18.0 + rng.uniform(-1, 1) * damage * dmg_max
        rz_r = -3.0 + rng.uniform(-1, 1) * damage * dmg_max * 0.5
        mc.move(0.9, 3.75 * h_sc, -0.15, wing_r, relative=True)
        mc.rotate(0, ry_r, rz_r, wing_r, relative=True)

        # ── 4. Cuña frontal ───────────────────────────────────────────────────
        wedge = mc.polyCube(
            w=0.6, h=5.5 * h_sc, d=0.8,
            sx=1, sy=1, sz=1,
            name='rm_monument_wedge_#'
        )[0]
        rx_w = 8.0 + rng.uniform(-1, 1) * damage * dmg_max * 0.8
        mc.move(0, 2.75 * h_sc, 0.5, wedge, relative=True)
        mc.rotate(rx_w, 0, 0, wedge, relative=True)

        # ── 5. Base (NUNCA se mueve) ──────────────────────────────────────────
        base = mc.polyCube(
            w=3.0, h=0.6, d=2.0,
            name='rm_monument_base_#'
        )[0]
        mc.move(0, 0.3, 0, base, relative=True)

        # ── Hendidura decorativa central (ranura vertical) ────────────────────
        # Un cubo delgado oscuro entre plano central y cuña, crea la ranura
        slot = mc.polyCube(
            w=0.08, h=8.0 * h_sc, d=0.15,
            name='rm_monument_slot_#'
        )[0]
        mc.move(0, 4.0 * h_sc, 0.25, slot, relative=True)

        mc.parent(central, wing_l, wing_r, wedge, base, slot, grp)

        return self._finalize_group(grp, position, rotation, scale)
