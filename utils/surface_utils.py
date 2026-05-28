"""
RetroMecha — utils/surface_utils.py
Utilidades de superficie: posicionar y conformar piezas sobre mallas.

Dos métodos principales:
  snap_to_mesh     → closestPointOnMesh + normal → piezas rígidas
  conform_to_mesh  → shrinkWrap + bake → paneles que siguen curvatura

Funciones puras: reciben nombres de nodos, retornan nombres de nodos.
"""

import random
import math

try:
    import maya.cmds as mc
    import maya.api.OpenMaya as om2
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


def snap_to_mesh(piece, target_mesh, desired_pos, offset=0.02):
    """
    Posiciona 'piece' en la superficie de 'target_mesh' más cercana
    a 'desired_pos', orientada según la normal de esa cara.

    Args:
        piece:        nombre del transform a posicionar
        target_mesh:  nombre de la malla destino (shape o transform)
        desired_pos:  (x, y, z) posición deseada aproximada
        offset:       distancia de flotación sobre la superficie

    Returns:
        nombre del piece posicionado, o None si falla
    """
    if not MAYA_AVAILABLE:
        return piece

    try:
        # Obtener el shape si nos pasaron el transform
        shapes = mc.listRelatives(target_mesh, shapes=True,
                                  type='mesh', fullPath=True) or []
        if not shapes:
            # target_mesh ya es un shape o no tiene mesh
            mesh_shape = target_mesh
        else:
            mesh_shape = shapes[0]

        # Crear nodo closestPointOnMesh temporal
        cpom = mc.createNode('closestPointOnMesh', name='rm_cpom_temp')
        mc.connectAttr(mesh_shape + '.worldMesh[0]', cpom + '.inMesh')
        mc.setAttr(cpom + '.inPositionX', desired_pos[0])
        mc.setAttr(cpom + '.inPositionY', desired_pos[1])
        mc.setAttr(cpom + '.inPositionZ', desired_pos[2])

        # Leer punto en superficie
        px = mc.getAttr(cpom + '.positionX')
        py = mc.getAttr(cpom + '.positionY')
        pz = mc.getAttr(cpom + '.positionZ')

        # Leer normal
        nx = mc.getAttr(cpom + '.normalX')
        ny = mc.getAttr(cpom + '.normalY')
        nz = mc.getAttr(cpom + '.normalZ')

        # Limpiar nodo temporal
        mc.delete(cpom)

        # Posicionar con offset sobre la normal
        mc.move(px + nx * offset,
                py + ny * offset,
                pz + nz * offset,
                piece, worldSpace=True)

        # Orientar según normal usando aimConstraint temporal
        _orient_to_normal(piece, (px, py, pz), (nx, ny, nz))

        return piece

    except Exception as e:
        print(f'[RetroMecha][surface] snap_to_mesh falló: {e}')
        # Fallback: posicionar sin orientación
        try:
            mc.move(desired_pos[0], desired_pos[1], desired_pos[2],
                    piece, worldSpace=True)
        except Exception:
            pass
        return piece


def conform_to_mesh(panel, target_mesh, offset=0.03):
    """
    Deforma 'panel' para que siga la curvatura de 'target_mesh'
    usando un deformer shrinkWrap, luego bake y limpia.

    Args:
        panel:        nombre del transform a deformar
        target_mesh:  nombre de la malla destino
        offset:       distancia de flotación (targetInflation)

    Returns:
        nombre del panel conformado, o None si falla
    """
    if not MAYA_AVAILABLE:
        return panel

    try:
        shapes = mc.listRelatives(target_mesh, shapes=True,
                                  type='mesh', fullPath=True) or []
        mesh_shape = shapes[0] if shapes else target_mesh

        # Crear shrinkWrap
        mc.select(panel, replace=True)
        deformer_list = mc.deformer(panel, type='shrinkWrap')
        if not deformer_list:
            return panel
        deformer = deformer_list[0]

        # Configurar
        mc.setAttr(deformer + '.projection', 0)   # closest point
        mc.setAttr(deformer + '.closestIfNoIntersection', 1)
        mc.setAttr(deformer + '.targetInflation', offset)

        # Conectar target
        mc.connectAttr(mesh_shape + '.worldMesh[0]',
                       deformer + '.targetGeom')

        # Forzar evaluación
        mc.dgeval(deformer)

        # Bake: borrar historia para que la deformación quede permanente
        mc.delete(panel, constructionHistory=True)

        return panel

    except Exception as e:
        print(f'[RetroMecha][surface] conform_to_mesh falló: {e}')
        return panel


