# Manual técnico — Proyecto Oráculo G1

**Integrante:** Johan Stiven Osorio Grisales  
**Grupo:** G1  
**Semana:** 2  
**Curso:** Análisis y Diseño de Algoritmos (2026-B)

## 1. Propósito

Este manual describe cómo instalar, configurar, ejecutar y reproducir la solución base desarrollada para el Proyecto Oráculo. El objetivo experimental es elegir una combinación de instrucciones de prompt que maximice la proporción de instancias que satisfacen todas las restricciones verificadas por el oráculo.

La configuración tiene cinco ranuras: `rol`, `estrategia`, `formato`, `estilo` y `cierre`. Cada ranura contiene ocho alternativas. En el experimento registrado, la temperatura permanece fija en 0.0, de modo que el espacio tiene 8^5 = 32.768 configuraciones.

## 2. Entorno de ejecución

Entorno registrado:

- Google Colab.
- GPU NVIDIA Tesla T4, con CUDA.
- Python 3.13.16.
- PyTorch 2.11.0+cu130.
- Transformers, Accelerate y BitsAndBytes.
- SpaCy con el modelo `en_core_web_sm`.
- NLTK con `punkt`, `punkt_tab`, `averaged_perceptron_tagger` y `averaged_perceptron_tagger_eng`.
- Verificadores del repositorio `allenai/open-instruct`, ubicados en `/content/open-instruct`.

El modelo empleado fue `Qwen/Qwen3-1.7B`, cargado mediante el alias `qwen17b` de `ayudas.py`. Para esta ejecución se utilizó `lote=1` en el oráculo para mantener un margen de memoria en la T4.

## 3. Estructura del repositorio

- `oraculo.py`: caja negra del curso. Recibe configuraciones e instancias y devuelve precisión y trazas. No debe modificarse.
- `ayudas.py`: carga del modelo y datos, partición de búsqueda/validación, visualización de prompts y exportación de entrega.
- `datos_visibles.json`: pool de 450 instancias.
- `src/optimizador.py`: validación de configuraciones, búsqueda por coordenadas, screening, refinamiento, registro y persistencia del historial.
- `src/reanudador.py`: restaura el checkpoint desde el historial y continúa las coordenadas pendientes, reutilizando la caché del oráculo.
- `tests/test_optimizador.py`: pruebas unitarias con un oráculo simulado.
- `docs/REGISTRO_EXPERIMENTAL_G1.md`: parámetros, resultados y limitaciones observadas.
- `entrega.json`: configuración mejor encontrada y metadatos de entrega.

## 4. Preparación en Google Colab

### 4.1 Clonar el repositorio

```python
import os, sys, subprocess

REPOSITORIO = "https://github.com/StivenLH24/ADA-2026-2-GP01.git"
RUTA_PROYECTO = "/content/ADA-2026-2-GP01"
RAMA = "trabajo-g1"

if not os.path.isdir(os.path.join(RUTA_PROYECTO, ".git")):
    subprocess.run([
        "git", "clone", "--branch", RAMA, "--single-branch",
        REPOSITORIO, RUTA_PROYECTO
    ], check=True)
else:
    subprocess.run(
        ["git", "pull", "--ff-only", "origin", RAMA],
        cwd=RUTA_PROYECTO, check=True
    )

os.chdir(RUTA_PROYECTO)
sys.path.insert(0, RUTA_PROYECTO)
```

### 4.2 Montar Drive para persistir la caché

```python
from google.colab import drive
from pathlib import Path

drive.mount("/content/drive")
CARPETA_DATOS = Path("/content/drive/MyDrive/ADA_G1")
CARPETA_DATOS.mkdir(parents=True, exist_ok=True)

CACHE_ORACULO = str(CARPETA_DATOS / "cache_oraculo_G1.json")
HISTORIAL_BUSQUEDA = CARPETA_DATOS / "historial_coordinate_search_G1.json"
```

La caché debe permanecer fuera de `/content`, porque el almacenamiento local de Colab se pierde al reiniciar o desconectar el entorno.

### 4.3 Instalar dependencias y verificadores

