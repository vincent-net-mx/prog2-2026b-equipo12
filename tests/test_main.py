from contextlib import redirect_stdout
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from excepciones import ArchivoInvalidoError, DatoInvalidoError
import main
from modelo import Becario, Investigador, Laboratorio


class TestFuncionesEntradaMain(unittest.TestCase):
    """Pruebas unitarias aisladas con mocks para los asistentes de lectura en main.py."""

    def setUp(self):
        self.prompts_esperados = []

    def tearDown(self):
        self.prompts_esperados.clear()

    @patch("builtins.input", return_value="  42  ")
    def test_pedir_entero_valido_retorna_int(self, _mock_input):
        """Evalúa conversión correcta de entero con espacios alrededor."""
        self.assertEqual(main.pedir_entero("Valor: "), 42)

    def test_pedir_entero_invalido_lanza_value_error(self):
        """Evalúa rechazo de texto no numérico, vacío y flotantes."""
        for entrada in ["abc", "", "   ", "3.5", "None"]:
            with self.subTest(entrada=repr(entrada)):
                with patch("builtins.input", return_value=entrada):
                    with self.assertRaises(ValueError) as contexto:
                        main.pedir_entero("Valor: ")
                    self.assertEqual(str(contexto.exception), "Se esperaba un número entero.")

    @patch("builtins.input", side_effect=EOFError)
    def test_pedir_entero_eof_propaga_eof_error(self, _mock_input):
        """Evalúa que EOFError no sea enmascarado por pedir_entero()."""
        with self.assertRaises(EOFError):
            main.pedir_entero("Valor: ")

    @patch("builtins.input", side_effect=["1", "123456789", "Ana Ruiz", "3", "Malware"])
    def test_pedir_persona_investigador_valido_retorna_investigador(self, _mock_input):
        """Evalúa construcción interactiva de un Investigador."""
        persona = main.pedir_persona()
        self.assertIsInstance(persona, Investigador)
        self.assertEqual(persona.codigo, "123456789")
        self.assertEqual(persona.nivel, 3)

    @patch("builtins.input", side_effect=["2", "987654321", "Luis Paz", "2", "Ciberseguridad", "4"])
    def test_pedir_persona_becario_valido_retorna_becario(self, _mock_input):
        """Evalúa construcción interactiva de un Becario."""
        persona = main.pedir_persona()
        self.assertIsInstance(persona, Becario)
        self.assertEqual(persona.codigo, "987654321")
        self.assertEqual(persona.nivel, 2)

    @patch("builtins.input", side_effect=["9", "123456789", "Ana", "2"])
    def test_pedir_persona_tipo_invalido_lanza_value_error(self, _mock_input):
        """Evalúa rechazo cuando el tipo elegido no es 1 ni 2."""
        with self.assertRaises(ValueError) as contexto:
            main.pedir_persona()
        self.assertEqual(str(contexto.exception), "El tipo debe ser 1 o 2.")

    @patch("builtins.input", side_effect=["1", "123456789", "Ana", "alto"])
    def test_pedir_persona_nivel_no_entero_lanza_value_error(self, _mock_input):
        """Evalúa manejo de nivel no entero en pedir_persona()."""
        with self.assertRaises(ValueError):
            main.pedir_persona()

    @patch("builtins.input", side_effect=["mal-01", "Lab Malware", "5", "2"])
    def test_pedir_laboratorio_valido_retorna_laboratorio(self, _mock_input):
        """Evalúa construcción interactiva de un Laboratorio."""
        lab = main.pedir_laboratorio()
        self.assertIsInstance(lab, Laboratorio)
        self.assertEqual(lab.clave, "MAL-01")

    @patch("builtins.input", side_effect=["mal-01", "Lab Malware", "cinco", "2"])
    def test_pedir_laboratorio_cupo_no_entero_lanza_value_error(self, _mock_input):
        """Evalúa error cuando el cupo introducido no es entero."""
        with self.assertRaises(ValueError):
            main.pedir_laboratorio()

    @patch("builtins.input", side_effect=["mal-01", "Lab Malware", "0", "2"])
    def test_pedir_laboratorio_cupo_cero_lanza_dato_invalido(self, _mock_input):
        """Evalúa que la validación del dominio rechace cupo 0 desde el menú."""
        with self.assertRaises(DatoInvalidoError):
            main.pedir_laboratorio()

    def test_pedir_persona_tipo_invalido_deberia_rechazarse_de_inmediato(self):
        """Evalúa que pedir_persona() rechace un tipo inválido en la primera entrada."""
        with patch("builtins.input", side_effect=["9", "123456789", "Ana", "2"]) as mock_input:
            with self.assertRaises(ValueError) as contexto:
                main.pedir_persona()
            self.assertEqual(str(contexto.exception), "El tipo debe ser 1 o 2.")
            self.assertEqual(mock_input.call_count, 1)


