# Proyecto Oráculo — Grupo G1

Proyecto de Análisis y Diseño de Algoritmos (2026-B).

**Grupo:** G1  
**Catálogo activo:** `g1-v2`  
**Rama de trabajo:** `catalogo-v2-g1`

## Objetivo

Encontrar una configuración de instrucciones para Qwen3-1.7B que maximice la proporción de instancias cuyas restricciones satisface el oráculo. Cada instancia se puntúa de forma todo-o-nada: solo cuenta como correcta si cumple todas sus restricciones.

La versión 2 del catálogo contiene cinco ranuras oficiales —`rol`, `estrategia`, `formato`, `verificacion` y `recordatorio`— con ocho alternativas cada una. Con temperatura fija en 0.0, el espacio tiene (8^5 = 32.768) configuraciones.

## Resultado experimental — catálogo v2

La ejecución se realizó en Google Colab con Qwen/Qwen3-1.7B, GPU Tesla T4, temperatura 0.0 y semilla 2026.

| Medición | Correctas | Precisión |
|---|---:|---:|
| Baseline de búsqueda v2 | 12/100 | 12,00 % |
| Configuración final en búsqueda v2 | 21/100 | 21,00 % |
| Validación independiente v2 | 19/87 | 21,84 % |

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

La búsqueda registró 46 evaluaciones. La configuración es la mejor observada por la heurística y el presupuesto utilizados; no se demuestra optimalidad global. La validación se informa como evaluación posterior y no se usa para seleccionar configuraciones.

**Comparabilidad:** el resultado histórico del catálogo v1 (9,0 % en búsqueda y 9,2 % en validación) pertenece a cinco ranuras diferentes (`rol`, `estrategia`, `formato`, `estilo`, `cierre`). No debe tratarse como baseline directo de v2. El baseline válido dentro de v2 es 12/100.

## Componentes

- `oraculo.py`: catálogo v2, construcción de prompts, caché y evaluación todo-o-nada.
- `ayudas.py`: carga del modelo y de los datos, partición y utilidades.
- `src/optimizador.py`: búsqueda por coordenadas con screening y refinamiento.
- `src/reanudador.py`: recuperación de una búsqueda interrumpida desde el checkpoint.
- `src/busqueda_pares_guiada.py`: estrategia experimental complementaria; no atribuirle resultados hasta ejecutar su experimento.
- `scripts/analizar_fallos_multirestriccion.py`: diagnóstico offline que evalúa todas las restricciones de cada respuesta fallida usando la caché, sin cargar Qwen. La ejecución v2 examinó 68 respuestas fallidas, detectó 110 incumplimientos individuales y encontró 31 respuestas con fallos múltiples.
- `scripts/analizar_coocurrencia_multirrestriccion.py`: calcula pares de restricciones que coocurren, soporte e índice Jaccard a partir de la matriz CSV del diagnóstico. La ejecución sobre validación observó 50 pares distintos entre 38 restricciones en 68 respuestas fallidas; la máxima frecuencia de un par fue dos.
- `docs/REGISTRO_EXPERIMENTAL_G1.md`: registro histórico v1 y resultados actuales v2.
- `docs/DIAGNOSTICO_MULTIRRESTRICCION_G1_V2.md`: procedimiento del análisis de fallos simultáneos.
- `tests/`: pruebas unitarias del código propio.
- `entrega.json`: configuración seleccionada para el catálogo activo.

## Reanudación y datos

La caché y el historial v2 deben mantenerse separados de los artefactos v1. En Colab se recomienda guardar ambos en Google Drive para poder reanudar sin volver a generar respuestas.

No versionar cachés, checkpoints ni salidas completas del modelo: son artefactos experimentales grandes. El dataset visible debe conservarse en la ubicación de trabajo acordada, sin reemplazarlo por resultados generados.

## Ejecución y pruebas

Desde la raíz del repositorio:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Las pruebas unitarias usan dobles de prueba y no cargan Qwen. El notebook de Colab realiza la instalación de dependencias, prepara `allenai/open-instruct`, ejecuta las pruebas y después carga el modelo.

## Limitaciones

- Coordinate Search es una heurística local; no garantiza un óptimo global.
- La validación visible contiene 87 instancias y no sustituye la evaluación privada del docente. El análisis multirrestricción es descriptivo; no se debe usar para seleccionar configuraciones.
- El oráculo conserva la primera restricción incumplida. Para contar todos los incumplimientos de cada salida se debe ejecutar el diagnóstico multirrestricción.
- La formalización y la reducción desde 3-SAT solicitadas por la guía deben demostrarse rigurosamente antes de afirmar NP-dureza.
