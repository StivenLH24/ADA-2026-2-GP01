# Registro experimental — Grupo G1

**Integrante:** Johan Stiven Osorio Grisales  
**Grupo:** G1  
**Semana:** 2  
**Proyecto:** Proyecto Oráculo — Análisis y Diseño de Algoritmos (2026-B)

Este documento distingue la exploración inicial de la ejecución formal de búsqueda por coordenadas y su validación. Ningún resultado se presenta como óptimo global demostrado.

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
