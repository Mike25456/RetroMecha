"""
RetroMecha — utils/material_assigner.py
Asigna materiales aiToon a las piezas del mecha según su tier visual.

Tiers:
  ARMOR  → superficie principal (main, body, surface)
  JOINT  → articulaciones, ranuras, cuellos
  DETAIL → sub-piezas attachadas (paneles, spikes, anillos)
  GLOW   → visores, núcleos, ojos (emission)

Usa config/materials.json para definir paletas y reglas de clasificación.
"""

import os
import json
import random

try:
    import maya.cmds as mc
    MAYA_AVAILABLE = True
except ImportError:
    MAYA_AVAILABLE = False


# Cache de materiales creados — evita recrear el mismo aiToon
_MATERIAL_CACHE: dict = {}


# ══════════════════════════════════════════════════════════════════════════════
#  PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════════════════

def assign_palette_to_group(group: str, palette_name: str = 'industrial'):
    """
    Recorre todos los meshes hijos del grupo y les asigna el material
    aiToon correspondiente a su tier.

    Args:
        group:        nombre del grupo de Maya (ej: 'rm_head_1')
        palette_name: 'industrial' | 'oxidado' | 'artico' | 'carmesi'
    """
    if not MAYA_AVAILABLE:
        return

    palette = _load_palette(palette_name)
    if not palette:
        print(f'[RetroMecha][materials] Paleta "{palette_name}" no encontrada')
        return

    classification = _load_classification()

    # Listar todos los meshes descendientes
    descendants = mc.listRelatives(group, allDescendents=True,
                                   type='transform', fullPath=True) or []
    descendants.append(group)

    counts = {'ARMOR': 0, 'JOINT': 0, 'DETAIL': 0, 'GLOW': 0, 'skipped': 0}

    for node in descendants:
        # Solo asignar a transforms que tengan mesh
        shapes = mc.listRelatives(node, shapes=True, type='mesh') or []
        if not shapes:
            counts['skipped'] += 1
            continue

        short = node.rsplit('|', 1)[-1].lower()
        tier  = _classify_node(short, classification)

        try:
            _assign_aitoon(node, tier, palette, palette_name)
            counts[tier] += 1
        except Exception as e:
            print(f'[RetroMecha][materials] error en {short}: {e}')

    print(f'[RetroMecha][materials] Paleta "{palette_name}" aplicada: '
          f'ARMOR={counts["ARMOR"]} JOINT={counts["JOINT"]} '
          f'DETAIL={counts["DETAIL"]} GLOW={counts["GLOW"]} '
          f'(omitidos: {counts["skipped"]})')


def clear_material_cache():
    """Limpia el cache. Útil al regenerar todo el mecha."""
    _MATERIAL_CACHE.clear()


# ══════════════════════════════════════════════════════════════════════════════
#  CLASIFICACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def _classify_node(node_name: str, rules: dict) -> str:
    """
    Determina el tier de un nodo según su nombre.
    Orden de evaluación: GLOW → JOINT → DETAIL → ARMOR (catch-all)
    """
    for tier in ('GLOW', 'JOINT', 'DETAIL'):
        patterns = rules.get(tier, [])
        for pattern in patterns:
            if pattern in node_name:
                return tier
    return 'ARMOR'


# ══════════════════════════════════════════════════════════════════════════════
#  ASIGNACIÓN DE aiToon
# ══════════════════════════════════════════════════════════════════════════════

def _assign_aitoon(node: str, tier: str, palette: dict, palette_name: str):
    """Crea (o reusa del cache) el aiToon del tier y lo asigna al nodo."""
    cache_key = f'{palette_name}_{tier}'
    shading_group = _MATERIAL_CACHE.get(cache_key)

    if shading_group is None or not mc.objExists(shading_group):
        shading_group = _create_aitoon_material(tier, palette, palette_name)
        _MATERIAL_CACHE[cache_key] = shading_group

    if shading_group:
        try:
            mc.sets(node, edit=True, forceElement=shading_group)
        except Exception:
            pass


def _create_aitoon_material(tier: str, palette: dict, palette_name: str) -> str:
    """
    Crea un nodo aiToon con su tonemap (ramp) y silhouette configurados.
    Devuelve el nombre del shading group.

    Si aiToon no está disponible (sin Arnold/MtoA), cae a Lambert como fallback.
    """
    shader_name = f'rm_toon_{palette_name}_{tier.lower()}_mat'
    sg_name     = f'{shader_name}SG'

    if mc.objExists(shader_name):
        return f'{shader_name}SG' if mc.objExists(f'{shader_name}SG') else None

    # Intentar aiToon; si falla, usar Lambert
    use_arnold = _has_arnold()

    if use_arnold:
        shader = mc.shadingNode('aiToon', asShader=True, name=shader_name)
        _configure_aitoon(shader, tier, palette)
    else:
        shader = mc.shadingNode('lambert', asShader=True, name=shader_name)
        _configure_lambert_fallback(shader, tier, palette)

    # Crear shading group
    sg = mc.sets(renderable=True, noSurfaceShader=True, empty=True, name=sg_name)
    mc.connectAttr(f'{shader}.outColor', f'{sg}.surfaceShader', force=True)

    return sg


