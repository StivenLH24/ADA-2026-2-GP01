import importlib
import sys
import types
import unittest


def _cargar_oraculo_sin_dependencias_de_modelo():
    # oraculo solo necesita estos módulos durante la importación; las pruebas
    # no cargan pesos ni ejecutan generación.
    registry = types.ModuleType("open_instruct.IFEvalG.instructions_registry")
    registry.INSTRUCTION_DICT = {}
    ifeval = types.ModuleType("open_instruct.IFEvalG")
    ifeval.instructions_registry = registry
    package = types.ModuleType("open_instruct")
    package.__path__ = []
    sys.modules.setdefault("open_instruct", package)
    sys.modules.setdefault("open_instruct.IFEvalG", ifeval)
    sys.modules.setdefault("open_instruct.IFEvalG.instructions_registry", registry)
    return importlib.import_module("oraculo")


oraculo = _cargar_oraculo_sin_dependencias_de_modelo()


class TestCatalogoG1V2(unittest.TestCase):
    def test_cinco_categorias_oficiales_y_ocho_opciones(self):
        self.assertEqual(
            oraculo.RANURAS,
            ["rol", "estrategia", "formato", "verificacion", "recordatorio"],
        )
        self.assertTrue(all(len(oraculo.CATALOGO[r]) == 8 for r in oraculo.RANURAS))

    def test_espacio_de_busqueda_conserva_tamano(self):
        self.assertEqual(len(oraculo.espacio((0.0,))), 32768)

    def test_prompt_incluye_verificacion_antes_y_recordatorio_despues(self):
        config = {
            "rol": 0,
            "estrategia": 0,
            "formato": 0,
            "verificacion": 4,
            "recordatorio": 4,
            "temperatura": 0.0,
        }
        instancia = {"prompt": "PETICION_DE_PRUEBA", "restriccion": "REGLA_A\tREGLA_B"}
        prompt = oraculo.armar(config, instancia)
        self.assertLess(prompt.index(oraculo.CATALOGO["verificacion"][4]), prompt.index("PETICION_DE_PRUEBA"))
        self.assertGreater(prompt.index("These are the requirements"), prompt.index("PETICION_DE_PRUEBA"))
        self.assertIn("REGLA_A", prompt)
        self.assertIn("REGLA_B", prompt)

    def test_rechaza_configuracion_de_catalogo_anterior(self):
        antigua = {
            "rol": 0, "estrategia": 0, "formato": 0,
            "estilo": 0, "cierre": 0, "temperatura": 0.0,
        }
        with self.assertRaises(ValueError):
            oraculo.armar(antigua, {"prompt": "test", "restriccion": ""})


if __name__ == "__main__":
    unittest.main()
