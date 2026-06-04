try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from animations.base import BaseAnimation
from animations.registry import register_animation


@register_animation('charge')
class ChargeAnimation(BaseAnimation):
    name = 'charge'

    FRAMES = 150
    _VARS = '''float $period  = 5.0;
float $phase   = (time % $period) / $period;
float $raw     = sin($phase * 3.14159);
float $charge  = $raw * $raw;
float $tremor  = sin(time * 18.0) * $charge * 0.55
               + sin(time * 27.3) * $charge * 0.25
               + sin(time * 41.7) * $charge * 0.10;
float $breathe = sin(time * 0.85) * 0.18 + sin(time * 2.1) * 0.04;'''

    def apply(self):
        if not MAYA_AVAILABLE:
            return

        self._clean_all()

        rig = self.resolve()
        ROOT = rig.get('ROOT') or self.mecha_root
        ROOT_S = self._short(ROOT)
        HEAD = rig.get('HEAD')
        ARM_L = rig.get('ARM_L')
        ARM_R = rig.get('ARM_R')
        WING_L = rig.get('WING_L')
        WING_R = rig.get('WING_R')

        parts = []
        if HEAD: parts.append('HEAD')
        if ARM_L: parts.append('ARM_L')
        if ARM_R: parts.append('ARM_R')
        if WING_L: parts.append('WING_L')
        if WING_R: parts.append('WING_R')
        print(f'[RetroMecha][Charge] Partes encontradas: {parts}')

        F = self.FRAMES
        mc.playbackOptions(min=0, max=F,
                           animationStartTime=0, animationEndTime=F)
        mc.currentTime(0)

        V = self._VARS

        root_ty = self._attr(ROOT, 'translateY')
        root_rx = self._attr(ROOT, 'rotateX')
        root_rz = self._attr(ROOT, 'rotateZ')
        root_ry = self._attr(ROOT, 'rotateY')
        mc.expression(name='rm_charge_root', string=f'''{V}
{ROOT_S}.translateY = {root_ty:.4f} + $breathe + $charge * 1.20 + $tremor * 0.12;
{ROOT_S}.rotateX = {root_rx:.4f} + $charge * -14.0 + sin(time * 0.6) * 1.0 * (1.0 - $charge) + $tremor * 0.8;
{ROOT_S}.rotateZ = {root_rz:.4f} + sin(time * 0.9) * 1.2 * (1.0 - $charge * 0.7) + $tremor * 0.6;
{ROOT_S}.rotateY = {root_ry:.4f} + sin(time * 0.22) * 4.0 * (1.0 - $charge);''')

        if HEAD:
            H = self._short(HEAD)
            hx = self._attr(HEAD, 'rotateX')
            hy = self._attr(HEAD, 'rotateY')
            hz = self._attr(HEAD, 'rotateZ')
            mc.expression(name='rm_charge_head', string=f'''{V}
{H}.rotateX = {hx:.4f} + $charge * -22.0 + sin(time * 0.55) * 5.0 * (1.0 - $charge) + $tremor * 1.2;
{H}.rotateY = {hy:.4f} + sin(time * 0.38) * 18.0 * (1.0 - $charge * 0.85);
{H}.rotateZ = {hz:.4f} + $tremor * 0.9;''')

        if ARM_L:
            A = self._short(ARM_L)
            ax = self._attr(ARM_L, 'rotateX')
            az = self._attr(ARM_L, 'rotateZ')
            mc.expression(name='rm_charge_arm_L', string=f'''{V}
{A}.rotateZ = {az:.4f} + sin(time * 0.9) * 3.5 * (1.0 - $charge * 0.6) + $charge * 28.0 + $tremor * 1.4;
{A}.rotateX = {ax:.4f} + $charge * -18.0 + sin(time * 0.7) * 2.0 * (1.0 - $charge) + $tremor * 1.0;''')

        if ARM_R:
            A = self._short(ARM_R)
            ax = self._attr(ARM_R, 'rotateX')
            az = self._attr(ARM_R, 'rotateZ')
            mc.expression(name='rm_charge_arm_R', string=f'''{V}
{A}.rotateZ = {az:.4f} + sin(time * 0.95) * -3.5 * (1.0 - $charge * 0.6) + $charge * -28.0 + $tremor * -1.4;
{A}.rotateX = {ax:.4f} + $charge * -18.0 + sin(time * 0.75) * 2.0 * (1.0 - $charge) + $tremor * 1.0;''')

        if WING_L:
            W = self._short(WING_L)
            wx = self._attr(WING_L, 'rotateX')
            wz = self._attr(WING_L, 'rotateZ')
            mc.expression(name='rm_charge_wing_L', string=f'''{V}
{W}.rotateZ = {wz:.4f} + sin(time * 1.1) * 2.5 * (1.0 - $charge * 0.5) + $charge * 35.0 + $tremor * 1.8;
{W}.rotateX = {wx:.4f} + $charge * -12.0 + sin(time * 0.8) * 1.5 * (1.0 - $charge) + $tremor * 0.8;''')

        if WING_R:
            W = self._short(WING_R)
            wx = self._attr(WING_R, 'rotateX')
            wz = self._attr(WING_R, 'rotateZ')
            mc.expression(name='rm_charge_wing_R', string=f'''{V}
{W}.rotateZ = {wz:.4f} + sin(time * 1.1) * -2.5 * (1.0 - $charge * 0.5) + $charge * -35.0 + $tremor * -1.8;
{W}.rotateX = {wx:.4f} + $charge * -12.0 + sin(time * 0.8) * 1.5 * (1.0 - $charge) + $tremor * 0.8;''')

        reactor_lines = self._build_reactor_expr()
        if reactor_lines:
            mc.expression(name='rm_charge_reactor', string='\n'.join(reactor_lines))

        print('[RetroMecha][Charge] Expresiones aplicadas')

    def remove(self):
        if not MAYA_AVAILABLE:
            return

        self._clean_all()

        mc.playbackOptions(min=0, max=self.FRAMES,
                           animationStartTime=0, animationEndTime=self.FRAMES)
        mc.currentTime(0)
        self._reset_root_channels()

        print('[RetroMecha][Charge] Animacion eliminada')
