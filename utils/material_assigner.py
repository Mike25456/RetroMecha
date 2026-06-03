"""
RetroMecha — utils/material_assigner.py
Asigna materiales aiToon (Arnold) a las piezas del mecha.

Tiers:
  ARMOR  → superficie principal (main, body, surface)
  JOINT  → articulaciones, ranuras, cuellos
  DETAIL → sub-piezas attachadas (paneles, spikes, anillos)
  GLOW   → visores, nucleos, ojos (emission)

Usa config/materials.json para definir paletas y reglas de clasificacion.
Requiere Arnold (mtoa) cargado — no hay fallback.
"""

import os
import json

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


# Cache de materiales creados — evita recrear el mismo shader
_MATERIAL_CACHE: dict = {}

# Resultado cacheado de la detección de Arnold para la sesión
_ARNOLD_CHECKED: list = [False, False]   # [ya_comprobado, resultado]


# ══════════════════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def assign_palette_to_group(group: str, palette_name: str = 'industrial'):
    """
    Recorre todos los meshes hijos del grupo y les asigna el material
    aiToon (Arnold) correspondiente a su tier.

    Args:
        group:        nombre del grupo de Maya (ej: 'rm_head_1')
        palette_name: 'industrial' | 'oxidado' | 'artico' | 'carmesi'
    """
    if not MAYA_AVAILABLE:
        print('[RetroMecha][materials] Maya no disponible')
        return
    if not palette_name:
        return
    if not group or not mc.objExists(group):
        print(f'[RetroMecha][materials] Grupo no encontrado: {group}')
        return

    palette = _load_palette(palette_name)
    if not palette:
        print(f'[RetroMecha][materials] Paleta "{palette_name}" no encontrada')
        return

    if not _has_arnold():
        print('[RetroMecha][materials] Arnold/aiToon no disponible — '
              'paleta no aplicada')
        return
    print(f'[RetroMecha][materials] Aplicando paleta "{palette_name}" [Arnold/aiToon]')

    classification = _load_classification()

    descendants = mc.listRelatives(group, allDescendents=True,
                                   type='transform', fullPath=True) or []
    descendants.append(group)

    counts = {'ARMOR': 0, 'JOINT': 0, 'DETAIL': 0, 'GLOW': 0, 'skipped': 0}

    for node in descendants:
        shapes = mc.listRelatives(node, shapes=True, type='mesh') or []
        if not shapes:
            counts['skipped'] += 1
            continue

        short = node.rsplit('|', 1)[-1].lower()
        tier  = _classify_node(short, classification)

        try:
            _assign_palette_material(node, tier, palette, palette_name)
            counts[tier] += 1
        except Exception as e:
            print(f'[RetroMecha][materials] Error en {short} ({tier}): {e}')

    print(f'[RetroMecha][materials] "{palette_name}" aplicada: '
          f'ARMOR={counts["ARMOR"]} JOINT={counts["JOINT"]} '
          f'DETAIL={counts["DETAIL"]} GLOW={counts["GLOW"]} '
          f'(omitidos: {counts["skipped"]})')


def clear_material_cache():
    """Limpia el cache. Llamar antes de regenerar el mecha."""
    _MATERIAL_CACHE.clear()
    _ARNOLD_CHECKED[0] = False


# ══════════════════════════════════════════════════════════════════════════════
#  CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def _classify_node(node_name: str, rules: dict) -> str:
    """
    Determina el tier de un nodo según su nombre.
    Orden: GLOW → JOINT → DETAIL → ARMOR (catch-all)
    """
    for tier in ('GLOW', 'JOINT', 'DETAIL'):
        for pattern in rules.get(tier, []):
            if pattern in node_name:
                return tier
    return 'ARMOR'


# ══════════════════════════════════════════════════════════════════════════════
#  ASIGNACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def _assign_palette_material(node: str, tier: str, palette: dict, palette_name: str):
    """Crea (o reutiliza del cache) el shader del tier y lo asigna al nodo."""
    cache_key = f'{palette_name}_{tier}'
    sg = _MATERIAL_CACHE.get(cache_key)

    if not sg or not mc.objExists(sg):
        sg = _create_palette_material(tier, palette, palette_name)
        _MATERIAL_CACHE[cache_key] = sg

    if sg and mc.objExists(sg):
        try:
            mc.sets(node, edit=True, forceElement=sg)
        except Exception as e:
            print(f'[RetroMecha][materials] No se pudo asignar {sg} a {node}: {e}')
    else:
        print(f'[RetroMecha][materials] Shading group inválido para {cache_key}')


