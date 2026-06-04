"""
RetroMecha — modules/head/head_module.py
Dispatcher de estilos de cabeza.
"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from modules.head._shared import HeadTune
from modules.head import style_helmet
from modules.head import style_drone
from modules.head import style_sentinel
from modules.head import style_skull
from modules.head import style_kabuto

_STYLE_MODS = {
    'helmet':   style_helmet,
    'drone':    style_drone,
    'sentinel': style_sentinel,
    'skull':    style_skull,
    'kabuto':   style_kabuto,
}


@register('HEAD')
class HeadModule(BaseModule):
    MODULE_NAME = 'HEAD'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_head_DEBUG'

        grp = mc.group(empty=True, name='rm_head_#')
        aggr = 0.5
        style = self._get('head_style', 'helmet')
        tune = HeadTune.from_params(self._get)

        mod = _STYLE_MODS.get(style, style_helmet)
        mod.build(grp, aggr, tune)

        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)
