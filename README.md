# Proyecto Oráculo — Grupo G1

Proyecto de Análisis y Diseño de Algoritmos (2026-B).

**Integrante registrado:** Johan Stiven Osorio Grisales  
**Grupo:** G1  
**Semana documentada:** 2  
**Rama de trabajo:** `trabajo-g1`

## Objetivo

Encontrar una configuración de instrucciones para Qwen3-1.7B que maximice la proporción de instancias cuyas restricciones satisface el oráculo. La configuración tiene cinco ranuras (`rol`, `estrategia`, `formato`, `estilo`, `cierre`) con ocho alternativas cada una. En el experimento documentado se fijó la temperatura en 0.0, por lo que el espacio contiene 8^5 = 32.768 configuraciones.

La precisión es todo-o-nada por instancia: una instancia cuenta como correcta únicamente si se cumplen todas sus restricciones.

## Resultado experimental actual

La búsqueda por coordenadas de una ronda terminó sobre las 100 instancias de búsqueda. La configuración mejor encontrada obtuvo 9/100 = 9,0 %. La validación independiente sobre 87 instancias obtuvo 8/87 = 9,2 %.

Configuración mejor encontrada hasta esta versión:

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

Esta configuración es la mejor observada en la ejecución registrada, no un óptimo global demostrado. Ninguna de las alternativas refinadas superó el baseline del 9,0 %. El historial contiene 46 evaluaciones y cinco coordenadas completadas. La interpretación y las limitaciones están en [docs/REGISTRO_EXPERIMENTAL_G1.md](docs/REGISTRO_EXPERIMENTAL_G1.md).

## Estructura

- `oraculo.py`, `ayudas.py`, `datos_visibles.json`: archivos base del monitor; se mantienen sin modificar.
- `src/optimizador.py`: búsqueda por coordenadas con screening, refinamiento y aceptación sobre el conjunto completo de búsqueda.
- `src/reanudador.py`: recuperación de una búsqueda interrumpida mediante el historial persistido y la caché del oráculo.
- `docs/REGISTRO_EXPERIMENTAL_G1.md`: resultados, parámetros, trazabilidad y limitaciones.
- `docs/MANUAL_TECNICO_G1.md`: instalación, arquitectura, ejecución y reproducibilidad.
- `tests/`: pruebas unitarias del código propio.
- `entrega.json`: configuración mejor encontrada hasta ahora, identificada para el grupo y la semana indicados.

Los notebooks obligatorios de búsqueda y evaluación se deben mantener coherentes con `entrega.json` antes de la entrega definitiva.

## Entorno experimental registrado

- Google Colab con GPU NVIDIA Tesla T4.
- Python 3.13.16.
- PyTorch 2.11.0+cu130.
- Modelo Qwen/Qwen3-1.7B.
- 450 registros visibles: 100 de búsqueda, 87 de validación y 263 descartados por la partición del monitor.
- Temperatura 0.0 y semilla 2026 para el muestreo del screening.

## Ejecución y pruebas

El detalle de instalación y ejecución está en [docs/MANUAL_TECNICO_G1.md](docs/MANUAL_TECNICO_G1.md).

Las pruebas unitarias del optimizador se ejecutan desde la raíz:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Las pruebas utilizan un oráculo simulado; no descargan ni ejecutan Qwen.

## Alcance y limitaciones académicas

La búsqueda por coordenadas es heurística y no garantiza optimalidad global. En esta implementación, las trazas se almacenan para el análisis, pero la selección de candidatos de esta primera ronda se hizo principalmente por precisión y no mediante una poda guiada por familias de fallos.

La guía específica de ADAG1 solicita una demostración de NP-dureza por reducción desde 3-SAT para la configuración óptima con oráculo exacto. Esa demostración no se considera completada en este repositorio hasta disponer de una reducción polinomial rigurosa y de una prueba en ambos sentidos. La dificultad de la búsqueda práctica con consultas limitadas debe analizarse por separado.

## Repositorio

- Repositorio: https://github.com/StivenLH24/ADA-2026-2-GP01
- Rama de trabajo G1: `trabajo-g1`
