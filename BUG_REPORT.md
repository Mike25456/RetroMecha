# Bug: Estilos no actualizan terreno en viewport

## Resumen
Cuando se genera el mecha primero y luego el escenario por separado (botones
"Ensamblar Mecha" + "Ensamblar Escenario"), los botones de estilo (swatches)
no actualizan los colores del terreno en el viewport, aunque los valores de los
shaders SÍ cambian correctamente. El botón "Ensamblar escena" (todo junto)
funciona perfectamente.

## Síntomas
- Shaders del terreno tienen los valores correctos (verificado via debug:
  `rm_terrain_base_mat.baseColor` sí cambia al color del preset seleccionado).
- Mallas del terreno están correctamente conectadas a sus Shading Groups.
- Conexiones SG → shader (`.outColor`) son correctas.
- Mecha cambia de color correctamente — solo el terreno no se actualiza.
- Cielo (sky) se ve completamente blanco aunque el ramp tenga colores correctos.
- Segunda generación de escenario (click "Ensamblar Escenario" otra vez) hace
  que los swatches funcionen correctamente.
- El botón "Ensamblar escena" (todo junto) funciona desde la primera vez.

## Diagnóstico
**El bug NO es de lógica de datos** — los valores `baseColor`, `base`, `emission`
se setean correctamente via `setAttr`. Las conexiones del DG (shader → SG → mesh)
son correctas. **El bug es del viewport de Maya**: no re-evalúa el GPU cache
cuando los atributos del shader cambian mediante `setAttr` en shaders existentes,
si las mallas ya estaban asignadas a ese SG.

## Reproducción
1. Abrir herramienta (sin swatch seleccionado)
2. Click "Ensamblar Mecha" → mecha generado (shaders con Predeterminado)
3. Click "Ensamblar Escenario" → terreno generado (shaders con Predeterminado)
4. Click swatch "Magma" → mecha cambia, terreno NO cambia visualmente
5. Click "Ensamblar Escenario" otra vez (2da vez)
6. Click swatch "Magma" → terreno SÍ cambia (funciona)

## Intentos fallidos

| # | Qué se probó | Código | Resultado |
|---|--------------|--------|-----------|
| 1 | `_apply_terrain_visuals(preset)` en `_select_swatch` | Llamar la función completa de sincronización (crea sky+luces+sync) | Crea sky y luces cuando solo hay mecha. Sin mejora. |
| 2 | `materialize_terrain()` en `_select_swatch` | Reasignar shaders a mallas existentes via `mc.sets(forceElement=sg)` | No-op cuando la malla ya está en ese SG. Sin mejora. |
| 3 | `mc.dgdirty(shader)` en 6 shaders + `force_preview_one()` | Marcar nodos como dirty + forzar displaySmoothness | Sin mejora. |
| 4 | Toggle viewport panel `wireframe → shaded` | `modelEditor(displayAppearance='wireframe')` luego restaurar | Rompió la sincronización en 2da generación. |
| 5 | Doble pasada en `rebuild_terrain_only()` | Construir terreno 2 veces en同一 llamada | Sin mejora. |
| 6 | Reordenar `_apply_terrain_visuals`: `apply_palette_full` ANTES de sky/luces | Aplicar preset a shaders primero | Sin mejora. |
| 7 | Toggle visibilidad OFF→ON en grupos `rm_terrain_*` | `setAttr(visibility, False/True)` | Sin mejora. |

## Observaciones clave

1. **`on_generar` (Ensamblar escena) funciona**: la única diferencia real es que
   `clean_scene()` elimina TODO (incluyendo mecha + shaders), y luego todo se
   reconstruye desde cero en la MISMA llamada a `scene_update`.

2. **Segunda generación de escenario funciona**: cuando se destruyen y recrean
   las mallas del terreno, Maya crea nuevas entradas en el GPU cache que sí
   recogen los valores actuales de los shaders.

3. **El viewport de Maya es el culpable**: los datos (shader attributes + SG
   connections + mesh membership) son 100% correctos según debug. El GPU cache
   simplemente no se invalida cuando cambian atributos de shader mediante
   `setAttr` ordinario.

## Posibles soluciones aún no probadas

### A. Reemplazar `_select_swatch` con recreación forzada de shaders
En vez de cambiar atributos via `setAttr`, ELIMINAR y RECREAR los 3 shaders
de terreno con `mc.delete()` + `ensure_material()`. Esto fuerza a Maya a crear
nuevos nodos DG, lo que garantiza que el GPU cache los procese desde cero.

```python
for name in ('rm_terrain_base_mat', 'rm_terrain_dark_mat', 'rm_terrain_accent_mat'):
    if mc.objExists(name):
        mc.delete(name)
```

Como `materialize_terrain()` llama a `ensure_material()`, las mallas se
reasignan automáticamente al siguiente rebuild. En `_select_swatch`, tras borrar
los shaders, llamar `apply_color_preset_quick` que llama `apply_preset` que
detecta que no existen y los crea via `ensure_material` con los valores del preset.

**Riesgo**: perder conexiones de animación u otros nodos que referencien
los shaders. Pero los shaders del terreno no deberían tener animación.

### B. Usar `arnoldRenderView` refresh
El viewport de Arnold tiene su propio mecanismo de refresco. Forzar una
actualización del Arnold Render View podría sincronizar los shaders:

```python
import mtoa.utils as mutils
mutils.updateViewport()
```

### C. Forzar rebuild de materiales Arnold via API
Usar el comando `arnoldRefreshViewport()` o `maya.utils` para forzar la
actualización de la caché de Arnold:

```python
import maya.utils
maya.utils.executeDeferred('arnoldRefreshViewport()')
```

### D. Disable/enable viewport override en los meshes
Algo más agresivo: cambiar `overrideEnabled` y `overrideDisplayType` en
cada mesh del terreno para forzar a Maya a re-procesarlas:

```python
for mesh in terrain_meshes:
    mc.setAttr(f'{mesh}.overrideEnabled', True)
    mc.setAttr(f'{mesh}.overrideEnabled', False)
```

### E. Solución estructural: unificar los botones
Si el bug es imposible de resolver por limitaciones del viewport de Maya,
la solución más robusta es cambiar la UI para que el botón "Ensamblar
Escenario" no exista como acción separada. En vez de eso, el botón
"Ensamblar escena" es el único camino: genera mecha + terreno siempre
juntos. El usuario puede regenerar el escenario individualmente solo
después de que el mecha ya existe (2da generación en adelante).

Esto aprovecha el hecho de que la 2da generación SÍ funciona.

## Conclusión
Es un bug del GPU viewport cache de Maya con `aiStandardSurface` cuando
los atributos se modifican via `setAttr` estándar en shaders que ya tienen
mallas asignadas. La solución más pragmática es probablemente la opción A
(recrear shaders) o la opción E (unificar botones).
