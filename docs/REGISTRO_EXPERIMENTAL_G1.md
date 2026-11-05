# Registro experimental inicial — Grupo G1

Este documento registra únicamente resultados que aparecen en el notebook de exploración exportado desde Google Colab. No representa todavía la ejecución final ni la configuración de entrega.

## Entorno comprobado

- Entorno: Google Colab.
- Python: 3.13.16.
- PyTorch: 2.11.0+cu130.
- GPU: NVIDIA Tesla T4.
- CUDA disponible: sí.
- Modelo: Qwen/Qwen3-1.7B.
- Dispositivo del modelo: cuda:0.
- Memoria GPU registrada después de cargar el modelo: aproximadamente 3.2 GB.

## Datos y espacio de búsqueda

- Registros visibles: 450.
- Instancias de búsqueda: 100.
- Instancias de validación: 87.
- Instancias descartadas por la función dividir: 263.
- Ranuras: rol, estrategia, formato, estilo y cierre.
- Alternativas por ranura: 8.
- Temperatura usada en los experimentos registrados: 0.0.
- Espacio de configuraciones a temperatura 0.0: 8^5 = 32.768.

## Calibración

### Primera muestra

Se evaluaron las referencias LIMPIA y PESADA sobre las primeras 10 instancias de búsqueda. Ambas obtuvieron 0/10 instancias correctas. Esta muestra inicial no permitió distinguir las configuraciones.

### Muestra aleatoria reproducible de 40 instancias

La muestra se seleccionó con `random.Random(2026)` y contiene los IDs:

`372, 488, 610, 611, 683, 369, 439, 648, 673, 634, 553, 639, 626, 603, 645, 565, 441, 309, 659, 357, 371, 472, 363, 570, 310, 694, 750, 411, 542, 443, 518, 526, 537, 743, 353, 516, 362, 471, 446, 386`.

| Configuración | Correctas | Fallidas | Precisión |
|---|---:|---:|---:|
| LIMPIA | 5 | 35 | 12,5 % |
| PESADA | 0 | 40 | 0,0 % |

LIMPIA superó las instancias 372, 518, 526, 537 y 471. PESADA no superó ninguna instancia de esta muestra.

### Primeras familias de fallo observadas en LIMPIA

| Identificador | Frecuencia |
|---|---:|
| keywords:keyword_specific_position | 4 |
| new:copy_span_idx | 3 |
| copy:copy | 3 |
| last_word:last_word_sent | 3 |
| first_word:first_word_sent | 2 |
| first_word:first_word_answer | 2 |
| keywords:frequency | 2 |
| copy:repeat_phrase | 2 |
| paragraphs:paragraphs | 2 |

El oráculo registra la primera restricción incumplida por instancia; estas frecuencias no representan todos los incumplimientos posibles de cada respuesta.

## Búsqueda por coordenadas: ejecución parcial

En el notebook se inició una búsqueda de una ronda con LIMPIA como configuración inicial. La muestra de optimización era la misma muestra de 40 instancias de calibración, no el conjunto completo de 100 instancias de búsqueda.

| Etapa | Resultado registrado |
|---|---|
| Baseline LIMPIA | 12,5 % sobre 40 instancias |
| Rol | El índice cambió de 5 a 2; la precisión refinada pasó a 20,0 % |
| Estrategia | No se aceptó un cambio; permaneció en índice 2 |
| Formato | No se aceptó un cambio; permaneció en índice 0 |
| Estilo | El screening comenzó, pero la celda se exportó antes de completar esta coordenada |
| Cierre | No alcanzado en la ejecución exportada |
| Gráfica de convergencia | No generada |

La ejecución parcial no debe reportarse como búsqueda completada. La celda no llegó a construir las tablas finales de candidatos ni a guardar un historial completo de la búsqueda.

## Limitaciones y próximos pasos

1. Repetir la búsqueda usando las 100 instancias de `busqueda` como conjunto de refinamiento y aceptación.
2. Mantener una muestra de screening reproducible, pero aceptar cambios solo después de compararlos sobre las 100 instancias.
3. Guardar un registro persistente después de cada evaluación y conservar la caché del oráculo fuera del directorio temporal de Colab (por ejemplo, en Google Drive).
4. Evaluar la configuración final en `validacion`, sin usar ese resultado para seguir seleccionando candidatos.
5. No afirmar optimalidad global: Coordinate Search es una heurística.
6. Formalizar rigurosamente la reducción desde 3-SAT exigida por la guía específica de G1. Este registro no contiene una demostración de NP-dureza.

## Reproducibilidad

Los parámetros registrados de calibración son: modelo Qwen/Qwen3-1.7B, temperatura 0.0, semilla 1 para el oráculo y semilla 2026 para seleccionar la muestra de 40 instancias.


## Segunda ejecución: Coordinate Search sobre las 100 instancias

Esta ejecución es independiente de la búsqueda exploratoria anterior. Se inició en `01_busqueda_G1.ipynb` con Qwen/Qwen3-1.7B, temperatura 0.0, semilla 2026, screening de 10 instancias, dos finalistas por coordenada y una ronda.

Configuración inicial:

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

El baseline obtuvo **9/100 = 9,0 %**.

| Coordenada | Screening | Refinamiento sobre 100 | Decisión |
|---|---|---|---|
| rol | Los siete candidatos alternativos obtuvieron 0/10 | Índice 0: 7/100; índice 2: 8/100 | Se conserva rol=1 |
| estrategia | Los siete candidatos alternativos obtuvieron 0/10 | Índice 0: 6/100; índice 1: 6/100 | Se conserva estrategia=5 |
| formato | Índices 0, 2, 3, 4, 5 y 6: 0/10; índice 7: 1/10 | El refinamiento del finalista todavía no había terminado al interrumpirse la sesión | Pendiente de reanudación |
| estilo | No iniciado | No iniciado | Pendiente |
| cierre | No iniciado | No iniciado | Pendiente |

Al momento de la interrupción, el historial persistido contenía 26 evaluaciones completas y dos coordenadas resumidas (`rol` y `estrategia`). El screening de `formato` estaba completo. La llamada de refinamiento del primer finalista se había interrumpido antes de completar las 90 instancias que faltaban después del screening; esa ejecución no aparece como evaluación completa en el historial, pero las respuestas guardadas por lotes permanecen en la caché del oráculo.

La reanudación debe comenzar por `formato`, calcular los finalistas a partir del screening ya registrado y completar sus refinamientos. Después debe continuar con `estilo` y `cierre`. No se deben repetir las coordenadas ya resumidas. El módulo `src/reanudador.py` implementa esta recuperación y utiliza el historial y la caché persistidos en Google Drive.

Archivos persistentes usados en Colab:

- `/content/drive/MyDrive/ADA_G1/cache_oraculo_G1.json`
- `/content/drive/MyDrive/ADA_G1/historial_coordinate_search_G1.json`

Estos valores son un checkpoint intermedio, no la configuración final de entrega. No se ha evaluado todavía ninguna configuración final sobre las 87 instancias de validación y no se afirma optimalidad global.
