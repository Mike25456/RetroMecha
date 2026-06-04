<p align="center">
  <img src="https://img.shields.io/badge/Maya-2025-0696D7?style=flat&logo=autodesk&logoColor=white" alt="Maya 2025">
  <img src="https://img.shields.io/badge/Arnold-MtoA-FF6F00?style=flat" alt="Arnold">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-Academic-lightgrey?style=flat" alt="License">
</p>

# RETROMECHA

**Generador procedural de robots mecha para Autodesk Maya + Arnold.**

RetroMecha crea escenas completas de robots estilo mecha con terreno, iluminacion, cielo volumetrico, materiales aiStandardSurface y render a un clic. Cada generacion es reproducible via semilla y personalizable a traves de una UI dual Rapido/Pro dentro de Maya.

> Electiva Technical Art | Ricardo Mancera & Mike Castaneda

---

## Arranque rapido

### Desde el proyecto (recomendado)

Doble clic en **`Run RetroMecha.bat`** o en terminal:

```bash
python run_retromecha.py
```

| Situacion | Que hace el lanzador |
|-----------|---------------------|
| Maya **cerrado** | Abre Maya y carga el plugin automaticamente |
| Maya **abierto** | Envia el plugin a la sesion actual (Windows) |

Si no encuentra `maya.exe`, copia `retromecha.local.json.example` a `retromecha.local.json` y define la ruta de tu instalacion.

---

## Que genera

Una escena completa con un solo clic:

- **Mecha** procedural con cabeza, torso, brazos, alas y nucleo de energia — cada modulo con multiples estilos.
- **Terreno** con monumento central, plataformas, fragmentos, escombros, pilares, rampas y skyline de fondo.
- **Cielo** geometrico (polyPlane 24x24 + doble bend deformer) con material ramp palette-aware.
- **5 luces Arnold** que toman color de la paleta activa: ambiente (terreno), foco (mecha), background, y 2 mesh lights simetricas (rayos de acento).
- **Atmosfera volumetrica** (aiAtmosphereVolume) con densidad configurable.
- **Camara de render** (`Camara_for_render`) con DOF, focal 21.39, fStop 5.6, posicion fija calibrada.
- **Materiales aiStandardSurface** con 5 paletas de color + paletas aiToon (4 tiers con silhouette).
- **Animacion idle** automatica con expresiones procedurales.

---

## Interfaz

RetroMecha usa una UI dual dentro de Maya:

### Modo Rapido

3 decisiones: genera un mecha aleatorio, elige escenario, aplica paleta. Un boton y listo.

### Modo Pro

Control total con 5 pestanas:

| Tab | Contenido |
|-----|-----------|
| **MECHA** | Sub-tabs por modulo (General, Head, Arms, Torso, Wings, Nucleus). Presets, sliders avanzados, simetria, estilos independientes por lado. |
| **TERRENO** | Preset de escena, controles de monumento, plataformas, fragmentos, debris, pilares, rampas, skyline. |
| **MAT** | Paleta de colores (Default, Atardecer, Frio, Oxidado, Neon), editor individual de shader (color, difuso, brillo), boton Aplicar. |
| **ANIM** | Seleccion y aplicacion de animaciones (idle, flight, spin). |
| **RENDER** | Boton Render 1920x1080 Arnold, sliders individuales de intensidad por luz (ambient/foco/background/mesh), densidad de atmosfera, controles de camara y cielo. |

---

## Arquitectura

