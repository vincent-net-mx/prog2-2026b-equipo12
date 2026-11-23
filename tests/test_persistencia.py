from contextlib import redirect_stdout
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from excepciones import ArchivoInvalidoError
from modelo import Becario, Investigador, Laboratorio
import persistencia
from sistema import SistemaAccesos


class TestPersistenciaGuardar(unittest.TestCase):
    """Pruebas unitarias y de fallos de entorno para persistencia.guardar()."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.temp_dir.name, "datos_test.json")
        self.sistema = SistemaAccesos()
        self.inv = Investigador("123456789", "Ana Núñez", 3, "Análisis de malware")
        self.bec = Becario("098765432", "Luis Paz", 2, "Ciberseguridad", 4)
        self.lab = Laboratorio("MAL-01", "Lab Malware", 3, 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_guardar_sistema_con_datos_y_unicode_escribe_json_valido(self):
        """Evalúa serialización UTF-8 correcta con acentos, ceros iniciales y ocupantes."""
        self.sistema.registrar(self.inv)
        self.sistema.registrar(self.bec)
        self.sistema.registrar(self.lab)
        self.sistema.asignar(self.bec.codigo, self.lab.clave)

        persistencia.guardar(self.sistema, self.ruta)

        with open(self.ruta, encoding="utf-8") as archivo:
            contenido = json.load(archivo)

        self.assertEqual(len(contenido["personas"]), 2)
        self.assertEqual(contenido["personas"][0]["nombre"], "Ana Núñez")
        self.assertEqual(contenido["personas"][1]["codigo"], "098765432")
        self.assertEqual(contenido["laboratorios"][0]["ocupantes"], ["098765432"])

    def test_guardar_sistema_vacio_escribe_listas_vacias(self):
        """Evalúa el caso límite de guardar un sistema sin registros."""
        persistencia.guardar(self.sistema, self.ruta)
        with open(self.ruta, encoding="utf-8") as archivo:
            self.assertEqual(json.load(archivo), {"personas": [], "laboratorios": []})

    def test_guardar_ruta_directorio_existente_lanza_archivo_invalido(self):
        """Evalúa que intentar escribir sobre un directorio lance ArchivoInvalidoError."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(self.sistema, self.temp_dir.name)

    def test_guardar_directorio_padre_inexistente_lanza_archivo_invalido(self):
        """Evalúa fallo cuando la ruta apunta a un directorio inexistente."""
        ruta_invalida = os.path.join(self.temp_dir.name, "no_existe", "datos.json")
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(self.sistema, ruta_invalida)

    def test_guardar_ruta_none_lanza_archivo_invalido(self):
        """Evalúa manejo de TypeError cuando la ruta es None."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(self.sistema, None)

    @patch("builtins.open", side_effect=PermissionError("Permiso denegado"))
    def test_guardar_error_permisos_simulado_lanza_archivo_invalido(self, _mock_open):
        """Evalúa aislamiento ante PermissionError del sistema de archivos."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(self.sistema, self.ruta)

    @patch("persistencia.json.dump", side_effect=TypeError("Objeto no serializable"))
    def test_guardar_dato_no_serializable_simulado_lanza_archivo_invalido(self, _mock_dump):
        """Evalúa conversión de TypeError durante json.dump en ArchivoInvalidoError."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(self.sistema, self.ruta)

    def test_guardar_sistema_none_deberia_lanzar_archivo_invalido(self):
        """Evalúa que guardar(None, ruta) convierta el error en ArchivoInvalidoError."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(None, self.ruta)

    def test_guardar_ruta_con_byte_nulo_deberia_lanzar_archivo_invalido(self):
        """Evalúa que una ruta con byte nulo lance ArchivoInvalidoError."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.guardar(self.sistema, os.path.join(self.temp_dir.name, "bad\x00.json"))

    def test_guardar_fallo_en_escritura_no_deberia_destruir_archivo_previo(self):
        """Evalúa escritura atómica: un fallo de json.dump preserva intacto el archivo anterior."""
        self.sistema.registrar(self.inv)
        persistencia.guardar(self.sistema, self.ruta)
        with open(self.ruta, encoding="utf-8") as archivo:
            contenido_previo = archivo.read()

        with patch("persistencia.json.dump", side_effect=OSError("Disco lleno")):
            with self.assertRaises(ArchivoInvalidoError):
                persistencia.guardar(self.sistema, self.ruta)

        with open(self.ruta, encoding="utf-8") as archivo:
            self.assertEqual(archivo.read(), contenido_previo)


class TestPersistenciaCargar(unittest.TestCase):
    """Pruebas unitarias, de archivos corruptos y casos límite para persistencia.cargar()."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.ruta = os.path.join(self.temp_dir.name, "datos_test.json")
        self.sistema = SistemaAccesos()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _escribir_texto(self, contenido):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            archivo.write(contenido)

    def _escribir_json(self, datos):
        with open(self.ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False)

    def test_cargar_roundtrip_completo_reconstruye_personas_labs_y_ocupantes(self):
        """Evalúa ciclo completo guardar -> cargar con investigadores, becarios y ocupantes."""
        origen = SistemaAccesos()
        origen.registrar(Investigador("123456789", "Ana Ruiz", 3, "Malware"))
        origen.registrar(Becario("098765432", "Luis Paz", 2, "Ciberseguridad", 3))
        origen.registrar(Laboratorio("MAL-01", "Lab Malware", 2, 2))
        origen.asignar("123456789", "MAL-01")
        origen.asignar("098765432", "MAL-01")
        persistencia.guardar(origen, self.ruta)

        persistencia.cargar(self.sistema, self.ruta)

        self.assertEqual(len(self.sistema.personas), 2)
        self.assertEqual(len(self.sistema.laboratorios), 1)
        self.assertTrue(self.sistema.laboratorios[0].esta_lleno())
        self.assertEqual(
            self.sistema.laboratorios[0].a_diccionario()["ocupantes"],
            ["123456789", "098765432"],
        )

    def test_cargar_archivo_inexistente_deja_sistema_vacio_sin_error(self):
        """Evalúa que cargar una ruta inexistente limpie el sistema sin lanzar excepción."""
        self.sistema.registrar(Investigador("123456789", "Ana", 3, "Malware"))
        ruta_inexistente = os.path.join(self.temp_dir.name, "no_existe.json")

        persistencia.cargar(self.sistema, ruta_inexistente)

        self.assertEqual(self.sistema.personas, [])
        self.assertEqual(self.sistema.laboratorios, [])

    def test_cargar_json_corrupto_vacia_sistema_y_lanza_archivo_invalido(self):
        """Evalúa manejo de JSON con sintaxis truncada o malformada."""
        self._escribir_texto('{"personas": [')
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.ruta)
        self.assertEqual(self.sistema.personas, [])

    def test_cargar_archivo_vacio_vacia_sistema_y_lanza_archivo_invalido(self):
        """Evalúa rechazo de archivo vacío de 0 bytes."""
        self._escribir_texto("")
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_bytes_utf8_invalidos_vacia_sistema_y_lanza_archivo_invalido(self):
        """Evalúa rechazo de archivo binario o con codificación UTF-8 corrupta."""
        with open(self.ruta, "wb") as archivo:
            archivo.write(b"\xff\xfe\x00\x80")
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_json_raiz_no_objeto_lanza_archivo_invalido(self):
        """Evalúa rechazo cuando la raíz del JSON es lista, nulo, texto o número."""
        for raiz in [[], None, "texto", 123, True]:
            with self.subTest(raiz=repr(raiz)):
                self._escribir_json(raiz)
                with self.assertRaises(ArchivoInvalidoError):
                    persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_claves_faltantes_en_raiz_lanza_archivo_invalido(self):
        """Evalúa rechazo cuando faltan las claves obligatorias 'personas' o 'laboratorios'."""
        for estructura in [{}, {"personas": []}, {"laboratorios": []}]:
            with self.subTest(estructura=estructura):
                self._escribir_json(estructura)
                with self.assertRaises(ArchivoInvalidoError):
                    persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_tipo_persona_desconocido_o_faltante_lanza_archivo_invalido(self):
        """Evalúa rechazo ante tipos inyectados, desconocidos o ausentes en personas."""
        casos = [
            {"codigo": "123456789", "nombre": "Ana", "nivel": 3},
            {"tipo": "Admin", "codigo": "123456789", "nombre": "Ana", "nivel": 3},
            {"tipo": "__class__", "codigo": "123456789", "nombre": "Ana", "nivel": 3},
            "no-es-diccionario",
        ]
        for entrada in casos:
            with self.subTest(entrada=entrada):
                self._escribir_json({"personas": [entrada], "laboratorios": []})
                with self.assertRaises(ArchivoInvalidoError):
                    persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_campos_extra_o_faltantes_en_persona_lanza_archivo_invalido(self):
        """Evalúa rechazo ante campos faltantes o inesperados en los registros JSON."""
        casos = [
            {"tipo": "Investigador", "codigo": "123456789", "nombre": "Ana", "nivel": 3},
            {
                "tipo": "Investigador",
                "codigo": "123456789",
                "nombre": "Ana",
                "nivel": 3,
                "area": "Malware",
                "extra": "inyectado",
            },
        ]
        for entrada in casos:
            with self.subTest(entrada=entrada):
                self._escribir_json({"personas": [entrada], "laboratorios": []})
                with self.assertRaises(ArchivoInvalidoError):
                    persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_inconsistencias_de_negocio_en_json_lanza_archivo_invalido(self):
        """Evalúa rechazo ante JSON con duplicados, niveles inválidos, cupo excedido u ocupantes inexistentes."""
        persona_n1 = {
            "tipo": "Becario",
            "codigo": "111111111",
            "nombre": "Luis",
            "nivel": 1,
            "carrera": "Sistemas",
            "semestre": 2,
        }
        persona_n3 = {
            "tipo": "Investigador",
            "codigo": "222222222",
            "nombre": "Ana",
            "nivel": 3,
            "area": "Malware",
        }
        casos = {
            "persona_duplicada": {"personas": [persona_n3, dict(persona_n3)], "laboratorios": []},
            "nivel_fuera_de_rango": {
                "personas": [{**persona_n3, "nivel": 9}],
                "laboratorios": [],
            },
            "ocupante_inexistente": {
                "personas": [],
                "laboratorios": [
                    {"clave": "L1", "nombre": "Lab", "cupo": 2, "nivel_minimo": 1, "ocupantes": ["999999999"]}
                ],
            },
            "ocupante_sin_nivel": {
                "personas": [persona_n1],
                "laboratorios": [
                    {"clave": "L1", "nombre": "Lab", "cupo": 2, "nivel_minimo": 3, "ocupantes": ["111111111"]}
                ],
            },
            "cupo_excedido": {
                "personas": [persona_n1, persona_n3],
                "laboratorios": [
                    {
                        "clave": "L1",
                        "nombre": "Lab",
                        "cupo": 1,
                        "nivel_minimo": 1,
                        "ocupantes": ["111111111", "222222222"],
                    }
                ],
            },
            "ocupante_duplicado": {
                "personas": [persona_n3],
                "laboratorios": [
                    {
                        "clave": "L1",
                        "nombre": "Lab",
                        "cupo": 2,
                        "nivel_minimo": 1,
                        "ocupantes": ["222222222", "222222222"],
                    }
                ],
            },
        }
        for nombre_caso, datos in casos.items():
            with self.subTest(caso=nombre_caso):
                self._escribir_json(datos)
                with self.assertRaises(ArchivoInvalidoError):
                    persistencia.cargar(self.sistema, self.ruta)
                self.assertEqual(self.sistema.personas, [])
                self.assertEqual(self.sistema.laboratorios, [])

    def test_cargar_ruta_directorio_o_permiso_denegado_lanza_archivo_invalido(self):
        """Evalúa manejo de IsADirectoryError y PermissionError al leer."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.temp_dir.name)

        with patch("builtins.open", side_effect=PermissionError("Sin permisos de lectura")):
            with self.assertRaises(ArchivoInvalidoError):
                persistencia.cargar(self.sistema, self.ruta)

    def test_cargar_fallo_parcial_revierte_personas_y_laboratorios(self):
        """Evalúa rollback de colecciones si el segundo registro del JSON es inválido."""
        self._escribir_json(
            {
                "personas": [
                    {"tipo": "Investigador", "codigo": "123456789", "nombre": "Ana", "nivel": 3, "area": "Malware"},
                    {"tipo": "Investigador", "codigo": "MALO", "nombre": "Roto", "nivel": 3, "area": "Malware"},
                ],
                "laboratorios": [],
            }
        )
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.ruta)
        self.assertEqual(self.sistema.personas, [])
        self.assertEqual(self.sistema.laboratorios, [])

    def test_cargar_sistema_none_deberia_lanzar_archivo_invalido(self):
        """Evalúa que cargar(None, ruta) lance ArchivoInvalidoError en lugar de AttributeError."""
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(None, self.ruta)

    def test_cargar_archivo_danado_no_deberia_dejar_eventos_fantasma_en_bitacora(self):
        """Evalúa rollback completo: tras fallo parcial en cargar(), la bitácora también queda limpia."""
        self._escribir_json(
            {
                "personas": [
                    {"tipo": "Investigador", "codigo": "123456789", "nombre": "Ana", "nivel": 3, "area": "Malware"},
                    {"tipo": "Invalido", "codigo": "999999999", "nombre": "Error", "nivel": 1},
                ],
                "laboratorios": [],
            }
        )
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.ruta)

        salida = io.StringIO()
        with redirect_stdout(salida):
            self.sistema.ver_bitacora()
        self.assertEqual(salida.getvalue(), "")

    def test_cargar_ocupantes_cadena_vacia_o_personas_dict_deberia_lanzar_archivo_invalido(self):
        """Evalúa validación estricta de listas en 'personas', 'laboratorios' y 'ocupantes'."""
        self._escribir_json(
            {
                "personas": {},
                "laboratorios": [
                    {"clave": "LAB-1", "nombre": "Lab", "cupo": 2, "nivel_minimo": 1, "ocupantes": ""}
                ],
            }
        )
        with self.assertRaises(ArchivoInvalidoError):
            persistencia.cargar(self.sistema, self.ruta)


if __name__ == "__main__":
    unittest.main()
