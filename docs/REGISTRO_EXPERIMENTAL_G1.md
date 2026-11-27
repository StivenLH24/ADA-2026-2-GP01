# Registro experimental — Grupo G1

**Integrante:** Johan Stiven Osorio Grisales  
**Grupo:** G1  
**Semana:** 2  
**Proyecto:** Proyecto Oráculo — Análisis y Diseño de Algoritmos (2026-B)

Este documento distingue la exploración inicial de la ejecución formal de búsqueda por coordenadas y su validación. Ningún resultado se presenta como óptimo global demostrado.

> **Estado actualizado al 27-11-2026:** las secciones anteriores de búsqueda y validación describen el experimento del catálogo v1 y se conservan como registro histórico. Los resultados vigentes del catálogo v2 están documentados al final de este archivo. No comparar directamente las métricas v1 y v2: cambiaron las cinco ranuras del catálogo.

## Entorno comprobado

- Entorno: Google Colab.
- Python: 3.13.16.
- PyTorch: 2.11.0+cu130.
- GPU: NVIDIA Tesla T4.
- CUDA disponible: sí.
- Modelo: Qwen/Qwen3-1.7B.
- Dispositivo del modelo: cuda:0.
- Memoria GPU registrada después de cargar el modelo: aproximadamente 3.4 GB.

## Datos y espacio de búsqueda

- Registros visibles: 450.
- Instancias de búsqueda: 100.
- Instancias de validación: 87.
- Instancias descartadas por la función `dividir`: 263.
- Ranuras: rol, estrategia, formato, estilo y cierre.
- Alternativas por ranura: 8.
- Temperatura usada: 0.0.
- Espacio de configuraciones a temperatura 0.0: 8^5 = 32.768.
- Precisión: proporción de instancias que satisfacen todas las restricciones (evaluación todo-o-nada por instancia).

## Calibración exploratoria anterior

### Primera muestra

Se evaluaron las referencias LIMPIA y PESADA sobre las primeras 10 instancias de búsqueda. Ambas obtuvieron 0/10 instancias correctas. Esta muestra inicial no permitió distinguir las configuraciones.

### Muestra aleatoria reproducible de 40 instancias

La muestra se seleccionó con `random.Random(2026)` y contiene los IDs:

`372, 488, 610, 611, 683, 369, 439, 648, 673, 634, 553, 639, 626, 603, 645, 565, 441, 309, 659, 357, 371, 472, 363, 570, 310, 694, 750, 411, 542, 443, 518, 526, 537, 743, 353, 516, 362, 471, 446, 386`.

| Configuración | Correctas | Fallidas | Precisión |
|---|---:|---:|---:|
| LIMPIA | 5 | 35 | 12,5 % |
| PESADA | 0 | 40 | 0,0 % |

Esta calibración pertenece a la etapa exploratoria previa y no debe confundirse con la búsqueda formal sobre las 100 instancias.

## Búsqueda por coordenadas — ejecución completada

### Parámetros

- Método: búsqueda por coordenadas con evaluación escalonada.
- Configuración inicial reproducible: `rol=1`, `estrategia=5`, `formato=1`, `estilo=3`, `cierre=6`, `temperatura=0.0`.
- Semilla: 2026.
- Screening: 10 instancias por alternativa.
- Finalistas refinados: 2 por ranura.
- Refinamiento y aceptación: conjunto completo de 100 instancias.
- Rondas: 1.
- Criterio de aceptación: aceptar un cambio solo si su precisión sobre las 100 instancias es estrictamente superior a la precisión actual.
- Criterio de parada: finalizar la ronda sin mejoras aceptadas.

### Baseline

La configuración inicial obtuvo 9/100 instancias correctas, equivalente a 9,0 %.

### Resultados del refinamiento

