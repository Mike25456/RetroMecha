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
    'rm_ramps_*', 'rm_pillars_*', 'rm_tower_*', 'rm_skyline_*',
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


def clean_scene():
    nodes = []
    for pat in SCENE_PATTERNS:
        nodes.extend(mc.ls(pat, type='transform') or [])
    delete_nodes(nodes)


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
        return fn()
    finally:
        try:
            mc.refresh(suspend=False)
            mc.refresh(force=True)
        except Exception:
            pass
        try:
            mc.undoInfo(closeChunk=True)
        except Exception:
            pass


def set_option_by_value(menu, mapping, value):
    for label, mapped in mapping.items():
        if mapped == value:
            mc.optionMenu(menu, e=True, value=label)
            return


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
        from utils.maya_scene import force_preview_one
        total = 0
        for root in roots:
            total += apply_support_edges(
                root, offset=0.018, fraction=0.045,
                segments=2, max_faces=500,
            )
            force_preview_one(root)
            mark_delimited(root)
        mc.select(roots)
        print(f'[RetroMecha] Delimitacion aplicada: {total} pieza(s)')
    return scene_update(_work)
