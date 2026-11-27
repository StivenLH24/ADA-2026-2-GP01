#!/usr/bin/env python3
"""Evalúa cada restricción por separado sobre respuestas ya cacheadas.

No carga el modelo ni genera texto. Reutiliza las clases de IFEvalG para
comprobar todas las restricciones de cada instancia fallida, incluso cuando
el oráculo original se detuvo en la primera que no se cumplió.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def cargar_json(path: str | Path) -> Any:
    with Path(path).open(encoding="utf-8") as archivo:
        return json.load(archivo)


def huella(config: dict[str, Any]) -> str:
    return hashlib.md5(json.dumps(config, sort_keys=True).encode()).hexdigest()[:8]


def resolver_registro(ids: list[str], registros: list[dict[str, Any]]) -> list[Any]:
    """Resuelve cada ID con la misma precedencia que Oraculo._clase."""
    clases = []
    for iid in ids:
        for registro in registros:
            if iid in registro:
                clases.append(registro[iid])
                break
        else:
            raise KeyError(f"Ningún registro conoce {iid!r}")
    return clases


def verificar_independientemente(instancia: dict[str, Any], respuesta: str,
                                  registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ejecuta todos los verificadores sin cortar en el primer incumplimiento."""
    if len(instancia["ids"]) != len(instancia["kwargs"]):
        raise ValueError(f"IDs y kwargs desalineados en instancia {instancia['id']}")
    clases = resolver_registro(instancia["ids"], registros)
    resultados = []
    for iid, kwargs, clase in zip(instancia["ids"], instancia["kwargs"], clases):
        verificador = clase(iid)
        verificador.build_description(**kwargs)
        args = verificador.get_instruction_args()
        if args and "prompt" in args:
            verificador.build_description(prompt=instancia["prompt"])
        cumple = bool(verificador.check_following(respuesta))
        resultados.append({"restriccion": iid, "familia": iid.split(":", 1)[0],
                           "cumple": cumple, "error": ""})
    return resultados


def reconstruir_respuestas(dataset, cache, historial):
    if historial.get("version_catalogo") != "g1-v2":
        raise ValueError("El historial no corresponde a g1-v2.")
    config = historial.get("configuracion_actual")
    if not isinstance(config, dict):
        raise ValueError("El historial no contiene configuracion_actual.")
    hconfig = huella(config)
    baseline = next((e for e in historial["evaluaciones"] if e.get("etapa") == "baseline"), None)
    if baseline is None:
        raise ValueError("No existe evaluación baseline en el historial.")
    ids_busqueda = set(map(int, baseline["ids_instancias"]))
    evaluacion_final = next((e for e in reversed(historial["evaluaciones"])
                             if e.get("configuracion") == config
                             and e.get("etapa") in {"refinamiento", "baseline"}), baseline)
    semilla = int(evaluacion_final.get("semilla", baseline.get("semilla", 2026)))
    candidatos = {}
    modelos = set()
    for clave, valor in cache.items():
        partes = clave.split("|")
        if len(partes) != 5:
            continue
        version, modelo, h, iid, semilla_cache = partes
        if version != "g1-v2" or h != hconfig or int(semilla_cache) != semilla:
            continue
        if int(iid) in ids_busqueda:
            continue
        modelos.add(modelo)
        candidatos[int(iid)] = valor
    if len(modelos) != 1:
        raise ValueError(f"Se esperaba un único modelo en la caché; encontrados: {sorted(modelos)}")

    filas = []
    for instancia in dataset:
        if instancia.get("split") != "validacion":
            continue
        iid = int(instancia["id"])
        if iid not in candidatos:
            raise ValueError(f"No hay respuesta cacheada para la instancia de validación {iid}.")
        valor = candidatos[iid]
        if not isinstance(valor, list) or len(valor) != 3:
            raise ValueError(f"Formato de caché inesperado para instancia {iid}.")
        correcto, primera_falla, salida = valor
        if not correcto:
            filas.append({"instancia": instancia, "salida": salida,
                          "primera_falla_cache": primera_falla})
    return filas, config, next(iter(modelos))