| Ranura | Índice candidato | Correctas / 100 | Precisión | Decisión |
|---|---:|---:|---:|---|
| rol | 0 | 7 | 7,0 % | Rechazado |
| rol | 2 | 8 | 8,0 % | Rechazado |
| estrategia | 0 | 6 | 6,0 % | Rechazado |
| estrategia | 1 | 6 | 6,0 % | Rechazado |
| formato | 7 | 5 | 5,0 % | Rechazado |
| formato | 0 | 9 | 9,0 % | Rechazado (igual al baseline, no mejora estricta) |
| estilo | 0 | 8 | 8,0 % | Rechazado |
| estilo | 1 | 6 | 6,0 % | Rechazado |
| cierre | 0 | 4 | 4,0 % | Rechazado |
| cierre | 1 | 7 | 7,0 % | Rechazado |

En el screening, las alternativas se filtraron con 10 instancias. Como el oráculo puntúa cada instancia de forma todo-o-nada, varias alternativas obtuvieron 0/10; el refinamiento sobre el conjunto completo permitió distinguirlas. El índice 0 de formato empató el baseline con 9/100 y no se aceptó porque el criterio estaba definido como mejora estricta.

### Resultado de búsqueda

- Evaluaciones completas: 46.
- Coordenadas resumidas: 5/5.
- Cambios aceptados: 0.
- Precisión final de búsqueda: 9/100 = 9,0 %.
- Configuración mejor encontrada:

```json
{
  "rol": 1,
  "estrategia": 5,
  "formato": 1,
  "estilo": 3,
  "cierre": 6,
  "temperatura": 0.0
}
```

La ronda terminó sin mejoras aceptadas. El resultado es la mejor configuración observada por esta heurística y este presupuesto; no demuestra optimalidad global.

## Validación final independiente

Se ejecutó explícitamente `oraculo.validar` sobre la configuración mejor encontrada, con la partición de validación completa (87 instancias) y semilla 2026.

- Correctas: 8/87.
- Fallidas: 79/87.
- Precisión: 9,2 %.

Familias que aparecen con mayor frecuencia en las trazas de validación:

| Primera familia de fallo reportada | Frecuencia |
|---|---:|
| `last_word:last_word_sent` | 6 |
| `punctuation:punctuation_dot` | 6 |
| `letters:letter_counting` | 5 |
| `copy:repeat_phrase` | 5 |
| `first_word:first_word_sent` | 4 |
| `keywords:no_adjacent_consecutive` | 4 |
| `keywords:word_once` | 4 |
| `language:response_language` | 3 |

El oráculo registra la primera familia que falla en cada respuesta, no todas las restricciones incumplidas. La validación es una estimación sobre instancias visibles reservadas; no es la evaluación privada que realizará el docente.

La cercanía entre 9,0 % de búsqueda y 9,2 % de validación no implica alto rendimiento absoluto. El porcentaje de aciertos sigue siendo bajo.

## Archivos persistentes y reproducibilidad

En Google Drive se conservaron:

- `ADA_G1/cache_oraculo_G1.json`: 1.438 respuestas almacenadas en el archivo entregado para este registro.
- `ADA_G1/historial_coordinate_search_G1.json`: 46 evaluaciones completas y cinco resúmenes de coordenadas.

La caché incluye las 100 instancias de búsqueda y las 87 instancias de validación para la configuración ganadora, además de las generaciones de screening y refinamiento.

La reanudación se implementó en `src/reanudador.py`. Las evaluaciones completas se omiten al restaurar el historial y las respuestas parciales que existan en la caché del oráculo pueden reutilizarse.

## Limitaciones y trabajo pendiente

1. Esta primera búsqueda terminó, pero no mejoró el baseline de 9,0 %.
2. El método explora un cambio de ranura a la vez; puede quedar atrapado en un óptimo local y no detectar sinergias entre cambios simultáneos.
3. Las trazas fueron almacenadas, pero esta versión no las usa todavía como criterio explícito para podar o proponer combinaciones.
4. Una estrategia complementaria debe compararse con el mismo modelo, temperatura, partición de búsqueda y presupuesto claramente declarado.
5. No se afirma optimalidad global.
6. La formalización y la reducción desde 3-SAT solicitadas por la guía específica de ADAG1 deben demostrarse rigurosamente antes de considerarse concluidas.
7. La evaluación privada del docente es distinta de `oraculo.validar` sobre las 87 instancias visibles.

## Reproducibilidad

