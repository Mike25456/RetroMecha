"""
RetroMecha — materials/presets.py  v2

Añade rm_terrain_accent2_mat a todos los presets.
accent2 = variante más cálida/saturada de accent, para cables y detalles
          estructurales calientes del terreno.

Relación de colores:
  accent2.color       ≈ accent.color más saturado / más cálido
  accent2.incandescence = rm_cyan_glow_mat.incandescence × 0.35
    (brillo estructural — menos intenso que el glow del mecha)
"""

try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import (
    ensure_material, set_semantic_attr, DEFAULT_DIFFUSE_ROUGHNESS,
)

SHADER_NAMES = [
    'rm_white_armor_mat',
    'rm_graphite_mat',
    'rm_cyan_glow_mat',
    'rm_terrain_base_mat',
    'rm_terrain_dark_mat',
    'rm_terrain_accent_mat',
    'rm_terrain_accent2_mat',   # ← nuevo
]

PRESETS = {
    'Predeterminado': {
        'rm_white_armor_mat': {
            'color': (0.86, 0.84, 0.78),
            'ambientColor': (0.12, 0.12, 0.11),
            'diffuse': 0.82,
        },
        'rm_graphite_mat': {
            'color': (0.12, 0.13, 0.13),
            'ambientColor': (0.03, 0.04, 0.04),
            'diffuse': 0.72,
        },
        'rm_cyan_glow_mat': {
            'color': (0.04, 0.75, 1.0),
            'ambientColor': (0.0, 0.22, 0.28),
            'incandescence': (0.0, 0.55, 0.85),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.30, 0.31, 0.29),
            'ambientColor': (0.05, 0.05, 0.045),
            'diffuse': 0.68,
        },
        'rm_terrain_dark_mat': {
            'color': (0.13, 0.14, 0.13),
            'ambientColor': (0.025, 0.025, 0.022),
            'diffuse': 0.58,
        },
        'rm_terrain_accent_mat': {
            'color': (0.42, 0.36, 0.28),
            'incandescence': (0.0, 0.275, 0.425),
            'emission': 0.5,
            'ambientColor': (0.07, 0.055, 0.04),
            'diffuse': 0.64,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.52, 0.48, 0.38),
            'incandescence': (0.0, 0.193, 0.298),   # cyan_glow.inc × 0.35
            'emission': 0.45,
            'ambientColor': (0.08, 0.07, 0.05),
            'diffuse': 0.62,
        },
    },

    'Atardecer': {
        'rm_white_armor_mat': {
            'color': (0.95, 0.65, 0.45),
            'ambientColor': (0.15, 0.08, 0.04),
            'diffuse': 0.82,
        },
        'rm_graphite_mat': {
            'color': (0.22, 0.10, 0.06),
            'ambientColor': (0.06, 0.03, 0.02),
            'diffuse': 0.72,
        },
        'rm_cyan_glow_mat': {
            'color': (1.0, 0.45, 0.05),
            'ambientColor': (0.30, 0.10, 0.0),
            'incandescence': (0.85, 0.30, 0.0),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.34, 0.29, 0.25),
            'ambientColor': (0.08, 0.055, 0.035),
            'diffuse': 0.62,
        },
        'rm_terrain_dark_mat': {
            'color': (0.16, 0.12, 0.10),
            'ambientColor': (0.04, 0.025, 0.018),
            'diffuse': 0.55,
        },
        'rm_terrain_accent_mat': {
            'color': (0.42, 0.30, 0.20),
            'incandescence': (0.425, 0.15, 0.0),
            'emission': 0.5,
            'ambientColor': (0.09, 0.045, 0.025),
            'diffuse': 0.60,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.55, 0.38, 0.22),
            'incandescence': (0.298, 0.105, 0.0),   # × 0.35
            'emission': 0.45,
            'ambientColor': (0.10, 0.05, 0.025),
            'diffuse': 0.60,
        },
    },

    'Frio': {
        'rm_white_armor_mat': {
            'color': (0.75, 0.82, 0.90),
            'ambientColor': (0.08, 0.10, 0.14),
            'diffuse': 0.82,
        },
        'rm_graphite_mat': {
            'color': (0.08, 0.10, 0.16),
            'ambientColor': (0.02, 0.03, 0.06),
            'diffuse': 0.72,
        },
        'rm_cyan_glow_mat': {
            'color': (0.30, 0.90, 1.0),
            'ambientColor': (0.0, 0.30, 0.40),
            'incandescence': (0.10, 0.70, 0.95),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.26, 0.30, 0.33),
            'ambientColor': (0.04, 0.055, 0.07),
            'diffuse': 0.64,
        },
        'rm_terrain_dark_mat': {
            'color': (0.10, 0.12, 0.16),
            'ambientColor': (0.02, 0.03, 0.045),
            'diffuse': 0.55,
        },
        'rm_terrain_accent_mat': {
            'color': (0.31, 0.35, 0.39),
            'incandescence': (0.05, 0.35, 0.475),
            'emission': 0.5,
            'ambientColor': (0.055, 0.07, 0.09),
            'diffuse': 0.60,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.36, 0.44, 0.50),
            'incandescence': (0.035, 0.245, 0.333),  # × 0.35
            'emission': 0.45,
            'ambientColor': (0.06, 0.09, 0.11),
            'diffuse': 0.60,
        },
    },

    'Oxidado': {
        'rm_white_armor_mat': {
            'color': (0.55, 0.35, 0.20),
            'ambientColor': (0.10, 0.06, 0.03),
            'diffuse': 0.78,
        },
        'rm_graphite_mat': {
            'color': (0.28, 0.18, 0.10),
            'ambientColor': (0.08, 0.05, 0.02),
            'diffuse': 0.70,
        },
        'rm_cyan_glow_mat': {
            'color': (0.90, 0.60, 0.15),
            'ambientColor': (0.25, 0.12, 0.0),
            'incandescence': (0.70, 0.35, 0.0),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.30, 0.24, 0.18),
            'ambientColor': (0.065, 0.045, 0.03),
            'diffuse': 0.60,
        },
        'rm_terrain_dark_mat': {
            'color': (0.14, 0.10, 0.075),
            'ambientColor': (0.035, 0.025, 0.015),
            'diffuse': 0.54,
        },
        'rm_terrain_accent_mat': {
            'color': (0.40, 0.26, 0.14),
            'incandescence': (0.35, 0.175, 0.0),
            'emission': 0.5,
            'ambientColor': (0.085, 0.045, 0.02),
            'diffuse': 0.58,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.52, 0.33, 0.16),
            'incandescence': (0.245, 0.123, 0.0),   # × 0.35
            'emission': 0.45,
            'ambientColor': (0.10, 0.052, 0.022),
            'diffuse': 0.58,
        },
    },

    'Magma': {
        'rm_white_armor_mat': {
            'color': (0.95, 0.70, 0.50),
            'ambientColor': (0.18, 0.08, 0.02),
            'diffuse': 0.82,
        },
        'rm_graphite_mat': {
            'color': (0.15, 0.06, 0.04),
            'ambientColor': (0.06, 0.02, 0.01),
            'diffuse': 0.72,
        },
        'rm_cyan_glow_mat': {
            'color': (1.0, 0.30, 0.0),
            'ambientColor': (0.40, 0.05, 0.0),
            'incandescence': (0.95, 0.15, 0.0),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.32, 0.22, 0.18),
            'ambientColor': (0.08, 0.04, 0.025),
            'diffuse': 0.62,
        },
        'rm_terrain_dark_mat': {
            'color': (0.12, 0.08, 0.06),
            'ambientColor': (0.03, 0.02, 0.015),
            'diffuse': 0.54,
        },
        'rm_terrain_accent_mat': {
            'color': (0.35, 0.24, 0.18),
            'incandescence': (0.475, 0.075, 0.0),
            'emission': 0.5,
            'ambientColor': (0.08, 0.035, 0.02),
            'diffuse': 0.58,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.48, 0.28, 0.16),
            'incandescence': (0.333, 0.053, 0.0),   # × 0.35
            'emission': 0.45,
            'ambientColor': (0.10, 0.04, 0.02),
            'diffuse': 0.58,
        },
    },

    'Veneno': {
        'rm_white_armor_mat': {
            'color': (0.78, 0.92, 0.72),
            'ambientColor': (0.08, 0.14, 0.06),
            'diffuse': 0.82,
        },
        'rm_graphite_mat': {
            'color': (0.06, 0.12, 0.06),
            'ambientColor': (0.02, 0.05, 0.02),
            'diffuse': 0.72,
        },
        'rm_cyan_glow_mat': {
            'color': (0.0, 1.0, 0.20),
            'ambientColor': (0.0, 0.35, 0.05),
            'incandescence': (0.0, 0.85, 0.10),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.24, 0.30, 0.24),
            'ambientColor': (0.04, 0.07, 0.04),
            'diffuse': 0.62,
        },
        'rm_terrain_dark_mat': {
            'color': (0.08, 0.12, 0.08),
            'ambientColor': (0.02, 0.04, 0.02),
            'diffuse': 0.54,
        },
        'rm_terrain_accent_mat': {
            'color': (0.22, 0.32, 0.24),
            'incandescence': (0.0, 0.425, 0.05),
            'emission': 0.5,
            'ambientColor': (0.04, 0.08, 0.04),
            'diffuse': 0.58,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.26, 0.42, 0.28),
            'incandescence': (0.0, 0.298, 0.035),   # × 0.35
            'emission': 0.45,
            'ambientColor': (0.05, 0.10, 0.05),
            'diffuse': 0.58,
        },
    },

    'Neon': {
        'rm_white_armor_mat': {
            'color': (0.92, 0.92, 0.95),
            'ambientColor': (0.10, 0.10, 0.14),
            'diffuse': 0.82,
        },
        'rm_graphite_mat': {
            'color': (0.06, 0.06, 0.10),
            'ambientColor': (0.02, 0.02, 0.04),
            'diffuse': 0.72,
        },
        'rm_cyan_glow_mat': {
            'color': (1.0, 0.05, 0.80),
            'ambientColor': (0.35, 0.0, 0.25),
            'incandescence': (0.90, 0.0, 0.65),
            'diffuse': 0.45,
        },
        'rm_terrain_base_mat': {
            'color': (0.24, 0.25, 0.29),
            'ambientColor': (0.04, 0.04, 0.06),
            'diffuse': 0.62,
        },
        'rm_terrain_dark_mat': {
            'color': (0.075, 0.075, 0.10),
            'ambientColor': (0.018, 0.018, 0.035),
            'diffuse': 0.54,
        },
        'rm_terrain_accent_mat': {
            'color': (0.26, 0.22, 0.34),
            'incandescence': (0.45, 0.0, 0.325),
            'emission': 0.5,
            'ambientColor': (0.055, 0.04, 0.09),
            'diffuse': 0.58,
        },
        'rm_terrain_accent2_mat': {
            'color': (0.36, 0.24, 0.46),
            'incandescence': (0.315, 0.0, 0.228),   # × 0.35
            'emission': 0.45,
            'ambientColor': (0.07, 0.04, 0.12),
            'diffuse': 0.58,
        },
    },
}


def list_presets() -> list[str]:
    return list(PRESETS.keys())


def apply_preset(name: str) -> bool:
    if mc is None:
        return False
    data = PRESETS.get(name)
    if not data:
        print(f'[RetroMecha][Material] Preset desconocido: {name}')
        return False
    for shader, attrs in data.items():
        if not mc.objExists(shader):
            ensure_material(shader)
        if not mc.objExists(shader):
            print(f'[RetroMecha][Material] Shader {shader} no existe')
            continue
        set_semantic_attr(shader, 'diffuseRoughness', DEFAULT_DIFFUSE_ROUGHNESS)
        for semantic, value in attrs.items():
            set_semantic_attr(shader, semantic, value)
    print(f"[RetroMecha][Material] Preset '{name}' aplicado")
    return True