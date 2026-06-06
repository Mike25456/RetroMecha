# RetroMecha — AGENTS.md

## Launch

```bat
Run RetroMecha.bat        # Maya cerrado → abre + carga plugin
                          # Maya abierto → envía plugin a sesión actual
```

Requires `retromecha.local.json` (copy from `.example` and set `maya_executable`).

## Entrypoints

| File | Purpose |
|---|---|
| `main.py` → `start()` | Plugin entry inside Maya; imports modules (auto-register), calls `build_ui()` |
| `ui/main_window.py` → `build_ui()` | Builds the Maya window with Quick/Pro mode switch, header (Guardar + scene dropdown), footer (Delimitar) |
| `ui/panels/quick_panel.py` | Modo Rápido (3 big buttons + palette swatches) |
| `ui/panels/pro_panel.py` | Modo Pro (4 tabs: Mecha/Terreno/Material/Render) |
| `ui/build_actions.py` | All build/random/reset/preset logic, scene save/load/delete |
| `launcher/bootstrap_in_maya.py` | Hot-reload: purges stale modules from `sys.modules`, calls `main.start(reload_modules=True)` |

## Architecture

```
main.py                     ← entry: imports all modules, calls build_ui()

core/
  module_registry.py         ← @register(name) decorator
  base_module.py             ← BaseModule ABC with v2 pipeline
  mecha_builder.py           ← MechaBuilder orchestrator (knows global structure)
  l_system.py                ← LSystem expander + parser

modules/
  head/                      ← dispatcher + 5 styles (helmet, drone, sentinel, skull, kabuto)
  torso/                     ← dispatcher + 6 styles (core, heavy, slim, compact, samurai, insect)
  arm/                       ← dispatcher + 5 styles (standard, heavy, blade, cannon, shield)
  wing/                      ← dispatcher + 5 styles (needle, compact, fan, delta, mantle)
  _TEMPLATE_nuevo_modulo.py  ← template for new modules

animations/
  registry.py                ← @register_animation(name, label)
  base.py                    ← BaseAnimation ABC (find, resolve, _clean_all, _set_keyframes)
  idle.py, flight.py,        ← 4 registered: idle, flight, spin, charge
  spin.py, charge.py

materials/
  presets.py                 ← 7 presets × 6 shader roles (aiStandardSurface, no aiToon)
  materializer.py            ← Token-based material assignment (split by _)
  sync.py                    ← apply_palette_full(): shader → sky ramp → lights cascade
  sky_material.py            ← Sky ramp with V/Spike interpolation

terrain/
  terrain_builder.py         ← TerrainBuilder: angular zone composition, L-system rules
  monument.py, platform.py,  ← 7 registered terrain modules (MONUMENT, platform, fragment,
  fragment.py, debris.py,      debris, tower, skyline, ground_plane)
  tower.py, skyline.py,
  ground_plane.py

ui/
  state.py                   ← CTRLS dict, reg/get, clear_dynamic, _PERMANENT, flags
  constants.py               ← Style label maps, PALETTE_SWATCH_COLORS
  theme.py                   ← Color constants + helpers
  widgets.py                 ← fsl, isl, big_button, mode_switch, button_grid
  main_window.py             ← build_ui, _switch_mode, scene save/load/delete UI
  build_actions.py           ← _safe_get/set dispatch, random_all, rebuild, scene CRUD
  scene_utils.py             ← clean_scene, on_delimitar, find_mecha_group
  module_advanced.py         ← Slider specs from config/module_advanced.json
  panels/
    quick_panel.py           ← 3 decision blocks + palette swatches
    pro_panel.py             ← 4-tab layout + animation radio buttons
    mecha_panel_v2.py        ← Sub-tab navigation (head/torso/arm/wing/nucleus) + presets + sliders
    terrain_panel.py         ← Terrain preset buttons + sliders
    material_panel.py        ← Palette swatches + shader selector + per-shader sliders + ping-pong swap
    animation_panel.py       ← Animation dropdown + apply/delete
    rendering_panel.py       ← Render + lights + atmosphere + sky + camera (Arnold + Arnold Render View)

utils/
  maya_materials.py          ← ensure_material, assign_material, set/get_semantic_attr, has_arnold (CANON)
  maya_scene.py              ← force_preview_one/three
  hard_surface.py            ← Support bevel pass, n-gon triangulation
  surface_utils.py           ← snap_to_mesh, conform_to_mesh
  deform_utils.py            ← deform_pipeline: non_uniform_scale + vertex_displace
  lighting.py                ← 5-light setup (ambient, foco, background, veam left/right)
  atmosphere.py              ← aiAtmosphere density/anisotropy
  camera.py                  ← create_default_camera, delete_camera, lift_mecha
  sky.py                     ← Sky dome with 2 bend deformers
  render.py                  ← set_render_settings, render_now (Arnold 1920×1080, arnoldRenderView)

launcher/
  maya_locator.py            ← Finds maya.exe (registry, %MAYA_LOCATION%, PATH)
  maya_process.py            ← Detects running Maya via tasklist
  maya_runner.py             ← Orchestrates find → listener → send or launch
  maya_listener.py           ← MEL commandPort :7001 (runs inside Maya)
  maya_install.py            ← Copies files + injects userSetup.py
  bootstrap_in_maya.py       ← Hot-reload: purge sys.modules, main.start()

config/
  l_system_rules.json        ← L-System rewrite rules (T→HEAD, A→ARM, etc.)
  module_advanced.json       ← Slider specs per module
  monument_spec.json         ← Design spec for 5-plane monument
  presets.json               ← 6 mecha presets
  subpieces.json             ← Sub-piece spawning spec per module
  terrain_presets.json       ← 4 terrain presets
  terrain_rules.json         ← Terrain L-System rules (5 layers)
```