Modelo Qwen/Qwen3-1.7B, temperatura 0.0, semilla 2026 para el screening, 10 instancias de screening, dos finalistas por coordenada, 100 instancias para el refinamiento, una ronda y aceptación solo ante mejora estricta.


## Estrategia complementaria preparada: búsqueda por pares guiada por trazas

Después de completar Coordinate Search se implementó `src/busqueda_pares_guiada.py`. El objetivo es explorar posibles interacciones entre dos ranuras a partir de los aciertos complementarios y la diversidad de familias de primera falla observados en los refinamientos individuales.

Parámetros propuestos: muestra de screening de 40 instancias, seis pares priorizados, dos finalistas, refinamiento sobre las 100 instancias de búsqueda y semilla 2026. La selección de pares usa la unión de IDs superados por los candidatos individuales como señal heurística de complementariedad; el resultado combinado se verifica realmente con el oráculo. La diversidad de familias de fallo se emplea como criterio secundario. La implementación usa como referencia la evaluación completa de la configuración final registrada en `configuracion_actual` (21/100 en v2), que puede diferir del baseline inicial (12/100). Los candidatos son refinamientos completos de una sola ranura alrededor de esa configuración final. La diversidad se calcula por familia general de primera falla (`keywords`, `punctuation`, etc.), no por identificador individual de restricción.

**Estado:** código implementado y pruebas unitarias añadidas, pero experimento con Qwen todavía no ejecutado. Por tanto, no existe aún una comparación empírica entre Coordinate Search y la búsqueda por pares. La configuración de `entrega.json` continúa siendo la mejor observada en Coordinate Search hasta que un segundo experimento termine y, si mejora, pase validación.


## Catálogo versión 2 — ejecución completada

Se ejecutó la búsqueda con el catálogo oficial de cinco ranuras: `rol`, `estrategia`, `formato`, `verificacion` y `recordatorio`. Cada ranura tiene ocho alternativas; temperatura fija 0.0. La rama de trabajo es `catalogo-v2-g1`.

### Entorno y partición

- Entorno: Google Colab Free.
- GPU: NVIDIA Tesla T4.
- Modelo: Qwen/Qwen3-1.7B.
- Temperatura: 0.0.
- Semilla: 2026.
- Dataset visible: 450 instancias (100 búsqueda, 87 validación, 263 descartadas).
- Caché e historial: archivos independientes con sufijo `G1_v2`; no se mezclan con los artefactos v1.

### Búsqueda

- Baseline v2: 12/100 = 12,00 %.
- Evaluaciones registradas: 46.
- Mejor precisión observada en búsqueda: 21/100 = 21,00 %.
- La recuperación desde checkpoint y caché persistente permitió continuar la ejecución sin repetir las generaciones ya almacenadas.

Configuración final observada:

```json
{
  "rol": 1,
  "estrategia": 2,
  "formato": 0,
  "verificacion": 4,
  "recordatorio": 4,
  "temperatura": 0.0
}
```

Esta configuración es la mejor observada por Coordinate Search con el presupuesto ejecutado; no se afirma que sea un óptimo global.

### Validación independiente

- Correctas: 19/87.
- Fallidas: 68/87.
- Precisión: 21,84 %.

La validación se utilizó únicamente para evaluar la configuración final. No se utilizó para elegir índices ni para continuar la búsqueda.

El oráculo conserva solo la primera restricción incumplida por respuesta. Por tanto, las frecuencias originales de `violo` son primeras causas detectadas, no un inventario de todas las restricciones que incumple cada salida.

### Análisis de fallos y diagnóstico multirrestricción

Se reconstruyeron las 87 respuestas de validación desde la caché y se cruzaron con el dataset visible. La configuración final, el modelo y la semilla coinciden con el historial. Las 68 respuestas fallidas tienen su primera restricción registrada dentro de los IDs de restricciones de su instancia.

Se ejecutó `scripts/analizar_fallos_multirrestriccion.py` con las clases IFEvalG reales sobre las 68 respuestas fallidas, sin cargar Qwen ni generar texto. El análisis terminó correctamente y detectó:

