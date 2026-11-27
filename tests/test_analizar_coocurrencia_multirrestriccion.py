import csv
import tempfile
import unittest
from pathlib import Path

from scripts.analizar_coocurrencia_multirrestriccion import cargar_instancias, calcular_coocurrencia


class TestCoocurrenciaMultirrestriccion(unittest.TestCase):
    def test_pares_jaccard_y_matriz_simetrica(self):
        datos = [("1", {"a:x", "b:y"}), ("2", {"a:x", "b:y", "c:z"}), ("3", {"a:x", "c:z"})]
        frecuencias, pares, matriz = calcular_coocurrencia(datos)
        self.assertEqual(frecuencias["a:x"], 3)
        ab = next(p for p in pares if (p["restriccion_a"], p["restriccion_b"]) == ("a:x", "b:y"))
        self.assertEqual(ab["coocurrencias"], 2)
        self.assertEqual(ab["jaccard_pct"], 66.67)
        self.assertEqual(matriz["a:x"]["b:y"], 2)
        self.assertEqual(matriz["b:y"]["a:x"], 2)

    def test_lee_csv_del_diagnostico(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "matriz.csv"
            with ruta.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=["id", "incumplidas", "cumplidas"])
                w.writeheader(); w.writerow({"id": 10, "incumplidas": "copy:repeat | keywords:once", "cumplidas": ""})
            self.assertEqual(cargar_instancias(ruta), [("10", {"copy:repeat", "keywords:once"})])

    def test_rechaza_fila_sin_fallos(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "matriz.csv"
            with ruta.open("w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=["id", "incumplidas"])
                w.writeheader(); w.writerow({"id": 11, "incumplidas": ""})
            with self.assertRaises(ValueError): cargar_instancias(ruta)


if __name__ == "__main__":
    unittest.main()
