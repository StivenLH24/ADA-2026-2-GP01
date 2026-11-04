# Proyecto Oráculo — Grupo G1

Proyecto de Análisis y Diseño de Algoritmos. El objetivo experimental es seleccionar una configuración de prompt que maximice la proporción de instancias cuyas restricciones son satisfechas por el modelo evaluado mediante el oráculo.

## Entorno de trabajo

La ejecución de modelos y experimentos se realiza en Google Colab con GPU. GitHub conserva el código, los notebooks, la documentación y los resultados reproducibles.

## Estructura del proyecto

- `oraculo.py`, `ayudas.py`, `datos_visibles.json`: archivos base del monitor; se mantienen sin modificar.
- `src/optimizador.py`: implementación de búsqueda por coordenadas del Grupo G1.
- `notebooks/`: notebooks de búsqueda y evaluación (se incorporarán en la siguiente etapa).
- `docs/`: informe académico, manual técnico y registro experimental.
- `tests/`: pruebas unitarias del código propio.
- `entrega.json`: configuración seleccionada para la entrega, pendiente de resultados finales.

## Estado experimental

La calibración inicial está documentada en [docs/REGISTRO_EXPERIMENTAL_G1.md](docs/REGISTRO_EXPERIMENTAL_G1.md). En esa muestra de 40 instancias, LIMPIA alcanzó 12,5 % y PESADA 0 %. La búsqueda por coordenadas iniciada en Colab quedó incompleta; su resultado no se presenta como final.

## Pruebas locales

Desde la raíz del repositorio:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Las pruebas usan un oráculo simulado y no descargan ni ejecutan el modelo.

## Alcance académico

La guía específica de G1 solicita formalización y reducción desde 3-SAT. La demostración debe verificarse formalmente antes de presentarse como NP-dureza probada. La búsqueda es heurística y no garantiza encontrar el óptimo global.
