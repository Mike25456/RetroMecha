import math

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from animations.base import BaseAnimation
from animations.registry import register_animation


@register_animation('spin')
class SpinAnimation(BaseAnimation):
    name = 'spin'

    FRAMES = 144
    _VARS = '''float $period = 6.0;
float $phase = (time % $period) / $period;
float $spin = sin($phase * 3.14159) * sin($phase * 3.14159);
float $spinY = $spin * 360.0;
float $impulse = sin($phase * 6.28318) * 8.0;
float $lookDown = $spin * -35.0;'''

    def _find(self, name: str):
        found = mc.ls(name, type='transform', long=True)
        return found[0] if found else None

    def _short(self, node: str) -> str:
        return node.split('|')[-1]

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
            lines.append(f'{R}.rotateY = time * 55;')
        if halo:
            H = self._short(halo)
            lines.append(f'{H}.rotateY = time * -35;')
            lines.append(f'{H}.rotateX = sin(time*1.5)*12.0;')
        if lines:
            return lines

        glow = self._find('rm_reactor_column_glow_1')
        if glow:
            G = self._short(glow)
            lines.append(f'{G}.scaleY = 1.0 + sin(time*2.0)*0.15;')
            lines.append(f'{G}.scaleX = 1.0 + sin(time*2.0)*0.05;')
            lines.append(f'{G}.scaleZ = 1.0 + sin(time*2.0)*0.05;')
            return lines

        outer = self._find('rm_reactor_outer_1')
        inner = self._find('rm_reactor_inner_1')
        core = self._find('rm_reactor_core_1')
        if outer:
            O = self._short(outer)
            lines.append(f'{O}.rotateY = time * 55;')
        if inner:
            I = self._short(inner)
            lines.append(f'{I}.rotateY = time * -35;')
        if core:
            C = self._short(core)
            lines.append(f'{C}.scaleZ = 1.0 + sin(time*1.5)*0.2;')
        return lines

    def apply(self):
        if not MAYA_AVAILABLE:
            return

        self._clean_all()

        ROOT = self.mecha_root
        ROOT_S = self._short(ROOT)
        HEAD = self._find('rm_head_1')
        TORSO = self._find('rm_torso_1')
        ARM_L = self._find('rm_arm_1')
        ARM_R = self._find('rm_arm_2')
        WING_L = self._find('rm_wing_1')
        WING_R = self._find('rm_wing_2')

        parts = []
        if HEAD: parts.append('HEAD')
        if TORSO: parts.append('TORSO')
        if ARM_L: parts.append('ARM_L')
        if ARM_R: parts.append('ARM_R')
        if WING_L: parts.append('WING_L')
        if WING_R: parts.append('WING_R')
        print(f'[RetroMecha][Spin] Partes encontradas: {parts}')

        for e in ('rm_spin_root', 'rm_spin_torso', 'rm_spin_head',
                  'rm_spin_arm_L', 'rm_spin_arm_R',
                  'rm_spin_wing_L', 'rm_spin_wing_R', 'rm_spin_reactor'):
            self._remove_expr(e)

        F = self.FRAMES
        mc.playbackOptions(min=0, max=F,
                           animationStartTime=0, animationEndTime=F)
        mc.currentTime(0)

        V = self._VARS

        # ── Root ──
        mc.expression(name='rm_spin_root', string=f'''{V}
{ROOT_S}.translateY = sin(time*1.1)*0.28 + sin(time*2.7)*0.05 + sin(time*0.4)*0.09;
{ROOT_S}.rotateY = $spinY;
{ROOT_S}.rotateZ = sin(time*0.9)*1.8 + sin(time*2.1)*0.4 + $impulse;
{ROOT_S}.rotateX = sin(time*0.7)*1.2 + sin(time*1.9)*0.3;''')

        # ── Torso ──
        if TORSO:
            T = self._short(TORSO)
            mc.expression(name='rm_spin_torso', string=f'''{V}
{T}.rotateZ = $impulse * 0.6;''')

        # ── Head ──
        if HEAD:
            H = self._short(HEAD)
            mc.expression(name='rm_spin_head', string=f'''{V}
{H}.rotateY = sin(time*0.38)*22.0 * (0.6 + sin(time*0.15)*0.4) * (1.0 - $spin);
{H}.rotateX = sin(time*0.55)*6.0 + $lookDown;
{H}.rotateZ = -{ROOT_S}.rotateZ * 0.5 + sin(time*1.3)*1.5;''')

        # ── Arms ──
        if ARM_L:
            A = self._short(ARM_L)
            mc.expression(name='rm_spin_arm_L', string=f'''{V}
{A}.rotateZ = sin(time*0.9 - 0.3)*4.0 + sin(time*1.8)*1.2 + $impulse * 1.5;
{A}.rotateX = sin(time*0.7)*2.5 + sin(time*2.2)*0.6;
{A}.rotateY = sin(time*0.5)*3.0 + $spin * 15.0;''')

        if ARM_R:
            A = self._short(ARM_R)
            mc.expression(name='rm_spin_arm_R', string=f'''{V}
{A}.rotateZ = sin(time*0.95 - 0.3)*-4.0 + sin(time*1.9)*-1.2 + $impulse * 1.5;
{A}.rotateX = sin(time*0.75)*2.5 + sin(time*2.0)*0.6;
{A}.rotateY = sin(time*0.55)*-3.0 + $spin * 15.0;''')

        # ── Wings ──
        if WING_L:
            W = self._short(WING_L)
            mc.expression(name='rm_spin_wing_L', string=f'''{V}
{W}.rotateZ = sin(time*1.1)*3.5 + {ROOT_S}.rotateZ*0.3 + $spin * 20.0;
{W}.rotateX = sin(time*0.8)*2.0 + sin(time*2.4)*0.5;
{W}.rotateY = sin(time*0.6)*2.5;''')

        if WING_R:
            W = self._short(WING_R)
            mc.expression(name='rm_spin_wing_R', string=f'''{V}
{W}.rotateZ = sin(time*1.1)*-3.5 + {ROOT_S}.rotateZ*0.3 - $spin * 20.0;
{W}.rotateX = sin(time*0.8)*2.0 + sin(time*2.4)*0.5;
{W}.rotateY = sin(time*0.6)*-2.5;''')

        # ── Reactor ──
        reactor_lines = self._build_reactor_expr()
        if reactor_lines:
            mc.expression(name='rm_spin_reactor', string='\n'.join(reactor_lines))

        print('[RetroMecha][Spin] Expresiones aplicadas')

    def remove(self):
        if not MAYA_AVAILABLE:
            return

        mc.playbackOptions(min=0, max=self.FRAMES,
                           animationStartTime=0, animationEndTime=self.FRAMES)
        mc.currentTime(0)

        for e in ('rm_spin_root', 'rm_spin_torso', 'rm_spin_head',
                  'rm_spin_arm_L', 'rm_spin_arm_R',
                  'rm_spin_wing_L', 'rm_spin_wing_R', 'rm_spin_reactor'):
            self._remove_expr(e)

        ROOT = self.mecha_root
        HEAD = self._find('rm_head_1')
        TORSO = self._find('rm_torso_1')
        ARM_L = self._find('rm_arm_1')
        ARM_R = self._find('rm_arm_2')
        WING_L = self._find('rm_wing_1')
        WING_R = self._find('rm_wing_2')

        if ROOT and mc.objExists(ROOT):
            mc.cutKey(ROOT, clear=True)
            mc.xform(ROOT, translation=(0, 0, 0), rotation=(0, 0, 0))
            mc.setAttr(f'{ROOT}.sx', 1)
            mc.setAttr(f'{ROOT}.sy', 1)
            mc.setAttr(f'{ROOT}.sz', 1)

        if HEAD: self._reset_rotation(HEAD)
        if TORSO: self._reset_rotation(TORSO)
        if ARM_L: self._reset_rotation(ARM_L)
        if ARM_R: self._reset_rotation(ARM_R)
        if WING_L: self._reset_rotation(WING_L)
        if WING_R: self._reset_rotation(WING_R)

        print('[RetroMecha][Spin] Animacion eliminada')
