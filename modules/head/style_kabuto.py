try:
    import maya.cmds as mc
except ImportError:
    mc = None

from modules.head._shared import finish, HeadTune

import math


def _taper_verts(mesh, y_min, y_max, scale_bot, scale_top):
    bb = mc.exactWorldBoundingBox(mesh)
    cx = (bb[0] + bb[3]) * 0.5
    cz = (bb[2] + bb[5]) * 0.5
    span = y_max - y_min or 1.0
    for v in mc.ls(f'{mesh}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = max(0.0, min(1.0, (pos[1] - y_min) / span))
        s = scale_bot + (scale_top - scale_bot) * t
        mc.move(cx + (pos[0] - cx) * s, pos[1],
                cz + (pos[2] - cz) * s, v, ws=True)


def _build_hachi(aggr, s):
    hachi = mc.polyCube(
        w=(0.78 + aggr * 0.16) * s,
        h=(0.62 + aggr * 0.14) * s,
        d=(0.82 + aggr * 0.18) * s,
        sx=5, sy=5, sz=5,
        name='rm_kabuto_hachi_#',
    )[0]
    mc.move(0, (0.52 + aggr * 0.08) * s, 0, hachi, relative=True)

    bb = mc.exactWorldBoundingBox(hachi)
    for v in mc.ls(f'{hachi}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = (pos[1] - bb[1]) / ((bb[4] - bb[1]) or 1.0)
        if t > 0.55:
            taper = 1.0 - (t - 0.55) / 0.45 * (0.52 + aggr * 0.12)
            cx = (bb[0] + bb[3]) * 0.5
            cz = (bb[2] + bb[5]) * 0.5
            mc.move(cx + (pos[0] - cx) * taper, pos[1],
                    cz + (pos[2] - cz) * taper, v, ws=True)

    bb2 = mc.exactWorldBoundingBox(hachi)
    for v in mc.ls(f'{hachi}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        cz = (bb2[2] + bb2[5]) * 0.5
        if pos[2] > cz:
            t_z = (pos[2] - cz) / ((bb2[5] - cz) or 1.0)
            t_y = (pos[1] - bb2[1]) / ((bb2[4] - bb2[1]) or 1.0)
            bulge = t_z * (1.0 - t_y) * 0.06 * s
            mc.move(pos[0], pos[1], pos[2] + bulge, v, ws=True)

    finish(hachi, 0.045, hard=True)
    return hachi


def _build_shikoro(aggr, s, plate_count=4):
    parts = []
    y_start = (0.18 + aggr * 0.04) * s
    y_step  = -(0.14 + aggr * 0.02) * s
    z_back  = -(0.22 + aggr * 0.06) * s

    for i in range(plate_count):
        t = i / max(plate_count - 1, 1)
        pw = (0.88 + t * 0.18 + aggr * 0.14) * s
        ph = (0.055 + aggr * 0.008) * s
        pd = (0.52 + t * 0.12 + aggr * 0.10) * s
        py = y_start + i * y_step
        pz = z_back - t * 0.06 * s

        plate = mc.polyCube(
            w=pw, h=ph, d=pd,
            sx=4, sy=1, sz=2,
            name=f'rm_kabuto_shikoro_{i}_#',
        )[0]
        mc.move(0, py, pz, plate, relative=True)
        mc.rotate(-(6 + t * 8), 0, 0, plate)

        for v in mc.ls(f'{plate}.vtx[*]', flatten=True) or []:
            pos = mc.pointPosition(v, w=True)
            bb  = mc.exactWorldBoundingBox(plate)
            cx  = (bb[0] + bb[3]) * 0.5
            dist = abs(pos[0] - cx) / (pw * 0.5 or 1.0)
            mc.move(pos[0], pos[1] - dist * 0.018 * s, pos[2], v, ws=True)

        finish(plate, 0.010, hard=True)
        parts.append(plate)

    return parts


def _build_fukigaeshi(aggr, s):
    parts = []
    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        sx = side * (0.40 + aggr * 0.10) * s
        fuki = mc.polyCube(
            w=(0.10 + aggr * 0.04) * s,
            h=(0.28 + aggr * 0.08) * s,
            d=(0.32 + aggr * 0.08) * s,
            sx=1, sy=2, sz=2,
            name=f'rm_kabuto_armor_fukigaeshi_{label}_#',
        )[0]
        mc.move(sx, (0.58 + aggr * 0.08) * s, (0.16 + aggr * 0.04) * s,
                fuki, relative=True)
        mc.rotate(0, side * -32, side * 18, fuki)
        finish(fuki, 0.022, hard=True)
        parts.append(fuki)
    return parts


def _build_mengu(aggr, s):
    parts = []

    mengu = mc.polyCube(
        w=(0.62 + aggr * 0.14) * s,
        h=(0.42 + aggr * 0.10) * s,
        d=(0.14 + aggr * 0.04) * s,
        sx=3, sy=3, sz=1,
        name='rm_kabuto_armor_mengu_#',
    )[0]
    mc.move(0, -(0.08 + aggr * 0.02) * s, (0.32 + aggr * 0.06) * s,
            mengu, relative=True)

    bb = mc.exactWorldBoundingBox(mengu)
    for v in mc.ls(f'{mengu}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = 1.0 - (pos[1] - bb[1]) / ((bb[4] - bb[1]) or 1.0)
        if t > 0.5:
            taper = 1.0 - (t - 0.5) * (0.60 + aggr * 0.18)
            cx = (bb[0] + bb[3]) * 0.5
            mc.move(cx + (pos[0] - cx) * taper, pos[1], pos[2], v, ws=True)

    finish(mengu, 0.028, hard=True)
    parts.append(mengu)

    for i in range(3):
        t = (i + 0.5) / 3
        vent_y = -(0.16 + t * 0.18 + aggr * 0.04) * s
        vent = mc.polyCube(
            w=(0.34 - t * 0.10 + aggr * 0.06) * s,
            h=0.018 * s,
            d=0.022 * s,
            name=f'rm_kabuto_mengu_vent_{i}_#',
        )[0]
        mc.move(0, vent_y, (0.38 + aggr * 0.06) * s, vent, relative=True)
        finish(vent, 0.004, hard=True)
        parts.append(vent)

    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        hinge = mc.polyCylinder(
            r=0.030 * s, h=0.055 * s,
            sa=6, name=f'rm_kabuto_mengu_hinge_{label}_#',
        )[0]
        mc.rotate(0, 0, 90, hinge)
        mc.move(side * (0.32 + aggr * 0.08) * s,
                (0.04 + aggr * 0.01) * s,
                (0.30 + aggr * 0.06) * s, hinge, relative=True)
        finish(hinge, 0.0, hard=True)
        parts.append(hinge)

    return parts


def _build_mabisashi(aggr, s):
    vis = mc.polyCube(
        w=(0.72 + aggr * 0.16) * s,
        h=(0.08 + aggr * 0.02) * s,
        d=(0.22 + aggr * 0.06) * s,
        sx=4, sy=1, sz=2,
        name='rm_kabuto_mabisashi_#',
    )[0]
    mc.move(0, (0.22 + aggr * 0.04) * s, (0.36 + aggr * 0.08) * s,
            vis, relative=True)
    mc.rotate(-14, 0, 0, vis)

    for v in mc.ls(f'{vis}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        bb  = mc.exactWorldBoundingBox(vis)
        cx  = (bb[0] + bb[3]) * 0.5
        dist = 1.0 - abs(pos[0] - cx) / ((bb[3] - bb[0]) * 0.5 or 1.0)
        mc.move(pos[0], pos[1], pos[2] + dist * 0.030 * s, v, ws=True)

    finish(vis, 0.014, hard=True)
    return vis


def _build_body_group(aggr, s, shikoro_count):
    parts = [
        _build_hachi(aggr, s),
        _build_mabisashi(aggr, s),
        *_build_fukigaeshi(aggr, s),
        *_build_shikoro(aggr, s, shikoro_count),
        *_build_mengu(aggr, s),
    ]
    return parts


def _build_eyes_group(aggr, s, d_mul, eye_mul):
    parts = []
    eye_r  = (0.10 + aggr * 0.04) * s * eye_mul
    eye_y  = (0.16 + aggr * 0.02) * s
    eye_z  = (0.40 + aggr * 0.06) * s
    eye_xo = (0.18 + aggr * 0.04) * s

    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        ex = side * eye_xo

        socket = mc.polyCylinder(
            r=eye_r * 1.18, h=0.022 * s,
            sa=12, name=f'rm_kabuto_eye_socket_{label}_#',
        )[0]
        mc.rotate(90, 0, 0, socket)
        mc.move(ex, eye_y, eye_z, socket, relative=True)
        finish(socket, 0.008, hard=True)
        parts.append(socket)

        outer = mc.polyTorus(
            r=eye_r * 0.88,
            sr=eye_r * 0.14 * d_mul,
            sa=18, sh=4,
            name=f'rm_kabuto_eye_outer_{label}_#',
        )[0]
        mc.rotate(90, 0, 0, outer)
        mc.move(ex, eye_y, eye_z + 0.008 * s, outer, relative=True)
        finish(outer, 0.0, hard=True)
        parts.append(outer)

        inner = mc.polyTorus(
            r=eye_r * 0.52,
            sr=eye_r * 0.090 * d_mul,
            sa=14, sh=4,
            name=f'rm_kabuto_eye_inner_{label}_#',
        )[0]
        mc.rotate(90, 0, 0, inner)
        mc.move(ex, eye_y, eye_z + 0.012 * s, inner, relative=True)
        finish(inner, 0.0)
        parts.append(inner)

        lens = mc.polySphere(
            r=eye_r * 0.44, sa=10, sh=6,
            name=f'rm_kabuto_eye_lens_{label}_#',
        )[0]
        mc.scale(1.0, 1.0, 0.38, lens)
        mc.move(ex, eye_y, eye_z + 0.014 * s, lens, relative=True)
        finish(lens, 0.0)
        parts.append(lens)

        for i in range(3):
            angle = math.radians(i * 60 + 30)
            seg_x = ex + math.cos(angle) * eye_r * 0.76
            seg_y = eye_y + math.sin(angle) * eye_r * 0.76
            seg = mc.polyCube(
                w=0.014 * d_mul * s,
                h=eye_r * 0.28,
                d=0.010 * d_mul * s,
                name=f'rm_kabuto_eye_seg_{label}_{i}_#',
            )[0]
            mc.move(seg_x, seg_y, eye_z + 0.016 * s, seg, relative=True)
            mc.rotate(0, 0, math.degrees(angle), seg)
            finish(seg, 0.003, hard=True)
            parts.append(seg)

    return parts


def _build_crest_group(aggr, s, d_mul):
    parts = []
    crest_y = (0.82 + aggr * 0.14) * s

    for side, label in ((-1.0, 'l'), (1.0, 'r')):
        kuw = mc.polyCube(
            w=(0.055 + aggr * 0.016) * s,
            h=(0.58 + aggr * 0.18) * s,
            d=(0.12 + aggr * 0.04) * s,
            sx=1, sy=5, sz=1,
            name=f'rm_kabuto_kuwagata_{label}_#',
        )[0]
        mc.move(side * (0.22 + aggr * 0.06) * s,
                crest_y + (0.28 + aggr * 0.08) * s,
                (0.06 + aggr * 0.02) * s, kuw, relative=True)
        mc.rotate(0, 0, side * -18, kuw)

        bb = mc.exactWorldBoundingBox(kuw)
        for v in mc.ls(f'{kuw}.vtx[*]', flatten=True) or []:
            pos = mc.pointPosition(v, w=True)
            t = (pos[1] - bb[1]) / ((bb[4] - bb[1]) or 1.0)
            if t > 0.5:
                lean = (t - 0.5) * 2.0 * side * -(0.14 + aggr * 0.06) * s
                mc.move(pos[0] + lean, pos[1], pos[2], v, ws=True)

        finish(kuw, 0.014, hard=True)
        parts.append(kuw)

        tip = mc.polyCone(
            r=(0.040 + aggr * 0.012) * s,
            h=(0.12 + aggr * 0.04) * s,
            sa=4,
            name=f'rm_kabuto_kuwagata_tip_{label}_#',
        )[0]
        bb2 = mc.exactWorldBoundingBox(kuw)
        mc.move(side * (0.22 + aggr * 0.06) * s,
                bb2[4] + (0.06 + aggr * 0.02) * s,
                (0.06 + aggr * 0.02) * s, tip, relative=True)
        finish(tip, 0.0, hard=True)
        parts.append(tip)

    maedate = mc.polyCube(
        w=(0.08 + aggr * 0.024) * s,
        h=(0.42 + aggr * 0.14) * s,
        d=(0.055 + aggr * 0.016) * s,
        sx=1, sy=4, sz=1,
        name='rm_kabuto_maedate_#',
    )[0]
    mc.move(0, crest_y + (0.20 + aggr * 0.06) * s,
            (0.18 + aggr * 0.04) * s, maedate, relative=True)

    bb = mc.exactWorldBoundingBox(maedate)
    for v in mc.ls(f'{maedate}.vtx[*]', flatten=True) or []:
        pos = mc.pointPosition(v, w=True)
        t = (pos[1] - bb[1]) / ((bb[4] - bb[1]) or 1.0)
        taper = 1.0 - t * 0.88
        cx = (bb[0] + bb[3]) * 0.5
        cz = (bb[2] + bb[5]) * 0.5
        mc.move(cx + (pos[0] - cx) * taper, pos[1],
                cz + (pos[2] - cz) * taper, v, ws=True)

    finish(maedate, 0.010, hard=True)
    parts.append(maedate)

    crest_ring = mc.polyTorus(
        r=(0.12 + aggr * 0.04) * s,
        sr=0.022 * s * d_mul,
        sa=16, sh=4,
        name='rm_kabuto_crest_ring_#',
    )[0]
    mc.rotate(90, 0, 0, crest_ring)
    mc.move(0, crest_y + 0.014 * s,
            (0.06 + aggr * 0.02) * s, crest_ring, relative=True)
    finish(crest_ring, 0.0)
    parts.append(crest_ring)

    return parts


def _build_spine_port(aggr, s):
    port = mc.polyCylinder(
        r=(0.088 + aggr * 0.024) * s,
        h=(0.10 + aggr * 0.02) * s,
        sa=6, name='rm_kabuto_spine_port_#',
    )[0]
    mc.move(0, -(0.10 + aggr * 0.02) * s,
            -(0.26 + aggr * 0.06) * s, port, relative=True)
    mc.rotate(12, 0, 0, port)
    finish(port, 0.0, hard=True)
    return port


def build(grp: str, aggr: float, tune: HeadTune) -> None:
    s  = (1.0 + aggr * 0.50) * tune.width
    d_mul = tune.detail
    eye_mul = tune.eye
    shikoro_count = 4

    all_parts = []
    all_parts += _build_body_group(aggr, s, shikoro_count)
    all_parts += _build_eyes_group(aggr, s, d_mul, eye_mul)
    all_parts += _build_crest_group(aggr, s, d_mul)
    all_parts.append(_build_spine_port(aggr, s))

    mc.parent(all_parts, grp)
