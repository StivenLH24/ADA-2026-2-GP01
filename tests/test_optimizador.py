import json
import tempfile
import unittest
from pathlib import Path

from src.optimizador import CoordinateSearch


class ResultadoFalso:
    def __init__(self, precision, n, trazas=None):
        self.precision = precision
        self.n = n
        self.trazas = trazas or []


class OraculoFalso:
    def __init__(self, objetivo, ranuras):
        self.objetivo = objetivo
        self.ranuras = ranuras
        self.llamadas = 0

    def evaluar(self, config, instancias, semilla=1, desc=""):
        self.llamadas += 1
        aciertos = sum(config[r] == self.objetivo[r] for r in self.ranuras)
        precision = aciertos / len(self.ranuras)
        n = len(instancias)
        fallos = 0 if precision == 1.0 else n
        trazas = (
            []
            if fallos == 0
            else [{"id": instancias[0]["id"], "violo": "demo", "salida": ""}]
        )
        return ResultadoFalso(precision, n, trazas)


class TestCoordinateSearch(unittest.TestCase):
    def setUp(self):
        self.catalogo = {"rol": ["r0", "r1"], "formato": ["f0", "f1"]}
        self.ranuras = ["rol", "formato"]
        self.objetivo = {"rol": 1, "formato": 1}
        self.datos = [{"id": i} for i in range(6)]
        self.oraculo = OraculoFalso(self.objetivo, self.ranuras)

    def test_busqueda_mejora_configuracion(self):
        optimizador = CoordinateSearch(
            self.oraculo, self.catalogo, self.ranuras
        )
        inicial = {"rol": 0, "formato": 0, "temperatura": 0.0}
        mejor, precision = optimizador.optimizar(
            self.datos,
            inicial,
            screen_n=3,
            finalistas=1,
            max_rondas=1,
            semilla=42,
        )
        self.assertEqual(mejor["rol"], 1)
        self.assertEqual(mejor["formato"], 1)
        self.assertEqual(precision, 1.0)

    def test_rechaza_indice_fuera_de_rango(self):
        optimizador = CoordinateSearch(
            self.oraculo, self.catalogo, self.ranuras
        )
        invalida = {"rol": 2, "formato": 0, "temperatura": 0.0}
        with self.assertRaises(ValueError):
            optimizador.validar_configuracion(invalida)

    def test_rechaza_booleano_como_indice(self):
        optimizador = CoordinateSearch(
            self.oraculo, self.catalogo, self.ranuras
        )
        invalida = {"rol": True, "formato": 0, "temperatura": 0.0}
        with self.assertRaises(TypeError):
            optimizador.validar_configuracion(invalida)

    def test_checkpoint_persistido(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "historial.json"
            optimizador = CoordinateSearch(
                self.oraculo,
                self.catalogo,
                self.ranuras,
                historial_path=ruta,
            )
            inicial = {"rol": 0, "formato": 0, "temperatura": 0.0}
            optimizador.optimizar(
                self.datos,
                inicial,
                screen_n=3,
                finalistas=1,
                max_rondas=1,
                semilla=42,
            )
            contenido = json.loads(ruta.read_text(encoding="utf-8"))
            self.assertTrue(contenido["evaluaciones"])
            self.assertEqual(
                contenido["configuracion_actual"],
                {"rol": 1, "formato": 1, "temperatura": 0.0},
            )

    def test_no_permite_temperatura_no_declarada(self):
        optimizador = CoordinateSearch(
            self.oraculo, self.catalogo, self.ranuras, temperaturas=(0.0,)
        )
        invalida = {"rol": 0, "formato": 0, "temperatura": 0.3}
        with self.assertRaises(ValueError):
            optimizador.validar_configuracion(invalida)


if __name__ == "__main__":
    unittest.main()
