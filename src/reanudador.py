"""Reanudación segura de una ronda de CoordinateSearch para G1.

Carga el checkpoint JSON del optimizador, omite evaluaciones completas y
reutiliza la caché persistente del Oraculo cuando una evaluación quedó a medias.
Diseñado para la estrategia de una ronda usada en 01_busqueda_G1.ipynb.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


def _ids(datos: list[dict[str, Any]]) -> list[Any]:
    return [fila.get("id") for fila in datos]


def _buscar_evaluacion(historial, *, etapa, ranura, indice, configuracion,
                       semilla, ids_instancias):
    """Busca una evaluación completa exactamente equivalente en el historial."""
    for registro in reversed(historial):
        if (
            registro.get("etapa") == etapa
            and registro.get("ranura") == ranura
            and registro.get("indice_candidato") == indice
            and registro.get("configuracion") == configuracion
            and registro.get("semilla") == semilla
            and registro.get("ids_instancias") == ids_instancias
        ):
            return float(registro["precision"])
    return None


def _evaluar_o_reutilizar(optimizador, *, configuracion, datos, semilla,
                          etapa, ranura=None, indice=None):
    """Evita reevaluar resultados completos; la caché del oráculo cubre parciales."""
    precision = _buscar_evaluacion(
        optimizador.historial,
        etapa=etapa,
        ranura=ranura,
        indice=indice,
        configuracion=configuracion,
        semilla=semilla,
        ids_instancias=_ids(datos),
    )
    if precision is not None:
        return precision
    return optimizador._evaluar(
        configuracion, datos, semilla, etapa=etapa,
        ranura=ranura, indice=indice
    )


def _restaurar_checkpoint(optimizador):
    ruta = getattr(optimizador, "historial_path", None)
    if ruta is None:
        raise ValueError("El optimizador debe tener historial_path en Google Drive.")
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el checkpoint: {ruta}")

    with ruta.open("r", encoding="utf-8") as archivo:
        estado = json.load(archivo)

    evaluaciones = estado.get("evaluaciones")
    resumen = estado.get("resumen_coordenadas")
    if not isinstance(evaluaciones, list) or not isinstance(resumen, list):
        raise ValueError("El historial no tiene el formato esperado.")

    optimizador.historial = evaluaciones
    optimizador.resumen = resumen
    optimizador._secuencia = max(
        (int(reg.get("evaluacion", 0)) for reg in evaluaciones), default=0
    )

    config = estado.get("configuracion_actual")
    precision = estado.get("precision_actual")
    if config is None or precision is None:
        baselines = [r for r in evaluaciones if r.get("etapa") == "baseline"]
        if not baselines:
            raise ValueError("El checkpoint no contiene una configuración recuperable.")
        config = copy.deepcopy(baselines[-1]["configuracion"])
        precision = float(baselines[-1]["precision"])

    optimizador.validar_configuracion(config)
    optimizador.configuracion_actual = copy.deepcopy(config)
    optimizador.precision_actual = float(precision)
    optimizador._guardar_historial()


def reanudar_busqueda_g1(optimizador, datos_busqueda, *, screen_n=10,
                         finalistas=2, semilla=2026, ronda=1):
    """Reanuda y termina una ronda desde el último checkpoint persistido.

    Si Colab se interrumpe otra vez, ejecutar la función de nuevo. Retoma la
    primera ranura sin resumen; no repite evaluaciones completas y la caché
    persistente del Oraculo reutiliza generaciones ya producidas.
    """
    if not datos_busqueda:
        raise ValueError("datos_busqueda está vacío.")
    if screen_n < 1 or finalistas < 1:
        raise ValueError("screen_n y finalistas deben ser >= 1.")

    _restaurar_checkpoint(optimizador)
    actual = copy.deepcopy(optimizador.configuracion_actual)
    precision_actual = float(optimizador.precision_actual)
    muestra = optimizador._muestra_reproducible(
        datos_busqueda, min(screen_n, len(datos_busqueda)), semilla
    )

    completadas = {
        r["ranura"] for r in optimizador.resumen
        if int(r.get("ronda", -1)) == ronda
    }
    hubo_mejora = any(
        bool(r.get("mejora")) for r in optimizador.resumen
        if int(r.get("ronda", -1)) == ronda
    )

    print("Checkpoint restaurado.")
    print("Evaluaciones:", len(optimizador.historial))
    print("Coordenadas completadas:", sorted(completadas))
    print("Configuración actual:", actual)
    print(f"Precisión actual: {precision_actual:.1%}")

    for ranura in optimizador.ranuras:
        if ranura in completadas:
            continue

        indice_actual = actual[ranura]
        candidatos = []
        print(f"\n========== REANUDANDO {ranura.upper()} ==========")

        for indice in range(len(optimizador.catalogo[ranura])):
            if indice == indice_actual:
                continue
            candidato = copy.deepcopy(actual)
            candidato[ranura] = indice
            p_screen = _evaluar_o_reutilizar(
                optimizador, configuracion=candidato, datos=muestra,
                semilla=semilla, etapa="screening",
                ranura=ranura, indice=indice
            )
            candidatos.append((p_screen, indice, candidato))

        candidatos.sort(key=lambda x: (-x[0], x[1]))
        shortlist = candidatos[:min(finalistas, len(candidatos))]
        print("Finalistas:", [
            {"indice": i, "precision_screen": p}
            for p, i, _ in shortlist
        ])

        mejor_config = copy.deepcopy(actual)
        mejor_precision = precision_actual
        precision_antes = precision_actual

        for _, indice, candidato in shortlist:
            p_full = _evaluar_o_reutilizar(
                optimizador, configuracion=candidato, datos=datos_busqueda,
                semilla=semilla, etapa="refinamiento",
                ranura=ranura, indice=indice
            )
            if p_full > mejor_precision:
                mejor_precision = p_full
                mejor_config = copy.deepcopy(candidato)

        mejora = mejor_precision > precision_actual
        if mejora:
            actual = mejor_config
            precision_actual = mejor_precision
            hubo_mejora = True

        optimizador.configuracion_actual = copy.deepcopy(actual)
        optimizador.precision_actual = precision_actual
        optimizador.resumen.append({
            "ronda": ronda,
            "ranura": ranura,
            "indice_anterior": indice_actual,
            "indice_seleccionado": actual[ranura],
            "precision_anterior": precision_antes,
            "precision_nueva": precision_actual,
            "mejora": mejora,
            "configuracion_resultante": copy.deepcopy(actual),
        })
        optimizador._guardar_historial()

        print(
            f"{ranura}: {indice_actual} -> {actual[ranura]}, "
            f"{precision_antes:.1%} -> {precision_actual:.1%}"
        )

    print("\n========== RONDA RECUPERADA ==========")
    print("Configuración:", actual)
    print(f"Precisión en búsqueda: {precision_actual:.1%}")
    print("Evaluaciones registradas:", len(optimizador.historial))
    print("Historial:", optimizador.historial_path)
    if not hubo_mejora:
        print("Sin mejoras en esta ronda; se alcanzó el criterio de parada.")
    return actual, precision_actual
