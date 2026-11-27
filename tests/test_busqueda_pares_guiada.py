import json
import tempfile
import unittest
from pathlib import Path

from src.busqueda_pares_guiada import (
    _aciertos, _cargar_historial_coordenadas, _crear_pares, _familias, _jaccard,
)


class TestBusquedaParesGuiada(unittest.TestCase):
    def test_aciertos_se_obtienen_resta_trazas(self):
        registro = {
            "ids_instancias": [1, 2, 3],
            "trazas": [{"id": 2, "violo": "familia_a"}],
        }
        self.assertEqual(_aciertos(registro), {"1", "3"})

    def test_jaccard_conjuntos_disjuntos(self):
        self.assertEqual(_jaccard({"a"}, {"b"}), 0.0)

    def test_familias_normaliza_identificadores_de_restriccion(self):
        registro = {
            "trazas": [
                {"violo": "keywords:no_adjacent_consecutive"},
                {"violo": "keywords:word_once"},
                {"violo": "punctuation:punctuation_dot"},
            ]
        }
        self.assertEqual(_familias(registro), {"keywords", "punctuation"})


    def test_usa_configuracion_final_si_mejoro_el_baseline(self):
        config_inicial = {
            "rol": 0, "estrategia": 0, "formato": 0,
            "verificacion": 0, "recordatorio": 0, "temperatura": 0.0,
        }
        config_final = {**config_inicial, "rol": 1}
        ids = [10, 20, 30, 40]
        historial = {
            "configuracion_actual": config_final,
            "precision_actual": 0.5,
            "evaluaciones": [
                {
                    "etapa": "baseline",
                    "configuracion": config_inicial,
                    "precision": 0.25,
                    "instancias": 4,
                    "ids_instancias": ids,
                    "semilla": 2026,
                    "trazas": [
                        {"id": 20, "violo": "familia_a"},
                        {"id": 30, "violo": "familia_b"},
                        {"id": 40, "violo": "familia_b"},
                    ],
                },
                {
                    "etapa": "refinamiento",
                    "ranura": "rol",
                    "configuracion": config_final,
                    "precision": 0.5,
                    "instancias": 4,
                    "ids_instancias": ids,
                    "semilla": 2026,
                    "trazas": [
                        {"id": 30, "violo": "familia_c"},
                        {"id": 40, "violo": "familia_c"},
                    ],
                },
                {
                    "etapa": "refinamiento",
                    "ranura": "rol",
                    "configuracion": {**config_final, "rol": 2},
                    "precision": 0.5,
                    "instancias": 4,
                    "ids_instancias": ids,
                    "semilla": 2026,
                    "trazas": [
                        {"id": 20, "violo": "familia_d"},
                        {"id": 40, "violo": "familia_d"},
                    ],
                },
                {
                    "etapa": "refinamiento",
                    "ranura": "estrategia",
                    "configuracion": {**config_final, "estrategia": 1},
                    "precision": 0.5,
                    "instancias": 4,
                    "ids_instancias": ids,
                    "semilla": 2026,
                    "trazas": [
                        {"id": 20, "violo": "familia_e"},
                        {"id": 30, "violo": "familia_e"},
                    ],
                },
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "historial.json"
            path.write_text(json.dumps(historial), encoding="utf-8")
            config, referencia, candidatos = _cargar_historial_coordenadas(path)

        self.assertEqual(config, config_final)
        self.assertEqual(referencia["precision"], 0.5)
        self.assertEqual(_aciertos(referencia), {"10", "20"})
        self.assertEqual({c["ranura"] for c in candidatos}, {"rol", "estrategia"})
        self.assertEqual(len(candidatos), 2)

    def test_prioriza_pares_con_aciertos_complementarios(self):
        config_base = {
            "rol": 0,
            "estrategia": 0,
            "formato": 0,
            "verificacion": 0,
            "recordatorio": 0,
            "temperatura": 0.0,
        }
        ids = [1, 2, 3, 4]
        baseline = {
            "ids_instancias": ids,
            "trazas": [
                {"id": 2, "violo": "base_a"},
                {"id": 3, "violo": "base_b"},
                {"id": 4, "violo": "base_b"},
            ],
        }
        candidatos = [
            {
                "ranura": "rol",
                "indice": 1,
                "configuracion": {**config_base, "rol": 1},
                "aciertos": {"1", "3"},
                "familias": {"familia_rol"},
                "precision": 0.5,
            },
            {
                "ranura": "estrategia",
                "indice": 1,
                "configuracion": {**config_base, "estrategia": 1},
                "aciertos": {"1", "2"},
                "familias": {"familia_estrategia"},
                "precision": 0.5,
            },
        ]
        pares = _crear_pares(config_base, baseline, candidatos, top_pares=2)
        self.assertEqual(len(pares), 1)
        self.assertEqual(pares[0]["configuracion"]["rol"], 1)
        self.assertEqual(pares[0]["configuracion"]["estrategia"], 1)
        self.assertEqual(pares[0]["aciertos_potenciales_union"], 3)


if __name__ == "__main__":
    unittest.main()
