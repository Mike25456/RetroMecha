"""
RetroMecha - utils/sky.py
Geometria de cielo (sky dome geometrico, no light): polyPlane + 2 bend deformers.

Reproduce el setup MEL del usuario:

  sky (polyPlane)
    - width 1, height 1, subdivX 24, subdivY 24, axis Y, createUVs Normalize
    - transform: T(0, -27.551, -100.721)  S(537.16, 579.057, 565.747)

  rm_sky_bend1
    - envelope 2,  curvature 98.549,  lowBound 0,  highBound 1
    - handle: T(0, -27.551, -100.721)  R(-90, 0, 90)  S(178.966, ...)

  rm_sky_bend2
    - envelope 1,  curvature 28.648,  lowBound -2, highBound 2
    - handle: T(0, 36.572, -53.848)  R(0, 0, 90)  S(178.966, ...)
"""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

SKY_NAME       = 'sky'
SKY_TAG        = 'rmSky'
BEND1          = 'rm_sky_bend1'
BEND2          = 'rm_sky_bend2'
BEND1_HANDLE   = 'rm_sky_bend1Handle'
BEND2_HANDLE   = 'rm_sky_bend2Handle'

# Plane
PLANE_TRANSLATE = (0.0, -27.551, -100.721)
PLANE_ROTATE    = (0.0, 0.0, 0.0)
PLANE_SCALE     = (537.16, 579.057, 565.747)

# Bend 1
BEND1_ENVELOPE   = 2.0
BEND1_CURVATURE  = 98.549
BEND1_LOW_BOUND  = 0.0
BEND1_HIGH_BOUND = 1.0
BEND1_H_TRANSLATE = (0.0, -27.551, -100.721)
BEND1_H_ROTATE    = (-90.0, 0.0, 90.0)
BEND1_H_SCALE     = (178.966, 178.966, 178.966)

# Bend 2
BEND2_ENVELOPE   = 1.0
BEND2_CURVATURE  = 28.648
BEND2_LOW_BOUND  = -2.0
BEND2_HIGH_BOUND = 2.0
BEND2_H_TRANSLATE = (0.0, 36.572, -53.848)
BEND2_H_ROTATE    = (0.0, 0.0, 90.0)
BEND2_H_SCALE     = (178.966, 178.966, 178.966)


# ══════════════════════════════════════════════════════════════════════
#  API PUBLICA
# ══════════════════════════════════════════════════════════════════════

def create_sky() -> str | None:
    """Crea (o recrea) la geometria de cielo con los 2 bend deformers,
    bakea el historial, freezea los transforms y la parentea al scene group."""
    if not MAYA_AVAILABLE:
        return None

    remove_sky()

    # 1. polyPlane
    try:
        result = mc.polyPlane(
            name=SKY_NAME,
            width=1.0, height=1.0,
            subdivisionsX=24, subdivisionsY=24,
            axis=(0, 1, 0),
            createUVs=2,           # Normalize
            constructionHistory=True,
        )
    except Exception as e:
        print(f'[RetroMecha][Sky] Error creando polyPlane: {e}')
        return None

    plane = result[0]
    if plane != SKY_NAME:
        plane = mc.rename(plane, SKY_NAME)

    # Tag para limpieza
    if not mc.attributeQuery(SKY_TAG, node=plane, exists=True):
        mc.addAttr(plane, longName=SKY_TAG,
                   attributeType='bool', defaultValue=True)
    mc.setAttr(f'{plane}.{SKY_TAG}', True)

    # 2. bend1 (aplicar ANTES de transformar el plane)
    _apply_bend(
        plane, BEND1, BEND1_HANDLE,
        envelope=BEND1_ENVELOPE, curvature=BEND1_CURVATURE,
        low=BEND1_LOW_BOUND, high=BEND1_HIGH_BOUND,
        translate=BEND1_H_TRANSLATE, rotate=BEND1_H_ROTATE, scale=BEND1_H_SCALE,
    )

    # 3. bend2
    _apply_bend(
        plane, BEND2, BEND2_HANDLE,
        envelope=BEND2_ENVELOPE, curvature=BEND2_CURVATURE,
        low=BEND2_LOW_BOUND, high=BEND2_HIGH_BOUND,
        translate=BEND2_H_TRANSLATE, rotate=BEND2_H_ROTATE, scale=BEND2_H_SCALE,
    )

    # 4. Transform final del plane (antes del bake para que la deformacion
    #    quede en world space al bakearse)
    _set_xform(plane, PLANE_TRANSLATE, PLANE_ROTATE, PLANE_SCALE)

    # 5. Delete history → bakea los 2 bends dentro de la mesh
    try:
        mc.delete(plane, constructionHistory=True)
    except Exception as e:
        print(f'[RetroMecha][Sky] delete history: {e}')

    # 6. Eliminar bend handles huerfanos (el delete history los deja sueltos)
    for h in (BEND1_HANDLE, BEND2_HANDLE):
        if mc.objExists(h):
            try:
                mc.delete(h)
            except Exception:
                pass

    # 7. Freeze transforms → bakea translate/rotate/scale en los vertices
    try:
        mc.makeIdentity(plane, apply=True,
                        translate=True, rotate=True, scale=True,
                        normal=False, preserveNormals=True)
    except Exception as e:
        print(f'[RetroMecha][Sky] freeze: {e}')

    # 8. Parentear al scene group si existe
    try:
        from ui.scene_utils import find_scene_group
        scene_grp = find_scene_group()
        if scene_grp and mc.objExists(scene_grp):
            # Verificar que no este ya parenteado al scene_grp
            current_parent = mc.listRelatives(plane, parent=True) or []
            if not current_parent or current_parent[0] != scene_grp:
                mc.parent(plane, scene_grp)
    except Exception as e:
        print(f'[RetroMecha][Sky] parent to scene: {e}')

    print(f'[RetroMecha][Sky] {SKY_NAME} creado (history baked + freezed + parented)')
    return plane