def _create_palette_material(tier: str, palette: dict, palette_name: str) -> str | None:
    """
    Crea un shader aiToon (requiere Arnold).
    Devuelve el nombre del shading group, o None si falla.
    """
    shader_name = f'rm_toon_{palette_name}_{tier.lower()}_mat'
    sg_name     = f'{shader_name}SG'

    if mc.objExists(shader_name) and mc.objExists(sg_name):
        return sg_name

    if not _has_arnold():
        print(f'[RetroMecha][materials] aiToon no disponible para {tier}')
        return None

    shader = None
    try:
        shader = mc.shadingNode('aiToon', asShader=True, name=shader_name)
        _configure_aitoon(shader, tier, palette)
    except Exception as e:
        print(f'[RetroMecha][materials] Error creando aiToon ({tier}): {e}')
        for leftover in (shader_name, sg_name):
            if leftover and mc.objExists(leftover):
                try:
                    mc.delete(leftover)
                except Exception:
                    pass
        return None

    if not shader or not mc.objExists(shader):
        return None

    try:
        sg = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
        mc.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)
        return sg
    except Exception as e:
        print(f'[RetroMecha][materials] Error creando shading group ({tier}): {e}')
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN aiToon (Arnold)
# ══════════════════════════════════════════════════════════════════════════════

def _configure_aitoon(shader: str, tier: str, palette: dict):
    """Configura un nodo aiToon según el tier y la paleta."""
    ramp_data = palette.get(tier)
    if ramp_data is None:
        return

    if tier == 'GLOW':
        rgb = ramp_data
        mc.setAttr(f'{shader}.baseTint', rgb[0], rgb[1], rgb[2], type='double3')
        try:
            mc.setAttr(f'{shader}.emission', 1.0)
            mc.setAttr(f'{shader}.emissionColor', rgb[0], rgb[1], rgb[2], type='double3')
        except Exception:
            pass
        mc.setAttr(f'{shader}.enableSilhouette', 0)
        return

    # ARMOR, JOINT, DETAIL: base + tonemap ramp + silhouette
    base_color = ramp_data[0][1]
    mc.setAttr(f'{shader}.baseTint', base_color[0], base_color[1], base_color[2],
               type='double3')
    mc.setAttr(f'{shader}.baseWeight', 0.95)

    ramp_node = mc.shadingNode('ramp', asTexture=True, name=f'{shader}_tonemap')
    _populate_ramp(ramp_node, ramp_data)
    mc.connectAttr(f'{ramp_node}.outColor', f'{shader}.tonemap', force=True)

    mc.setAttr(f'{shader}.enableSilhouette', 1)
    outline_color = palette.get('outline_color', [0.0, 0.0, 0.0])
    outline_width = palette.get('outline_width', 3.0)
    mc.setAttr(f'{shader}.silhouetteColor',
               outline_color[0], outline_color[1], outline_color[2],
               type='double3')
    mc.setAttr(f'{shader}.silhouetteWidthScale', outline_width)

    try:
        mc.setAttr(f'{shader}.enableEdges', 1)
        mc.setAttr(f'{shader}.creaseEdgeColor', 0.0, 0.0, 0.0, type='double3')
        mc.setAttr(f'{shader}.crease_angle_threshold', 30.0)
    except Exception:
        pass


def _populate_ramp(ramp_node: str, stops: list):
    """Llena un ramp con los stops dados [(pos, [r,g,b]), ...]."""
    for i in range(10):
        try:
            mc.removeMultiInstance(f'{ramp_node}.colorEntryList[{i}]', b=True)
        except Exception:
            break

    for i, (pos, rgb) in enumerate(stops):
        mc.setAttr(f'{ramp_node}.colorEntryList[{i}].position', pos)
        mc.setAttr(f'{ramp_node}.colorEntryList[{i}].color',
                   rgb[0], rgb[1], rgb[2], type='double3')

    # 0=none (cel duro), 1=linear, 4=smooth
    mc.setAttr(f'{ramp_node}.interpolation', 0)


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _has_arnold() -> bool:
    """
    Verifica si el shader aiToon de Arnold está realmente disponible.
    Comprueba que el tipo de nodo esté registrado, no solo que el plugin figure.
    Cachea el resultado por sesión para evitar llamadas repetidas.
    """
    if not MAYA_AVAILABLE:
        return False
    if _ARNOLD_CHECKED[0]:
        return _ARNOLD_CHECKED[1]

    result = False
    try:
        # La forma más fiable: comprobar si el tipo de nodo está registrado
        result = 'aiToon' in (mc.allNodeTypes() or [])
    except Exception:
        result = False

    _ARNOLD_CHECKED[0] = True
    _ARNOLD_CHECKED[1] = result

    if result:
        print('[RetroMecha][materials] Arnold/aiToon detectado')
    else:
        print('[RetroMecha][materials] Arnold no disponible')

    return result


def _load_palette(name: str) -> dict:
    data = _load_config()
    return data.get('_palettes', {}).get(name)


def _load_classification() -> dict:
    data = _load_config()
    return data.get('_classification', {})


def _load_config() -> dict:
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'materials.json')
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f'[RetroMecha][materials] Error leyendo materials.json: {e}')
    return {}


def list_palettes() -> list:
    return list(_load_config().get('_palettes', {}).keys())
