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
        """Retorna dict con {ROOT, TORSO, HEAD, ARM_L, ARM_R, WING_L, WING_R}."""
        if self._resolved:
            return self._resolved
        root = self.mecha_root

        torso = self.find('rm_torso')
        head = self.find('rm_head')
        arm_l = self.find('rm_arm', 'L')
        arm_r = self.find('rm_arm', 'R')
        wing_l = self.find('rm_wing', 'L')
        wing_r = self.find('rm_wing', 'R')

        self._resolved = dict(
            ROOT=root,
            TORSO=torso,
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

    def _clean_all(self, reset_root: bool = False):
        """Limpia la animacion de RetroMecha sin tocar animaciones externas."""
        root = self.mecha_root
        if not root or not mc.objExists(root):
            return

        removed_path = False
        try:
            mc.currentTime(0)
        except Exception:
            pass

        def _short_name(node: str) -> str:
            return node.split('|')[-1].split('.')[0]

        def _is_retro_anim_node(node: str) -> bool:
            try:
                short = _short_name(node)
                node_type = mc.nodeType(node)
            except Exception:
                return False
            return (
                short.startswith('rm_idle_')
                or short.startswith('rm_spin_')
                or short.startswith('rm_motionPath')
                or short.startswith('rm_flight_path')
                or node_type == 'motionPath'
                or node_type == 'unitConversion'
                or node_type == 'pairBlend'
                or node_type == 'blendWeighted'
                or node_type == 'addDoubleLinear'
                or node_type == 'multDoubleLinear'
                or node_type == 'expression'
                or node_type == 'animCurveTL'
                or node_type == 'animCurveTA'
                or node_type == 'animCurveTU'
            )

        def _delete_node(node: str):
            nonlocal removed_path
            if not node or not mc.objExists(node):
                return
            try:
                if mc.nodeType(node) == 'motionPath':
                    removed_path = True
                mc.delete(node)
            except Exception:
                pass

        # 1) Borra solo auxiliares creados por RetroMecha.
        for pattern in ('rm_flight_path*', 'rm_motionPath*', 'rm_look_target*',
                        'rm_lookPath*', 'rm_bobber*'):
            for obj in (mc.ls(pattern) or []):
                _delete_node(obj)

        for mp in (mc.listConnections(root, type='motionPath') or []):
            _delete_node(mp)

        def _upstream_anim_nodes(node: str) -> set:
            found = set()
            try:
                upstream = mc.listConnections(node, source=True, destination=False) or []
            except Exception:
                return found
            for src in upstream:
                if _is_retro_anim_node(src):
                    found.add(src)
            return found

        def _disconnect_destination(dest: str) -> set:
            source_plugs = set()
            try:
                src = mc.connectionInfo(dest, sourceFromDestination=True)
                if src:
                    source_plugs.add(src)
            except Exception:
                pass
            try:
                source_plugs.update(
                    mc.listConnections(dest, source=True, destination=False,
                                       plugs=True) or []
                )
            except Exception:
                pass

            source_nodes = set()
            for plug in source_plugs:
                node = plug.split('.', 1)[0]
                source_nodes.add(node)
                source_nodes.update(_upstream_anim_nodes(node))
                try:
                    mc.disconnectAttr(plug, dest)
                except Exception:
                    pass
            return source_nodes

        # 2) Desconecta cualquier control entrante sobre el root actual.
        root_attrs = (
            'tx', 'ty', 'tz', 'rx', 'ry', 'rz',
            'translateX', 'translateY', 'translateZ',
            'rotateX', 'rotateY', 'rotateZ',
            'translate', 'rotate',
        )
        for attr in root_attrs:
            for node in _disconnect_destination(f'{root}.{attr}'):
                if _is_retro_anim_node(node):
                    _delete_node(node)

        still_blocked = []
        for attr in root_attrs:
            dest = f'{root}.{attr}'
            try:
                if mc.connectionInfo(dest, isDestination=True):
                    still_blocked.append(dest)
            except Exception:
                pass
        if still_blocked:
            print('[RetroMecha][Anim] Limpieza fuerte: motionPath residual en root')
            for mp in (mc.ls(type='motionPath') or []):
                _delete_node(mp)
            for dest in still_blocked:
                for node in _disconnect_destination(dest):
                    if _is_retro_anim_node(node):
                        _delete_node(node)

        # 3) Keyframes del root.
        try:
            mc.cutKey(root, clear=True)
        except Exception:
            pass
        try:
            for node in set(self.resolve().values()):
                if node and node != root and mc.objExists(node):
                    mc.cutKey(node, clear=True)
        except Exception:
            pass

        # 4) Unlock basico para poder limpiar conexiones propias.
        for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz'):
            try:
                mc.setAttr(f'{root}.{a}', lock=False)
            except Exception:
                pass

        # 5) El root siempre vuelve a pose base; la escala se conserva.
        try:
            mc.xform(root, translation=(0, 0, 0), rotation=(0, 0, 0))
        except Exception as e:
            print(f'[RetroMecha] _clean_all xform error: {e}')
        for a in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz'):
            try:
                mc.setAttr(f'{root}.{a}', 0)
            except Exception as e:
                print(f'[RetroMecha] _clean_all setAttr {root}.{a} error: {e}')

        # 6) Expresiones conocidas.
        for expr in ('rm_idle_root', 'rm_idle_head',
                     'rm_idle_arm_L', 'rm_idle_arm_R',
                     'rm_idle_wing_L', 'rm_idle_wing_R', 'rm_idle_reactor',
                     'rm_spin_root', 'rm_spin_torso', 'rm_spin_head',
                     'rm_spin_arm_L', 'rm_spin_arm_R',
                     'rm_spin_wing_L', 'rm_spin_wing_R', 'rm_spin_reactor'):
            _delete_node(expr)

    # ── Helpers compartidos ──────────────────────────────

    def _find(self, name: str):
        """Busca un nodo por nombre exacto dentro del mecha actual."""
        found = mc.ls(name, type='transform', long=True)
        if not found:
            return None
        root_long = (mc.ls(self.mecha_root, long=True) or [self.mecha_root])[0]
        for node in found:
            if node == root_long or node.startswith(root_long + '|'):
                return node
        return found[0]

    def _short(self, node: str) -> str:
        return node.split('|')[-1]

    def _attr(self, node: str | None, attr: str, default: float = 0.0) -> float:
        if not node or not mc.objExists(node):
            return default
        try:
            return float(mc.getAttr(f'{node}.{attr}'))
        except Exception:
            return default

    def _clear_rotation_keys(self, node, attrs=('rx', 'ry', 'rz')):
        if not node or not mc.objExists(node):
            return
        for attr in attrs:
            try:
                mc.cutKey(node, at=attr, clear=True)
            except Exception:
                pass

    def _remove_expr(self, name: str):
        if mc.objExists(name):
            try:
                mc.delete(name)
            except Exception:
                pass

    def _build_reactor_expr(self) -> list:
        lines = []
        ring = self._find('rm_reactor_orb_ring_1')
        halo = self._find('rm_reactor_orb_halo_1')
        if ring:
            R = self._short(ring)
            ry = self._attr(ring, 'rotateY')
            lines.append(f'{R}.rotateY = {ry:.4f} + time * 55;')
        if halo:
            H = self._short(halo)
            hx = self._attr(halo, 'rotateX')
            hy = self._attr(halo, 'rotateY')
            lines.append(f'{H}.rotateY = {hy:.4f} + time * -35;')
            lines.append(f'{H}.rotateX = {hx:.4f} + sin(time*1.5)*12.0;')
        if lines:
            return lines

        glow = self._find('rm_reactor_column_glow_1')
        if glow:
            G = self._short(glow)
            sx = self._attr(glow, 'scaleX', 1.0)
            sy = self._attr(glow, 'scaleY', 1.0)
            sz = self._attr(glow, 'scaleZ', 1.0)
            lines.append(f'{G}.scaleY = {sy:.4f} + sin(time*2.0)*0.15;')
            lines.append(f'{G}.scaleX = {sx:.4f} + sin(time*2.0)*0.05;')
            lines.append(f'{G}.scaleZ = {sz:.4f} + sin(time*2.0)*0.05;')
            return lines

        outer = self._find('rm_reactor_outer_1')
        inner = self._find('rm_reactor_inner_1')
        core = self._find('rm_reactor_core_1')
        if outer:
            O = self._short(outer)
            oy = self._attr(outer, 'rotateY')
            lines.append(f'{O}.rotateY = {oy:.4f} + time * 55;')
        if inner:
            I = self._short(inner)
            iy = self._attr(inner, 'rotateY')
            lines.append(f'{I}.rotateY = {iy:.4f} + time * -35;')
        if core:
            C = self._short(core)
            sz = self._attr(core, 'scaleZ', 1.0)
            lines.append(f'{C}.scaleZ = {sz:.4f} + sin(time*1.5)*0.2;')
        return lines

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

    @abstractmethod
    def apply(self):
        """Aplica la animación al mecha."""

    @abstractmethod
    def remove(self):
        """Elimina toda la animación (keyframes + nodos auxiliares)."""
