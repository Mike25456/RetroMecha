"""
RetroMecha — modules/torso/torso_module.py
Dispatcher de estilos de torso.
"""
try:
    import maya.cmds as mc
except ImportError:
    mc = None

from core.base_module import BaseModule
from core.module_registry import register
from modules.torso import style_base
from modules.torso import style_samurai

_STYLE_MODS = {
    'core':    style_base,
    'heavy':   style_base,
    'slim':    style_base,
    'compact': style_base,
    'samurai': style_samurai,
}


@register('TORSO')
class TorsoModule(BaseModule):
    MODULE_NAME = 'TORSO'

    def generate(self,
                 position: tuple = (0, 0, 0),
                 scale: float = 1.0,
                 rotation: tuple = (0, 0, 0)) -> str:

        if mc is None:
            return 'rm_torso_DEBUG'

        grp = mc.group(empty=True, name='rm_torso_#')

        aggr = 0.5
        h_sc = self._get('height_scale', 1.0)
        torso_style = self._get('torso_style', 'core')
        nucleus_style = self._get('nucleus_style', 'ring')
        torso_h = 2.0 * h_sc
        tt = style_base.TorsoTune.from_params(self._get)
        nt = style_base.NucleusTune.from_params(self._get)

        mod = _STYLE_MODS.get(torso_style, style_base)
        result = mod.build(aggr, torso_h, tt, nt,
                           torso_style=torso_style, nucleus_style=nucleus_style)

        children = []
        if result['body']:
            children.append(result['body'])
        if result['waist']:
            children.append(result['waist'])
        if result['reactor']:
            children.append(result['reactor'])
        if result['chest_strip']:
            children.append(result['chest_strip'])
        children.extend(result.get('style_parts', []))
        if result['pad_l']:
            children.append(result['pad_l'])
        if result['pad_r']:
            children.append(result['pad_r'])
        if result['stub']:
            children.append(result['stub'])

        children = [c for c in children if c and mc.objExists(c)]
        if children:
            mc.parent(children, grp)

        self._assign_materials(grp)
        return self._finalize_group(grp, position, rotation, scale)