## Styles Inventory (21)

| Module | Styles |
|--------|--------|
| **Head** | helmet, drone, sentinel, skull, kabuto |
| **Torso** | core, heavy, slim, compact, samurai, insect |
| **Arm** | standard, heavy, blade, cannon, shield |
| **Wing** | needle, compact, fan, delta, mantle |

## Animations Registered (4)

| Key | Label | Duration | Description |
|-----|-------|----------|-------------|
| `idle` | Idle | 120f | Floating expressions (auto-play en cada build) |
| `flight` | Vuelo | 8s | Figure-8 motion path + bobbing (bbox adaptativo) |
| `spin` | Spin | 144f | Exhibition rotation |
| `charge` | Carga | 150f | 5s cycle, 3 tremor freqs (18, 27.3, 41.7 Hz), root elevation, head tilt, arm fold, wing open |

## Material Presets (7)

Predeterminado, Atardecer, Frio, Neon, Oxidado, Magma, Veneno

Each defines 6 shader roles: `white_armor`, `graphite`, `cyan_glow`, `terrain_base`, `terrain_dark`, `terrain_accent`

## Lighting Rig (5 lights)

| Name | Type | Color source |
|------|------|-------------|
| `luz_ambiente` | aiAreaLight quad | terrain_accent |
| `foco_mecha` | aiAreaLight disk | White |
| `background` | aiAreaLight quad | White |
| `veam_light_izquierdo` | aiMeshLight cube | cyan_glow accent |
| `veam_light_derecho` | aiMeshLight cube | cyan_glow accent (X-sym) |

## Camera Specs

- Name: `Camara_for_render`
- Translation: `(0, 0.62, 20.715)`, Rotation: `(6.6, 0, 0)`
- Focal Length: 21.387 mm, f/Stop: 5.6, DOF: ON
- Focus distance: dinámica (distancia real cámara→mecha)
- **Render camera fix**: `render_now()` reposiciona con `setAttr` directo (sin delete+recreate). `frame_mecha=False`.

## Mecha Presets (6)

balanced, aggressive, compact, asymmetric, aerial, sentinel

## Terrain Presets (4)

avanzada, hangar, campo_de_batalla, centinela

## Critical Conventions

### UI & State
- **No external dependencies** beyond Maya. No pip, no npm, no test framework.
- **State registry**: `ui/state.py` maintains `CTRLS` dict. Use `state.reg()` / `state.get()`. `_PERMANENT` set = `{'main_content', 'scene_menu'}` — survive `clear_dynamic()`.
- **`clear_dynamic()`**: call before rebuilding UI on mode switch. Removes all controls not in `_PERMANENT`.
- **`_switch_mode`**: set `state._MODE[0] = mode` **antes** del `try`. Wrap in `try/finally`:
  ```python
  state._UI_BUILDING[0] = True
  state._MODE[0] = mode
  try:
      state.clear_dynamic()
      # rebuild content...
  finally:
      state._UI_BUILDING[0] = False
  ```
