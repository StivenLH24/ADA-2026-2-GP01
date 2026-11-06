"""Búsqueda por pares guiada por trazas para el Proyecto Oráculo G1.

Toma como punto de partida la mejor configuración de CoordinateSearch y sus
refinamientos de una sola ranura. Propone combinaciones de dos cambios usando
la complementariedad de instancias acertadas y la diversidad de familias de
fallo observadas en las trazas. Luego comprueba las combinaciones con el
oráculo: primero en un screening reproducible y después sobre todo el split
de búsqueda para los finalistas.

No consulta la partición de validación para seleccionar candidatos.
"""
from __future__ import annotations

import copy
import itertools
import json
import os
import random
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any


def _normalizar_ids(values):
    return {str(value) for value in values}


def _aciertos(registro):
    ids = _normalizar_ids(registro.get("ids_instancias", []))
    fallos = _normalizar_ids(
        t.get("id") for t in registro.get("trazas", []) if t.get("id") is not None
    )
    return ids - fallos


def _familias(registro):
    return {
        t.get("violo")
        for t in registro.get("trazas", [])
        if t.get("violo")
    }


def _jaccard(a, b):
    union = set(a) | set(b)
    if not union:
        return 1.0
    return len(set(a) & set(b)) / len(union)


def _guardar_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(value, f, ensure_ascii=False, indent=2)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def _cargar_historial_coordenadas(path):
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)

    evaluaciones = data.get("evaluaciones")
    if not isinstance(evaluaciones, list):
        raise ValueError("El historial de coordenadas no contiene evaluaciones.")

    baselines = [e for e in evaluaciones if e.get("etapa") == "baseline"]
    if not baselines:
        raise ValueError("El historial no contiene un baseline.")

    baseline = baselines[0]
    config_base = copy.deepcopy(data.get("configuracion_actual"))
    if not isinstance(config_base, dict):
        config_base = copy.deepcopy(baseline["configuracion"])

    if config_base != baseline["configuracion"]:
        raise ValueError(
            "Esta implementación de búsqueda por pares requiere que la "
            "configuración final de CoordinateSearch coincida con el baseline. "
            "En la primera ejecución G1 sí coinciden porque no hubo cambios aceptados."
        )

    n = int(baseline["instancias"])
    ids_base = _normalizar_ids(baseline.get("ids_instancias", []))
    if len(ids_base) != n:
        raise ValueError("Los IDs del baseline no coinciden con su tamaño.")

    refinamientos = [
        e for e in evaluaciones
        if e.get("etapa") == "refinamiento" and int(e.get("instancias", 0)) == n
    ]

    candidatos = []
    ranuras = [r for r in config_base if r != "temperatura"]
    for registro in refinamientos:
        config = registro.get("configuracion", {})
        diferencias = [
            r for r in ranuras
            if config.get(r) != config_base.get(r)
        ]
        if len(diferencias) != 1:
            continue
        ranura = diferencias[0]
        if registro.get("ranura") != ranura:
            continue
        if _normalizar_ids(registro.get("ids_instancias", [])) != ids_base:
            continue
        candidatos.append({
            "ranura": ranura,
            "indice": int(config[ranura]),
            "configuracion": copy.deepcopy(config),
            "aciertos": _aciertos(registro),
            "familias": _familias(registro),
            "precision": float(registro["precision"]),
        })

    if not candidatos:
        raise ValueError("No se encontraron refinamientos individuales completos.")
    return config_base, baseline, candidatos


