import unittest

from scripts.analizar_fallos_multirestriccion import analizar, verificar_independientemente


class VerificadorFalso:
    def __init__(self, iid):
        self.iid = iid

    def build_description(self, **kwargs):
        pass

    def get_instruction_args(self):
        return {}

    def check_following(self, respuesta):
        return self.iid in respuesta


class TestAnalisisMultirrestriccion(unittest.TestCase):
    def setUp(self):
        self.instancia = {
            "id": 101,
            "prompt": "prompt de prueba",
            "ids": ["copy:repeat", "keywords:word_once", "punctuation:dot"],
            "kwargs": [{}, {}, {}],
        }
        self.registros = [{iid: VerificadorFalso for iid in self.instancia["ids"]}]

    def test_ejecuta_todos_los_verificadores(self):
        checks = verificar_independientemente(
            self.instancia, "copy:repeat", self.registros
        )
        self.assertEqual([x["cumple"] for x in checks], [True, False, False])

    def test_detecta_fallos_simultaneos_y_conserva_primera_falla(self):
        filas = [{
            "instancia": self.instancia,
            "salida": "copy:repeat",
            "primera_falla_cache": "keywords:word_once",
        }]
        detalle, restricciones, familias, multiples = analizar(filas, self.registros)
        self.assertEqual(multiples, 1)
        self.assertEqual(detalle[0]["restricciones_incumplidas"], 2)
        self.assertEqual(restricciones["keywords:word_once"], 1)
        self.assertEqual(restricciones["punctuation:dot"], 1)
        self.assertEqual(familias["keywords"], 1)
        self.assertEqual(familias["punctuation"], 1)

    def test_falla_si_no_reproduce_la_primera_falla_cacheada(self):
        filas = [{
            "instancia": self.instancia,
            "salida": "copy:repeat",
            "primera_falla_cache": "punctuation:dot",
        }]
        with self.assertRaises(AssertionError):
            analizar(filas, self.registros)


if __name__ == "__main__":
    unittest.main()