def remove_sky():
    """Elimina sky y sus deformadores (por tag o nombre)."""
    if not MAYA_AVAILABLE:
        return

    # Por tag (si el usuario tiene su propio 'sky', no lo tocamos)
    for shape in (mc.ls(type='mesh') or []):
        parents = mc.listRelatives(shape, parent=True) or []
        xform = parents[0] if parents else shape
        if mc.attributeQuery(SKY_TAG, node=xform, exists=True):
            try:
                mc.delete(xform)
            except Exception:
                pass

    # Por nombre — bend nodes + handles + plane si quedo
    for name in (BEND1, BEND2, BEND1_HANDLE, BEND2_HANDLE):
        if mc.objExists(name):
            try:
                mc.delete(name)
            except Exception:
                pass

    # Plane por nombre solo si lleva nuestro tag (ya cubierto arriba)
    # Nunca borramos un 'sky' externo del usuario.


def has_sky() -> bool:
    if not MAYA_AVAILABLE:
        return False
    if not mc.objExists(SKY_NAME):
        return False
    return mc.attributeQuery(SKY_TAG, node=SKY_NAME, exists=True)


# ══════════════════════════════════════════════════════════════════════
#  INTERNOS
# ══════════════════════════════════════════════════════════════════════

def _apply_bend(mesh, bend_name, handle_name, *,
                envelope, curvature, low, high,
                translate, rotate, scale):
    """Aplica un nonLinear bend al mesh y configura deformer + handle."""
    try:
        result = mc.nonLinear(mesh, type='bend')
    except Exception as e:
        print(f'[RetroMecha][Sky] Error aplicando bend a {mesh}: {e}')
        return None, None

    deformer = mc.rename(result[0], bend_name)
    handle   = mc.rename(result[1], handle_name)

    # Atributos del deformer
    try:
        mc.setAttr(f'{deformer}.envelope',  float(envelope))
        mc.setAttr(f'{deformer}.curvature', float(curvature))
        mc.setAttr(f'{deformer}.lowBound',  float(low))
        mc.setAttr(f'{deformer}.highBound', float(high))
    except Exception as e:
        print(f'[RetroMecha][Sky] setAttr deformer {deformer}: {e}')

    # Transform del handle
    _set_xform(handle, translate, rotate, scale)
    return deformer, handle


def _set_xform(node, translate, rotate, scale):
    try:
        mc.setAttr(f'{node}.translateX', float(translate[0]))
        mc.setAttr(f'{node}.translateY', float(translate[1]))
        mc.setAttr(f'{node}.translateZ', float(translate[2]))
        mc.setAttr(f'{node}.rotateX',    float(rotate[0]))
        mc.setAttr(f'{node}.rotateY',    float(rotate[1]))
        mc.setAttr(f'{node}.rotateZ',    float(rotate[2]))
        mc.setAttr(f'{node}.scaleX',     float(scale[0]))
        mc.setAttr(f'{node}.scaleY',     float(scale[1]))
        mc.setAttr(f'{node}.scaleZ',     float(scale[2]))
    except Exception as e:
        print(f'[RetroMecha][Sky] xform {node}: {e}')