```
RetroMecha/
├── run_retromecha.py            # Lanzador externo (ejecutar desde Windows)
├── Run RetroMecha.bat           # Doble clic para abrir el plugin
├── main.py                      # Entrada del plugin (dentro de Maya)
│
├── core/                        # Motor procedural
│   ├── base_module.py           # Clase base de todos los modulos
│   ├── l_system.py              # Motor L-System para ramificacion
│   ├── mecha_builder.py         # Orquestador de ensamblaje
│   └── module_registry.py       # Auto-registro de modulos
│
├── modules/                     # Piezas del mecha
│   ├── head.py                  # Cabeza (helmet, drone, sentinel)
│   ├── torso.py                 # Torso (core, heavy, slim, compact)
│   ├── arm/                     # Brazos (standard, heavy, blade, cannon, shield)
│   └── wing/                    # Alas (needle, compact, fan)
│
├── terrain/                     # Generacion de terreno
│   ├── terrain_builder.py       # Constructor principal
│   ├── monument.py              # Monumento central
│   ├── platform.py              # Plataformas dispersas
│   ├── fragment.py / debris.py  # Fragmentos y escombros
│   ├── tower.py                 # Torres/pilares
│   ├── skyline.py               # Silueta de fondo
│   └── ground_plane.py          # Plano base
│
├── materials/                   # Sistema de materiales
│   ├── presets.py               # 5 paletas (Default, Atardecer, Frio, Oxidado, Neon)
│   ├── materializer.py          # Asignacion automatica mecha → shader por token
│   └── sky_material.py          # Material del cielo (aiStandardSurface + ramp)
│
├── animations/                  # Animaciones procedurales
│   ├── base.py                  # Clase base con cleanup robusto
│   ├── idle.py                  # Idle (expresiones de flotacion)
│   ├── flight.py                # Vuelo (motion path + bobbing)
│   ├── spin.py                  # Rotacion de exhibicion
│   └── registry.py              # Registro de animaciones
│
├── utils/                       # Utilidades
│   ├── maya_materials.py        # Bridge semantico aiStandardSurface
│   ├── material_assigner.py     # Paletas aiToon (4 tiers, ramps, silhouette)
│   ├── lighting.py              # 5 luces Arnold palette-aware
│   ├── atmosphere.py            # aiAtmosphereVolume
│   ├── camera.py                # Camara de render con DOF
│   ├── render.py                # Trigger de render Arnold 1920x1080
│   ├── sky.py                   # Cielo (polyPlane + bends)
│   ├── hard_surface.py          # Aristas de soporte (delimitacion)
│   ├── deform_utils.py          # Utilidades de deformacion
│   └── surface_utils.py         # Utilidades de superficie
│
├── ui/                          # Interfaz Maya
│   ├── main_window.py           # Ventana principal (Quick/Pro toggle)
│   ├── build_actions.py         # Orquestacion de generacion/random/reset
│   ├── state.py                 # Estado compartido de controles UI
│   ├── widgets.py               # Widgets reutilizables (sliders, botones, switch)
│   ├── constants.py             # Labels y maps compartidos
│   ├── scene_utils.py           # Cleanup de escena
│   └── panels/
│       ├── quick_panel.py       # Modo Rapido
│       ├── pro_panel.py         # Modo Pro (5 tabs)
│       ├── mecha_panel_v2.py    # Panel mecha con sub-tabs por modulo
│       ├── terrain_panel.py     # Panel terreno
│       ├── material_panel.py    # Panel materiales (paletas + editor shader)
│       ├── animation_panel.py   # Panel animaciones
│       └── rendering_panel.py   # Panel render (luces, atmosfera, camara, cielo)
│
├── config/                      # Configuracion editable (JSON)
│   ├── presets.json             # Presets de mecha (Balanceado, Agresivo, etc.)
│   ├── materials.json           # Paletas aiToon (industrial, oxidado, artico, carmesi)
│   ├── l_system_rules.json      # Reglas L-System
│   ├── module_advanced.json     # Specs avanzadas por modulo
│   ├── terrain_presets.json     # Presets de terreno
│   ├── terrain_rules.json       # Reglas de terreno
│   ├── monument_spec.json       # Especificacion del monumento
│   └── subpieces.json           # Configuracion de sub-piezas
│
└── launcher/                    # Deteccion de Maya + envio del script
    ├── maya_locator.py          # Busca maya.exe en el sistema
    ├── maya_runner.py           # Lanza Maya si no esta abierta
    ├── maya_process.py          # Deteccion de proceso Maya
    ├── maya_listener.py         # Listener de commandPort
    └── bootstrap_in_maya.py     # Script que Maya ejecuta al cargar
```

---

## Sistema de paletas

Cada paleta define colores para **6 shaders del mecha/terreno** (aiStandardSurface) + **4 tiers aiToon** + **cielo** + **luces**:

| Paleta | Caracter | Cielo | Accent terreno |
|--------|----------|-------|----------------|
| **Default** | Limpio, neutro | Cian degradado | Tierra calida |
| **Atardecer** | Calido, dorado | Naranja profundo | Naranja terroso |
| **Frio** | Gelido, azulado | Cian helado | Gris azulado |
| **Oxidado** | Desgastado, campo de batalla | Ambar oxidado | Oxido |
| **Neon** | Cyberpunk, saturado | Magenta neon | Violeta |

Al cambiar la paleta, **todo se sincroniza**: materiales del mecha, terreno emisivo, ramp del cielo, color de las luces ambient + mesh.

---

## Sistema de iluminacion

5 luces Arnold creadas automaticamente, palette-aware:

| Luz | Tipo | Color | Rol |
|-----|------|-------|-----|
| `luz_ambiente` | aiAreaLight quad | Accent terreno | Iluminacion del suelo |
| `foco_mecha` | aiAreaLight disk | Blanca | Foco directo sobre el mecha |
| `background` | aiAreaLight quad | Blanca | Iluminacion del fondo |
| `veam_light_izquierdo` | aiMeshLight cubo | Accent mecha | Rayo de acento izquierdo |
| `veam_light_derecho` | aiMeshLight cubo | Accent mecha | Rayo de acento derecho (simetrico en X) |

Las luces se recoloran automaticamente al cambiar de paleta. Background y mesh lights se posicionan 4 unidades delante del skyline.

---

## Reproducibilidad

Cada generacion depende de una **semilla** (`seed`):
- Una semilla fija siempre produce el mismo mecha.
- La semilla se muestra en el campo de la UI.
- Se imprime en consola con cada generacion.

---

## Requisitos

- **Autodesk Maya 2025** (o 2024+)
- **Arnold for Maya (MtoA)** — requerido para materiales aiStandardSurface, luces, atmosfera y render
- **Python 3.11+** (incluido con Maya 2025)
- **Windows 10/11** (launcher optimizado para Windows; el plugin funciona en cualquier OS con Maya)

---

## Creditos

| Rol | Persona |
|-----|---------|
| Modulos de geometria, materiales, render pipeline | Ricardo Mancera |
| Ensamblaje, L-System, terreno, animaciones, UI | Mike Castaneda |

Proyecto academico — Electiva Technical Art.
