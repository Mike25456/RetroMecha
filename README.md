# RetroMecha — Guía del Proyecto

Herramienta de generación procedural de robots/mechas para Autodesk Maya.
Electiva Technical Art · Ricardo Mancera & Mike Castañeda

---

## Arranque rápido

```python
# Desde el bridge de VS Code → Maya, ejecutar:
exec(open('ruta/absoluta/a/RetroMecha/main.py').read())
```

O si el bridge ya apunta a la carpeta del proyecto:
```python
import main
```

---

## Estructura del proyecto

```
RetroMecha/
├── main.py                    ← Punto de entrada (ejecutar este)
├── core/
│   ├── base_module.py         ← Clase base — NO modificar la interfaz
│   ├── l_system.py            ← Motor L-System
│   ├── mecha_builder.py       ← Orquestador de ensamblaje
│   └── module_registry.py     ← Auto-registro de módulos
├── modules/
│   ├── _TEMPLATE_nuevo_modulo.py  ← Copiar para crear módulos nuevos
│   ├── head.py                ← Cabeza (placeholder → reemplazar)
│   ├── torso.py               ← Torso
│   ├── arm.py                 ← Brazo
│   └── wing.py                ← Ala
├── layers/
│   └── panel_layer.py         ← Post-proceso: paneles decorativos
├── config/
│   ├── l_system_rules.json    ← Reglas L-System (editable sin código)
│   └── presets.json           ← Presets de parámetros
└── ui/
    └── main_window.py         ← UI Maya (tabs Mecha / Materiales)
```

---

## Cómo agregar un módulo nuevo

1. Modela la pieza en Maya manualmente.
2. Captura el historial MEL (ver instrucciones en `_TEMPLATE_nuevo_modulo.py`).
3. Copia el template → renómbralo (ej: `modules/thruster.py`).
4. Pasa el template + el historial MEL al AI (ver prompt en el template).
5. Valida que el módulo generado tenga el origen en `(0,0,0)`.
6. Agrega una línea en `main.py`: `import modules.thruster`.
7. Usa el módulo en `mecha_builder.py` con `self._spawn('THRUSTER', ...)`.

---

## Workflow con OpenCode / Claude

### Generación de módulos desde MEL
Ver el prompt documentado en `modules/_TEMPLATE_nuevo_modulo.py`.

### Contexto mínimo que el AI necesita saber
Incluir siempre en el prompt:
- El template completo del módulo
- El fragmento MEL de la pieza específica
- El nombre del módulo (`MODULE_NAME`)
- Qué parámetros de `self.params` afectan la pieza

### Qué NO pedirle al AI
- Lógica de ensamblaje global (eso es de `mecha_builder.py`)
- Código de UI Maya
- Cambios al Registry o a `base_module.py`

### Para modificar parámetros del L-System
Editar `config/l_system_rules.json` directamente — no requiere código Python.

---

## Reproducibilidad

Toda generación depende de una **semilla** (`seed`).
- Una semilla fija → siempre produce el mismo mecha.
- La semilla se puede escribir manualmente en el campo de la UI.
- Se imprime en consola con cada generación para poder reproducirla.

---

## División de trabajo sugerida (equipo)

| Área | Archivos | Responsable |
|------|----------|-------------|
| Módulos de geometría | `modules/*.py` | Ricardo |
| Ensamblaje y L-System | `core/mecha_builder.py`, `core/l_system.py` | Mike |
| UI | `ui/main_window.py` | Cualquiera |
| Capas (paneles, materiales) | `layers/*.py` | Ambos |
| Config/Presets | `config/*.json` | Ambos |

Los archivos en `core/` son de **dominio compartido** — comunicar antes de modificar.
Los archivos en `modules/` son **independientes** — se pueden trabajar en paralelo sin conflictos.