def conform_stack(panels, target_mesh, offsets=None):
    """
    Aplica shrinkWrap a múltiples paneles con offsets progresivos.
    Estilo Takayuki Yanase: placas superpuestas con profundidad.

    Args:
        panels:       lista de nombres de transforms
        target_mesh:  malla destino
        offsets:      lista de offsets [0.03, 0.06, 0.09] o None para auto

    Returns:
        lista de paneles conformados
    """
    if offsets is None:
        offsets = [0.03 + i * 0.03 for i in range(len(panels))]

    result = []
    for panel, off in zip(panels, offsets):
        p = conform_to_mesh(panel, target_mesh, offset=off)
        if p:
            result.append(p)
    return result


def get_random_surface_point(mesh, rng):
    """
    Genera un punto aleatorio sobre la superficie de 'mesh'.

    Args:
        mesh:  nombre del transform o shape
        rng:   instancia de random.Random (para reproducibilidad)

    Returns:
        (x, y, z) sobre la superficie, o (0,0,0) si falla
    """
    if not MAYA_AVAILABLE:
        return (0, 0, 0)

    try:
        # Contar caras
        face_count = mc.polyEvaluate(mesh, face=True)
        if face_count < 1:
            return (0, 0, 0)

        # Elegir cara aleatoria
        face_id = rng.randint(0, face_count - 1)
        face_name = f'{mesh}.f[{face_id}]'

        # Centro de la cara via bounding box
        bb = mc.xform(face_name, q=True, bb=True, ws=True)
        cx = (bb[0] + bb[3]) * 0.5
        cy = (bb[1] + bb[4]) * 0.5
        cz = (bb[2] + bb[5]) * 0.5

        # Jitter dentro de la cara para variación
        jx = rng.uniform(-0.2, 0.2) * (bb[3] - bb[0])
        jz = rng.uniform(-0.2, 0.2) * (bb[5] - bb[2])

        return (cx + jx, cy, cz + jz)

    except Exception:
        return (0, 0, 0)


def get_face_normal(mesh, face_id):
    """
    Retorna la normal promedio de una cara.

    Returns:
        (nx, ny, nz) normalizado, o (0,1,0) si falla
    """
    if not MAYA_AVAILABLE:
        return (0, 1, 0)

    try:
        info = mc.polyInfo(f'{mesh}.f[{face_id}]', faceNormals=True)
        if info:
            parts = info[0].split(':')[1].split()
            return (float(parts[0]), float(parts[1]), float(parts[2]))
    except Exception:
        pass
    return (0, 1, 0)


# ── Helpers internos ──────────────────────────────────────────────────────────

def _orient_to_normal(piece, surface_point, normal):
    """Orienta piece para que su eje Z local apunte en dirección de normal."""
    try:
        nx, ny, nz = normal
        # Crear locator temporal en la dirección de la normal
        target_pos = (
            surface_point[0] + nx * 2.0,
            surface_point[1] + ny * 2.0,
            surface_point[2] + nz * 2.0,
        )
        loc = mc.spaceLocator(p=target_pos, name='rm_aim_temp')[0]

        aim = mc.aimConstraint(
            loc, piece,
            aimVector=(0, 0, 1),
            upVector=(0, 1, 0),
            worldUpType='scene',
        )
        # Bake la orientación y limpiar
        mc.delete(aim)
        mc.delete(loc)
    except Exception:
        pass  # Si falla, piece queda sin orientar — aceptable
