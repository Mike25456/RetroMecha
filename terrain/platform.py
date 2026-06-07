"""
RetroMecha — terrain/platform.py  v3
Plataforma industrial de alto detalle — estilo Syd Mead.

MEJORAS sobre v2:
  - Conductos / cables longitudinales sobre la superficie
  - Escaleras laterales (bloques escalonados) cuando la altura es suficiente
  - Panel de control adosado a un costado (caja con ranura)
  - Vigas de refuerzo diagonales entre columnas (polyCube inclinado)
  - Borde perimetral con canales de acento en los cuatro lados
  - Columnas con sección cuadrada alternativa (psa=4) más industrial
  - Franja anti-deslizante (slot) ahora puede ser múltiple y rotada
  - Seed completamente derivada de position para variedad sin repetición
"""

import random
import math

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('PLATFORM')
class PlatformModule(BaseModule):
    MODULE_NAME = 'PLATFORM'

    def generate(self, position=(0, 0, 0), scale=1.0, rotation=(0, 0, 0)) -> str:
        if mc is None:
            return 'rm_platform_DEBUG'

        grp = mc.group(empty=True, name='rm_platform_#')

        aggr = self._get('aggressiveness', 0.5)
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + hash(str(position)) % 99991)

        # ── Dimensiones del tablero ───────────────────────────────────────────
        bw = rng.uniform(3.5, 6.5)
        bd = rng.uniform(2.5, 5.0)
        bh = rng.uniform(0.22, 0.40)

        # ── 1. Tablero principal ──────────────────────────────────────────────
        surface = mc.polyCube(w=bw, h=bh, d=bd,
                              name='rm_plat_surface_#')[0]

        # ── 2. Borde perimetral doble ─────────────────────────────────────────
        lip = mc.polyCube(w=bw + 0.14, h=bh * 0.35, d=bd + 0.14,
                          name='rm_plat_lip_#')[0]
        mc.move(0, -(bh * 0.5 + bh * 0.175), 0, lip, relative=True)

        # Borde acento (canal en el exterior del lip)
        lip2 = mc.polyCube(w=bw + 0.08, h=bh * 0.12, d=bd + 0.08,
                           name='rm_plat_cap_#')[0]
        mc.move(0, bh * 0.5 + bh * 0.06, 0, lip2, relative=True)

        parts = [surface, lip, lip2]

        # ── 3. Franjas anti-deslizantes (slots) ──────────────────────────────
        n_slots = rng.randint(2, 4)
        slot_axis = rng.choice(['x', 'z'])   # dirección de las franjas
        for si in range(n_slots):
            if slot_axis == 'x':
                sw, sd2 = bw * 0.75, 0.055
                offset_z = rng.uniform(-bd * 0.3, bd * 0.3)
                offset_x = 0.0
            else:
                sw, sd2 = 0.055, bd * 0.75
                offset_x = rng.uniform(-bw * 0.3, bw * 0.3)
                offset_z = 0.0
            slot = mc.polyCube(w=sw, h=0.028, d=sd2,
                               name='rm_plat_slot_#')[0]
            mc.move(offset_x, bh * 0.5 + 0.014, offset_z, slot, relative=True)
            parts.append(slot)

        # ── 4. Conducto longitudinal central ─────────────────────────────────
        cond_w = bw * rng.uniform(0.55, 0.80)
        cond_r = rng.uniform(0.035, 0.065)
        conduit = mc.polyCylinder(
            r=cond_r, h=cond_w, sa=6,
            name='rm_plat_cap_conduit_#'
        )[0]
        # Orientar a lo largo de X
        mc.rotate(0, 0, 90, conduit, relative=True)
        cond_z = rng.uniform(-bd * 0.22, bd * 0.22)
        mc.move(0, bh * 0.5 + cond_r + 0.01, cond_z, conduit, relative=True)
        parts.append(conduit)

        # ── 5. Panel de control lateral ──────────────────────────────────────
        if rng.random() < 0.65:
            pw = rng.uniform(0.5, 1.0)
            ph = rng.uniform(0.4, 0.8)
            pd = 0.12
            panel_side = rng.choice([-1, 1])
            panel = mc.polyCube(w=pd, h=ph, d=pw,
                                name='rm_plat_cap_panel_#')[0]
            mc.move(panel_side * (bw * 0.5 + pd * 0.5),
                    bh * 0.5 - ph * 0.5 + rng.uniform(0.0, 0.3),
                    rng.uniform(-bd * 0.2, bd * 0.2),
                    panel, relative=True)
            # Ranura en el panel
            pslot = mc.polyCube(w=pd + 0.01, h=ph * 0.35, d=pw * 0.5,
                                name='rm_plat_slot_panel_#')[0]
            mc.move(panel_side * (bw * 0.5 + pd * 0.5),
                    bh * 0.5 - ph * 0.5 + rng.uniform(0.1, 0.25),
                    rng.uniform(-bd * 0.1, bd * 0.1),
                    pslot, relative=True)
            parts.extend([panel, pslot])

        # ── 6. Columnas de soporte ────────────────────────────────────────────
        col_h = position[1]
        offsets = [
            (-bw * 0.38,  bd * 0.38),
            ( bw * 0.38,  bd * 0.38),
            (-bw * 0.38, -bd * 0.38),
            ( bw * 0.38, -bd * 0.38),
        ]
        if col_h > 0.15:
            col_r  = rng.uniform(0.10, 0.18)
            col_sa = rng.choice([4, 4, 6, 8])   # 4 más probable → columna cuadrada

            for cx, cz in offsets:
                col = mc.polyCylinder(r=col_r, h=col_h, sa=col_sa,
                                      name='rm_plat_col_#')[0]
                mc.move(cx, -(bh * 0.5 + col_h * 0.5), cz, col, relative=True)
                parts.append(col)

            # Anillos de refuerzo en todas las columnas (antes solo 2)
            ring_y_fracs = [0.30, 0.65]
            for cx, cz in offsets:
                for yf in ring_y_fracs:
                    ring = mc.polyTorus(r=col_r * 2.0, sr=col_r * 0.30, sa=8, sh=4,
                                        name='rm_plat_ring_#')[0]
                    mc.move(cx, -(bh * 0.5 + col_h * yf), cz, ring, relative=True)
                    parts.append(ring)

            # Vigas diagonales entre pares de columnas frontales y traseras
            if col_h > 0.8 and rng.random() < 0.70:
                for (ax, az), (bx, bz) in [
                    (offsets[0], offsets[2]),
                    (offsets[1], offsets[3]),
                ]:
                    dist = math.hypot(bx - ax, bz - az)
                    brace = mc.polyCube(
                        w=col_r * 0.8, h=col_h * 0.85, d=dist,
                        name='rm_plat_col_brace_#'
                    )[0]
                    mc.move(
                        (ax + bx) * 0.5,
                        -(bh * 0.5 + col_h * 0.5),
                        (az + bz) * 0.5,
                        brace, relative=True
                    )
                    angle_z = math.degrees(math.atan2(col_h * 0.85, dist)) * rng.choice([-1, 1])
                    mc.rotate(angle_z, 0, 0, brace, relative=True)
                    parts.append(brace)

            # Escalones cuando col_h es suficiente
            if col_h > 1.5 and rng.random() < 0.55:
                n_steps = rng.randint(3, 5)
                step_side = rng.choice([-1, 1])
                sw_step = rng.uniform(0.5, 0.9)
                for si in range(n_steps):
                    frac = (si + 1) / (n_steps + 1)
                    sy = -(bh * 0.5 + col_h * frac)
                    step = mc.polyCube(
                        w=sw_step, h=0.06, d=0.45,
                        name='rm_plat_cap_step_#'
                    )[0]
                    mc.move(
                        step_side * (bw * 0.5 + sw_step * 0.5),
                        sy, 0,
                        step, relative=True
                    )
                    parts.append(step)

        # ── 7. Deformación de bordes (alta agresividad) ───────────────────────
        if aggr > 0.45:
            try:
                vtx_n = mc.polyEvaluate(surface, vertex=True)
                n_deform = rng.randint(2, 4)
                for _ in range(n_deform):
                    vi = rng.randint(0, vtx_n - 1)
                    mc.polyMoveVertex(
                        f'{surface}.vtx[{vi}]',
                        translateX=rng.uniform(-0.12, 0.12) * aggr,
                        translateY=rng.uniform(-0.06, 0.0) * aggr,
                        localTranslate=True
                    )
            except Exception:
                pass

        mc.parent(*parts, grp)
        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)