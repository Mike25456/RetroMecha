try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from abc import ABC, abstractmethod


class BaseAnimation(ABC):
    name = ""

    def __init__(self, mecha_root: str):
        self.mecha_root = mecha_root
        self._resolved = {}

    def find(self, pattern: str, side: str = None) -> str | None:
        """Busca un hijo directo del root que empiece con pattern.
        side='L' → X < 0, side='R' → X > 0, None → primero."""
        if not MAYA_AVAILABLE:
            return None
        root_long = (mc.ls(self.mecha_root, long=True) or [self.mecha_root])[0]
        if not root_long.startswith('|'):
            root_long = f'|{root_long}'
        for node in (mc.ls(type='transform', long=True) or []):
            short = node.rsplit('|', 1)[-1]
            if not short.startswith(pattern):
                continue
            parent = mc.listRelatives(node, parent=True, fullPath=True)
            if not parent:
                continue
            if parent[0] != root_long:
                continue
            if side is None:
                return node
            try:
                pos = mc.xform(node, q=True, worldSpace=True, translation=True)
            except Exception:
                continue
            if side == 'L' and pos[0] < 0:
                return node
            if side == 'R' and pos[0] > 0:
                return node
        return None

    def resolve(self) -> dict:
        """Retorna dict con {HEAD, ARM_L, ARM_R, WING_L, WING_R, ROOT}."""
        if self._resolved:
            return self._resolved
        root = self.mecha_root

        def _first(node_or_list):
            if isinstance(node_or_list, list):
                return node_or_list[0] if node_or_list else None
            return node_or_list

        head = self.find('rm_head')
        arm_l = _first(self.find('rm_arm', 'L') or mc.ls('rm_arm_1', type='transform'))
        arm_r = _first(self.find('rm_arm', 'R') or mc.ls('rm_arm_2', type='transform'))
        wing_l = _first(self.find('rm_wing', 'L') or mc.ls('rm_wing_1', type='transform'))
        wing_r = _first(self.find('rm_wing', 'R') or mc.ls('rm_wing_2', type='transform'))

        self._resolved = dict(
            ROOT=root,
            HEAD=head,
            ARM_L=arm_l,
            ARM_R=arm_r,
            WING_L=wing_l,
            WING_R=wing_r,
        )
        return self._resolved

    def clear_keys(self, nodes: list, attrs: list = None):
        """Borra keyframes y reseta atributos de una lista de nodos.
        Por defecto no toca escala (sx/sy/sz)."""
        if not MAYA_AVAILABLE:
            return
        if attrs is None:
            attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
        scale_default = 1.0
        for node in nodes:
            if not node or not mc.objExists(node):
                continue
            try:
                mc.cutKey(node, clear=True)
            except Exception:
                pass
            for attr in attrs:
                try:
                    val = scale_default if attr in ('sx', 'sy', 'sz') else 0
                    mc.setAttr(f'{node}.{attr}', val)
                except Exception:
                    pass

    def freeze(self):
        """Freeze Transformations en el root del mecha (translate, rotate, scale)."""
        if not MAYA_AVAILABLE:
            return
        if not mc.objExists(self.mecha_root):
            return
        try:
            mc.makeIdentity(self.mecha_root, apply=True,
                            translate=True, rotate=True, scale=True,
                            normal=False, preserveNormals=True)
        except Exception as e:
            print(f'[RetroMecha][Anim] Error al freeze: {e}')

    def _reset_rotation(self, node, attrs=('rx', 'ry', 'rz')):
        """Resetea solo rotacion a 0, no toca translate/scale."""
        if not node or not mc.objExists(node):
            return
        for attr in attrs:
            try:
                mc.cutKey(node, at=attr, clear=True)
            except Exception:
                pass
            try:
                mc.setAttr(f'{node}.{attr}', 0)
            except Exception:
                pass

    def delete_objects(self, names: list):
        """Borra objetos por nombre si existen."""
        if not MAYA_AVAILABLE:
            return
        for name in names:
            if mc.objExists(name):
                try:
                    mc.delete(name)
                except Exception:
                    pass

    @abstractmethod
    def apply(self):
        """Aplica la animación al mecha."""

    @abstractmethod
    def remove(self):
        """Elimina toda la animación (keyframes + nodos auxiliares)."""
