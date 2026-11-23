import unittest

from excepciones import (
    AccesoDenegadoError,
    CupoLlenoError,
    DatoInvalidoError,
    DuplicadoError,
)
from modelo import (
    Becario,
    Investigador,
    Laboratorio,
    Persona,
    validar_entero,
    validar_texto,
)


class TestValidadoresModelo(unittest.TestCase):
    """Pruebas de validación de tipos, rangos y casos límite en funciones auxiliares."""

    def setUp(self):
        self.campo = "prueba"

    def tearDown(self):
        self.campo = None

    def test_validar_texto_valido_elimina_espacios_extremos(self):
        """Evalúa el happy path y el recorte de espacios al inicio y final."""
        self.assertEqual(validar_texto("  Ana Ruiz  ", self.campo), "Ana Ruiz")

    def test_validar_texto_unicode_y_caracteres_especiales_retorna_texto(self):
        """Evalúa soporte de acentos, ñ, símbolos y caracteres Unicode."""
        texto = "Criptografía & Redes (Ñandú) 🔒"
        self.assertEqual(validar_texto(texto, self.campo), texto)

    def test_validar_texto_vacio_o_solo_espacios_lanza_dato_invalido(self):
        """Evalúa rechazo de cadenas vacías, espacios ASCII y espacios Unicode."""
        casos = ["", " ", "   \t\n\r  ", "\u00a0"]
        for valor in casos:
            with self.subTest(valor=repr(valor)):
                with self.assertRaises(DatoInvalidoError):
                    validar_texto(valor, self.campo)

    def test_validar_texto_tipos_no_cadena_lanza_dato_invalido(self):
        """Evalúa rechazo de valores None y tipos distintos a str."""
        casos = [None, 0, 123, 3.14, True, False, ["texto"], {"k": "v"}]
        for valor in casos:
            with self.subTest(tipo=type(valor).__name__, valor=valor):
                with self.assertRaises(DatoInvalidoError):
                    validar_texto(valor, self.campo)

    def test_validar_entero_en_rango_retorna_entero(self):
        """Evalúa valores válidos en los límites exactos y sin cota superior."""
        self.assertEqual(validar_entero(1, self.campo, 1, 3), 1)
        self.assertEqual(validar_entero(2, self.campo, 1, 3), 2)
        self.assertEqual(validar_entero(3, self.campo, 1, 3), 3)
        self.assertEqual(validar_entero(10**12, self.campo, 1), 10**12)

    def test_validar_entero_fuera_de_rango_lanza_dato_invalido(self):
        """Evalúa rechazo de enteros negativos, cero o superiores al máximo."""
        casos = [(-10, 1, 3), (0, 1, 3), (4, 1, 3), (0, 1, None), (-1, 1, None)]
        for valor, minimo, maximo in casos:
            with self.subTest(valor=valor, minimo=minimo, maximo=maximo):
                with self.assertRaises(DatoInvalidoError):
                    validar_entero(valor, self.campo, minimo, maximo)

    def test_validar_entero_tipos_invalidos_incluyendo_bool_lanza_dato_invalido(self):
        """Evalúa que bool (subclase de int), float, str y None sean rechazados."""
        casos = [True, False, 1.0, 2.5, "2", None, [], {}]
        for valor in casos:
            with self.subTest(tipo=type(valor).__name__, valor=valor):
                with self.assertRaises(DatoInvalidoError):
                    validar_entero(valor, self.campo, 1, 3)

    def test_validar_entero_maximo_cero_mensaje_error_indica_rango_correcto(self):
        """Evalúa que maximo=0 se informe correctamente como 'entre <min> y 0'."""
        with self.assertRaises(DatoInvalidoError) as contexto:
            validar_entero(5, self.campo, -10, 0)
        self.assertIn("entre -10 y 0", str(contexto.exception))


