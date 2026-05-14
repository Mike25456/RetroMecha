"""
RetroMecha — modules/head.py
Módulo de cabeza: geometría placeholder para beta.

── CÓMO REEMPLAZAR CON GEOMETRÍA MANUAL ──────────────────────────────────────
1. En Maya, modela la cabeza manualmente.
2. Abre el Script Editor → pestaña MEL → activa "Echo All Commands".
3. Selecciona el objeto → Edit > Delete by Type > History (limpia el historial).
4. Copia el historial MEL de creación (polyCube, polyBevel, etc.).
5. Pega ese MEL en el método generate() de esta clase, reemplazando
   los mc.polyCube() por los comandos correspondientes traducidos a Python.
6. Ajusta la posición de origen al (0,0,0) para que MechaBuilder
   pueda posicionarlo correctamente.
── ────────────────────────────────────────────────────────────────────────────

PROMPT SUGERIDO PARA OpenCode/Claude al generar este módulo:
"Dado este historial MEL de Maya: [pegar MEL aquí]
Conviértelo a Python usando maya.cmds.
La función debe retornar el nombre del grupo raíz.
El origen de la geometría debe estar en (0,0,0).
Respeta la interfaz: generate(self, position, scale, rotation) -> str"
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('HEAD')
class HeadModule(BaseModule):
    """
    Módulo de cabeza — geometría de placeholder (cubos y cilindros).
    Reemplazar el contenido de generate() con la geometría manual cuando esté lista.
    """
    MODULE_NAME = 'HEAD'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_head_DEBUG'

        grp = mc.group(empty=True, name='rm_head_#')

        aggr = self._get('aggressiveness', 0.5)

        # ── Bloque principal de la cabeza ─────────────────────────────────────
        main = mc.polyCube(w=1.1, h=0.95, d=0.95,
                           sx=1, sy=1, sz=1,
                           name='rm_head_main_#')[0]

        # ── Visor (panel frontal) ─────────────────────────────────────────────
        visor = mc.polyCube(w=0.75, h=0.18, d=0.06,
                            name='rm_head_visor_#')[0]
        mc.move(0, 0.08, 0.50, visor, relative=True)

        # ── Sensores laterales (tamaño variable según agresividad) ────────────
        ear_h = 0.35 + aggr * 0.15
        ear_l = mc.polyCube(w=0.13, h=ear_h, d=0.28,
                            name='rm_head_ear_l_#')[0]
        mc.move(-0.62, 0.05, 0, ear_l, relative=True)

        ear_r = mc.polyCube(w=0.13, h=ear_h, d=0.28,
                            name='rm_head_ear_r_#')[0]
        mc.move(0.62, 0.05, 0, ear_r, relative=True)

        # ── Antena superior (hexagonal, referencia retro) ─────────────────────
        antenna = mc.polyCylinder(r=0.07, h=0.28, sa=6,
                                  name='rm_head_antenna_#')[0]
        mc.move(0, 0.62, 0, antenna, relative=True)

        # ── Placa superior (escalonada) ───────────────────────────────────────
        top_plate = mc.polyCube(w=0.7, h=0.1, d=0.7,
                                name='rm_head_top_plate_#')[0]
        mc.move(0, 0.52, 0, top_plate, relative=True)

        mc.parent(main, visor, ear_l, ear_r, antenna, top_plate, grp)

        return self._finalize_group(grp, position, rotation, scale)