def _crear_pares(config_base, baseline, candidatos, top_pares):
    aciertos_base = _aciertos(baseline)
    pares = []

    for a, b in itertools.combinations(candidatos, 2):
        if a["ranura"] == b["ranura"]:
            continue

        config = copy.deepcopy(config_base)
        config[a["ranura"]] = a["indice"]
        config[b["ranura"]] = b["indice"]

        cobertura_potencial = aciertos_base | a["aciertos"] | b["aciertos"]
        familias_a, familias_b = a["familias"], b["familias"]
        diversidad_familias = 1.0 - _jaccard(familias_a, familias_b)
        ganancia_potencial = len(cobertura_potencial - aciertos_base)

        pares.append({
            "configuracion": config,
            "cambio_a": {"ranura": a["ranura"], "indice": a["indice"]},
            "cambio_b": {"ranura": b["ranura"], "indice": b["indice"]},
            "aciertos_potenciales_union": len(cobertura_potencial),
            "ganancia_potencial_sobre_base": ganancia_potencial,
            "diversidad_familias_fallo": round(diversidad_familias, 6),
            "familias_a": sorted(familias_a),
            "familias_b": sorted(familias_b),
        })

    # La unión de aciertos individuales es una cota heurística de complementariedad,
    # no una predicción garantizada del comportamiento conjunto.
    pares.sort(
        key=lambda p: (
            -p["aciertos_potenciales_union"],
            -p["diversidad_familias_fallo"],
            p["cambio_a"]["ranura"],
            p["cambio_a"]["indice"],
            p["cambio_b"]["ranura"],
            p["cambio_b"]["indice"],
        )
    )

    distintos = []
    vistos = set()
    for par in pares:
        key = json.dumps(par["configuracion"], sort_keys=True)
        if key in vistos:
            continue
        vistos.add(key)
        distintos.append(par)
        if len(distintos) >= top_pares:
            break
    return distintos


def _ids_datos(datos):
    return [x.get("id") for x in datos]


def _buscar_evaluacion(historial, etapa, config, ids, semilla):
    for item in reversed(historial.get("evaluaciones", [])):
        if (
            item.get("etapa") == etapa
            and item.get("configuracion") == config
            and item.get("ids_instancias") == ids
            and item.get("semilla") == semilla
        ):
            return item
    return None


def _evaluar(
    oraculo,
    historial,
    ruta_historial,
    config,
    datos,
    etapa,
    semilla,
):
    ids = _ids_datos(datos)
    anterior = _buscar_evaluacion(historial, etapa, config, ids, semilla)
    if anterior is not None:
        return anterior

    resultado = oraculo.evaluar(
        config,
        instancias=datos,
        semilla=semilla,
        desc=f"G1-pares-{etapa}",
    )
    trazas = list(resultado.trazas or [])
    familias = Counter(t.get("violo") for t in trazas if t.get("violo"))

    registro = {
        "evaluacion": len(historial["evaluaciones"]) + 1,
        "etapa": etapa,
        "configuracion": copy.deepcopy(config),
        "precision": float(resultado.precision),
        "precision_porcentaje": round(100 * float(resultado.precision), 4),
        "instancias": int(resultado.n),
        "correctas": int(resultado.n) - len(trazas),
        "fallidas": len(trazas),
        "semilla": semilla,
        "ids_instancias": ids,
        "ids_fallidos": [t.get("id") for t in trazas],
        "familias_primera_falla": dict(familias),
    }
    historial["evaluaciones"].append(registro)
    _guardar_json(ruta_historial, historial)
    return registro


