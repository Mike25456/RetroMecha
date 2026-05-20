"""
RetroMecha — terrain/platform.py
Plataforma industrial horizontal con alturas cuantizadas.
Estilo Syd Mead: geometría fabricada, bordes rectos, superficies planas.
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
    """
    Bloque horizontal industrial con borde perimetral.

    Parámetros usados:
        aggressiveness → deformación sutil de bordes (alta = bordes rotos)
        decay          → escala de sub-plataformas
        separation     → grosor del borde perimetral
        _seed          → variación de proporciones
    """
    MODULE_NAME = 'PLATFORM'

    # Alturas cuantizadas permitidas (sensación de diseño intencional)
    Y_LEVELS = [0.0, -0.3, -0.6, -1.0]

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_platform_DEBUG'

        grp = mc.group(empty=True, name='rm_platform_#')

        aggr = self._get('aggressiveness', 0.5)
        seed = self._get('_seed', 42)
        rng = random.Random(seed + hash(str(position)) % 10000)

        # Proporciones con variación por seed
        base_w = rng.uniform(2.2, 3.5)
        base_d = rng.uniform(1.6, 2.8)
        base_h = rng.uniform(0.18, 0.35)

        # ── Superficie principal ──────────────────────────────────────────────
        surface = mc.polyCube(
            w=base_w, h=base_h, d=base_d,
            name='rm_platform_surface_#'
        )[0]

        # ── Borde perimetral (labio) ──────────────────────────────────────────
        lip_h = 0.06
        lip_offset = 0.05
        lip = mc.polyCube(
            w=base_w + lip_offset * 2,
            h=lip_h,
            d=base_d + lip_offset * 2,
            name='rm_platform_lip_#'
        )[0]
        mc.move(0, -(base_h * 0.5 + lip_h * 0.5), 0, lip, relative=True)

        # ── Detalle de superficie (línea de separación) ───────────────────────
        line_w = base_w * 0.8
        line = mc.polyCube(
            w=line_w, h=0.015, d=0.03,
            name='rm_platform_line_#'
        )[0]
        mc.move(0, base_h * 0.5 + 0.008, rng.uniform(-0.3, 0.3) * base_d,
                line, relative=True)

        # ── Deformación por agresividad (bordes rotos) ────────────────────────
        # Con aggr alta, desplazamos 1-2 vértices del borde
        if aggr > 0.4 and mc:
            try:
                vtx_count = mc.polyEvaluate(surface, vertex=True)
                # Mover 2 vértices aleatorios ligeramente
                for _ in range(min(2, vtx_count)):
                    vi = rng.randint(0, vtx_count - 1)
                    ox = rng.uniform(-0.1, 0.1) * aggr
                    oy = rng.uniform(-0.05, 0.02) * aggr
                    mc.polyMoveVertex(
                        f'{surface}.vtx[{vi}]',
                        translateX=ox, translateY=oy,
                        localTranslate=True
                    )
            except Exception:
                pass  # Si falla, la plataforma queda intacta — OK

        mc.parent(surface, lip, line, grp)

        return self._finalize_group(grp, position, rotation, scale)
