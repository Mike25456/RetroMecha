"""
RetroMecha - materials/sync.py
Sincronizacion centralizada de paleta entre shaders, sky y luces.

Punto de entrada unico para aplicar una paleta al setup completo:
  - Shaders del mecha (rm_white_armor / rm_graphite / rm_cyan_glow)
  - Shaders del terreno (rm_terrain_base/dark/accent)
  - Ramp del sky (top + bottom stops)
  - Color de las 5 luces (ambient + 2 veam; foco y bg son blancos)

Usado por:
  - Dropdown de paleta (material_panel._on_preset_change)
  - apply_palette_quick (cambio rapido de paleta en Quick mode)
  - _apply_materials (boton Aplicar del panel Material)
  - build_actions._apply_terrain_visuals (flujo Generar)
  - utils.render.render_now (pre-render: asegura sync)

No expone UI: la sincronizacion es implicita, sin botones.
"""

try:
    from materials.presets import list_presets, apply_preset
    from materials.sky_material import update_sky_ramp, has_sky_material
    from utils import lighting
    from utils.lighting import has_rm_lights
except Exception:
    list_presets = None
    apply_preset = None
    update_sky_ramp = None
    has_sky_material = None
    lighting = None
    has_rm_lights = None


DEFAULT_PALETTE = 'Default'


def list_palettes() -> list:
    """Paletas disponibles (las mismas que materials.presets)."""
    if list_presets is None:
        return [DEFAULT_PALETTE]
    try:
        return list_presets()
    except Exception:
        return [DEFAULT_PALETTE]


def apply_palette_full(palette_label: str) -> bool:
    """Aplica la paleta a TODO: shaders + sky_ramp + luces.

    Idempotente. Si sky_material o luces no existen, se omiten
    sin error. Llamar tras crearlos para sincronizar.
    """
    palettes = list_palettes()
    if palette_label not in palettes:
        print(f'[RetroMecha][Sync] Paleta "{palette_label}" no existe')
        return False

    # 1. Shaders del mecha y terreno
    if apply_preset is not None:
        try:
            apply_preset(palette_label)
        except Exception as e:
            print(f'[RetroMecha][Sync] Preset: {e}')

    # 2. Ramp del sky (si existe sky_material)
    if update_sky_ramp is not None and has_sky_material is not None:
        try:
            if has_sky_material():
                update_sky_ramp(palette_label)
        except Exception as e:
            print(f'[RetroMecha][Sync] Sky ramp: {e}')

    # 3. Luces (si existen)
    if lighting is not None and has_rm_lights is not None:
        try:
            if has_rm_lights():
                lighting.set_palette(palette_label)
        except Exception as e:
            print(f'[RetroMecha][Sync] Luces: {e}')

    print(f'[RetroMecha][Sync] Paleta "{palette_label}" aplicada a todo')
    return True
