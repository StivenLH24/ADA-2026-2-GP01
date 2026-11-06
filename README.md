# Proyecto Oráculo — Grupo G1

Proyecto de Análisis y Diseño de Algoritmos (2026-B).

**Integrante registrado:** Johan Stiven Osorio Grisales  
**Grupo:** G1  
**Semana documentada:** 2  
**Rama de trabajo:** `trabajo-g1`

## Objetivo

Encontrar una configuración de instrucciones para Qwen3-1.7B que maximice la proporción de instancias cuyas restricciones satisface el oráculo. La configuración tiene cinco ranuras (`rol`, `estrategia`, `formato`, `estilo`, `cierre`) con ocho alternativas cada una. En el experimento registrado se fijó la temperatura en 0.0, por lo que el espacio contiene 8^5 = 32.768 configuraciones.

La precisión es todo-o-nada por instancia: una instancia cuenta como correcta únicamente si se cumplen todas sus restricciones.

## Resultado experimental de referencia

La primera búsqueda por coordenadas terminó sobre las 100 instancias de búsqueda. La configuración mejor encontrada obtuvo 9/100 = 9,0 %. La validación independiente sobre 87 instancias obtuvo 8/87 = 9,2 %.

Configuración mejor encontrada en esa ejecución:

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

Esta configuración es la mejor observada en la ejecución registrada, no un óptimo global demostrado. Ninguna de las alternativas refinadas superó el baseline del 9,0 %. El historial contiene 46 evaluaciones y cinco coordenadas completadas. Ver [docs/REGISTRO_EXPERIMENTAL_G1.md](docs/REGISTRO_EXPERIMENTAL_G1.md).

## Métodos implementados

1. **Coordinate Search:** screening de 10 instancias, refinamiento de dos finalistas por ranura sobre las 100 instancias y aceptación solo ante mejora estricta.
2. **Búsqueda por pares guiada por trazas:** módulo adicional que propone combinaciones de dos ranuras a partir de aciertos complementarios y diversidad de familias de fallo. Está implementado para compararlo con el primer método, pero **todavía no ha sido ejecutado**; no se le atribuyen resultados.

## Estructura

- `oraculo.py`, `ayudas.py`, `datos_visibles.json`: archivos base del monitor; se mantienen sin modificar.
- `src/optimizador.py`: búsqueda por coordenadas con screening, refinamiento y aceptación sobre el conjunto completo de búsqueda.
- `src/reanudador.py`: recuperación de una búsqueda interrumpida mediante el historial persistido y la caché del oráculo.
- `src/busqueda_pares_guiada.py`: búsqueda experimental de pares con priorización guiada por las trazas.
- `notebooks/01_busqueda_G1.ipynb`: notebook de búsqueda, resultados, trazas y validación.
- `notebooks/02_evaluacion_G1.ipynb`: carga `entrega.json` y ejecuta `oraculo.validar`.
- `docs/FORMALIZACION_G1.md`: formalización del problema y alcance de la demostración requerida.
- `docs/REGISTRO_EXPERIMENTAL_G1.md`: resultados, parámetros, trazabilidad y limitaciones.
- `docs/MANUAL_TECNICO_G1.md`: instalación, arquitectura, ejecución y reproducibilidad.
- `tests/`: pruebas unitarias del código propio.
- `entrega.json`: configuración mejor encontrada hasta ahora, con grupo y semana.

Los notebooks y `entrega.json` deben mantenerse coherentes. Si la búsqueda por pares obtiene una mejora confirmada sobre las 100 instancias, se debe actualizar `entrega.json`, el notebook y el registro con la nueva configuración.

## Entorno experimental registrado

- Google Colab con GPU NVIDIA Tesla T4.
- Python 3.13.16.
- PyTorch 2.11.0+cu130.
- Modelo Qwen/Qwen3-1.7B.
- 450 registros visibles: 100 de búsqueda, 87 de validación y 263 descartados por la partición del monitor.
- Temperatura 0.0 y semilla 2026 para el muestreo.

## Ejecución y pruebas

Las instrucciones están en [docs/MANUAL_TECNICO_G1.md](docs/MANUAL_TECNICO_G1.md).

Las pruebas unitarias se ejecutan desde la raíz:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Las pruebas utilizan un oráculo simulado; no descargan ni ejecutan Qwen. La ejecución de las pruebas debe registrarse como evidencia separada.

## Alcance y limitaciones académicas

La búsqueda por coordenadas es heurística y no garantiza encontrar el óptimo global. La primera versión registra las trazas, pero no las utiliza sistemáticamente para podar candidatos. La búsqueda por pares incorpora esas trazas en la priorización experimental, aunque su eficacia debe medirse.

La guía específica de G1 solicita formalización y reducción desde 3-SAT. La demostración debe verificarse formalmente antes de presentarse como NP-dureza probada. La complejidad de la búsqueda práctica con consultas limitadas o ruidosas debe analizarse por separado.

## Repositorio

- Repositorio: https://github.com/StivenLH24/ADA-2026-2-GP01
- Rama de trabajo G1: `trabajo-g1`
