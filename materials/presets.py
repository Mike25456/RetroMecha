try:
    import maya.cmds as mc
except ImportError:
    mc = None

from utils.maya_materials import ensure_material

SHADER_NAMES = [
    "rm_white_armor_mat",
    "rm_graphite_mat",
    "rm_cyan_glow_mat",
    "rm_terrain_base_mat",
    "rm_terrain_dark_mat",
    "rm_terrain_accent_mat",
]

PRESETS = {
    "Default": {
        "rm_white_armor_mat": {
            "color": (0.86, 0.84, 0.78),
            "ambientColor": (0.12, 0.12, 0.11),
            "diffuse": 0.82,
        },
        "rm_graphite_mat": {
            "color": (0.12, 0.13, 0.13),
            "ambientColor": (0.03, 0.04, 0.04),
            "diffuse": 0.72,
        },
        "rm_cyan_glow_mat": {
            "color": (0.04, 0.75, 1.0),
            "ambientColor": (0.0, 0.22, 0.28),
            "incandescence": (0.0, 0.55, 0.85),
            "diffuse": 0.45,
        },
        "rm_terrain_base_mat": {
            "color": (0.30, 0.31, 0.29),
            "ambientColor": (0.05, 0.05, 0.045),
            "diffuse": 0.68,
        },
        "rm_terrain_dark_mat": {
            "color": (0.13, 0.14, 0.13),
            "ambientColor": (0.025, 0.025, 0.022),
            "diffuse": 0.58,
        },
        "rm_terrain_accent_mat": {
            "color": (0.42, 0.36, 0.28),
            "ambientColor": (0.07, 0.055, 0.04),
            "diffuse": 0.64,
        },
    },
    "Atardecer": {
        "rm_white_armor_mat": {
            "color": (0.95, 0.65, 0.45),
            "ambientColor": (0.15, 0.08, 0.04),
            "diffuse": 0.82,
        },
        "rm_graphite_mat": {
            "color": (0.22, 0.10, 0.06),
            "ambientColor": (0.06, 0.03, 0.02),
            "diffuse": 0.72,
        },
        "rm_cyan_glow_mat": {
            "color": (1.0, 0.45, 0.05),
            "ambientColor": (0.30, 0.10, 0.0),
            "incandescence": (0.85, 0.30, 0.0),
            "diffuse": 0.45,
        },
        "rm_terrain_base_mat": {
            "color": (0.34, 0.29, 0.25),
            "ambientColor": (0.08, 0.055, 0.035),
            "diffuse": 0.62,
        },
        "rm_terrain_dark_mat": {
            "color": (0.16, 0.12, 0.10),
            "ambientColor": (0.04, 0.025, 0.018),
            "diffuse": 0.55,
        },
        "rm_terrain_accent_mat": {
            "color": (0.42, 0.30, 0.20),
            "ambientColor": (0.09, 0.045, 0.025),
            "diffuse": 0.60,
        },
    },
    "Frio": {
        "rm_white_armor_mat": {
            "color": (0.75, 0.82, 0.90),
            "ambientColor": (0.08, 0.10, 0.14),
            "diffuse": 0.82,
        },
        "rm_graphite_mat": {
            "color": (0.08, 0.10, 0.16),
            "ambientColor": (0.02, 0.03, 0.06),
            "diffuse": 0.72,
        },
        "rm_cyan_glow_mat": {
            "color": (0.30, 0.90, 1.0),
            "ambientColor": (0.0, 0.30, 0.40),
            "incandescence": (0.10, 0.70, 0.95),
            "diffuse": 0.45,
        },
        "rm_terrain_base_mat": {
            "color": (0.26, 0.30, 0.33),
            "ambientColor": (0.04, 0.055, 0.07),
            "diffuse": 0.64,
        },
        "rm_terrain_dark_mat": {
            "color": (0.10, 0.12, 0.16),
            "ambientColor": (0.02, 0.03, 0.045),
            "diffuse": 0.55,
        },
        "rm_terrain_accent_mat": {
            "color": (0.31, 0.35, 0.39),
            "ambientColor": (0.055, 0.07, 0.09),
            "diffuse": 0.60,
        },
    },
    "Oxidado": {
        "rm_white_armor_mat": {
            "color": (0.55, 0.35, 0.20),
            "ambientColor": (0.10, 0.06, 0.03),
            "diffuse": 0.78,
        },
        "rm_graphite_mat": {
            "color": (0.28, 0.18, 0.10),
            "ambientColor": (0.08, 0.05, 0.02),
            "diffuse": 0.70,
        },
        "rm_cyan_glow_mat": {
            "color": (0.90, 0.60, 0.15),
            "ambientColor": (0.25, 0.12, 0.0),
            "incandescence": (0.70, 0.35, 0.0),
            "diffuse": 0.45,
        },
        "rm_terrain_base_mat": {
            "color": (0.30, 0.24, 0.18),
            "ambientColor": (0.065, 0.045, 0.03),
            "diffuse": 0.60,
        },
        "rm_terrain_dark_mat": {
            "color": (0.14, 0.10, 0.075),
            "ambientColor": (0.035, 0.025, 0.015),
            "diffuse": 0.54,
        },
        "rm_terrain_accent_mat": {
            "color": (0.40, 0.26, 0.14),
            "ambientColor": (0.085, 0.045, 0.02),
            "diffuse": 0.58,
        },
    },
    "Neon": {
        "rm_white_armor_mat": {
            "color": (0.92, 0.92, 0.95),
            "ambientColor": (0.10, 0.10, 0.14),
            "diffuse": 0.82,
        },
        "rm_graphite_mat": {
            "color": (0.06, 0.06, 0.10),
            "ambientColor": (0.02, 0.02, 0.04),
            "diffuse": 0.72,
        },
        "rm_cyan_glow_mat": {
            "color": (1.0, 0.05, 0.80),
            "ambientColor": (0.35, 0.0, 0.25),
            "incandescence": (0.90, 0.0, 0.65),
            "diffuse": 0.45,
        },
        "rm_terrain_base_mat": {
            "color": (0.24, 0.25, 0.29),
            "ambientColor": (0.04, 0.04, 0.06),
            "diffuse": 0.62,
        },
        "rm_terrain_dark_mat": {
            "color": (0.075, 0.075, 0.10),
            "ambientColor": (0.018, 0.018, 0.035),
            "diffuse": 0.54,
        },
        "rm_terrain_accent_mat": {
            "color": (0.26, 0.22, 0.34),
            "ambientColor": (0.055, 0.04, 0.09),
            "diffuse": 0.58,
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
        print(f"[RetroMecha][Material] Preset desconocido: {name}")
        return False
    for shader, attrs in data.items():
        if not mc.objExists(shader):
            ensure_material(shader)
        if not mc.objExists(shader):
            print(f"[RetroMecha][Material] Shader {shader} no existe")
            continue
        for attr, value in attrs.items():
            try:
                if isinstance(value, tuple):
                    mc.setAttr(f"{shader}.{attr}", *value, type="double3")
                else:
                    mc.setAttr(f"{shader}.{attr}", value)
            except Exception as e:
                print(f"[RetroMecha][Material] Error setAttr {shader}.{attr}: {e}")
    print(f"[RetroMecha][Material] Preset '{name}' aplicado")
    return True