class TestPersonas(unittest.TestCase):
    """Pruebas unitarias y de frontera para Persona, Investigador y Becario."""

    def setUp(self):
        self.codigo_valido = "123456789"
        self.nombre_valido = "Ana Ruiz"

    def tearDown(self):
        self.codigo_valido = None
        self.nombre_valido = None

    def test_persona_creacion_valida_y_normalizacion_espacios_exito(self):
        """Evalúa la creación válida de Persona con recorte de espacios en código y nombre."""
        persona = Persona(" 123456789 ", "  Ana Ruiz  ", 2)
        self.assertEqual(persona.codigo, "123456789")
        self.assertEqual(persona.nivel, 2)
        self.assertEqual(persona.describir(), "123456789 | Ana Ruiz | nivel 2")

    def test_persona_codigo_con_ceros_iniciales_preserva_cadena(self):
        """Evalúa que los códigos con ceros a la izquierda se mantengan exactos."""
        persona = Persona("000123456", self.nombre_valido, 1)
        self.assertEqual(persona.codigo, "000123456")

    def test_persona_propiedades_solo_lectura_lanza_attribute_error(self):
        """Evalúa encapsulamiento: modificar codigo o nivel directamente debe fallar."""
        persona = Persona(self.codigo_valido, self.nombre_valido, 2)
        with self.assertRaises(AttributeError):
            persona.codigo = "999999999"
        with self.assertRaises(AttributeError):
            persona.nivel = 3

    def test_persona_codigo_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de códigos vacíos, longitud incorrecta, no numéricos, int o dígitos Unicode."""
        casos = [
            "",
            "         ",
            "12345678",
            "1234567890",
            "12345678a",
            "-12345678",
            "1234 5678",
            "123456789\n0",
            "١٢٣٤٥٦٧٨٩",  # Dígitos arábigo-índicos (Unicode)
            123456789,
            None,
            ["123456789"],
        ]
        for codigo in casos:
            with self.subTest(codigo=repr(codigo)):
                with self.assertRaises(DatoInvalidoError):
                    Persona(codigo, self.nombre_valido, 1)

    def test_persona_nombre_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de nombres vacíos, espacios o no textuales."""
        for nombre in ["", "   ", "\t\n", None, 123]:
            with self.subTest(nombre=repr(nombre)):
                with self.assertRaises(DatoInvalidoError):
                    Persona(self.codigo_valido, nombre, 1)

    def test_persona_nivel_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de niveles fuera de 1..3 o tipos incorrectos."""
        for nivel in [0, -1, 4, 1.5, True, False, "2", None]:
            with self.subTest(nivel=repr(nivel)):
                with self.assertRaises(DatoInvalidoError):
                    Persona(self.codigo_valido, self.nombre_valido, nivel)

    def test_persona_a_diccionario_retorna_estructura_esperada(self):
        """Evalúa serialización a diccionario de Persona."""
        persona = Persona(self.codigo_valido, self.nombre_valido, 3)
        self.assertEqual(
            persona.a_diccionario(),
            {
                "tipo": "Persona",
                "codigo": "123456789",
                "nombre": "Ana Ruiz",
                "nivel": 3,
            },
        )

    def test_investigador_creacion_valida_describir_y_a_diccionario_exito(self):
        """Evalúa creación, descripción y serialización correcta de Investigador."""
        inv = Investigador(self.codigo_valido, self.nombre_valido, 3, "  Malware  ")
        self.assertEqual(
            inv.describir(),
            "[Investigador] 123456789 | Ana Ruiz | nivel 3 | área: Malware",
        )
        self.assertEqual(
            inv.a_diccionario(),
            {
                "tipo": "Investigador",
                "codigo": "123456789",
                "nombre": "Ana Ruiz",
                "nivel": 3,
                "area": "Malware",
            },
        )

    def test_investigador_area_invalida_lanza_dato_invalido(self):
        """Evalúa rechazo de áreas de investigación vacías o no textuales."""
        for area in ["", "   ", None, 42, []]:
            with self.subTest(area=repr(area)):
                with self.assertRaises(DatoInvalidoError):
                    Investigador(self.codigo_valido, self.nombre_valido, 3, area)

    def test_becario_creacion_valida_limites_semestre_exito(self):
        """Evalúa límites exactos de semestre (1 y 12) y métodos describir/a_diccionario."""
        becario_min = Becario("000000001", "Luis Paz", 1, "Ciberseguridad", 1)
        becario_max = Becario("000000002", "Sofía Gil", 3, "Computación", 12)
        self.assertEqual(
            becario_min.describir(),
            "[Becario] 000000001 | Luis Paz | nivel 1 | Ciberseguridad, semestre 1",
        )
        self.assertEqual(
            becario_max.a_diccionario(),
            {
                "tipo": "Becario",
                "codigo": "000000002",
                "nombre": "Sofía Gil",
                "nivel": 3,
                "carrera": "Computación",
                "semestre": 12,
            },
        )

    def test_becario_carrera_invalida_lanza_dato_invalido(self):
        """Evalúa rechazo de carrera vacía o no textual."""
        for carrera in ["", "   ", None, 100]:
            with self.subTest(carrera=repr(carrera)):
                with self.assertRaises(DatoInvalidoError):
                    Becario(self.codigo_valido, self.nombre_valido, 1, carrera, 3)

    def test_becario_semestre_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de semestres fuera de 1..12 o con tipo incorrecto."""
        for semestre in [0, -2, 13, 1.0, True, False, "3", None]:
            with self.subTest(semestre=repr(semestre)):
                with self.assertRaises(DatoInvalidoError):
                    Becario(self.codigo_valido, self.nombre_valido, 1, "Sistemas", semestre)

    def test_persona_nombre_con_salto_de_linea_deberia_rechazarse_por_inyeccion_log(self):
        """Evalúa prevención de CWE-117: nombres con salto de línea son rechazados."""
        with self.assertRaises(DatoInvalidoError):
            Persona(self.codigo_valido, "Ana\n[2026-01-01 00:00:00] Evento falso", 2)


