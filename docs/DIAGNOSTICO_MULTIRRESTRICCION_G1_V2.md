# Diagnóstico multirrestricción — G1 catálogo v2

## Propósito

El oráculo de `oraculo.py` se detiene en la primera restricción incumplida de cada instancia. Por ello, las frecuencias habituales de `violo` no describen todos los defectos de una respuesta.

El script `scripts/analizar_fallos_multirestriccion.py` vuelve a pasar cada respuesta ya guardada por **todos** los verificadores de su instancia, de forma independiente. Permite distinguir fallos únicos de fallos simultáneos y obtener conteos completos por restricción y familia.

## Entradas

- Dataset visible de catálogo v2. En la ejecución registrada se utilizó `datos_visibles.json` en la raíz del repositorio; se comprobó que contiene 450 IDs únicos (100 búsqueda, 87 validación y 263 descartadas).
- Caché de respuestas de Oráculo v2 (`cache_oraculo_G1_v2.json`).
- Historial de Coordinate Search v2 (`historial_coordinate_search_G1_v2.json`).
- Clon de `allenai/open-instruct`, que contiene el registro IFEvalG.

El script reconstruye la configuración final y la semilla desde el historial. Comprueba la versión del catálogo, el hash de configuración, el modelo y la correspondencia de IDs antes de ejecutar verificadores.

## Ejecución

En Colab, después de instalar las dependencias y clonar `allenai/open-instruct` como en el notebook:

```bash
python scripts/analizar_fallos_multirrestriccion.py \
  --dataset /content/ADA-2026-2-GP01/datos_visibles.json \
  --cache /content/drive/MyDrive/ADA_G1/cache_oraculo_G1_v2.json \
  --historial /content/drive/MyDrive/ADA_G1/historial_coordinate_search_G1_v2.json \
  --open-instruct /content/open-instruct \
  --salida /content/drive/MyDrive/ADA_G1/reporte_multirestriccion_G1_v2
```

Ajustar las rutas a la ubicación real de los archivos. En Colab, si faltan dependencias, instalar `langdetect` con `pip install langdetect` y descargar los recursos NLTK con `nltk.download('punkt_tab')` y `nltk.download('punkt')`. No es necesario cargar Qwen ni volver a generar respuestas.

## Salidas

- `matriz_fallos_multirestriccion_G1_v2.csv`: resultado por instancia, con todas las restricciones cumplidas e incumplidas.
- `conteo_restricciones_G1_v2.csv`: número de incumplimientos por restricción.
- `conteo_familias_G1_v2.csv`: número de incumplimientos por familia.
- `reporte_multirestriccion_G1_v2.md`: resumen y lectura metodológica.

## Controles de consistencia

El análisis se detiene si:
- faltan respuestas cacheadas para instancias de validación;
- el historial no corresponde a `g1-v2`;
- el registro no conoce una restricción;
- los verificadores recalculados no reproducen la primera falla registrada en caché;
- una respuesta marcada como fallida no incumple ninguno de sus verificadores.

Una excepción del verificador no se contabiliza como incumplimiento: detiene el análisis para evitar resultados incompletos.

## Alcance

Es un diagnóstico posterior, no una nueva búsqueda. No modifica el catálogo, el oráculo, el historial ni la caché. La validación se utiliza exclusivamente para describir errores de la configuración ya elegida; no debe utilizarse para seleccionar otra configuración. Los CSV y reportes generados son artefactos locales del experimento y no se versionan junto con el código.

## Resultados observados de la ejecución v2

La ejecución completa con IFEvalG real examinó las 68 instancias fallidas y detectó 110 incumplimientos individuales. En 31 de las 68 respuestas (45,59 %) se encontraron dos o más restricciones incumplidas.

Conteos por familia: `keywords` 24 (21,82 %), `punctuation` 14 (12,73 %), `detectable_format` 13 (11,82 %), `copy` 11 (10,00 %), `last_word` 9 (8,18 %), `length_constraints` 8 (7,27 %) y `letters` 8 (7,27 %). Las cuatro primeras familias concentran 62 de los 110 incumplimientos (56,36 %).

Las restricciones individuales más frecuentes fueron `punctuation:punctuation_dot` (10), `last_word:last_word_sent` (7), `length_constraints:nth_paragraph_first_word` (6) y `copy:repeat_phrase` (6). Una respuesta puede contribuir a varios conteos.

Los archivos se generaron en la carpeta de Drive `reporte_multirestriccion_G1_v2`. No se incorporan al repositorio los CSV con respuestas del modelo, porque son artefactos de ejecución. El resultado es descriptivo y no se utilizó para optimizar la configuración.

## Coocurrencia entre restricciones

El script `scripts/analizar_coocurrencia_multirrestriccion.py` toma `matriz_fallos_multirestriccion_G1_v2.csv` y genera:
- `pares_coocurrencia_G1_v2.csv`: pares ordenados por frecuencia, soporte e índice Jaccard.
- `matriz_coocurrencia_G1_v2.csv`: matriz simétrica de conteos conjuntos.
- `reporte_coocurrencia_G1_v2.md`: resumen de los pares más frecuentes y alcance metodológico.

Ejecución en Colab desde la raíz del repositorio:

```bash
python scripts/analizar_coocurrencia_multirrestriccion.py \
  --matriz /content/drive/MyDrive/ADA_G1/reporte_multirestriccion_G1_v2/matriz_fallos_multirestriccion_G1_v2.csv \
  --salida /content/drive/MyDrive/ADA_G1/reporte_coocurrencia_G1_v2
```

El soporte representa el porcentaje de respuestas fallidas en las que aparece el par. Jaccard se calcula como intersección dividida por unión de los conjuntos de instancias donde aparece cada restricción. Es una medida descriptiva y no implica causalidad. Los valores quedan pendientes de ejecutar sobre el CSV real; no se anticipan cifras.


## Resultados de coocurrencia obtenidos

Se ejecutó el script sobre la matriz multirrestricción de las 68 respuestas fallidas. Se analizaron 68 instancias, 38 restricciones distintas y 50 pares distintos con al menos una coocurrencia.

Los tres pares más frecuentes aparecieron en dos instancias cada uno:
- `last_word:last_word_sent` + `punctuation:punctuation_dot` (Jaccard: 13,33 %).
- `new:copy_span_idx` + `punctuation:no_comma` (Jaccard: 40,00 %).
- `keywords:no_adjacent_consecutive` + `length_constraints:nth_paragraph_first_word` (Jaccard: 22,22 %).

El resto de los pares incluidos en el top 10 presentó una coocurrencia. Aunque `new:copy_span_idx` + `punctuation:no_comma` obtuvo el mayor Jaccard del top 10, su frecuencia absoluta fue de solo dos instancias. Por ello, los resultados son descriptivos y no permiten afirmar causalidad ni una asociación estable.

Los tres archivos generados (`pares_coocurrencia_G1_v2.csv`, `matriz_coocurrencia_G1_v2.csv` y `reporte_coocurrencia_G1_v2.md`) se conservaron en Drive bajo `reporte_coocurrencia_G1_v2`. No se versionan los CSV ni las respuestas del modelo.
