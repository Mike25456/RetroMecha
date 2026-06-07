"""
RetroMecha — terrain/skyline.py  v3
Skyline de fondo con mega-estructuras: edificios grandes, torres, arcos y
placas angulares inspirados en Syd Mead. Escala aumentada para visibilidad
desde cualquier distancia de cámara.
"""
import random
import math

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


def _finish(mesh):
    try:
        mc.polySoftEdge(mesh, angle=30, ch=0)
        mc.delete(mesh, ch=True)
    except Exception:
        pass
    return mesh


@register('SKYLINE')
class SkylineModule(BaseModule):
    MODULE_NAME = 'SKYLINE'

    # Distribución: fracción del ancho asignada a cada tipo de bloque
    BLOCK_COUNT = 14   # bloques base en la franja

    def generate(self, position=(0, 0, 0), scale=1.0, rotation=(0, 0, 0)) -> str:
        if mc is None:
            return 'rm_skyline_DEBUG'

        grp  = mc.group(empty=True, name='rm_skyline_#')
        seed = self._get('_seed', 42)
        rng  = random.Random(seed + hash(str(position)) % 9999)
        aggr = self._get('aggressiveness', 0.5)

        # Franja total — mucho más ancha y alta que v2
        total_w  = 55.0
        block_w  = total_w / self.BLOCK_COUNT
        start_x  = -(total_w * 0.5) + block_w * 0.5

        parts = []

        # ── 1. CUERPOS PRINCIPALES (bloques grandes variados) ─────────────────
        for i in range(self.BLOCK_COUNT):
            btype = rng.choices(
                ['tower', 'slab', 'wedge', 'obelisk'],
                weights=[0.35, 0.30, 0.20, 0.15]
            )[0]

            bx = start_x + i * block_w + rng.uniform(-block_w*0.2, block_w*0.2)
            bz = rng.uniform(-1.5, 1.5)

            if btype == 'tower':
                parts += self._make_tower(bx, bz, rng, block_w)
            elif btype == 'slab':
                parts += self._make_slab(bx, bz, rng, block_w)
            elif btype == 'wedge':
                parts += self._make_wedge(bx, bz, rng, block_w, aggr)
            else:
                parts += self._make_obelisk(bx, bz, rng, block_w)

        # ── 2. MEGA-ESTRUCTURAS (1-3 dominando el skyline) ────────────────────
        n_mega = rng.randint(1, 3)
        mega_xs = [rng.uniform(-total_w*0.4, total_w*0.4) for _ in range(n_mega)]
        for mx in mega_xs:
            mtype = rng.choice(['mega_tower', 'arch', 'cross_spire'])
            if mtype == 'mega_tower':
                parts += self._make_mega_tower(mx, rng)
            elif mtype == 'arch':
                parts += self._make_arch(mx, rng)
            else:
                parts += self._make_cross_spire(mx, rng)

        # ── 3. DETALLES HORIZONTALES (cornisas, franjas) ───────────────────────
        for _ in range(rng.randint(2, 4)):
            parts += self._make_cornice(
                rng.uniform(-total_w*0.4, total_w*0.4), rng)

        if parts:
            mc.parent(*parts, grp)

        return self._finalize_group(grp, position, rotation, scale)

    # ── Bloques base ──────────────────────────────────────────────────────────

    def _make_tower(self, bx, bz, rng, slot_w):
        """Torre alta y estrecha con retranqueos."""
        parts = []
        bh = rng.uniform(8.0, 20.0)
        bw = slot_w * rng.uniform(0.5, 0.85)
        bd = rng.uniform(1.2, 3.0)

        # Cuerpo principal
        base = mc.polyCube(w=bw, h=bh, d=bd, name='rm_skyline_tower_#')[0]
        mc.move(bx, bh*0.5, bz, base)
        parts.append(_finish(base))

        # Retranqueo superior (sección más estrecha)
        sh = bh * rng.uniform(0.25, 0.45)
        sx = bw * rng.uniform(0.55, 0.80)
        step = mc.polyCube(w=sx, h=sh, d=bd*0.8, name='rm_skyline_tower_step_#')[0]
        mc.move(bx, bh + sh*0.5, bz, step)
        parts.append(_finish(step))

        # Antena / remate
        if rng.random() > 0.4:
            ah = rng.uniform(1.5, 4.0)
            ant = mc.polyCylinder(r=0.08, h=ah, sa=6, name='rm_skyline_ant_#')[0]
            mc.move(bx, bh + sh + ah*0.5, bz, ant)
            parts.append(_finish(ant))

        return parts

    def _make_slab(self, bx, bz, rng, slot_w):
        """Edificio losa horizontal sobre pilares."""
        parts = []
        bh = rng.uniform(4.0, 11.0)
        bw = slot_w * rng.uniform(0.8, 1.2)
        bd = rng.uniform(1.5, 3.5)

        body = mc.polyCube(w=bw, h=bh, d=bd, name='rm_skyline_slab_#')[0]
        mc.move(bx, bh*0.5, bz, body)
        parts.append(_finish(body))

        # Placa superior saliente
        cap = mc.polyCube(w=bw*1.1, h=bh*0.08, d=bd*1.1,
                          name='rm_skyline_slab_cap_#')[0]
        mc.move(bx, bh + bh*0.04, bz, cap)
        parts.append(_finish(cap))

        return parts

    def _make_wedge(self, bx, bz, rng, slot_w, aggr):
        """Bloque con perfil triangular/cuña — estilo Syd Mead."""
        parts = []
        bh = rng.uniform(6.0, 16.0)
        bw = slot_w * rng.uniform(0.5, 0.9)
        bd = rng.uniform(1.0, 2.5)

        wedge = mc.polyCube(w=bw, h=bh, d=bd, sx=1, sy=2, sz=1,
                            name='rm_skyline_wedge_#')[0]
        mc.move(bx, bh*0.5, bz, wedge)

        # Deformar vértices superiores para crear la cuña
        try:
            vtx_count = mc.polyEvaluate(wedge, vertex=True)
            for vi in range(vtx_count):
                pos = mc.xform(f'{wedge}.vtx[{vi}]', q=True, t=True, ws=True)
                if pos[1] > bh * 0.6:
                    side = 1 if pos[0] > bx else -1
                    mc.xform(f'{wedge}.vtx[{vi}]',
                             t=(pos[0] + side * bw * 0.3, pos[1], pos[2]),
                             ws=True)
        except Exception:
            pass

        parts.append(_finish(wedge))
        return parts

    def _make_obelisk(self, bx, bz, rng, slot_w):
        """Obelisco — columna que termina en punta."""
        parts = []
        bh = rng.uniform(10.0, 22.0)
        br = slot_w * rng.uniform(0.18, 0.35)

        shaft = mc.polyCone(r=br, h=bh, sa=4, name='rm_skyline_obelisk_#')[0]
        mc.move(bx, bh*0.5, bz, shaft)
        mc.rotate(0, rng.uniform(0, 45), 0, shaft)
        parts.append(_finish(shaft))

        # Base del obelisco
        base = mc.polyCube(w=br*3.5, h=br*1.2, d=br*3.5,
                           name='rm_skyline_obelisk_base_#')[0]
        mc.move(bx, br*0.6, bz, base)
        parts.append(_finish(base))

        return parts

    # ── Mega-estructuras ──────────────────────────────────────────────────────

    def _make_mega_tower(self, bx, rng):
        """Torre masiva de 25-40u con silueta articulada."""
        parts = []
        h1 = rng.uniform(25.0, 40.0)
        w1 = rng.uniform(3.5, 6.0)
        d1 = rng.uniform(2.5, 4.5)
        bz = rng.uniform(-1.0, 1.0)

        # Cuerpo A (principal)
        bodyA = mc.polyCube(w=w1, h=h1, d=d1, name='rm_skyline_mega_a_#')[0]
        mc.move(bx, h1*0.5, bz, bodyA)
        parts.append(_finish(bodyA))

        # Cuerpo B (adosado, desplazado)
        h2 = h1 * rng.uniform(0.55, 0.80)
        ox = rng.choice([-1, 1]) * w1 * rng.uniform(0.4, 0.7)
        bodyB = mc.polyCube(w=w1*0.6, h=h2, d=d1*0.75,
                            name='rm_skyline_mega_b_#')[0]
        mc.move(bx+ox, h2*0.5, bz, bodyB)
        parts.append(_finish(bodyB))

        # Puente entre cuerpos
        bridge_h = h1 * rng.uniform(0.5, 0.7)
        bridge = mc.polyCube(w=abs(ox)+w1*0.3, h=w1*0.18, d=d1*0.5,
                             name='rm_skyline_mega_bridge_#')[0]
        mc.move(bx+ox*0.5, bridge_h, bz, bridge)
        parts.append(_finish(bridge))

        # Antena triple
        for i, off in enumerate((-w1*0.25, 0, w1*0.25)):
            ah = rng.uniform(3.0, 8.0)
            ant = mc.polyCylinder(r=0.10, h=ah, sa=6,
                                  name=f'rm_skyline_mega_ant_{i}_#')[0]
            mc.move(bx+off, h1+ah*0.5, bz, ant)
            parts.append(_finish(ant))

        return parts

    def _make_arch(self, bx, rng):
        """Arco monumental — dos pilares + dintel."""
        parts = []
        ah   = rng.uniform(18.0, 30.0)
        aw   = rng.uniform(8.0, 14.0)
        pt_w = rng.uniform(1.8, 3.2)
        bz   = rng.uniform(-1.0, 1.0)

        for side, name_sfx in [(-1, 'l'), (1, 'r')]:
            pillar = mc.polyCube(w=pt_w, h=ah, d=pt_w*1.3,
                                 name=f'rm_skyline_arch_pillar_{name_sfx}_#')[0]
            mc.move(bx + side*(aw*0.5 - pt_w*0.3), ah*0.5, bz, pillar)
            parts.append(_finish(pillar))

        # Dintel (parte horizontal superior)
        lintel = mc.polyCube(w=aw+pt_w, h=pt_w*0.9, d=pt_w*1.2,
                             name='rm_skyline_arch_lintel_#')[0]
        mc.move(bx, ah + pt_w*0.45, bz, lintel)
        parts.append(_finish(lintel))

        # Remate en punta sobre el dintel
        peak_h = rng.uniform(3.0, 7.0)
        peak = mc.polyCone(r=pt_w*0.8, h=peak_h, sa=4,
                           name='rm_skyline_arch_peak_#')[0]
        mc.move(bx, ah + pt_w*0.9 + peak_h*0.5, bz, peak)
        parts.append(_finish(peak))

        return parts

    def _make_cross_spire(self, bx, rng):
        """Cruz de dos losas intersectadas + aguja central."""
        parts = []
        h  = rng.uniform(20.0, 35.0)
        w  = rng.uniform(2.0, 4.0)
        d  = rng.uniform(1.0, 2.0)
        bz = rng.uniform(-1.0, 1.0)

        # Losa vertical principal
        slabA = mc.polyCube(w=w, h=h, d=d, name='rm_skyline_cross_a_#')[0]
        mc.move(bx, h*0.5, bz, slabA)
        parts.append(_finish(slabA))

        # Losa rotada 20-30° (intersecta la primera)
        slabB = mc.polyCube(w=w*0.7, h=h*0.75, d=d,
                            name='rm_skyline_cross_b_#')[0]
        mc.move(bx, h*0.5*0.75, bz, slabB)
        mc.rotate(0, rng.uniform(20, 35), 0, slabB)
        parts.append(_finish(slabB))

        # Aguja central
        sp_h = rng.uniform(4.0, 10.0)
        spire = mc.polyCone(r=0.25, h=sp_h, sa=4,
                            name='rm_skyline_cross_spire_#')[0]
        mc.move(bx, h + sp_h*0.5, bz, spire)
        parts.append(_finish(spire))

        return parts

    # ── Detalles ──────────────────────────────────────────────────────────────

    def _make_cornice(self, bx, rng):
        """Franja horizontal larga y baja — da profundidad al fondo."""
        parts = []
        cw = rng.uniform(10.0, 25.0)
        ch = rng.uniform(0.6, 1.8)
        cy = rng.uniform(2.0, 8.0)
        bz = rng.uniform(-2.0, 2.0)

        cornice = mc.polyCube(w=cw, h=ch, d=rng.uniform(0.4, 1.0),
                              name='rm_skyline_cornice_#')[0]
        mc.move(bx, cy, bz, cornice)
        parts.append(_finish(cornice))
        return parts
