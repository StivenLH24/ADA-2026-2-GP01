# Diagnóstico multirrestricción — G1 catálogo v2

## Propósito

El oráculo de `oraculo.py` se detiene en la primera restricción incumplida de cada instancia. Por ello, las frecuencias habituales de `violo` no describen todos los defectos de una respuesta.

El script `scripts/analizar_fallos_multirestriccion.py` vuelve a pasar cada respuesta ya guardada por **todos** los verificadores de su instancia, de forma independiente. Permite distinguir fallos únicos de fallos simultáneos y obtener conteos completos por restricción y familia.

## Entradas

- Dataset visible de catálogo v2 (`datos_visibles_G1_v2.json`).
- Caché de respuestas de Oráculo v2 (`cache_oraculo_G1_v2.json`).
- Historial de Coordinate Search v2 (`historial_coordinate_search_G1_v2.json`).
- Clon de `allenai/open-instruct`, que contiene el registro IFEvalG.

El script reconstruye la configuración final y la semilla desde el historial. Comprueba la versión del catálogo, el hash de configuración, el modelo y la correspondencia de IDs antes de ejecutar verificadores.

## Ejecución

En Colab, después de instalar las dependencias y clonar `allenai/open-instruct` como en el notebook:

```bash
python scripts/analizar_fallos_multirestriccion.py \
  --dataset /content/drive/MyDrive/ada_v2/datos_visibles_G1_v2.json \
  --cache /content/drive/MyDrive/ada_v2/cache_oraculo_G1_v2.json \
  --historial /content/drive/MyDrive/ada_v2/historial_coordinate_search_G1_v2.json \
  --open-instruct /content/open-instruct \
  --salida /content/drive/MyDrive/ada_v2/reporte_multirestriccion_G1_v2
```

Ajustar las rutas a la ubicación real de los archivos. No es necesario cargar Qwen ni volver a generar respuestas.

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