```bash
pip install -U "bitsandbytes>=0.46.1" transformers accelerate nltk spacy emoji langdetect immutabledict
python -m spacy download en_core_web_sm
git clone https://github.com/allenai/open-instruct /content/open-instruct
```

Descargar los recursos NLTK indicados en la sección 2 y añadir `/content/open-instruct` a `sys.path`.

### 4.4 Cargar datos y modelo

```python
from ayudas import cargar_datos, dividir, cargar_modelo
from oraculo import Oraculo, CATALOGO, RANURAS

datos = cargar_datos()
busqueda, validacion = dividir(datos)

modelo = cargar_modelo("qwen17b")

oraculo = Oraculo(
    modelo=modelo,
    datos=busqueda,
    validacion=validacion,
    cache=CACHE_ORACULO,
    max_new_tokens=384,
    lote=1
)
```

La función `dividir` produce 100 instancias de búsqueda, 87 de validación y descarta 263. La partición de validación no debe utilizarse para seleccionar candidatos.

## 5. Funcionamiento de Coordinate Search

La implementación registrada utiliza búsqueda por coordenadas con evaluación escalonada:

1. Construye una configuración completa inicial.
2. Para una ranura, sustituye su índice por cada una de las otras siete alternativas.
3. Evalúa esas alternativas sobre una muestra fija de 10 instancias (`screening`).
4. Ordena los candidatos por precisión y selecciona los dos finalistas.
5. Evalúa los finalistas sobre las 100 instancias de búsqueda (`refinamiento`).
6. Acepta un cambio únicamente si la precisión completa supera estrictamente la precisión actual.
7. Repite el procedimiento para las cinco ranuras. En el experimento documentado se ejecutó una ronda.

La precisión se calcula como instancias totalmente correctas dividido por el número de instancias evaluadas. Una respuesta que incumple una o más restricciones cuenta como fallo.

### 5.1 Ejecutar la búsqueda

```python
from src.optimizador import CoordinateSearch

optimizador = CoordinateSearch(
    oraculo=oraculo,
    catalogo=CATALOGO,
    ranuras=RANURAS,
    historial_path=HISTORIAL_BUSQUEDA,
    temperaturas=(0.0,)
)

CONFIG_INICIAL = {
    "rol": 1,
    "estrategia": 5,
    "formato": 1,
    "estilo": 3,
    "cierre": 6,
    "temperatura": 0.0
}

config_encontrada, precision = optimizador.optimizar(
    datos_busqueda=busqueda,
    configuracion_inicial=CONFIG_INICIAL,
    screen_n=10,
    finalistas=2,
    max_rondas=1,
    semilla=2026
)
```

### 5.2 Recuperar una búsqueda interrumpida

La caché del oráculo guarda respuestas por lotes. El historial del optimizador registra evaluaciones completas y resúmenes de coordenadas. Si Colab se interrumpe:

1. Reconstruir el entorno, montar Drive y cargar el modelo.
2. Inicializar nuevamente `Oraculo` con el mismo archivo de caché.
3. Crear un nuevo `CoordinateSearch` apuntando al mismo historial.
4. Ejecutar `reanudar_busqueda_g1` desde `src/reanudador.py`.

```python
from src.optimizador import CoordinateSearch
from src.reanudador import reanudar_busqueda_g1

optimizador = CoordinateSearch(
    oraculo=oraculo,
    catalogo=CATALOGO,
    ranuras=RANURAS,
    historial_path=HISTORIAL_BUSQUEDA,
    temperaturas=(0.0,)
)

config_encontrada, precision = reanudar_busqueda_g1(
    optimizador,
    busqueda,
    screen_n=10,
    finalistas=2,
    semilla=2026,
    ronda=1
)
```

No se debe iniciar otra vez `optimizador.optimizar()` si el objetivo es continuar un checkpoint existente. El reanudador omite coordenadas ya resumidas y el oráculo reutiliza las respuestas presentes en la caché.

## 6. Validación final

Una vez elegida la configuración solo con el conjunto `busqueda`, medir su comportamiento en la partición reservada:

```python
resultado_validacion = oraculo.validar(
    config_encontrada,
    semilla=2026
)
```

Esta validación mide generalización sobre las 87 instancias visibles reservadas. No equivale a la evaluación privada posterior del docente.

