import unittest

from src.busqueda_pares_guiada import _aciertos, _crear_pares, _jaccard


class TestBusquedaParesGuiada(unittest.TestCase):
    def test_aciertos_se_obtienen_resta_trazas(self):
        registro = {
            "ids_instancias": [1, 2, 3],
            "trazas": [{"id": 2, "violo": "familia_a"}],
        }
        self.assertEqual(_aciertos(registro), {"1", "3"})

    def test_jaccard_conjuntos_disjuntos(self):
        self.assertEqual(_jaccard({"a"}, {"b"}), 0.0)

    def test_prioriza_pares_con_aciertos_complementarios(self):
        config_base = {
            "rol": 0,
            "estrategia": 0,
            "formato": 0,
            "estilo": 0,
            "cierre": 0,
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