def ejecutar_busqueda_pares_guiada(
    oraculo: Any,
    datos_busqueda: list[dict[str, Any]],
    historial_coordinate_path: str | Path,
    historial_pares_path: str | Path,
    *,
    screen_n: int = 40,
    top_pares: int = 6,
    finalistas: int = 2,
    semilla: int = 2026,
) -> tuple[dict[str, Any], float, dict[str, Any]]:
    """Ejecuta o reanuda una búsqueda limitada de combinaciones de dos ranuras.

    1. Lee refinamientos individuales y trazas del historial CoordinateSearch.
    2. Prioriza parejas con instancias acertadas complementarias y familias de
       fallo distintas.
    3. Evalúa las parejas priorizadas en una muestra reproducible.
    4. Refina los mejores candidatos sobre todas las instancias de búsqueda.
    5. Acepta únicamente una mejora estricta sobre el baseline original.

    Si la ejecución se interrumpe, se puede llamar de nuevo con los mismos
    parámetros y rutas. Las evaluaciones completas se recuperan del historial
    de pares y las generaciones parciales de la caché del oráculo.
    """
    if not datos_busqueda:
        raise ValueError("datos_busqueda está vacío.")
    if screen_n < 1 or top_pares < 1 or finalistas < 1:
        raise ValueError("screen_n, top_pares y finalistas deben ser >= 1.")

    ruta_coord = Path(historial_coordinate_path)
    ruta_pares = Path(historial_pares_path)
    config_base, baseline, candidatos = _cargar_historial_coordenadas(ruta_coord)

    ids_busqueda = _normalizar_ids(_ids_datos(datos_busqueda))
    if ids_busqueda != _normalizar_ids(baseline["ids_instancias"]):
        raise ValueError("datos_busqueda no coincide con las 100 instancias del baseline.")

    if ruta_pares.exists():
        with ruta_pares.open("r", encoding="utf-8") as f:
            historial = json.load(f)
        if historial.get("configuracion_base") != config_base:
            raise ValueError("El historial de pares pertenece a otra configuración base.")
        if historial.get("parametros", {}).get("semilla") != semilla:
            raise ValueError("El historial de pares utiliza otra semilla.")
    else:
        pares = _crear_pares(config_base, baseline, candidatos, top_pares)
        historial = {
            "version": 1,
            "metodo": "busqueda por pares guiada por complementariedad de aciertos y diversidad de fallos",
            "configuracion_base": config_base,
            "precision_base": float(baseline["precision"]),
            "parametros": {
                "screen_n": screen_n,
                "top_pares": top_pares,
                "finalistas": finalistas,
                "semilla": semilla,
            },
            "pares_priorizados": pares,
            "evaluaciones": [],
            "resultado": None,
        }
        _guardar_json(ruta_pares, historial)

    pares = historial["pares_priorizados"]
    if not pares:
        raise ValueError("No se pudieron construir combinaciones de dos ranuras.")

    muestra = (
        list(datos_busqueda)
        if screen_n >= len(datos_busqueda)
        else random.Random(semilla).sample(datos_busqueda, screen_n)
    )

    # Baseline de screening para comparar novedad de IDs fallidos en la misma muestra.
    base_screen = _evaluar(
        oraculo, historial, ruta_pares, config_base, muestra,
        "baseline_screening", semilla
    )
    base_fail_sample = _normalizar_ids(base_screen["ids_fallidos"])

    print("Configuración base:", config_base)
    print(f"Baseline completo: {baseline['precision_porcentaje']:.1f}%")
    print("Muestra screening:", len(muestra))
    print("Pares priorizados:", len(pares))

    screen_records = []
    for par in pares:
        rec = _evaluar(
            oraculo, historial, ruta_pares,
            par["configuracion"], muestra, "pair_screening", semilla
        )
        fallos = _normalizar_ids(rec["ids_fallidos"])
        novedad = 1.0 - _jaccard(fallos, base_fail_sample)
        rec_view = dict(rec)
        rec_view["novedad_fallos_vs_base"] = round(novedad, 6)
        screen_records.append((rec_view, par))

    screen_records.sort(
        key=lambda item: (
            -item[0]["precision"],
            -item[0]["novedad_fallos_vs_base"],
            -len(item[0]["familias_primera_falla"]),
        )
    )
    shortlist = screen_records[:min(finalistas, len(screen_records))]
    print("Finalistas del screening:")
    for rec, par in shortlist:
        print(
            f"  {par['cambio_a']} + {par['cambio_b']}: "
            f"{rec['precision_porcentaje']:.1f}%"
        )

    full_records = []
    for rec, par in shortlist:
        full = _evaluar(
            oraculo, historial, ruta_pares,
            par["configuracion"], datos_busqueda, "pair_refinamiento", semilla
        )
        full_records.append((full, par))

    mejor = max(full_records, key=lambda item: item[0]["precision"])
    baseline_precision = float(baseline["precision"])
    if float(mejor[0]["precision"]) > baseline_precision:
        config_final = copy.deepcopy(mejor[1]["configuracion"])
        precision_final = float(mejor[0]["precision"])
    else:
        config_final = copy.deepcopy(config_base)
        precision_final = baseline_precision

    historial["resultado"] = {
        "configuracion": config_final,
        "precision": precision_final,
        "precision_porcentaje": round(100 * precision_final, 4),
        "mejora_sobre_baseline": precision_final > baseline_precision,
        "finalistas_refinados": [
            {
                "configuracion": rec["configuracion"],
                "precision": rec["precision"],
                "precision_porcentaje": rec["precision_porcentaje"],
            }
            for rec, _ in full_records
        ],
    }
    _guardar_json(ruta_pares, historial)

    print("Resultado de búsqueda por pares:")
    print("Configuración:", config_final)
    print(f"Precisión: {precision_final:.1%}")
    print("Mejora estricta:", precision_final > baseline_precision)
    print("Historial:", ruta_pares)
    return config_final, precision_final, historial
