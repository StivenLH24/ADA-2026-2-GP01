"""Búsqueda por coordenadas para el Proyecto Oráculo (G1).

El optimizador no modifica la caja negra oraculo.py. Recibe el objeto Oraculo
y el catálogo desde el notebook, registra cada evaluación y persiste un
historial auditable. Si el proceso se repite con la caché del oráculo intacta,
las generaciones ya hechas se reutilizan.
"""
from __future__ import annotations

import copy
import json
import os
import random
import tempfile
from pathlib import Path
from typing import Any


class CoordinateSearch:
    """Búsqueda local por coordenadas con preselección y refinamiento.

    Para cada ranura:
      1. Explora todas sus alternativas en una muestra fija de screening.
      2. Refina los mejores candidatos sobre el conjunto completo de búsqueda.
      3. Acepta un cambio solo si mejora la precisión en el conjunto completo.

    Esta heurística no garantiza un óptimo global. El conjunto de validación
    debe reservarse para evaluar la configuración final, no para seleccionarla.
    """

    def __init__(
        self,
        oraculo: Any,
        catalogo: dict[str, list[str]],
        ranuras: list[str],
        historial_path: str | Path | None = None,
        temperaturas: tuple[float, ...] = (0.0,),
    ) -> None:
        if not ranuras:
            raise ValueError("La lista de ranuras no puede estar vacía.")
        if set(catalogo) != set(ranuras):
            raise ValueError("El catálogo debe contener exactamente las ranuras indicadas.")
        if any(not catalogo[ranura] for ranura in ranuras):
            raise ValueError("Cada ranura debe tener al menos una alternativa.")
        if not temperaturas:
            raise ValueError("Debe definirse al menos una temperatura.")

        self.oraculo = oraculo
        self.catalogo = catalogo
        self.ranuras = list(ranuras)
        self.temperaturas = tuple(temperaturas)
        self.historial_path = Path(historial_path) if historial_path else None
        self.historial: list[dict[str, Any]] = []
        self.resumen: list[dict[str, Any]] = []
        self._secuencia = 0

    def validar_configuracion(self, config: dict[str, Any]) -> None:
        """Valida las claves, índices y temperatura de una configuración."""
        if not isinstance(config, dict):
            raise TypeError("La configuración debe ser un diccionario.")

        claves_esperadas = set(self.ranuras) | {"temperatura"}
        if set(config) != claves_esperadas:
            raise ValueError(
                f"Claves esperadas: {sorted(claves_esperadas)}; "
                f"recibidas: {sorted(config)}."
            )

        for ranura in self.ranuras:
            indice = config[ranura]
            if isinstance(indice, bool) or not isinstance(indice, int):
                raise TypeError(f"El índice de {ranura!r} debe ser entero.")
            if not 0 <= indice < len(self.catalogo[ranura]):
                raise ValueError(f"Índice fuera de rango para {ranura!r}.")

        temperatura = config["temperatura"]
        if isinstance(temperatura, bool) or not isinstance(temperatura, (int, float)):
            raise TypeError("'temperatura' debe ser numérica.")
        if temperatura not in self.temperaturas:
            raise ValueError(f"'temperatura' debe pertenecer a {self.temperaturas}.")

    def _guardar_historial(self) -> None:
        """Guarda el historial atómicamente después de cada evaluación."""
        if self.historial_path is None:
            return

        self.historial_path.parent.mkdir(parents=True, exist_ok=True)
        contenido = {
            "version": 1,
            "evaluaciones": self.historial,
            "resumen_coordenadas": self.resumen,
            "configuracion_actual": getattr(self, "configuracion_actual", None),
            "precision_actual": getattr(self, "precision_actual", None),
        }
        fd, temporal = tempfile.mkstemp(
            prefix=self.historial_path.name,
            suffix=".tmp",
            dir=str(self.historial_path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as archivo:
                json.dump(contenido, archivo, ensure_ascii=False, indent=2)
            Path(temporal).replace(self.historial_path)
        except Exception:
            Path(temporal).unlink(missing_ok=True)
            raise

    def _evaluar(
        self,
        config: dict[str, Any],
        datos: list[dict[str, Any]],
        semilla: int,
        etapa: str,
        ranura: str | None = None,
        indice: int | None = None,
    ) -> float:
        self.validar_configuracion(config)
        if not datos:
            raise ValueError("No se puede evaluar sobre un conjunto vacío.")

        resultado = self.oraculo.evaluar(
            config,
            instancias=datos,
            semilla=semilla,
            desc=f"G1-{etapa}",
        )
        precision = float(resultado.precision)
        n = int(resultado.n)
        trazas = list(resultado.trazas or [])
        if not 0.0 <= precision <= 1.0:
            raise ValueError(f"Precisión fuera del intervalo [0, 1]: {precision}")
        if n != len(datos):
            raise ValueError(
                f"El oráculo informó n={n}, pero se enviaron {len(datos)} instancias."
            )

        self._secuencia += 1
        registro = {
            "evaluacion": self._secuencia,
            "etapa": etapa,
            "ranura": ranura,
            "indice_candidato": indice,
            "configuracion": copy.deepcopy(config),
            "precision": precision,
            "precision_porcentaje": round(100 * precision, 4),
            "instancias": n,
            "correctas": n - len(trazas),
            "fallidas": len(trazas),
            "semilla": semilla,
            "ids_instancias": [x.get("id") for x in datos],
            "trazas": trazas,
        }
        self.historial.append(registro)
        self._guardar_historial()
        return precision

    @staticmethod
    def _muestra_reproducible(
        datos: list[dict[str, Any]], n: int, semilla: int
    ) -> list[dict[str, Any]]:
        if n < 1:
            raise ValueError("screen_n debe ser al menos 1.")
        if n >= len(datos):
            return list(datos)
        return random.Random(semilla).sample(datos, n)

    def optimizar(
        self,
        datos_busqueda: list[dict[str, Any]],
        configuracion_inicial: dict[str, Any],
        *,
        screen_n: int = 10,
        finalistas: int = 2,
        max_rondas: int = 1,
        semilla: int = 1,
    ) -> tuple[dict[str, Any], float]:
        """Optimiza en búsqueda; acepta cambios solo medidos sobre todo el split.

        La muestra de screening filtra candidatos. Las decisiones de aceptación
        se toman comparando finalistas sobre todos los datos_busqueda.
        """
        if not datos_busqueda:
            raise ValueError("El conjunto de búsqueda está vacío.")
        if finalistas < 1:
            raise ValueError("finalistas debe ser >= 1.")
        if max_rondas < 1:
            raise ValueError("max_rondas debe ser >= 1.")

        actual = copy.deepcopy(configuracion_inicial)
        self.validar_configuracion(actual)
        muestra_screen = self._muestra_reproducible(
            datos_busqueda, min(screen_n, len(datos_busqueda)), semilla
        )

        precision_actual = self._evaluar(
            actual, datos_busqueda, semilla, etapa="baseline"
        )
        self.configuracion_actual = copy.deepcopy(actual)
        self.precision_actual = precision_actual
        self._guardar_historial()
        print(
            f"[Coordinate Search] Baseline: {precision_actual:.1%} "
            f"({len(datos_busqueda)} instancias)"
        )

        for ronda in range(1, max_rondas + 1):
            hubo_mejora_ronda = False
            print(f"\n========== RONDA {ronda} ==========")

            for ranura in self.ranuras:
                indice_actual = actual[ranura]
                candidatos = []

                for indice in range(len(self.catalogo[ranura])):
                    if indice == indice_actual:
                        continue
                    candidato = copy.deepcopy(actual)
                    candidato[ranura] = indice
                    precision_screen = self._evaluar(
                        candidato,
                        muestra_screen,
                        semilla,
                        etapa="screening",
                        ranura=ranura,
                        indice=indice,
                    )
                    candidatos.append((precision_screen, indice, candidato))

                candidatos.sort(key=lambda item: (-item[0], item[1]))
                shortlist = candidatos[: min(finalistas, len(candidatos))]

                mejor_config = copy.deepcopy(actual)
                mejor_precision = precision_actual
                precision_antes = precision_actual

                for _, indice, candidato in shortlist:
                    precision_full = self._evaluar(
                        candidato,
                        datos_busqueda,
                        semilla,
                        etapa="refinamiento",
                        ranura=ranura,
                        indice=indice,
                    )
                    if precision_full > mejor_precision:
                        mejor_precision = precision_full
                        mejor_config = copy.deepcopy(candidato)

                mejora = mejor_precision > precision_actual
                if mejora:
                    actual = mejor_config
                    precision_actual = mejor_precision
                    hubo_mejora_ronda = True

                self.configuracion_actual = copy.deepcopy(actual)
                self.precision_actual = precision_actual
                self.resumen.append(
                    {
                        "ronda": ronda,
                        "ranura": ranura,
                        "indice_anterior": indice_actual,
                        "indice_seleccionado": actual[ranura],
                        "precision_anterior": precision_antes,
                        "precision_nueva": precision_actual,
                        "mejora": mejora,
                        "configuracion_resultante": copy.deepcopy(actual),
                    }
                )
                self._guardar_historial()

                print(
                    f"{ranura}: índice {indice_actual} -> {actual[ranura]}, "
                    f"precisión {precision_antes:.1%} -> {precision_actual:.1%}"
                )

            if not hubo_mejora_ronda:
                print("Sin mejoras en la ronda; se detiene la búsqueda.")
                break

        return actual, precision_actual
