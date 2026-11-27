#!/usr/bin/env python3
"""Calcula coocurrencia de restricciones incumplidas desde la matriz multirrestricción."""
from __future__ import annotations
import argparse
import csv
from collections import Counter
from itertools import combinations
from pathlib import Path


def cargar_instancias(path):
    instancias = []
    with Path(path).open(encoding="utf-8-sig", newline="") as archivo:
        lector = csv.DictReader(archivo)
        requeridas = {"id", "incumplidas"}
        if not lector.fieldnames or not requeridas.issubset(lector.fieldnames):
            raise ValueError(f"El CSV debe contener columnas {sorted(requeridas)}; encontradas: {lector.fieldnames}")
        for fila in lector:
            restricciones = {x.strip() for x in (fila.get("incumplidas") or "").split("|") if x.strip()}
            if not restricciones:
                raise ValueError(f"La instancia {fila.get('id')} no contiene restricciones incumplidas.")
            instancias.append((str(fila["id"]), restricciones))
    if not instancias:
        raise ValueError("La matriz no contiene instancias.")
    return instancias


def calcular_coocurrencia(instancias):
    frecuencias, pares = Counter(), Counter()
    for _, restricciones in instancias:
        frecuencias.update(restricciones)
        pares.update(combinations(sorted(restricciones), 2))
    orden = sorted(frecuencias, key=lambda x: (-frecuencias[x], x))
    matriz = {a: {b: (frecuencias[a] if a == b else pares[tuple(sorted((a, b)))]) for b in orden} for a in orden}
    filas = []
    for (a, b), n in pares.most_common():
        union = frecuencias[a] + frecuencias[b] - n
        filas.append({
            "restriccion_a": a, "restriccion_b": b, "coocurrencias": n,
            "soporte_instancias_pct": round(100*n/len(instancias), 2),
            "jaccard_pct": round(100*n/union, 2) if union else 0.0,
            "frecuencia_a": frecuencias[a], "frecuencia_b": frecuencias[b],
        })
    return frecuencias, filas, matriz


def guardar_resultados(salida, instancias, frecuencias, pares, matriz):
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    path_pares = salida / "pares_coocurrencia_G1_v2.csv"
    path_matriz = salida / "matriz_coocurrencia_G1_v2.csv"
    path_reporte = salida / "reporte_coocurrencia_G1_v2.md"
    campos = ["restriccion_a", "restriccion_b", "coocurrencias", "soporte_instancias_pct", "jaccard_pct", "frecuencia_a", "frecuencia_b"]
    with path_pares.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos); writer.writeheader(); writer.writerows(pares)
    orden = list(matriz)
    with path_matriz.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f); writer.writerow(["restriccion", *orden])
        for restriccion in orden: writer.writerow([restriccion, *(matriz[restriccion][x] for x in orden)])
    lines = [
        "# Coocurrencia de restricciones — G1 catálogo v2", "",
        f"- Instancias fallidas analizadas: {len(instancias)}",
        f"- Restricciones distintas observadas: {len(frecuencias)}",
        f"- Pares distintos con coocurrencia: {len(pares)}", "",
        "Cada par se cuenta una vez por instancia. El soporte es el porcentaje de instancias fallidas donde aparece el par. Jaccard es |A ∩ B| / |A ∪ B|. Son medidas descriptivas y no implican causalidad.", "",
        "## Pares más frecuentes", "",
        "| Restricción A | Restricción B | Instancias conjuntas | Soporte (%) | Jaccard (%) |",
        "|---|---|---:|---:|---:|",
    ]
    lines.extend(f"| `{p['restriccion_a']}` | `{p['restriccion_b']}` | {p['coocurrencias']} | {p['soporte_instancias_pct']:.2f} | {p['jaccard_pct']:.2f} |" for p in pares[:20])
    lines += ["", "## Alcance", "", "Análisis descriptivo de las respuestas fallidas de la validación visible. No demuestra causalidad, no constituye una prueba de significancia y no debe utilizarse para ajustar la configuración evaluada.", ""]
    path_reporte.write_text("\n".join(lines), encoding="utf-8")
    return path_pares, path_matriz, path_reporte


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matriz", required=True)
    parser.add_argument("--salida", required=True)
    args = parser.parse_args()
    instancias = cargar_instancias(args.matriz)
    frecuencias, pares, matriz = calcular_coocurrencia(instancias)
    archivos = guardar_resultados(args.salida, instancias, frecuencias, pares, matriz)
    print(f"Instancias analizadas: {len(instancias)}")
    print(f"Restricciones distintas: {len(frecuencias)}")
    print(f"Pares distintos: {len(pares)}")
    print("Top 10 pares:")
    for p in pares[:10]:
        print(f"  {p['coocurrencias']:3}  {p['restriccion_a']} + {p['restriccion_b']} (Jaccard {p['jaccard_pct']:.2f}%)")
    print("Archivos generados:")
    for path in archivos: print(f"  {path}")


if __name__ == "__main__":
    main()
