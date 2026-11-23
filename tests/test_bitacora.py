from contextlib import redirect_stdout
from datetime import datetime
import io
import unittest
from unittest.mock import patch

from bitacora import Bitacora
from excepciones import DatoInvalidoError


class TestBitacora(unittest.TestCase):
    """Pruebas unitarias, de formato y de seguridad (log injection) para Bitacora."""

    def setUp(self):
        self.bitacora = Bitacora()

    def tearDown(self):
        self.bitacora = None

    @patch("bitacora.datetime")
    def test_agregar_evento_valido_incluye_timestamp_y_mensaje(self, mock_datetime):
        """Evalúa que agregar() registre la marca de tiempo formateada junto al mensaje."""
        mock_datetime.now.return_value = datetime(2026, 5, 10, 14, 30, 5)
        self.bitacora.agregar("Asignado 123456789 a MAL-01")

        salida = io.StringIO()
        with redirect_stdout(salida):
            self.bitacora.listar()

        self.assertEqual(
            salida.getvalue(),
            "[2026-05-10 14:30:05] Asignado 123456789 a MAL-01\n",
        )

    @patch("bitacora.datetime")
    def test_listar_multiples_eventos_preserva_orden_cronologico(self, mock_datetime):
        """Evalúa que listar() imprima los eventos estrictamente en orden FIFO."""
        mock_datetime.now.side_effect = [
            datetime(2026, 5, 10, 10, 0, 0),
            datetime(2026, 5, 10, 10, 0, 1),
            datetime(2026, 5, 10, 10, 0, 2),
        ]
        self.bitacora.agregar("Evento 1")
        self.bitacora.agregar("Evento 2")
        self.bitacora.agregar("Evento 3")

        salida = io.StringIO()
        with redirect_stdout(salida):
            self.bitacora.listar()

        lineas = salida.getvalue().splitlines()
        self.assertEqual(
            lineas,
            [
                "[2026-05-10 10:00:00] Evento 1",
                "[2026-05-10 10:00:01] Evento 2",
                "[2026-05-10 10:00:02] Evento 3",
            ],
        )

    def test_listar_bitacora_vacia_no_imprime_salida(self):
        """Evalúa el caso límite de listar una bitácora sin eventos."""
        salida = io.StringIO()
        with redirect_stdout(salida):
            self.bitacora.listar()
        self.assertEqual(salida.getvalue(), "")

    @patch("bitacora.datetime")
    def test_agregar_caracteres_especiales_y_unicode_conserva_texto(self, mock_datetime):
        """Evalúa manejo seguro de tildes, ñ y caracteres especiales en la bitácora."""
        mock_datetime.now.return_value = datetime(2026, 5, 10, 12, 0, 0)
        mensaje = "Registrado José Núñez — Lab #1 (100%)"
        self.bitacora.agregar(mensaje)

        salida = io.StringIO()
        with redirect_stdout(salida):
            self.bitacora.listar()

        self.assertEqual(salida.getvalue(), f"[2026-05-10 12:00:00] {mensaje}\n")

    def test_agregar_mensaje_none_o_vacio_deberia_lanzar_dato_invalido(self):
        """Evalúa que Bitacora.agregar() rechace None o cadenas vacías con DatoInvalidoError."""
        with self.assertRaises(DatoInvalidoError):
            self.bitacora.agregar(None)
        with self.assertRaises(DatoInvalidoError):
            self.bitacora.agregar("   ")

    @patch("bitacora.datetime")
    def test_agregar_mensaje_con_salto_de_linea_deberia_evitar_inyeccion_log(self, mock_datetime):
        """Evalúa mitigación de CWE-117: saltos de línea se neutralizan en una única entrada."""
        mock_datetime.now.return_value = datetime(2026, 5, 10, 12, 0, 0)
        self.bitacora.agregar("Acceso normal\n[2026-05-10 12:00:01] Asignado 999999999 a ADMIN")

        salida = io.StringIO()
        with redirect_stdout(salida):
            self.bitacora.listar()

        # Un único evento registrado no debería producir dos líneas en la bitácora.
        self.assertEqual(len(salida.getvalue().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