def analizar(filas, registros):
    detalle = []
    conteos = Counter()
    familias = Counter()
    multiples = 0
    for fila in filas:
        instancia, salida = fila["instancia"], fila["salida"]
        checks = verificar_independientemente(instancia, salida, registros)
        fallidas = [x["restriccion"] for x in checks if not x["cumple"]]
        if not fallidas:
            raise AssertionError(f"Instancia {instancia['id']}: caché dice fallida, pero todos los verificadores pasan.")
        if fallidas[0] != fila["primera_falla_cache"]:
            raise AssertionError(
                f"Orden inconsistente en {instancia['id']}: caché={fila['primera_falla_cache']}, "
                f"recalculado={fallidas[0]}"
            )
        if len(fallidas) > 1:
            multiples += 1
        for check in checks:
            conteos[check["restriccion"]] += int(not check["cumple"])
            familias[check["familia"]] += int(not check["cumple"])
        detalle.append({
            "id": instancia["id"],
            "primera_falla": fila["primera_falla_cache"],
            "restricciones_totales": len(checks),
            "restricciones_incumplidas": len(fallidas),
            "incumplidas": " | ".join(fallidas),
            "cumplidas": " | ".join(x["restriccion"] for x in checks if x["cumple"]),
            "salida": salida,
        })
    return detalle, conteos, familias, multiples


def cargar_registros(ruta_open_instruct: str):
    if ruta_open_instruct and ruta_open_instruct not in sys.path:
        sys.path.insert(0, ruta_open_instruct)
    from open_instruct.IFEvalG import instructions_registry
    return [instructions_registry.INSTRUCTION_DICT]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, help="datos_visibles_G1_v2.json")
    parser.add_argument("--cache", required=True, help="cache_oraculo_G1_v2.json")
    parser.add_argument("--historial", required=True, help="historial_coordinate_search_G1_v2.json")
    parser.add_argument("--open-instruct", default="/content/open-instruct",
                        help="Ruta al clon de allenai/open-instruct")
    parser.add_argument("--salida", default="reporte_multirestriccion_G1_v2")
    args = parser.parse_args()

    dataset = cargar_json(args.dataset)
    cache = cargar_json(args.cache)
    historial = cargar_json(args.historial)
    filas, config, modelo = reconstruir_respuestas(dataset, cache, historial)
    registros = cargar_registros(args.open_instruct)
    detalle, conteos, familias, multiples = analizar(filas, registros)

    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)
    path_detalle = salida / "matriz_fallos_multirestriccion_G1_v2.csv"
    path_restricciones = salida / "conteo_restricciones_G1_v2.csv"
    path_familias = salida / "conteo_familias_G1_v2.csv"
    path_reporte = salida / "reporte_multirestriccion_G1_v2.md"

    with path_detalle.open("w", newline="", encoding="utf-8-sig") as f:
        campos = ["id", "primera_falla", "restricciones_totales", "restricciones_incumplidas",
                  "incumplidas", "cumplidas", "salida"]
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(detalle)
    for path, conteo, titulo in [
        (path_restricciones, conteos, "restriccion"),
        (path_familias, familias, "familia"),
    ]:
        total = sum(conteo.values())
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([titulo, "incumplimientos", "porcentaje"])
            for nombre, n in conteo.most_common():
                writer.writerow([nombre, n, round(100*n/total, 2) if total else 0])

    total_checks = sum(conteos.values())
    lines = [
        "# Diagnóstico multirrestricción — G1 catálogo v2", "",
        f"- Modelo: `{modelo}`", f"- Configuración: `{json.dumps(config, sort_keys=True)}`",
        f"- Instancias fallidas examinadas: {len(detalle)}",
        f"- Instancias con más de una restricción incumplida: {multiples}",
        f"- Incumplimientos individuales detectados: {total_checks}", "",
        "## Incumplimientos por restricción", "", "| Restricción | Incumplimientos |", "|---|---:|",
    ]
    lines.extend(f"| `{nombre}` | {n} |" for nombre, n in conteos.most_common())
    lines += ["", "## Incumplimientos por familia", "", "| Familia | Incumplimientos |", "|---|---:|"]
    lines.extend(f"| `{nombre}` | {n} |" for nombre, n in familias.most_common())
    lines += ["", "## Interpretación", "",
              "Cada salida se pasó por separado a todos los verificadores asociados a su instancia. "
              "Los conteos representan incumplimientos individuales; por eso una instancia puede "
              "contribuir más de una vez. Las excepciones de los verificadores detienen el análisis "
              "en lugar de clasificarse como incumplimientos. Este diagnóstico no modifica la "
              "configuración ni usa la validación para optimizar.", ""]
    path_reporte.write_text("\n".join(lines), encoding="utf-8")
    print(f"Modelo: {modelo}; instancias fallidas: {len(detalle)}")
    print(f"Con fallos múltiples: {multiples}/{len(detalle)}")
    print(f"Incumplimientos individuales: {total_checks}")
    print("Top restricciones:")
    for nombre, n in conteos.most_common(10):
        print(f"  {n:3}  {nombre}")
    print(f"Archivos generados en: {salida.resolve()}")


if __name__ == "__main__":
    main()
