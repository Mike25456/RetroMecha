"""Scene management utilities for RetroMecha UI."""

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False

MECHA_PATTERNS = ['RetroMecha_*']
SCENE_PATTERNS = ['RetroMecha_Scene_*']
TERRAIN_PATTERNS = [
    'rm_terrain_*', 'rm_ground_*', 'rm_monument_*',
    'rm_platform_*', 'rm_fragment_*', 'rm_debris_*',
    'rm_ramps_*', 'rm_pillars_*', 'rm_tower_*',
    'rm_bg_tower_*', 'rm_plat_tower_*',
    'rm_skyline_*',
]
ANIM_AUX_PATTERNS = [
    'rm_anim_offset_*', 'rm_flight_path*', 'rm_motionPath*',
    'rm_flight_driver*', 'rm_look_target*', 'rm_lookPath*', 'rm_bobber*',
]
ANIM_EXPR_NAMES = [
    'rm_idle_root', 'rm_idle_head',
    'rm_idle_arm_L', 'rm_idle_arm_R',
    'rm_idle_wing_L', 'rm_idle_wing_R', 'rm_idle_reactor',
    'rm_spin_root', 'rm_spin_torso', 'rm_spin_head',
    'rm_spin_arm_L', 'rm_spin_arm_R',
    'rm_spin_wing_L', 'rm_spin_wing_R', 'rm_spin_reactor',
]


def find_mecha_group():
    for n in (mc.ls('RetroMecha_*', type='transform') or []):
        if 'Scene' not in n and mc.objExists(n):
            return n
    return None


def find_scene_group():
    for n in (mc.ls('RetroMecha_Scene_*', type='transform') or []):
        if mc.objExists(n):
            return n
    return None


def mecha_bbox():
    grp = find_mecha_group()
    if grp and mc.objExists(grp):
        try:
            return tuple(mc.exactWorldBoundingBox(grp))
        except Exception:
            pass
    return (-2.0, 0.5, -1.5, 2.0, 5.0, 1.5)


def parent_to_scene(node):
    scene = find_scene_group()
    if scene and node and mc.objExists(node):
        try:
            mc.parent(node, scene)
        except Exception:
            pass


def ensure_scene_group():
    """Encuentra o crea el grupo escena y mueve mecha + terreno adentro.

    Garantiza que todo el escenario esta bajo un solo grupo en el outliner.
    """
    scene = find_scene_group()
    if not scene:
        scene = mc.group(empty=True, name='RetroMecha_Scene_#')
    for root_name in ('rm_terrain_*', 'RetroMecha_*'):
        for node in (mc.ls(root_name, type='transform') or []):
            if 'Scene' in node or not mc.objExists(node):
                continue
            parent = mc.listRelatives(node, parent=True) or [None]
            if parent[0] != scene:
                try:
                    mc.parent(node, scene)
                except Exception:
                    pass
    return scene


def delete_nodes(nodes):
    nodes = [n for n in nodes if n and mc.objExists(n)]
    if not nodes:
        return
    try:
        mc.delete(nodes)
    except Exception:
        for n in nodes:
            try:
                mc.delete(n)
            except Exception:
                pass


def clean_animations():
    """Borra expresiones, motion paths, offset groups y curvas de animacion
    creadas por RetroMecha. No toca animaciones externas."""
    for expr_name in ANIM_EXPR_NAMES:
        if mc.objExists(expr_name):
            try:
                mc.delete(expr_name)
            except Exception:
                pass

    aux_nodes = []
    for pat in ANIM_AUX_PATTERNS:
        aux_nodes.extend(mc.ls(pat) or [])
    delete_nodes(aux_nodes)

    for mp in (mc.ls(type='motionPath') or []):
        try:
            mc.delete(mp)
        except Exception:
            pass

    root = find_mecha_group()
    if not root:
        return
    try:
        if mc.attributeQuery('offsetParentMatrix', node=root, exists=True):
            dest = f'{root}.offsetParentMatrix'
            src = mc.connectionInfo(dest, sourceFromDestination=True)
            if src:
                mc.disconnectAttr(src, dest)
            identity = (
                1.0, 0.0, 0.0, 0.0,
                0.0, 1.0, 0.0, 0.0,
                0.0, 0.0, 1.0, 0.0,
                0.0, 0.0, 0.0, 1.0,
            )
            mc.setAttr(dest, *identity, type='matrix')
    except Exception:
        pass
    for attr in ('tx', 'ty', 'tz', 'rx', 'ry', 'rz'):
        try:
            mc.setAttr(f'{root}.{attr}', 0)
        except Exception:
            pass
    for attr in ('sx', 'sy', 'sz'):
        try:
            mc.setAttr(f'{root}.{attr}', 1)
        except Exception:
            pass


def clean_camera():
    """Borra la camara default Camara_for_render creada por RetroMecha."""
    try:
        from utils.camera import remove_camera
        remove_camera()
    except Exception:
        pass


def clean_atmosphere():
    """Borra el aiAtmosphereVolume creado por RetroMecha."""
    try:
        from utils.atmosphere import remove_atmosphere
        remove_atmosphere()
    except Exception:
        pass


def clean_sky():
    """Borra el cielo (polyPlane + 2 bend deformers) + sky_material asociado."""
    try:
        from utils.sky import remove_sky
        remove_sky()
    except Exception:
        pass
    try:
        from materials.sky_material import remove_sky_material
        remove_sky_material()
    except Exception:
        pass