## 7. Resultado reproducible de la ejecución documentada

Modelo: Qwen/Qwen3-1.7B. Temperatura: 0.0. Semilla: 2026. Screening: 10 instancias. Finalistas: 2 por ranura. Refinamiento: 100 instancias. Rondas: 1.

Configuración mejor encontrada:

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

- Búsqueda: 9/100 = 9,0 %.
- Validación: 8/87 = 9,2 %.
- Historial: 46 evaluaciones completas.
- Coordenadas: cinco de cinco.
- Mejoras aceptadas: cero.

La configuración es la mejor encontrada por la heurística ejecutada, no una solución óptima global demostrada.

## 8. Pruebas y límites

Las pruebas unitarias se ejecutan con:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

El conjunto de pruebas utiliza un oráculo simulado para comprobar validación de configuraciones, mejora en un caso controlado y persistencia del historial. Estas pruebas no demuestran la calidad estadística de la heurística ni sustituyen una ejecución con Qwen.

La implementación actual registra trazas, pero el criterio de selección de la primera búsqueda se basa principalmente en precisión. No implementa todavía una poda sistemática guiada por familias de fallos ni garantiza un óptimo global.

La demostración de NP-dureza por reducción desde 3-SAT es un requisito académico independiente y debe agregarse solo después de demostrar la reducción y sus dos direcciones correctamente.


## 9. Segunda estrategia experimental: búsqueda por pares guiada por trazas

Se incorporó `src/busqueda_pares_guiada.py` para explorar combinaciones de dos cambios de ranura. Su finalidad es estudiar interacciones que Coordinate Search (un cambio a la vez) puede no detectar.

### 9.1 Cómo prioriza los pares

El módulo lee el baseline y los refinamientos individuales del historial de Coordinate Search. Para cada par de candidatos de ranuras distintas:

1. Obtiene los IDs de instancias superadas y fallidas a partir de las trazas.
2. Calcula la unión de instancias superadas por el baseline y por ambos candidatos individuales. Esta unión es una señal heurística de complementariedad, no una predicción garantizada del resultado combinado.
3. Calcula la diversidad entre conjuntos de familias de primera falla.
4. Ordena los pares por cobertura potencial y diversidad de fallos.
5. Conserva los seis pares mejor priorizados.

### 9.2 Screening y refinamiento

Parámetros propuestos para la comparación:

- Screening reproducible: 40 instancias.
- Pares priorizados: 6.
- Finalistas: 2.
- Refinamiento: 100 instancias de búsqueda.
- Semilla: 2026.
- Temperatura: 0.0.

El uso de 40 instancias intenta reducir los empates de 0 % que aparecieron con muestras de 10. La selección se basa primero en precisión del screening; la novedad del conjunto de IDs fallidos y la diversidad de familias se usan como desempate. Los finalistas se evalúan sobre todas las 100 instancias y solo se acepta una mejora estricta frente al baseline.

### 9.3 Ejecución en Colab

Con el entorno, el modelo y `oraculo` ya preparados, y con los archivos de búsqueda y caché persistidos en Drive:

```python
from src.busqueda_pares_guiada import ejecutar_busqueda_pares_guiada

HISTORIAL_PARES = CARPETA_DATOS / "historial_busqueda_pares_G1.json"

CONFIG_PARES, PRECISION_PARES, HISTORIAL_PARES_RESULTADO = (
    ejecutar_busqueda_pares_guiada(
        oraculo=oraculo,
        datos_busqueda=busqueda,
        historial_coordinate_path=HISTORIAL_BUSQUEDA,
        historial_pares_path=HISTORIAL_PARES,
        screen_n=40,
        top_pares=6,
        finalistas=2,
        semilla=2026,
    )
)
```

Si Colab se interrumpe, volver a ejecutar la misma llamada después de reconstruir el oráculo con la misma caché y volver a montar Drive. El módulo conserva su propio historial y el oráculo reutiliza las generaciones ya guardadas.

**Estado de esta estrategia en esta versión del manual:** implementada y preparada para ejecución, pero aún sin resultado medido con Qwen. No debe reportarse como mejora hasta completar screening y refinamiento.