class TestMenuMain(unittest.TestCase):
    """Pruebas de integración aisladas para el bucle interactivo main()."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ruta_temp = os.path.join(self.temp_dir.name, "datos_main.json")
        self.patch_ruta = patch.object(main, "RUTA", self.ruta_temp)
        self.patch_ruta.start()

    def tearDown(self):
        self.patch_ruta.stop()
        self.temp_dir.cleanup()

    def _ejecutar_main(self, entradas):
        salida = io.StringIO()
        with patch("builtins.input", side_effect=entradas), redirect_stdout(salida):
            main.main()
        return salida.getvalue()

    def test_main_flujo_completo_registrar_asignar_listar_bitacora_y_salir_persiste_datos(self):
        """Evalúa happy path completo de todas las opciones del menú y persistencia final."""
        entradas = [
            "1", "1", "123456789", "Ana Ruiz", "3", "Malware",  # Registrar investigador
            "2", "MAL-01", "Lab Malware", "2", "2",             # Registrar laboratorio
            "3", "123456789", "MAL-01",                         # Asignar
            "4",                                                 # Listar
            "5",                                                 # Ver bitácora
            "6",                                                 # Salir
        ]
        salida = self._ejecutar_main(entradas)

        self.assertIn("[Investigador] 123456789 | Ana Ruiz | nivel 3 | área: Malware", salida)
        self.assertIn("[Laboratorio] MAL-01 | Lab Malware | 1/2 | nivel mínimo 2 | 123456789", salida)
        self.assertIn("Asignado 123456789 a MAL-01", salida)

        with open(self.ruta_temp, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        self.assertEqual(len(datos["personas"]), 1)
        self.assertEqual(datos["laboratorios"][0]["ocupantes"], ["123456789"])

    def test_main_opcion_invalida_muestra_mensaje_y_continua(self):
        """Evalúa tolerancia del menú ante opciones fuera de 1..6."""
        salida = self._ejecutar_main(["99", "abc", "6"])
        self.assertGreaterEqual(salida.count("Opción inválida."), 2)

    def test_main_error_de_negocio_se_muestra_sin_detener_programa(self):
        """Evalúa que errores de dominio (p. ej., asignar inexistente) no cierren el menú."""
        salida = self._ejecutar_main(["3", "000000000", "NO-LAB", "6"])
        self.assertIn("Error:", salida)

    def test_main_archivo_danado_al_iniciar_muestra_error_y_arranca_vacio(self):
        """Evalúa recuperación inicial cuando el archivo de datos está corrupto."""
        with open(self.ruta_temp, "w", encoding="utf-8") as archivo:
            archivo.write("{corrupto")

        salida = self._ejecutar_main(["6"])
        self.assertIn("Error:", salida)

    def test_main_error_al_guardar_se_captura_sin_caer(self):
        """Evalúa que un ArchivoInvalidoError al persistir una operación sea reportado sin romper el bucle."""
        with patch("sistema.SistemaAccesos.guardar", side_effect=ArchivoInvalidoError("Sin espacio")):
            salida = self._ejecutar_main(["2", "MAL-01", "Lab Malware", "2", "2", "6"])
        self.assertIn("Error: Sin espacio", salida)

    def test_main_eof_termina_limpiamente(self):
        """Evalúa salida limpia cuando stdin alcanza EOF."""
        salida = self._ejecutar_main([EOFError()])
        self.assertIn("1. Registrar persona", salida)

    def test_main_keyboard_interrupt_termina_limpiamente(self):
        """Evalúa salida limpia cuando el usuario presiona Ctrl+C."""
        salida = self._ejecutar_main([KeyboardInterrupt()])
        self.assertIn("1. Registrar persona", salida)

    def test_main_opcion_solo_lectura_no_deberia_sobrescribir_archivo_danado(self):
        """Evalúa que listar (4) u opciones inválidas no sobrescriban un datos.json dañado."""
        contenido_original = "{corrupto_pendiente_de_rescate"
        with open(self.ruta_temp, "w", encoding="utf-8") as archivo:
            archivo.write(contenido_original)

        self._ejecutar_main(["4", "99", "6"])

        with open(self.ruta_temp, encoding="utf-8") as archivo:
            self.assertEqual(archivo.read(), contenido_original)


if __name__ == "__main__":
    unittest.main()