def _configure_aitoon(shader: str, tier: str, palette: dict):
    """Configura un aiToon según el tier."""
    ramp_data = palette.get(tier)
    if ramp_data is None:
        return

    if tier == 'GLOW':
        # Glow: color sólido, emission alto, sin silhouette, sin tonemap
        rgb = ramp_data  # es [r,g,b] no ramp
        mc.setAttr(f'{shader}.baseTint', rgb[0], rgb[1], rgb[2], type='double3')
        try:
            mc.setAttr(f'{shader}.emission', 1.0)
            mc.setAttr(f'{shader}.emissionColor', rgb[0], rgb[1], rgb[2],
                       type='double3')
        except Exception:
            pass
        mc.setAttr(f'{shader}.enableSilhouette', 0)
        return

    # ARMOR, JOINT, DETAIL: configurar base + tonemap (ramp)
    base_color = ramp_data[0][1]   # primer stop
    mc.setAttr(f'{shader}.baseTint', base_color[0], base_color[1], base_color[2],
               type='double3')
    mc.setAttr(f'{shader}.baseWeight', 0.95)

    # Crear el ramp del tonemap
    ramp_node = mc.shadingNode('ramp', asTexture=True,
                                name=f'{shader}_tonemap')
    _populate_ramp(ramp_node, ramp_data)
    mc.connectAttr(f'{ramp_node}.outColor', f'{shader}.tonemap', force=True)

    # Silhouette (outline cómic)
    mc.setAttr(f'{shader}.enableSilhouette', 1)
    outline_color = palette.get('outline_color', [0.0, 0.0, 0.0])
    outline_width = palette.get('outline_width', 3.0)
    mc.setAttr(f'{shader}.silhouetteColor',
               outline_color[0], outline_color[1], outline_color[2],
               type='double3')
    mc.setAttr(f'{shader}.silhouetteWidthScale', outline_width)

    # Edge detection — para resaltar biseles duros
    try:
        mc.setAttr(f'{shader}.enableEdges', 1)
        mc.setAttr(f'{shader}.creaseEdgeColor', 0.0, 0.0, 0.0, type='double3')
        mc.setAttr(f'{shader}.crease_angle_threshold', 30.0)
    except Exception:
        pass


def _populate_ramp(ramp_node: str, stops: list):
    """Llena un ramp con los stops dados [(pos, [r,g,b]), ...]."""
    # Limpiar stops por defecto (Maya crea 2 por defecto)
    for i in range(10):
        try:
            mc.removeMultiInstance(f'{ramp_node}.colorEntryList[{i}]', b=True)
        except Exception:
            break

    for i, (pos, rgb) in enumerate(stops):
        mc.setAttr(f'{ramp_node}.colorEntryList[{i}].position', pos)
        mc.setAttr(f'{ramp_node}.colorEntryList[{i}].color',
                   rgb[0], rgb[1], rgb[2], type='double3')

    # Interpolación: 0=none (cel-shading duro), 1=linear, 4=smooth
    mc.setAttr(f'{ramp_node}.interpolation', 0)


def _configure_lambert_fallback(shader: str, tier: str, palette: dict):
    """Si Arnold no está cargado, usar Lambert con el color base del tier."""
    ramp_data = palette.get(tier)
    if ramp_data is None:
        return

    if tier == 'GLOW':
        rgb = ramp_data
        mc.setAttr(f'{shader}.color', rgb[0], rgb[1], rgb[2], type='double3')
        try:
            mc.setAttr(f'{shader}.incandescence',
                       rgb[0] * 0.6, rgb[1] * 0.6, rgb[2] * 0.6,
                       type='double3')
        except Exception:
            pass
    else:
        # Usar el color medio del ramp
        mid = ramp_data[len(ramp_data) // 2][1]
        mc.setAttr(f'{shader}.color', mid[0], mid[1], mid[2], type='double3')


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _has_arnold() -> bool:
    """Verifica si MtoA (Arnold for Maya) está disponible."""
    if not MAYA_AVAILABLE:
        return False
    try:
        return 'mtoa' in (mc.pluginInfo(q=True, listPlugins=True) or [])
    except Exception:
        return False


def _load_palette(name: str) -> dict:
    """Carga una paleta desde config/materials.json."""
    data = _load_config()
    return data.get('_palettes', {}).get(name)


def _load_classification() -> dict:
    """Carga las reglas de clasificación."""
    data = _load_config()
    return data.get('_classification', {})


def _load_config() -> dict:
    """Lee config/materials.json."""
    path = os.path.join(
        os.path.dirname(__file__), '..', 'config', 'materials.json'
    )
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f'[RetroMecha][materials] Error leyendo materials.json: {e}')
    return {}


def list_palettes() -> list:
    """Lista los nombres de paletas disponibles."""
    return list(_load_config().get('_palettes', {}).keys())
