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

    def apply(self):
        if not MAYA_AVAILABLE:
            return

        self._clean_all()

        rig = self.resolve()
        ROOT = rig.get('ROOT') or self.mecha_root
        ROOT_S = self._short(ROOT)
        HEAD = rig.get('HEAD')
        TORSO = rig.get('TORSO')
        ARM_L = rig.get('ARM_L')
        ARM_R = rig.get('ARM_R')
        WING_L = rig.get('WING_L')
        WING_R = rig.get('WING_R')

        parts = []
        if HEAD: parts.append('HEAD')
        if TORSO: parts.append('TORSO')
        if ARM_L: parts.append('ARM_L')
        if ARM_R: parts.append('ARM_R')
        if WING_L: parts.append('WING_L')
        if WING_R: parts.append('WING_R')
        print(f'[RetroMecha][Spin] Partes encontradas: {parts}')

        F = self.FRAMES
        mc.playbackOptions(min=0, max=F,
                           animationStartTime=0, animationEndTime=F)
        mc.currentTime(0)

        V = self._VARS

        root_ty = self._attr(ROOT, 'translateY')
        root_rx = self._attr(ROOT, 'rotateX')
        root_ry = self._attr(ROOT, 'rotateY')
        root_rz = self._attr(ROOT, 'rotateZ')
        mc.expression(name='rm_spin_root', string=f'''{V}
{ROOT_S}.translateY = {root_ty:.4f} + sin(time*1.1)*0.28 + sin(time*2.7)*0.05 + sin(time*0.4)*0.09;
{ROOT_S}.rotateY = {root_ry:.4f} + $spinY;
{ROOT_S}.rotateZ = {root_rz:.4f} + sin(time*0.9)*1.8 + sin(time*2.1)*0.4 + $impulse;
{ROOT_S}.rotateX = {root_rx:.4f} + sin(time*0.7)*1.2 + sin(time*1.9)*0.3;''')

        if TORSO:
            T = self._short(TORSO)
            tz = self._attr(TORSO, 'rotateZ')
            mc.expression(name='rm_spin_torso', string=f'''{V}
{T}.rotateZ = {tz:.4f} + $impulse * 0.6;''')

        if HEAD:
            H = self._short(HEAD)
            hx = self._attr(HEAD, 'rotateX')
            hy = self._attr(HEAD, 'rotateY')
            hz = self._attr(HEAD, 'rotateZ')
            mc.expression(name='rm_spin_head', string=f'''{V}
{H}.rotateY = {hy:.4f} + sin(time*0.38)*22.0 * (0.6 + sin(time*0.15)*0.4) * (1.0 - $spin);
{H}.rotateX = {hx:.4f} + sin(time*0.55)*6.0 + $lookDown;
{H}.rotateZ = {hz:.4f} - ({ROOT_S}.rotateZ - {root_rz:.4f}) * 0.5 + sin(time*1.3)*1.5;''')

        if ARM_L:
            A = self._short(ARM_L)
            ax = self._attr(ARM_L, 'rotateX')
            ay = self._attr(ARM_L, 'rotateY')
            az = self._attr(ARM_L, 'rotateZ')
            mc.expression(name='rm_spin_arm_L', string=f'''{V}
{A}.rotateZ = {az:.4f} + sin(time*0.9 - 0.3)*4.0 + sin(time*1.8)*1.2 + $impulse * 1.5;
{A}.rotateX = {ax:.4f} + sin(time*0.7)*2.5 + sin(time*2.2)*0.6;
{A}.rotateY = {ay:.4f} + sin(time*0.5)*3.0 + $spin * 15.0;''')

        if ARM_R:
            A = self._short(ARM_R)
            ax = self._attr(ARM_R, 'rotateX')
            ay = self._attr(ARM_R, 'rotateY')
            az = self._attr(ARM_R, 'rotateZ')
            mc.expression(name='rm_spin_arm_R', string=f'''{V}
{A}.rotateZ = {az:.4f} + sin(time*0.95 - 0.3)*-4.0 + sin(time*1.9)*-1.2 + $impulse * 1.5;
{A}.rotateX = {ax:.4f} + sin(time*0.75)*2.5 + sin(time*2.0)*0.6;
{A}.rotateY = {ay:.4f} + sin(time*0.55)*-3.0 + $spin * 15.0;''')

        if WING_L:
            W = self._short(WING_L)
            wx = self._attr(WING_L, 'rotateX')
            wy = self._attr(WING_L, 'rotateY')
            wz = self._attr(WING_L, 'rotateZ')
            mc.expression(name='rm_spin_wing_L', string=f'''{V}
{W}.rotateZ = {wz:.4f} + sin(time*1.1)*3.5 + ({ROOT_S}.rotateZ - {root_rz:.4f}) * 0.3 + $spin * 20.0;
{W}.rotateX = {wx:.4f} + sin(time*0.8)*2.0 + sin(time*2.4)*0.5;
{W}.rotateY = {wy:.4f} + sin(time*0.6)*2.5;''')

        if WING_R:
            W = self._short(WING_R)
            wx = self._attr(WING_R, 'rotateX')
            wy = self._attr(WING_R, 'rotateY')
            wz = self._attr(WING_R, 'rotateZ')
            mc.expression(name='rm_spin_wing_R', string=f'''{V}
{W}.rotateZ = {wz:.4f} + sin(time*1.1)*-3.5 + ({ROOT_S}.rotateZ - {root_rz:.4f}) * 0.3 - $spin * 20.0;
{W}.rotateX = {wx:.4f} + sin(time*0.8)*2.0 + sin(time*2.4)*0.5;
{W}.rotateY = {wy:.4f} + sin(time*0.6)*-2.5;''')

        reactor_lines = self._build_reactor_expr()
        if reactor_lines:
            mc.expression(name='rm_spin_reactor', string='\n'.join(reactor_lines))

        print('[RetroMecha][Spin] Expresiones aplicadas')

    def remove(self):
        if not MAYA_AVAILABLE:
            return

        self._clean_all()

        mc.playbackOptions(min=0, max=self.FRAMES,
                           animationStartTime=0, animationEndTime=self.FRAMES)
        mc.currentTime(0)

        print('[RetroMecha][Spin] Animacion eliminada')
