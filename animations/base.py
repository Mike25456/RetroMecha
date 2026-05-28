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

    def _clean_all(self):
        """Limpia TODO rastro de animacion del root y la escena."""
        root = self.mecha_root
        if not root or not mc.objExists(root):
            return

        # 0) Si el mecha esta dentro de un offset group previo, sacarlo y borrarlo
        self._remove_anim_offset_group()

        # 1) Borra motionPath en toda la escena + objetos auxiliares
        for mp in (mc.ls(type='motionPath') or []):
            try:
                mc.delete(mp)
            except Exception:
                pass
        for obj in ('rm_flight_path', 'rm_motionPath', 'rm_look_target',
                    'rm_lookPath', 'rm_bobber'):
            if mc.objExists(obj):
                try:
                    mc.delete(obj)
                except Exception:
                    pass

        # 2) Desconecta TODO source de cada atributo transform del root
        for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz',
                     'translateX', 'translateY', 'translateZ',
                     'rotateX', 'rotateY', 'rotateZ',
                     'translate', 'rotate'):
            for plug in (mc.listConnections(f'{root}.{attr}',
                                            source=True, destination=False,
                                            plugs=True) or []):
                try:
                    mc.disconnectAttr(plug, f'{root}.{attr}')
                except Exception:
                    pass
            for node in (mc.listConnections(f'{root}.{attr}',
                                            source=True, destination=False) or []):
                try:
                    nt = mc.nodeType(node)
                    if nt in ('motionPath', 'expression'):
                        mc.delete(node)
                except Exception:
                    pass

        # 3) Keyframes
        try:
            mc.cutKey(root, clear=True)
        except Exception:
            pass

        # 4) Unlock + force set a 0/1
        for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'):
            try:
                mc.setAttr(f'{root}.{a}', lock=False)
            except Exception:
                pass
        try:
            mc.xform(root, translation=(0, 0, 0), rotation=(0, 0, 0))
        except Exception as e:
            print(f'[RetroMecha] _clean_all xform error: {e}')
        for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz'):
            try:
                mc.setAttr(f'{root}.{a}', 0)
            except Exception as e:
                print(f'[RetroMecha] _clean_all setAttr {root}.{a} error: {e}')
        for a in ('sx', 'sy', 'sz'):
            try:
                mc.setAttr(f'{root}.{a}', 1)
            except Exception as e:
                print(f'[RetroMecha] _clean_all setAttr {root}.{a} error: {e}')

        # 5) Expressiones conocidas
        for expr in ('rm_idle_root', 'rm_idle_head',
                     'rm_idle_arm_L', 'rm_idle_arm_R',
                     'rm_idle_wing_L', 'rm_idle_wing_R', 'rm_idle_reactor',
                     'rm_spin_root', 'rm_spin_torso', 'rm_spin_head',
                     'rm_spin_arm_L', 'rm_spin_arm_R',
                     'rm_spin_wing_L', 'rm_spin_wing_R', 'rm_spin_reactor'):
            if mc.objExists(expr):
                try:
                    mc.delete(expr)
                except Exception:
                    pass

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

    # ──────────────────────────────────────────────────────────────────────────
    #  ANIM OFFSET GROUP  (evita que el mecha cruce el suelo Y=0)
    #  El usuario puede editar translateY del grupo para afinar la altura.
    # ──────────────────────────────────────────────────────────────────────────

    def _anim_offset_name(self) -> str:
        root_short = self.mecha_root.split('|')[-1] if self.mecha_root else ''
        return f'rm_anim_offset_{root_short}'

    def _ensure_anim_offset_group(self, default_y: float = 0.6) -> str | None:
        """
        Inserta un grupo padre encima del mecha que aplica un offset Y global.
        Las expresiones de animacion siguen actuando sobre el root, pero el
        grupo padre lo levanta sobre el suelo. Idempotente.
        """
        if not MAYA_AVAILABLE or not self.mecha_root:
            return None
        if not mc.objExists(self.mecha_root):
            return None

        offset_name = self._anim_offset_name()

        # Si ya existe el padre correcto, no recrear.
        parents = mc.listRelatives(self.mecha_root, parent=True, fullPath=True) or []
        if parents:
            parent_short = parents[0].rsplit('|', 1)[-1]
            if parent_short == offset_name:
                try:
                    if mc.getAttr(f'{offset_name}.translateY') < default_y:
                        mc.setAttr(f'{offset_name}.translateY', default_y)
                except Exception:
                    pass
                return offset_name

        # Crear grupo nuevo manteniendo la posicion mundial del mecha.
        try:
            world_pos = mc.xform(self.mecha_root, q=True, worldSpace=True,
                                 translation=True)
            grp = mc.group(empty=True, name=offset_name, world=True)
            mc.xform(grp, worldSpace=True,
                     translation=(world_pos[0],
                                  world_pos[1] + default_y,
                                  world_pos[2]))
            mc.parent(self.mecha_root, grp)
            return grp
        except Exception as e:
            print(f'[RetroMecha][Anim] Error creando offset group: {e}')
            return None

    def _remove_anim_offset_group(self):
        """Desempaqueta el mecha del offset group y borra el grupo."""
        if not MAYA_AVAILABLE or not self.mecha_root:
            return
        if not mc.objExists(self.mecha_root):
            return

        parents = mc.listRelatives(self.mecha_root, parent=True, fullPath=True) or []
        if not parents:
            return
        parent_short = parents[0].rsplit('|', 1)[-1]
        if not parent_short.startswith('rm_anim_offset_'):
            return

        try:
            mc.parent(self.mecha_root, world=True)
        except Exception:
            pass
        try:
            mc.delete(parent_short)
        except Exception:
            pass

    @abstractmethod
    def apply(self):
        """Aplica la animación al mecha."""

    @abstractmethod
    def remove(self):
        """Elimina toda la animación (keyframes + nodos auxiliares)."""
