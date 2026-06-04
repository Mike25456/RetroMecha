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
| `ui/main_window.py` → `build_ui()` | Builds the Maya window with Quick/Pro mode switch |
| `ui/panels/quick_panel.py` | Modo Rápido (3 decision blocks) |
| `ui/panels/pro_panel.py` | Modo Pro (tabs: Mecha/Terrain/Materials/Anim) |
| `ui/build_actions.py` | All build/random/reset/preset logic |

## Architecture

```
core/mecha_builder.py        ← orchestrator
core/module_registry.py      ← auto-register via @register()
modules/*.py                 ← geometry modules (head, arm, wing, torso)
animations/registry.py       ← auto-register via @register_animation()
animations/{flight,idle,spin}.py
materials/presets.py          ← Lambert palettes
materials/materializer.py    ← assign materials to pieces
terrain/                     ← terrain parts (monument, platform, etc.)
ui/
  state.py                   ← global CTRLS dict + seed + mode flags
  widgets.py                 ← dark theme UI widgets (mode_switch, fsl, tab_bar, etc.)
  build_actions.py           ← _safe_* accessors with try/except
  main_window.py             ← Quick/Pro switch, dynamic content
  panels/
    quick_panel.py           ← 3-block rapid mode
    pro_panel.py             ← Tabbed pro mode (mecha_v2 sub-tabs)
    rendering_panel.py       ← Arnold + Render Settings (merged from main)
```

## Critical conventions

- **No external dependencies** beyond Maya. No pip, no npm, no test framework.
- **State registry**: `ui/state.py` maintains a dict `CTRLS` mapping string names to Maya control handles. Always use `state.reg()` / `state.get()`.
- **Safe access**: always use `_safe_val()`, `_safe_opt()`, `_safe_cb()`, etc. from `build_actions.py` — they silently return defaults when controls don't exist (critical for mode switching where controls differ between Quick/Pro).
- **`clear_dynamic()`**: call before rebuilding UI on mode switch. Preserves permanent controls (`seed_field`, `main_content`). Without it, stale Maya handles accumulate and cause crashes.
- **`_switch_mode`**: must wrap in `try/finally` to reset `_UI_BUILDING` even on error. Pattern:
  ```python
  state._UI_BUILDING[0] = True
  try:
      state.clear_dynamic()
      # ... rebuild content ...
      state._MODE[0] = mode
  finally:
      state._UI_BUILDING[0] = False
  ```
- **`_on_mecha_cc`**: guards with `_UI_BUILDING` and `_APPLYING_MECHA_PRESET` to prevent recursive rebuilds.
- **Seed reproducibility**: all generation uses a seed stored in `state._SEED[0]`. Empty seed field = random.
- **Animation idle auto-play**: `_apply_idle_to_mecha()` is called in `on_generar()`, `rebuild_mecha()`, and `random_all()`.
- **Modules**: must have origin at `(0,0,0)`. Created from captured MEL history via `_TEMPLATE_nuevo_modulo.py`.
- **Auto-registration**: import a module file to trigger its `@register()` or `@register_animation()`. `main.py` lists all imports explicitly.

## How to add a new module

1. Model the piece manually in Maya, capture MEL history from Script Editor.
2. Copy `modules/_TEMPLATE_nuevo_modulo.py` → `modules/mi_pieza.py`.
3. Replace `NOMBRE_MODULO` with the registration name (e.g. `THRUSTER`).
4. Paste the converted MEL geometry inside the `generate()` method.
5. Add the style label → value mapping in `ui/constants.py` (e.g. `'Laser': 'laser'`).
6. Add slider specs in `ui/module_advanced.py` via `get_slider_specs()`.
7. Import the file in `main.py` → `_import_modules()`.
8. Wire it in `core/mecha_builder.py` → `_build_mecha()` with `self._spawn('THRUSTER', ...)`.
9. Add the sub-tab in `ui/panels/mecha_panel_v2.py` → `_render_mecha()` tab list.

## How to add a new style to an existing module

Each module reads its style from `self.params['head_style']` (etc.) in `modules/head.py`. To add a new visual variant:

1. Add the new geometry branch inside the module's `generate()` — use `self._get('param_name', default)` for parameters.
2. Register the label in `ui/constants.py` — append to the corresponding `STYLE_MAPS` dict (e.g. add `'Nuevo': 'nuevo'` to `HEAD_STYLE_LABELS`). The UI option menu in Pro mode auto-picks it up.
3. Add new advanced sliders (if needed) in `ui/module_advanced.py` → `get_slider_specs()`.
4. Materials auto-assign via token matching in `materials/materializer.py` — no manual wiring needed unless the new style introduces new tokens.

## Optimization (real-time viewport)

This tool runs entirely in Maya's viewport — every rebuild is a full scene regeneration. Keep geometry lightweight:

- Minimize polygon count in module `generate()` methods. Use low-poly primitives where possible.
- Avoid `polySmooth` or subdivision during generation. Apply as post-process via `Delimitar escena` button only when needed.
- Prefer simple transforms (move/rotate/scale) over deformers, booleans, or lattice operations.
- Each module's `generate()` is called per mecha — nested loops over hundreds of pieces multiply instantly.
- Use `self._finalize_group()` at the end of each module — avoids redundant parent/child transforms.
- Keep `modules/*.py` single-purpose: generate geometry only, no materials or animation logic.
- If a piece has many variants, use `self._get()` params to toggle geometry instead of spawning all variants then hiding.