- **Safe control access**: `_safe_get(ctrl, kind, flag)` / `_safe_set(ctrl, val, kind, flag)` con dispatch dict `_MC` por tipo (`fsl`, `isl`, `opt`, `cb`, `txt`). Reemplaza 9 funciones antiguas.
- **`_UI_BUILDING` / `_APPLYING_MECHA_PRESET`**: guards en `_on_mecha_cc` y otras callbacks para evitar rebuild recursivo.
- **Slider drag debounce**: `_on_mecha_drag` usa throttle 120ms (`time.time()`). `changeCommand` (mouse release) hace rebuild final.
- **`button_grid()`** en `widgets.py`: helper que itera en filas de 4 con `rowLayout`. Usado en: mecha preset buttons, style buttons, terrain preset buttons, shader tabs.
- **Radio buttons en pares**: cada opción binaria (Brazos, Alas, Simetría, Anillos) usa un par `radioButton` en su propio `radioCollection` con `onCommand` (NO `on_cc`, NO `data=str` — `data` solo acepta `int`).
- **Booleanos sin controles UI**: `_collect_mecha`, `_toggle_symmetry_ui`, `_toggle_module_disabled` leen de `state._MECHA_PARAMS` directamente, no de checkboxes.
- **Mecha style buttons**: reemplazan dropdowns. Escriben en `state._MECHA_PARAMS` y disparan `rebuild_mecha()`. `_resolve_style` lee de `state._MECHA_PARAMS` como fallback.
- **Presets como botones**: iluminación en cian al hacer clic. Mismo patrón que terreno. Usan `button_grid` con filas de 4.
- **Palette swatches en Quick y Pro**: ambos leen de `PALETTE_SWATCH_COLORS` en `ui/constants.py`.
- **`current_palette_label()`** usa exclusivamente `state._QUICK_PALETTE[0]` (no hay dropdown).
- **Scene dropdown**: optionMenu con `changeCommand` que carga escena. Guardar con promptDialog. Eliminar con botón ✕ + confirmDialog. `_SCENE_GUARD` evita recursión. Los `menuItem` usan `parent=menu` explícito.

### Materials
- **aiToon eliminado completamente**: solo `aiStandardSurface` con Lambert presets.
- **Materiales centralizados vía materializer**: módulos NO llaman `assign_material`. `materialize_mecha()` asigna post-build.
- **Matching por tokens**: split por `_`. Patrones multi-token (ej. `_MULTI_CYAN`) tienen prioridad sobre single-token.
- **Terreno**: resolver separado — monumentos/towers/skylines/platforms/pilares → `white_armor`, resto → `graphite`.
- **Shader reads/writes**: usar `get_semantic_attr` / `set_semantic_attr` (mapean `color→baseColor`, `diffuse→base`, `incandescence→emissionColor`).
- **Ping-pong terrain swap**: dos sets de shaders swap (`_pingA` / `_pingB`) pre-creados. En cada cambio de paleta se colorean ambos y se asigna el opuesto al que estaba en las caras del terreno. Sin creación/eliminación de nodos.
- **Sky bounce**: se asigna temp shader al sky (invalida GPU cache), inmediatamente se restaura el material real.
- **`has_arnold`**: canon único en `utils/maya_materials.py:68`. Los demás archivos importan desde ahí.
- **`_rematerialize_terrain_shapes`**: acepta `replacements` dict para asignación por-face.

### Build & Scene
- **Seed**: `state._SEED[0]` maneja la semilla. `_resolve_seed()` genera random si no hay semilla.
- **`on_generar()`**: limpia escena, construye mecha + terreno, aplica palette, lift, cámara, sky+luces, idle+play.
- **Auto-idle**: `_apply_idle_to_mecha()` en `on_generar()`, `rebuild_mecha()`, `random_all()`. Siempre seguido de `mc.play(forward=True)`.
- **Render pausa timeline**: `mc.play(state=False)` antes de renderizar. Al cambiar animación o regenerar se reanuda.
- **Delimitar**: smooth preview level 3. Al regenerar vuelve a level 1.
- **Render view**: `arnoldRenderView` con `minimize=False` + `showWindow`. No se usa `deleteUI`.
- **Camara**: si existe se reposiciona con `setAttr` directo + `lock_camera('Camara_for_render', False/True)` + `look_through_camera('Camara_for_render')`.
- **`_build_mecha`**: `mc.makeIdentity()` post-lift, freezea root. Animaciones no freezean de nuevo.
- **Terreno batch parent**: `_spawn` acumula en `_all_pieces`, batch parent al final antes de support_edges/materialize. `polyCube(ch=False)` en debris/rampas. Default debris 80→50.
- **Scene save/load**: `config/saved_scenes.json`. Persiste seed + palette + terrain_preset + mecha_params + terrain_params.