def clean_lighting():
    """Borra TODAS las luces creadas por RetroMecha (nuevas + legacy).
    Delega a utils.lighting.remove_lighting() que busca por tag rmLight
    y por nombre (aiAreaLight, aiMeshLight, directionalLight, aiSkyDomeLight,
    cubos de mesh light, nombres legacy)."""
    try:
        from utils.lighting import remove_lighting
        remove_lighting()
    except Exception:
        pass


def clean_scene():
    """Limpia TODO lo creado por RetroMecha: scene group, mecha, terreno,
    animaciones (expresiones + motion paths + offset groups) y luces."""
    clean_animations()

    nodes = []
    for pat in SCENE_PATTERNS:
        nodes.extend(mc.ls(pat, type='transform') or [])
    for pat in MECHA_PATTERNS:
        for node in (mc.ls(pat, type='transform') or []):
            if 'Scene' not in node:
                nodes.append(node)
    for pat in TERRAIN_PATTERNS:
        nodes.extend(mc.ls(pat, type='transform') or [])
    delete_nodes(nodes)

    clean_lighting()
    clean_atmosphere()
    clean_sky()
    clean_camera()


def clean_mecha():
    nodes = []
    for pat in MECHA_PATTERNS:
        for node in (mc.ls(pat, type='transform') or []):
            if 'Scene' in node:
                continue
            nodes.append(node)
    delete_nodes(nodes)


def clean_terrain():
    nodes = []
    for pat in TERRAIN_PATTERNS:
        nodes.extend(mc.ls(pat, type='transform') or [])
    delete_nodes(nodes)


# Patrones de limpieza por componente de terreno (para rebuild parcial)
COMPONENT_CLEAN_PATTERNS = {
    'monument':  ['rm_monument_*', 'rm_bg_tower_*'],
    'skyline':   ['rm_skyline_*'],
    'platforms': ['rm_platform_*', 'rm_plat_tower_*'],
    'pillars':   ['rm_pillar_*'],
    'fragments': ['rm_fragment_*'],
    'debris':    ['rm_debris_*', 'rm_deb_*'],
    'ramps':     ['rm_ramps_*', 'rm_ramp_*'],
    'ground':    ['rm_ground_*'],
}


def clean_terrain_component(component):
    """Borra solo las piezas de UN componente del terreno."""
    patterns = COMPONENT_CLEAN_PATTERNS.get(component)
    if not patterns:
        return
    for pat in patterns:
        for node in (mc.ls(pat, type='transform') or []):
            try:
                mc.delete(node)
            except Exception:
                pass


def lift_mecha(group):
    try:
        bb = mc.exactWorldBoundingBox(group)
        lift = 0.5 - bb[1]
        if abs(lift) > 0.01:
            mc.move(0, lift, 0, group, relative=True, worldSpace=True)
    except Exception:
        pass


def scene_update(fn):
    try:
        mc.undoInfo(openChunk=True)
    except Exception:
        pass
    try:
        mc.refresh(suspend=True)
    except Exception:
        pass
    try:
        mc.undoInfo(stateWithoutFlush=False)
    except Exception:
        pass
    try:
        return fn()
    finally:
        try:
            mc.undoInfo(stateWithoutFlush=True)
        except Exception:
            pass
        try:
            mc.refresh(suspend=False)
            mc.refresh(force=True)
        except Exception:
            pass
        try:
            mc.undoInfo(closeChunk=True)
        except Exception:
            pass

def delimit_roots():
    scene = find_scene_group()
    if scene:
        return [scene]
    roots = []
    mecha = find_mecha_group()
    if mecha:
        roots.append(mecha)
    roots.extend(
        n for n in (mc.ls('rm_terrain_*', type='transform') or [])
        if mc.objExists(n)
    )
    return roots


def is_delimited(root):
    try:
        return (
            mc.attributeQuery('rm_delimited', node=root, exists=True)
            and mc.getAttr(f'{root}.rm_delimited')
        )
    except Exception:
        return False


def mark_delimited(root):
    try:
        if not mc.attributeQuery('rm_delimited', node=root, exists=True):
            mc.addAttr(root, longName='rm_delimited', attributeType='bool')
        mc.setAttr(f'{root}.rm_delimited', True)
    except Exception:
        pass


def mark_undelimited(root):
    if not root or not mc.objExists(root):
        return
    try:
        if not mc.attributeQuery('rm_delimited', node=root, exists=True):
            mc.addAttr(root, longName='rm_delimited', attributeType='bool')
        mc.setAttr(f'{root}.rm_delimited', False)
    except Exception:
        pass


def on_delimitar(*_):
    def _work():
        roots = [r for r in delimit_roots() if not is_delimited(r)]
        if not roots:
            print('[RetroMecha] No hay escena nueva por delimitar')
            return
        from utils.hard_surface import apply_support_edges
        from utils.maya_scene import force_preview_three
        total = 0
        for root in roots:
            total += apply_support_edges(
                root, offset=0.018, fraction=0.045,
                segments=2, max_faces=500,
            )
            force_preview_three(root)
            mark_delimited(root)
        mc.select(roots)
        try:
            panel = mc.getPanel(withFocus=True)
            if panel and mc.getPanel(typeOf=panel) == 'modelPanel':
                mc.modelEditor(panel, e=True, displayAppearance='smoothShaded')
        except Exception:
            pass
        print(f'[RetroMecha] Delimitacion aplicada: {total} pieza(s)')
    return scene_update(_work)