class TestLaboratorio(unittest.TestCase):
    """Pruebas unitarias, de reglas de admisión y seguridad para Laboratorio."""

    def setUp(self):
        self.lab = Laboratorio("mal-01", "Laboratorio de Malware", 2, 2)
        self.inv_nivel3 = Investigador("111111111", "Ana Ruiz", 3, "Malware")
        self.bec_nivel2 = Becario("222222222", "Luis Paz", 2, "Ciberseguridad", 4)
        self.bec_nivel1 = Becario("333333333", "Eva Cruz", 1, "Ciberseguridad", 1)
        self.inv_extra = Investigador("444444444", "Raúl Díaz", 3, "Criptografía")

    def tearDown(self):
        self.lab = None

    def test_laboratorio_creacion_valida_normaliza_clave_mayusculas(self):
        """Evalúa normalización de clave a mayúsculas y estado inicial vacío."""
        lab = Laboratorio("  red-02  ", "  Redes  ", 1, 1)
        self.assertEqual(lab.clave, "RED-02")
        self.assertFalse(lab.esta_lleno())

    def test_laboratorio_propiedad_clave_solo_lectura_lanza_attribute_error(self):
        """Evalúa encapsulamiento: la clave del laboratorio no debe poder reasignarse."""
        with self.assertRaises(AttributeError):
            self.lab.clave = "OTRA-01"

    def test_laboratorio_clave_invalida_lanza_dato_invalido(self):
        """Evalúa rechazo de claves vacías o no textuales."""
        for clave in ["", "   ", None, 101]:
            with self.subTest(clave=repr(clave)):
                with self.assertRaises(DatoInvalidoError):
                    Laboratorio(clave, "Lab", 2, 1)

    def test_laboratorio_nombre_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de nombres de laboratorio vacíos o no textuales."""
        for nombre in ["", "   ", None, 101]:
            with self.subTest(nombre=repr(nombre)):
                with self.assertRaises(DatoInvalidoError):
                    Laboratorio("LAB-01", nombre, 2, 1)

    def test_laboratorio_cupo_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de cupos menores a 1 o de tipo no entero."""
        for cupo in [0, -5, 1.5, True, False, "2", None]:
            with self.subTest(cupo=repr(cupo)):
                with self.assertRaises(DatoInvalidoError):
                    Laboratorio("LAB-01", "Lab", cupo, 1)

    def test_laboratorio_nivel_minimo_invalido_lanza_dato_invalido(self):
        """Evalúa rechazo de niveles mínimos fuera de 1..3 o tipo inválido."""
        for nivel in [0, -1, 4, 2.0, True, False, "2", None]:
            with self.subTest(nivel=repr(nivel)):
                with self.assertRaises(DatoInvalidoError):
                    Laboratorio("LAB-01", "Lab", 2, nivel)

    def test_admitir_personas_validas_actualiza_ocupantes_y_esta_lleno(self):
        """Evalúa admisión con nivel exacto y superior hasta llenar el cupo."""
        self.lab.admitir(self.bec_nivel2)
        self.assertFalse(self.lab.esta_lleno())
        self.lab.admitir(self.inv_nivel3)
        self.assertTrue(self.lab.esta_lleno())

    def test_admitir_persona_duplicada_misma_instancia_lanza_duplicado_error(self):
        """Evalúa que no se permita admitir dos veces la misma instancia de persona."""
        self.lab.admitir(self.inv_nivel3)
        with self.assertRaises(DuplicadoError):
            self.lab.admitir(self.inv_nivel3)

    def test_admitir_persona_nivel_insuficiente_lanza_acceso_denegado(self):
        """Evalúa rechazo de personas cuyo nivel es inferior al mínimo del laboratorio."""
        with self.assertRaises(AccesoDenegadoError):
            self.lab.admitir(self.bec_nivel1)
        self.assertEqual(self.lab.a_diccionario()["ocupantes"], [])

    def test_admitir_laboratorio_lleno_lanza_cupo_lleno_error(self):
        """Evalúa rechazo cuando el laboratorio alcanzó su cupo máximo."""
        self.lab.admitir(self.inv_nivel3)
        self.lab.admitir(self.bec_nivel2)
        with self.assertRaises(CupoLlenoError):
            self.lab.admitir(self.inv_extra)

    def test_admitir_prioridad_errores_duplicado_antes_que_cupo_lleno(self):
        """Evalúa que persona ya admitida en laboratorio lleno reciba DuplicadoError."""
        self.lab.admitir(self.inv_nivel3)
        self.lab.admitir(self.bec_nivel2)
        with self.assertRaises(DuplicadoError):
            self.lab.admitir(self.inv_nivel3)

    def test_admitir_prioridad_errores_acceso_denegado_antes_que_cupo_lleno(self):
        """Evalúa que persona sin nivel suficiente en laboratorio lleno reciba AccesoDenegadoError."""
        self.lab.admitir(self.inv_nivel3)
        self.lab.admitir(self.bec_nivel2)
        with self.assertRaises(AccesoDenegadoError):
            self.lab.admitir(self.bec_nivel1)

    def test_describir_sin_ocupantes_y_con_ocupantes_formato_correcto(self):
        """Evalúa el formato de salida de describir() vacío y con ocupantes."""
        self.assertEqual(
            self.lab.describir(),
            "[Laboratorio] MAL-01 | Laboratorio de Malware | 0/2 | nivel mínimo 2 | sin ocupantes",
        )
        self.lab.admitir(self.inv_nivel3)
        self.lab.admitir(self.bec_nivel2)
        self.assertEqual(
            self.lab.describir(),
            "[Laboratorio] MAL-01 | Laboratorio de Malware | 2/2 | nivel mínimo 2 | 111111111, 222222222",
        )

    def test_a_diccionario_retorna_estructura_serializable(self):
        """Evalúa la estructura del diccionario devuelto por a_diccionario()."""
        self.lab.admitir(self.inv_nivel3)
        self.assertEqual(
            self.lab.a_diccionario(),
            {
                "clave": "MAL-01",
                "nombre": "Laboratorio de Malware",
                "cupo": 2,
                "nivel_minimo": 2,
                "ocupantes": ["111111111"],
            },
        )

    def test_admitir_dos_instancias_mismo_codigo_deberia_lanzar_duplicado_error(self):
        """Evalúa que dos instancias distintas con el mismo código sean rechazadas por duplicado."""
        clon_mismo_codigo = Investigador("111111111", "Ana Ruiz", 3, "Malware")
        self.lab.admitir(self.inv_nivel3)
        with self.assertRaises(DuplicadoError):
            self.lab.admitir(clon_mismo_codigo)

    def test_admitir_objeto_invalido_none_deberia_lanzar_dato_invalido(self):
        """Evalúa que admitir(None) rechace el argumento con DatoInvalidoError."""
        with self.assertRaises(DatoInvalidoError):
            self.lab.admitir(None)


if __name__ == "__main__":
    unittest.main()
