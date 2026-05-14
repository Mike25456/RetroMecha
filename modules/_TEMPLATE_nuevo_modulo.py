"""
RetroMecha — modules/_TEMPLATE_nuevo_modulo.py
══════════════════════════════════════════════════════════════════════════════

INSTRUCCIONES DE USO CON OpenCode / Claude
──────────────────────────────────────────
Este archivo es el contrato que el AI debe respetar al generar un módulo nuevo.
Copia este template, renómbralo (ej: modules/thruster.py) y pásalo al AI
junto con el historial MEL de tu modelo manual.

PROMPT RECOMENDADO PARA OPENCODE/CLAUDE:
────────────────────────────────────────────────────────────────────────────
"Tengo este historial MEL de Maya de una pieza [NOMBRE]:

[PEGAR HISTORIAL MEL AQUÍ]

Conviértelo a Python (maya.cmds) siguiendo EXACTAMENTE este template:

[PEGAR ESTE ARCHIVO COMPLETO]

Reglas:
- MODULE_NAME = '[NOMBRE_EN_MAYÚSCULAS]'
- El decorador @register('[NOMBRE_EN_MAYÚSCULAS]') debe estar presente
- La geometría debe tener su origen en (0,0,0) antes de que
  _finalize_group() aplique la posición global
- Usa self._get('aggressiveness', 0.5) para variaciones visuales
- No agregues lógica de ensamblaje — solo geometría local
- Retorna solo el nombre del grupo raíz (str)
- El grupo raíz debe llamarse 'rm_[nombre]_#'
"
────────────────────────────────────────────────────────────────────────────

CÓMO CAPTURAR EL HISTORIAL MEL:
1. Modela la pieza manualmente en Maya
2. Script Editor → pestaña MEL → activa "Echo All Commands"
3. Edit > Delete by Type > History (limpiar historial constructivo)
4. Mueve el pivot al origen: Modify > Center Pivot, luego
   mueve el objeto a (0,0,0) con Freeze Transformations
5. Copia el bloque de comandos relevantes del Script Editor
6. Pásaselo al AI con este template

══════════════════════════════════════════════════════════════════════════════
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register


@register('NOMBRE_MODULO')   # <-- cambiar por el nombre real, ej: 'THRUSTER'
class NuevoModuloModule(BaseModule):
    """
    Módulo de [descripción breve de la pieza].

    Parámetros que usa de self.params:
        aggressiveness: afecta [qué aspecto visual]
        decay:          afecta [qué aspecto]
        (agregar los que uses)
    """
    MODULE_NAME = 'NOMBRE_MODULO'   # <-- mismo que @register()

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_nuevo_DEBUG'

        # ── Crear grupo raíz ──────────────────────────────────────────────────
        grp = mc.group(empty=True, name='rm_nuevo_#')  # <-- cambiar prefijo

        # ── Leer parámetros relevantes ────────────────────────────────────────
        aggr  = self._get('aggressiveness', 0.5)
        decay = self._get('decay', 0.85)

        # ════════════════════════════════════════════════════════════════════
        # PEGAR AQUÍ la geometría convertida desde MEL
        # Ejemplo de estructura:
        #
        # pieza_a = mc.polyCube(w=1.0, h=1.0, d=1.0, name='rm_nuevo_base_#')[0]
        # mc.move(0, 0, 0, pieza_a, relative=True)
        #
        # pieza_b = mc.polyCylinder(r=0.3, h=0.5, sa=8, name='rm_nuevo_det_#')[0]
        # mc.move(0, 0.75, 0, pieza_b, relative=True)
        #
        # mc.parent(pieza_a, pieza_b, grp)
        # ════════════════════════════════════════════════════════════════════

        # ── Aplicar transformaciones y retornar ───────────────────────────────
        # NO mover el objeto antes de esta línea — MechaBuilder lo posiciona
        return self._finalize_group(grp, position, rotation, scale)
