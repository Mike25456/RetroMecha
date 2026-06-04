import math

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

from animations.base import BaseAnimation
from animations.registry import register_animation


@register_animation('flight')
class FlightAnimation(BaseAnimation):
    name = 'flight'

    def apply(self):
        if not MAYA_AVAILABLE:
            return

        self._clean_all(reset_root=True)

        rig = self.resolve()
        ROOT = rig.get('ROOT') or self.mecha_root
        HEAD = rig.get('HEAD')
        ARM_L = rig.get('ARM_L')
        ARM_R = rig.get('ARM_R')
        WING_L = rig.get('WING_L')
        WING_R = rig.get('WING_R')

        parts = {'HEAD': HEAD, 'ARM_L': ARM_L, 'ARM_R': ARM_R,
                 'WING_L': WING_L, 'WING_R': WING_R}
        found = [k for k, v in parts.items() if v is not None]
        print(f'[RetroMecha][Flight] Partes encontradas: {found}')

        FPS      = 24
        DURATION = 8
        FRAMES   = DURATION * FPS

        if HEAD: self._reset_rotation(HEAD, ('rx', 'ry'))
        if ARM_L: self._reset_rotation(ARM_L, ('rx', 'rz'))
        if ARM_R: self._reset_rotation(ARM_R, ('rx', 'rz'))
        if WING_L: self._reset_rotation(WING_L, ('rz',))
        if WING_R: self._reset_rotation(WING_R, ('rz',))
        if HEAD:
            for con in (mc.listRelatives(HEAD, type='aimConstraint') or []):
                try:
                    mc.delete(con)
                except Exception:
                    pass

        # ── Curva figura 8 (escalada al tamaño del mecha) ──
        bb = mc.exactWorldBoundingBox(ROOT)
        mh = bb[4] - bb[1]   # alto del mecha
        mw = bb[3] - bb[0]   # ancho
        sz = max(mh, mw, bb[5] - bb[2])
        sf = max(sz / 3.0, 0.7)   # escala proporcional, mínimo 0.7

        X_AMP   = 7.0 * sf
        Y_AMP   = 3.5 * sf
        Y_OFF   = Y_AMP + mh * 0.5 + 0.5
        Z_AMP   = 3.5 * sf

        points = []
        STEPS  = 64
        W      = (2 * math.pi) / DURATION

        for i in range(STEPS + 1):
            t  = (i / STEPS) * DURATION
            px = math.sin(W * t) * X_AMP
            py = math.sin(W * 2 * t) * Y_AMP + Y_OFF
            pz = math.sin(W * 2 * t) * Z_AMP
            points.append((px, py, pz))

        points[-1] = points[0]
        curve = mc.curve(d=3, p=points, name='rm_flight_path')
        mc.closeCurve(curve, ch=False, replaceOriginal=True)
        mc.hide(curve)

        mc.playbackOptions(min=1, max=FRAMES,
                           animationStartTime=1, animationEndTime=FRAMES)

        mp = mc.pathAnimation(
            ROOT, curve,
            name='rm_motionPath',
            fractionMode=True,
            follow=True,
            followAxis='y',
            upAxis='z',
            inverseUp=True,
            inverseFront=False,
            bank=True,
            bankScale=1.4,
            bankThreshold=90,
            startTimeU=1,
            endTimeU=FRAMES,
        )

        # ── Bobbing (offsetY) ───────────────────────────
        BOB_AMP  = 0.45
        BOB_FREQ = 1.75

        mc.cutKey(mp, at='offsetY', clear=True)
        bob_keys = []
        for f in range(1, FRAMES + 1):
            t   = (f - 1) / FPS
            bob = math.sin(t * BOB_FREQ) * BOB_AMP
            bob += math.sin(t * BOB_FREQ * 2.3) * (BOB_AMP * 0.25)
            bob_keys.append((f, bob))

        for f, v in bob_keys:
            mc.setKeyframe(mp, at='offsetY', t=f, v=v)

        mc.setKeyframe(mp, at='offsetY', t=FRAMES, v=bob_keys[0][1])
        mc.keyTangent(mp, at='offsetY', itt='flat', ott='flat')

        # ── FrontTwist cíclico ──────────────────────────
        TWIST_FRAMES = [45, 140]
        RAMP_FRAMES  = 25

        mc.cutKey(mp, at='frontTwist', clear=True)
        accumulated = 0.0
        prev_key_f  = None

        for twist_f in TWIST_FRAMES:
            ramp_start = twist_f - RAMP_FRAMES
            if prev_key_f is None or ramp_start - 1 > prev_key_f:
                mc.setKeyframe(mp, at='frontTwist', t=ramp_start - 1, v=accumulated)
            mc.setKeyframe(mp, at='frontTwist', t=ramp_start, v=accumulated)
            accumulated += 180.0
            mc.setKeyframe(mp, at='frontTwist', t=twist_f, v=accumulated)
            prev_key_f = twist_f

        mc.setKeyframe(mp, at='frontTwist', t=FRAMES, v=360.0)
        mc.keyTangent(mp, at='frontTwist', itt='flat', ott='flat')
        for twist_f in TWIST_FRAMES:
            mc.keyTangent(mp, at='frontTwist', t=(twist_f - RAMP_FRAMES,), ott='linear')
            mc.keyTangent(mp, at='frontTwist', t=(twist_f,), itt='linear')
        mc.keyTangent(mp, at='frontTwist', t=(FRAMES,), itt='linear')

        # ── Cabeza ──────────────────────────────────────
        if HEAD:
            for twist_f in TWIST_FRAMES:
                mc.setKeyframe(HEAD, at='rotateY', t=twist_f - 20, v=0.0)
                mc.setKeyframe(HEAD, at='rotateY', t=twist_f - 8, v=25.0)
                mc.setKeyframe(HEAD, at='rotateY', t=twist_f + 12, v=0.0)
            mc.setKeyframe(HEAD, at='rotateY', t=1, v=0.0)
            mc.setKeyframe(HEAD, at='rotateY', t=FRAMES, v=0.0)
            mc.keyTangent(HEAD, at='rotateY', itt='flat', ott='flat')

            head_pitch = [
                (1, 0.0), (20, -7.0), (45, 9.0), (70, -5.0),
                (97, 4.0), (122, -5.0), (140, 9.0), (165, -7.0),
                (192, 0.0),
            ]
            for f, v in head_pitch:
                mc.setKeyframe(HEAD, at='rotateX', t=f, v=v)
            mc.keyTangent(HEAD, at='rotateX', itt='flat', ott='flat')

        # ── Alas ────────────────────────────────────────
        def _wing_val(t, side):
            curve_factor = abs(math.sin(math.pi * t / 4.0))
            flap_freq = 4.5 + 2.0 * (1.0 - curve_factor)
            wing_flap = math.sin(t * flap_freq) * 2.2
            extra_open = 5.0 * curve_factor
            return 28.0 + extra_open + wing_flap if side == 'L' else -28.0 - extra_open - wing_flap

        if WING_L or WING_R:
            for f in range(1, FRAMES + 1):
                t = 0.0 if f == FRAMES else (f - 1) / FPS
                if WING_L:
                    mc.setKeyframe(WING_L, at='rotateZ', t=f, v=_wing_val(t, 'L'))
                if WING_R:
                    mc.setKeyframe(WING_R, at='rotateZ', t=f, v=_wing_val(t, 'R'))

        # ── Brazos ──────────────────────────────────────
        arm_keys = [
            (1, 12.0, -12.0, -4.0),
            (20, 20.0, -20.0, -9.0),
            (45, 40.0, -40.0, -20.0),
            (65, 15.0, -15.0, -7.0),
            (97, 8.0, -8.0, -2.0),
            (122, 20.0, -20.0, -9.0),
            (140, 40.0, -40.0, -20.0),
            (162, 15.0, -15.0, -7.0),
            (192, 12.0, -12.0, -4.0),
        ]
        if ARM_L or ARM_R:
            for frame, rz_l, rz_r, rx in arm_keys:
                if ARM_L:
                    mc.setKeyframe(ARM_L, at='rotateZ', t=frame, v=rz_l)
                    mc.setKeyframe(ARM_L, at='rotateX', t=frame, v=rx)
                if ARM_R:
                    mc.setKeyframe(ARM_R, at='rotateZ', t=frame, v=rz_r)
                    mc.setKeyframe(ARM_R, at='rotateX', t=frame, v=rx)

        if ARM_L:
            mc.keyTangent(ARM_L, at='rotateZ', itt='flat', ott='flat')
            mc.keyTangent(ARM_L, at='rotateX', itt='flat', ott='flat')
        if ARM_R:
            mc.keyTangent(ARM_R, at='rotateZ', itt='flat', ott='flat')
            mc.keyTangent(ARM_R, at='rotateX', itt='flat', ott='flat')

        print(f'[RetroMecha][Flight] {FRAMES} frames aplicados')

    def remove(self):
        if not MAYA_AVAILABLE:
            return
        self._clean_all(reset_root=True)
        mc.currentTime(0)

        rig = self.resolve()
        HEAD = rig.get('HEAD')
        ARM_L = rig.get('ARM_L')
        ARM_R = rig.get('ARM_R')
        WING_L = rig.get('WING_L')
        WING_R = rig.get('WING_R')

        if HEAD: self._reset_rotation(HEAD, ('rx', 'ry'))
        if ARM_L: self._reset_rotation(ARM_L, ('rx', 'rz'))
        if ARM_R: self._reset_rotation(ARM_R, ('rx', 'rz'))
        if WING_L: self._reset_rotation(WING_L, ('rz',))
        if WING_R: self._reset_rotation(WING_R, ('rz',))
        self._reset_root_channels()

        print('[RetroMecha][Flight] Animacion eliminada')
