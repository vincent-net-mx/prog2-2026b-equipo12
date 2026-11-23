from contextlib import redirect_stdout
import io
import unittest
from unittest.mock import patch

from excepciones import (
    AccesoDenegadoError,
    CupoLlenoError,
    DatoInvalidoError,
    DuplicadoError,
    NoEncontradoError,
)
from modelo import Becario, Investigador, Laboratorio, Persona
from sistema import SistemaAccesos


class TestSistemaAccesos(unittest.TestCase):
    """Pruebas unitarias de lógica de negocio, estado y bitácora en SistemaAccesos."""

    def setUp(self):
        self.sistema = SistemaAccesos()
        self.inv = Investigador("123456789", "Ana Ruiz", 3, "Malware")
        self.bec = Becario("987654321", "Luis Paz", 1, "Ciberseguridad", 3)
        self.bec_nivel2 = Becario("555555555", "Sofía Gil", 2, "Sistemas", 6)
        self.lab = Laboratorio("MAL-01", "Lab Malware", 1, 2)

    def tearDown(self):
        self.sistema.vaciar()
        self.sistema = None

    def _capturar_bitacora(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            self.sistema.ver_bitacora()
        return salida.getvalue()

    def test_registrar_investigador_becario_y_laboratorio_exito_y_registra_bitacora(self):
        """Evalúa el happy path de registro y su reflejo en propiedades y bitácora."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.bec)
        self.sistema.registrar(self.lab)

        self.assertEqual(len(self.sistema.personas), 2)
        self.assertEqual(len(self.sistema.laboratorios), 1)

        log = self._capturar_bitacora()
        self.assertIn("Registrado [Investigador] 123456789", log)
        self.assertIn("Registrado [Becario] 987654321", log)
        self.assertIn("Agregado [Laboratorio] MAL-01", log)

    def test_registrar_duplicado_persona_lanza_duplicado_error(self):
        """Evalúa que registrar un código de persona ya existente lance DuplicadoError."""
        self.sistema.registrar(self.inv)
        duplicado = Becario("123456789", "Otro Nombre", 2, "Redes", 2)
        with self.assertRaises(DuplicadoError):
            self.sistema.registrar(duplicado)
        self.assertEqual(len(self.sistema.personas), 1)

    def test_registrar_duplicado_laboratorio_case_insensitive_lanza_duplicado_error(self):
        """Evalúa que claves equivalentes en minúsculas/mayúsculas se rechacen como duplicadas."""
        self.sistema.registrar(self.lab)
        duplicado = Laboratorio("mal-01", "Otro Lab", 5, 1)
        with self.assertRaises(DuplicadoError):
            self.sistema.registrar(duplicado)
        self.assertEqual(len(self.sistema.laboratorios), 1)

    def test_registrar_objetos_invalidos_lanza_dato_invalido(self):
        """Evalúa rechazo de tipos ajenos al dominio (None, str, int, dict, list, object)."""
        for objeto in [None, "persona", 123456789, {}, [], object()]:
            with self.subTest(objeto=repr(objeto)):
                with self.assertRaises(DatoInvalidoError):
                    self.sistema.registrar(objeto)

    def test_propiedades_personas_y_laboratorios_retornan_copia_de_lista(self):
        """Evalúa que mutar las listas devueltas por las propiedades no altere el estado interno."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.lab)

        self.sistema.personas.clear()
        self.sistema.laboratorios.clear()

        self.assertEqual(len(self.sistema.personas), 1)
        self.assertEqual(len(self.sistema.laboratorios), 1)

    def test_propiedades_personas_y_laboratorios_solo_lectura_lanza_attribute_error(self):
        """Evalúa que las colecciones expuestas no admitan reasignación directa."""
        with self.assertRaises(AttributeError):
            self.sistema.personas = []
        with self.assertRaises(AttributeError):
            self.sistema.laboratorios = []

    def test_asignar_valido_con_espacios_y_minusculas_exito_y_registra_bitacora(self):
        """Evalúa normalización de identificador y clave al asignar correctamente."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.lab)

        self.sistema.asignar(" 123456789 ", " mal-01 ")

        self.assertTrue(self.lab.esta_lleno())
        self.assertIn("Asignado 123456789 a MAL-01", self._capturar_bitacora())

    def test_asignar_persona_inexistente_lanza_no_encontrado_error(self):
        """Evalúa rechazo al asignar un código de persona no registrado."""
        self.sistema.registrar(self.lab)
        with self.assertRaises(NoEncontradoError):
            self.sistema.asignar("000000000", "MAL-01")

    def test_asignar_laboratorio_inexistente_lanza_no_encontrado_error(self):
        """Evalúa rechazo al asignar a una clave de laboratorio inexistente."""
        self.sistema.registrar(self.inv)
        with self.assertRaises(NoEncontradoError):
            self.sistema.asignar("123456789", "NO-EXISTE")

    def test_asignar_identificador_o_clave_none_o_vacio_lanza_no_encontrado_error(self):
        """Evalúa comportamiento ante argumentos None o cadenas vacías en asignar()."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.lab)
        for identificador, clave in [(None, "MAL-01"), ("", "MAL-01"), ("123456789", None), ("123456789", "")]:
            with self.subTest(identificador=identificador, clave=clave):
                with self.assertRaises(NoEncontradoError):
                    self.sistema.asignar(identificador, clave)

    def test_asignar_nivel_insuficiente_lanza_acceso_denegado_y_registra_rechazo(self):
        """Evalúa que el rechazo por nivel lance AccesoDenegadoError y deje traza en bitácora."""
        self.sistema.registrar(self.bec)
        self.sistema.registrar(self.lab)

        with self.assertRaises(AccesoDenegadoError):
            self.sistema.asignar(self.bec.codigo, self.lab.clave)

        log = self._capturar_bitacora()
        self.assertIn("Rechazado 987654321 en MAL-01", log)

    def test_asignar_laboratorio_lleno_lanza_cupo_lleno_y_registra_rechazo(self):
        """Evalúa que el rechazo por cupo lleno lance CupoLlenoError y se audite en bitácora."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.bec_nivel2)
        self.sistema.registrar(self.lab)
        self.sistema.asignar(self.inv.codigo, self.lab.clave)

        with self.assertRaises(CupoLlenoError):
            self.sistema.asignar(self.bec_nivel2.codigo, self.lab.clave)

        log = self._capturar_bitacora()
        self.assertIn("Rechazado 555555555 en MAL-01", log)

    def test_asignar_persona_duplicada_lanza_duplicado_y_registra_rechazo(self):
        """Evalúa que asignar dos veces a la misma persona lance DuplicadoError y quede en bitácora."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.lab)
        self.sistema.asignar(self.inv.codigo, self.lab.clave)

        with self.assertRaises(DuplicadoError):
            self.sistema.asignar(self.inv.codigo, self.lab.clave)

        log = self._capturar_bitacora()
        self.assertIn("Rechazado 123456789 en MAL-01", log)

    def test_listar_sistema_vacio_imprime_sin_registros(self):
        """Evalúa salida de listar() cuando no existen personas ni laboratorios."""
        salida = io.StringIO()
        with redirect_stdout(salida):
            self.sistema.listar()
        self.assertEqual(salida.getvalue(), "No hay registros.\n")

    def test_listar_con_registros_imprime_personas_y_laboratorios(self):
        """Evalúa que listar() muestre todas las personas y laboratorios registrados."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.lab)

        salida = io.StringIO()
        with redirect_stdout(salida):
            self.sistema.listar()

        texto = salida.getvalue()
        self.assertIn(self.inv.describir(), texto)
        self.assertIn(self.lab.describir(), texto)

    def test_vaciar_elimina_personas_y_laboratorios(self):
        """Evalúa que vaciar() borre las colecciones de personas y laboratorios."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.lab)
        self.sistema.vaciar()

        self.assertEqual(self.sistema.personas, [])
        self.assertEqual(self.sistema.laboratorios, [])

    @patch("sistema.persistencia.guardar")
    @patch("sistema.persistencia.cargar")
    def test_guardar_y_cargar_estaticos_delegan_en_persistencia(self, mock_cargar, mock_guardar):
        """Evalúa que los métodos estáticos guardar() y cargar() deleguen en persistencia sin I/O real."""
        SistemaAccesos.guardar(self.sistema, "fake.json")
        SistemaAccesos.cargar(self.sistema, "fake.json")

        mock_guardar.assert_called_once_with(self.sistema, "fake.json")
        mock_cargar.assert_called_once_with(self.sistema, "fake.json")

    def test_registrar_persona_base_deberia_rechazarse_segun_contrato(self):
        """Evalúa que registrar() solo acepte Investigador, Becario o Laboratorio."""
        persona_base = Persona("111222333", "Genérico", 1)
        with self.assertRaises(DatoInvalidoError):
            self.sistema.registrar(persona_base)

    def test_registrar_laboratorio_con_ocupantes_no_registrados_deberia_rechazarse(self):
        """Evalúa que registrar un laboratorio con ocupantes previos sea rechazado."""
        lab_sucio = Laboratorio("EXT-01", "Lab Externo", 2, 1)
        lab_sucio.admitir(self.inv)  # self.inv NO está registrado en self.sistema
        with self.assertRaises(DatoInvalidoError):
            self.sistema.registrar(lab_sucio)

    def test_vaciar_deberia_limpiar_tambien_la_bitacora(self):
        """Evalúa que vaciar() borre personas, laboratorios y también la bitácora."""
        self.sistema.registrar(self.inv)
        self.sistema.vaciar()
        self.assertEqual(self._capturar_bitacora(), "")


if __name__ == "__main__":
    unittest.main()
