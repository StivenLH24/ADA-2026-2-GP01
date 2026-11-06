# Formalización del problema — ADAG1, Grupo G1

**Integrante:** Johan Stiven Osorio Grisales  
**Semana:** 2  
**Estado:** borrador de formalización; la demostración de NP-dureza está pendiente de validación formal.

## 1. Problema de optimización

El proyecto selecciona una combinación de instrucciones (prompt) que maximiza la proporción de instancias para las cuales un modelo de lenguaje satisface simultáneamente todas las restricciones verificadas por el oráculo.

La configuración del experimento se representa por:

```
x = (x_rol, x_estrategia, x_formato, x_estilo, x_cierre, T)
```

Cada índice pertenece a `{0,1,2,3,4,5,6,7}`. En los experimentos registrados se fijó `T = 0.0`.

## 2. Entradas

Para la formulación empírica registrada:

- Un modelo de lenguaje fijo: Qwen/Qwen3-1.7B.
- Un catálogo de cinco ranuras, con ocho instrucciones alternativas en cada ranura.
- Una temperatura fijada en 0.0.
- Un conjunto de instancias de búsqueda `B` con 100 elementos.
- Un conjunto de validación `V` disjunto de `B`, con 87 elementos.
- Un oráculo que, dada una configuración y una instancia, verifica si la respuesta cumple todas las restricciones de esa instancia.

Los datos visibles contienen 450 registros; la función `dividir` asigna 100 a búsqueda, 87 a validación y descarta 263.

## 3. Espacio de soluciones

Con cinco ranuras y ocho alternativas por ranura, el espacio experimental a temperatura fija es:

```
X = {0,...,7} × {0,...,7} × {0,...,7} × {0,...,7} × {0,...,7}
|X| = 8^5 = 32.768
```

Una solución es una configuración completa x ∈ X.

## 4. Función objetivo

Sea `g(x, d)` el resultado del oráculo para la configuración `x` y la instancia `d`:

```
g(x,d) = 1, si la respuesta satisface todas las restricciones de d
g(x,d) = 0, en caso contrario
```

Para un conjunto de evaluación `D` de tamaño `n`, la precisión es:

```
f_D(x) = (1/n) · Σ[g(x,d) : d ∈ D]
```

El objetivo de optimización es:

```
maximizar f_B(x), sujeto a x ∈ X y T = 0.0
```

La precisión es todo-o-nada por instancia. Una sola restricción incumplida hace que la instancia aporte cero al numerador.

## 5. Versión de decisión asociada

Una versión de decisión natural se define así:

**Entrada:** catálogo, conjunto de instancias `B`, oráculo exacto y umbral racional `q`.

**Pregunta:** ¿Existe una configuración válida `x` tal que `f_B(x) ≥ q`?

La versión de decisión permite expresar si existe una configuración que alcanza al menos un nivel de cumplimiento dado.

## 6. Búsqueda práctica con consultas

La implementación no enumera exhaustivamente las 32.768 configuraciones. Utiliza consultas al oráculo:

- Screening de candidatos sobre una muestra reproducible de 10 instancias.
- Refinamiento de dos finalistas por ranura sobre las 100 instancias de búsqueda.
- Aceptación de un cambio solo si mejora estrictamente la precisión sobre el conjunto completo de búsqueda.
- Validación posterior e independiente sobre las 87 instancias reservadas.

La búsqueda de consultas limitadas es una heurística práctica. Su costo depende del número de consultas, las instancias evaluadas en cada consulta, la longitud de los prompts y el costo de generación del modelo. No se debe confundir con la complejidad de resolver la versión exacta de decisión.

## 7. Resultado experimental documentado

La primera búsqueda por coordenadas obtuvo 9/100 = 9,0 % en búsqueda y la configuración resultante obtuvo 8/87 = 9,2 % en validación. No se aceptó ningún cambio respecto del baseline. La configuración es la mejor observada por el procedimiento ejecutado, no un óptimo global demostrado.

## 8. NP-dureza: requisito y estado

La guía específica de ADAG1 solicita demostrar NP-dureza de la configuración óptima con oráculo exacto mediante una reducción polinomial desde 3-SAT. La guía también indica que la búsqueda práctica con consultas limitadas o ruidosas debe analizarse por complejidad de muestreo, separadamente.

**Esta demostración no se declara completada en este borrador.** Para que sea válida hay que:

1. Definir con precisión una familia generalizada de instancias cuyo tamaño crezca con la entrada (por ejemplo, número de variables, restricciones o ranuras).
2. Definir la representación de la instancia, el catálogo y el comportamiento del oráculo exacto como parte del problema formal.
3. Construir una transformación polinomial `φ ↦ I(φ)` desde una fórmula 3-SAT.
4. Demostrar ambos sentidos: `φ` satisfacible si y solo si `I(φ)` admite una configuración con el umbral requerido.
5. Verificar que la transformación y el umbral se computan en tiempo polinomial y que la equivalencia no depende de asumir el resultado que se quiere probar.

**Advertencia de alcance:** el catálogo empírico actual tiene exactamente cinco ranuras y ocho alternativas por ranura. Ese espacio fijo de 32.768 configuraciones puede enumerarse por completo y, por sí solo, no proporciona una familia de tamaño variable para una reducción desde 3-SAT. La demostración debe referirse a una generalización formal que esté justificada por el enunciado, no atribuir NP-dureza automáticamente al experimento finito.

## 9. Referencias internas

- README del monitor: definición del espacio, datasets y evaluación todo-o-nada.
- Guía de Primera Entrega ADAG1, secciones 3, 4 y 7.
- `docs/REGISTRO_EXPERIMENTAL_G1.md`: evidencia de la ejecución y validación.
