"""
RetroMecha — utils/deform_utils.py
Deformación procedural: escala no-uniforme + desplazamiento de vértices.

Se aplica DESPUÉS de construir la geometría base y ANTES de attachar sub-piezas.
Controlado por aggressiveness (intensidad) y seed (reproducibilidad).
"""

import random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


def deform_pipeline(mesh, aggr, height_scale, rng):
    """
    Pipeline completo de deformación: escala + vértices.

    Args:
        mesh:         nombre del transform en Maya
        aggr:         float 0-1 (aggressiveness) — intensidad de deformación
        height_scale: float 0.5-2.0 — escala vertical global
        rng:          instancia random.Random para reproducibilidad

    Returns:
        nombre del mesh deformado
    """
    if not MAYA_AVAILABLE or not mc.objExists(mesh):
        return mesh

    # Paso 1: escala no-uniforme
    non_uniform_scale(mesh, aggr, height_scale, rng)

    # Paso 2: desplazamiento de vértices (solo si aggr > 0.05)
    if aggr > 0.05:
        groups = define_vertex_groups(mesh)
        vertex_displace(mesh, aggr, rng, groups)

    return mesh


def non_uniform_scale(mesh, aggr, height_scale, rng):
    """
    Escala independiente por eje. Proporciones distintas cada seed.

    Con aggr=0: escala casi 1.0 en X/Z, solo height_scale en Y.
    Con aggr=1: escala varía ±30% en X, ±20% en Z.
    """
    if not MAYA_AVAILABLE:
        return

    # Rango de variación crece con agresividad
    var_x = aggr * 0.30   # ±30% máximo en X
    var_z = aggr * 0.20   # ±20% máximo en Z
    var_y = 0.15           # ±15% siempre (sutil)

    sx = 1.0 + rng.uniform(-var_x, var_x)
    sy = height_scale * (1.0 + rng.uniform(-var_y, var_y))
    sz = 1.0 + rng.uniform(-var_z, var_z)

    # Clamp para evitar escalas absurdas
    sx = max(0.6, min(1.5, sx))
    sy = max(0.5, min(2.2, sy))
    sz = max(0.6, min(1.4, sz))

    try:
        mc.scale(sx, sy, sz, mesh, relative=False)
        mc.makeIdentity(mesh, apply=True, scale=True, normal=0)
    except Exception as e:
        print(f'[RetroMecha][deform] non_uniform_scale falló: {e}')


def define_vertex_groups(mesh):
    """
    Clasifica los vértices de 'mesh' en 3 grupos por altura relativa:
      top  (Y > 66%)  → máxima deformación
      mid  (33-66%)   → deformación media
      base (Y < 33%)  → mínima deformación (estabilidad)

    Returns:
        dict {'top': [indices], 'mid': [indices], 'base': [indices]}
    """
    groups = {'top': [], 'mid': [], 'base': []}

    if not MAYA_AVAILABLE:
        return groups

    try:
        vtx_count = mc.polyEvaluate(mesh, vertex=True)
        if vtx_count < 1:
            return groups

        # Obtener bounding box para normalizar
        bb = mc.exactWorldBoundingBox(mesh)
        y_min = bb[1]
        y_max = bb[4]
        y_range = y_max - y_min
        if y_range < 0.001:
            return groups

        threshold_low  = y_min + y_range * 0.33
        threshold_high = y_min + y_range * 0.66

        for i in range(vtx_count):
            pos = mc.xform(f'{mesh}.vtx[{i}]', q=True, t=True, ws=True)
            y = pos[1]
            if y > threshold_high:
                groups['top'].append(i)
            elif y > threshold_low:
                groups['mid'].append(i)
            else:
                groups['base'].append(i)

    except Exception as e:
        print(f'[RetroMecha][deform] define_vertex_groups falló: {e}')

    return groups


def vertex_displace(mesh, aggr, rng, groups=None):
    """
    Desplaza vértices aleatoriamente dentro de rangos controlados.
    Cada grupo tiene distinta intensidad para mantener la silueta reconocible.

    Args:
        mesh:    nombre del transform
        aggr:    float 0-1 — intensidad máxima
        rng:     random.Random
        groups:  dict de vertex groups (o None para calcular)
    """
    if not MAYA_AVAILABLE:
        return

    if groups is None:
        groups = define_vertex_groups(mesh)

    # Calcular bounding box para escalar la intensidad
    try:
        bb = mc.exactWorldBoundingBox(mesh)
    except Exception:
        return

    bbox_size = max(
        bb[3] - bb[0],  # width
        bb[4] - bb[1],  # height
        bb[5] - bb[2],  # depth
    )
    if bbox_size < 0.01:
        return

    # Intensidad máxima = 15% del bounding box × agresividad
    max_intensity = bbox_size * 0.15 * aggr

    # Pesos por grupo: top se deforma más, base casi nada
    weights = {
        'top':  1.0,
        'mid':  0.45,
        'base': 0.15,
    }

    try:
        for group_name, indices in groups.items():
            w = weights.get(group_name, 0.5)
            intensity = max_intensity * w

            if intensity < 0.001:
                continue

            for vi in indices:
                ox = rng.uniform(-intensity, intensity)
                oy = rng.uniform(-intensity * 0.5, intensity * 0.5)
                oz = rng.uniform(-intensity, intensity)

                mc.polyMoveVertex(
                    f'{mesh}.vtx[{vi}]',
                    translateX=ox,
                    translateY=oy,
                    translateZ=oz,
                    localTranslate=True,
                )

        # Actualizar la malla después de mover vértices
        mc.polyMergeVertex(mesh, distance=0.0001, ch=False)

    except Exception as e:
        print(f'[RetroMecha][deform] vertex_displace falló: {e}')
