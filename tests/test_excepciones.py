import unittest

from excepciones import (
    AccesoDenegadoError,
    ArchivoInvalidoError,
    CupoLlenoError,
    DatoInvalidoError,
    DuplicadoError,
    ErrorAccesos,
    NoEncontradoError,
)


class TestExcepciones(unittest.TestCase):
    """Verifica la jerarquía y comportamiento de las excepciones del dominio."""

    def setUp(self):
        self.subclases = [
            DatoInvalidoError,
            DuplicadoError,
            NoEncontradoError,
            CupoLlenoError,
            AccesoDenegadoError,
            ArchivoInvalidoError,
        ]

    def tearDown(self):
        self.subclases.clear()

    def test_error_accesos_herencia_es_subclase_de_value_error(self):
        """Evalúa que ErrorAccesos herede de ValueError para compatibilidad con main.py."""
        self.assertTrue(issubclass(ErrorAccesos, ValueError))

    def test_excepciones_especificas_herencia_todas_heredan_de_error_accesos(self):
        """Evalúa que todas las excepciones específicas hereden de ErrorAccesos y ValueError."""
        for clase in self.subclases:
            with self.subTest(excepcion=clase.__name__):
                self.assertTrue(issubclass(clase, ErrorAccesos))
                self.assertTrue(issubclass(clase, ValueError))

    def test_excepciones_mensaje_personalizado_se_preserva_al_lanzar(self):
        """Evalúa que el mensaje de diagnóstico se conserve intacto al lanzar y capturar."""
        for clase in self.subclases:
            mensaje = f"Fallo controlado en {clase.__name__}"
            with self.subTest(excepcion=clase.__name__):
                with self.assertRaises(clase) as contexto:
                    raise clase(mensaje)
                self.assertEqual(str(contexto.exception), mensaje)

    def test_excepciones_sin_mensaje_permite_instanciacion(self):
        """Evalúa que las excepciones puedan lanzarse sin argumentos sin fallar."""
        for clase in self.subclases:
            with self.subTest(excepcion=clase.__name__):
                with self.assertRaises(ErrorAccesos):
                    raise clase()


if __name__ == "__main__":
    unittest.main()