### Modules
- **Auto-registration**: `@register('THRUSTER')` en class. Importar el archivo lo registra. `main.py._import_modules()` importa todo explícitamente.
- **Style dispatcher**: cada parte (head, torso, arm, wing) tiene un módulo dispatcher que delega a `style_*.py` via dict `_STYLES`.
- **Dataclasses `*Tune`**: `HeadTune`, `TorsoTune`, `NucleusTune`, `ArmTune`, `WingTune` — frozen dataclasses con `from_params(getter)`.
- **`BaseModule.v2` pipeline**: `generate()` → `_build_X()` → `_deform_mesh()` → `_attach_subpieces()` → `_cleanup_history()` → `_finalize_group()`.
- **`finish()` vs `finish_bevel()`**: `finish()` = legacy (smoothness + delete history); `finish_bevel()` = con bevel + softEdge. Samurai e Insect usan `finish_bevel()`.
- **Reactor intercambiable por torso**: si `nucleus_style` coincide con el reactor nativo → interno; si no → `style_base.build_reactor()`.
- **Reactores**: ring, column, orb, cross, orb_cluster. cross y orb_cluster usan posicionamiento local (partes en `(0,0,offset)`, grupo movido a `(cx, cy, cz+0.04)`).
- **Arm attach point**: `_ARM_SHOULDER_JOINT_Y = 0.60` en mecha_builder.py.
- **Material tokens**: piezas de kabuto llevan token `armor` en el nombre.

### L-System
- `config/l_system_rules.json`: `T→HEAD, A→ARM, W→WING, J→JOINT, N→NUCLEUS, P→PANEL, C→CONNECTOR, S→SUB`
- `core/l_system.py`: `DEFAULT_RULES`, `SYMBOL_TO_MODULE` dict, `expand(iterations, rules)`, `parse_to_instructions()`
- Terrain L-System: `config/terrain_rules.json` (5 layers: skyline/monument/mecha+platforms/fragments/debris)
- Iteraciones: mecha=2, terrain=2 (recomendado)

### Optimization
- Minimizar polígonos en módulos. Sin polySmooth/subdiv durante generación.
- Preferir transforms simples sobre deformers/booleans/lattice.
- `self._finalize_group()` al final de cada módulo.
- Módulos: solo geometría (no materiales ni animación).
- Usar `self._get()` para togglear geometría, no spawnear todo y ocultar.

## How to add a new module

1. Model the piece manually in Maya, capture MEL history from Script Editor.
2. Copy `modules/_TEMPLATE_nuevo_modulo.py` → `modules/mi_pieza.py`.
3. Replace `NOMBRE_MODULO` with the registration name (e.g. `THRUSTER`).
4. Paste the converted MEL geometry inside the `generate()` method.
5. Add the style label → value mapping in `ui/constants.py`.
6. Add slider specs in `ui/module_advanced.py` via `get_slider_specs()`.
7. Import the file in `main.py` → `_import_modules()`.
8. Wire it in `core/mecha_builder.py` → `_build_mecha()` with `self._spawn('THRUSTER', ...)`.
9. Add the sub-tab in `ui/panels/mecha_panel_v2.py`.

## How to add a new style to an existing module

1. Add geometry branch inside the module's `generate()` — use `self._get('param_name', default)` for params.
2. Register the label in `ui/constants.py` → append to the corresponding `STYLE_MAPS` dict.
3. Add new advanced sliders (if needed) in `ui/module_advanced.py` → `get_slider_specs()`.
4. Materials auto-assign via token matching in `materials/materializer.py`.

## Hot-reload Flow

```python
# bootstrap_in_maya.py
_purge_stale_modules()      # borra módulos stale de sys.modules
main.start(reload_modules=True)  # reimporta todo + rebuild UI
```

## Pro Mode Tab Structure

```
┌─────────────────────────────────┐
│  [MECHA] [TERRENO] [MATERIAL] [RENDER]  │
├─────────────────────────────────┤
│  ◉ Vuelo  ○ Spin  ○ Carga       │ (animación radio buttons, siempre visibles)
├─────────────────────────────────┤
│                                 │
│  MECHA sub-tabs:                │
│  [CABEZA] [TORSO] [BRAZO] [ALA] [NUCLEO] │
│                                 │
│  Presets: [row of 4 buttons]    │
│  Estilos: [row of buttons]      │
│  Sliders: [height, detail...]   │
│  Toggles: [Brazos] [Alas]       │
│           [Simetría] [Anillos]  │
└─────────────────────────────────┘
```