- Instancias con más de una restricción incumplida: 31/68 (45,59 %).
- Incumplimientos individuales detectados: 110.
- Familias con más incumplimientos: `keywords` (24; 21,82 %), `punctuation` (14; 12,73 %), `detectable_format` (13; 11,82 %) y `copy` (11; 10,00 %). Estas cuatro familias reúnen 62/110 (56,36 %) de los incumplimientos.
- Restricciones individuales más frecuentes: `punctuation:punctuation_dot` (10), `last_word:last_word_sent` (7), `length_constraints:nth_paragraph_first_word` (6) y `copy:repeat_phrase` (6).

Los conteos representan incumplimientos individuales; una respuesta puede contribuir a varios. Las excepciones de los verificadores detienen el análisis y no se clasifican como incumplimientos. El diagnóstico caracteriza la configuración final y no modifica la configuración ni usa la validación para optimizar.

Los archivos generados en la carpeta local de Drive `reporte_multirestriccion_G1_v2` son: `matriz_fallos_multirestriccion_G1_v2.csv`, `conteo_restricciones_G1_v2.csv`, `conteo_familias_G1_v2.csv` y `reporte_multirestriccion_G1_v2.md`. No se versionan los CSV con respuestas del modelo ni otros artefactos derivados de la ejecución.

Se incorporó `scripts/analizar_coocurrencia_multirrestriccion.py`, que calcula pares de restricciones que aparecen incumplidos en una misma respuesta, soporte por instancia, índice Jaccard y matriz simétrica. Los resultados obtenidos se documentan en la sección «Coocurrencia de restricciones — resultados v2».

### Comparabilidad y limitaciones

El baseline v1 fue 9/100 y su validación 8/87. Esos números corresponden al catálogo previo (`estilo` y `cierre` en lugar de `verificacion` y `recordatorio`) y no son una línea base comparable de v2. La línea base interna de v2 es 12/100.

La validación de 87 instancias es una medición descriptiva reservada, no la evaluación privada del docente. No se debe reutilizar para seleccionar configuraciones. La búsqueda por coordenadas sigue siendo heurística y no garantiza optimalidad global.


### Coocurrencia de restricciones — resultados v2

Se ejecutó `scripts/analizar_coocurrencia_multirrestriccion.py` sobre la matriz de 68 respuestas fallidas generada por el diagnóstico multirrestricción. Se analizaron 68 instancias, con 38 restricciones distintas observadas y 50 pares distintos de restricciones que coocurrieron al menos una vez.

Los pares con dos apariciones fueron:

| Restricción A | Restricción B | Coocurrencias | Jaccard |
|---|---|---:|---:|
| `last_word:last_word_sent` | `punctuation:punctuation_dot` | 2 | 13,33 % |
| `new:copy_span_idx` | `punctuation:no_comma` | 2 | 40,00 % |
| `keywords:no_adjacent_consecutive` | `length_constraints:nth_paragraph_first_word` | 2 | 22,22 % |

Los siete pares restantes del top 10 aparecieron una vez cada uno. Entre ellos se observó la coocurrencia de `punctuation:no_comma` con `punctuation:punctuation_dot`, y de `keywords:no_adjacent_consecutive` con `letters:letter_counting2`.

El mayor índice Jaccard del top 10 fue 40,00 % para `new:copy_span_idx` junto con `punctuation:no_comma`. Ese porcentaje debe interpretarse junto con su frecuencia absoluta: el par aparece en solo dos instancias. Los pares son señales descriptivas y no evidencia de causalidad ni de una interacción sistemática entre instrucciones. En una muestra de 68 respuestas fallidas, las frecuencias observadas son reducidas y no permiten generalizar sin una evaluación adicional.

Los resultados se guardaron en Drive en `reporte_coocurrencia_G1_v2`:
- `pares_coocurrencia_G1_v2.csv`.
- `matriz_coocurrencia_G1_v2.csv`.
- `reporte_coocurrencia_G1_v2.md`.

La coocurrencia completa este diagnóstico descriptivo de validación. No se modificó la configuración final ni se utilizó el conjunto de validación para optimizarla.
