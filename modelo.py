import re

from excepciones import AccesoDenegadoError, CupoLlenoError, DatoInvalidoError, DuplicadoError


def validar_texto(valor, campo):
    """Regresa el texto sin espacios en los extremos o lanza error si está vacío."""
    if not isinstance(valor, str) or not valor.strip():
        raise DatoInvalidoError(f"El campo '{campo}' es obligatorio y debe ser texto.")
    return valor.strip()


def validar_entero(valor, campo, minimo, maximo=None):
    """Regresa el entero si está dentro del rango o lanza error."""
    if type(valor) is not int or valor < minimo or (maximo is not None and valor > maximo):
        rango = f"entre {minimo} y {maximo}" if maximo else f"mayor o igual a {minimo}"
        raise DatoInvalidoError(f"El campo '{campo}' debe ser un número entero {rango}.")
    return valor


class Persona:
    """Guarda los datos comunes de quien participa en un laboratorio."""

    def __init__(self, codigo, nombre, nivel):
        if not isinstance(codigo, str) or not re.fullmatch(r"[0-9]{9}", codigo.strip()):
            raise DatoInvalidoError("El código es obligatorio y debe tener exactamente 9 dígitos.")
        self._codigo = codigo.strip()
        self._nombre = validar_texto(nombre, "nombre")
        self._nivel = validar_entero(nivel, "nivel", 1, 3)

    @property
    def codigo(self):
        """Código de la persona, solo lectura."""
        return self._codigo

    @property
    def nivel(self):
        """Nivel de autorización, solo lectura."""
        return self._nivel

    def describir(self):
        """Regresa los datos comunes en una línea."""
        return f"{self._codigo} | {self._nombre} | nivel {self._nivel}"

    def a_diccionario(self):
        """Regresa los datos comunes listos para guardarse."""
        return {"tipo": type(self).__name__, "codigo": self._codigo,
                "nombre": self._nombre, "nivel": self._nivel}


class Investigador(Persona):
    """Representa a una persona investigadora con su área de investigación."""

    def __init__(self, codigo, nombre, nivel, area):
        super().__init__(codigo, nombre, nivel)
        self._area = validar_texto(area, "área de investigación")

    def describir(self):
        """Agrega el área a la descripción común."""
        return f"[Investigador] {super().describir()} | área: {self._area}"

    def a_diccionario(self):
        """Agrega el área a los datos comunes."""
        datos = super().a_diccionario()
        datos["area"] = self._area
        return datos


class Becario(Persona):
    """Representa a una persona becaria junto con los datos de su carrera."""

    def __init__(self, codigo, nombre, nivel, carrera, semestre):
        super().__init__(codigo, nombre, nivel)
        self._carrera = validar_texto(carrera, "carrera")
        self._semestre = validar_entero(semestre, "semestre", 1, 12)

    def describir(self):
        """Agrega la carrera y el semestre a la descripción común."""
        return f"[Becario] {super().describir()} | {self._carrera}, semestre {self._semestre}"

    def a_diccionario(self):
        """Agrega la carrera y el semestre a los datos comunes."""
        datos = super().a_diccionario()
        datos["carrera"] = self._carrera
        datos["semestre"] = self._semestre
        return datos


class Laboratorio:
    """Controla quién entra a un laboratorio sin exceder su cupo ni su nivel mínimo."""

    def __init__(self, clave, nombre, cupo, nivel_minimo):
        self._clave = validar_texto(clave, "clave").upper()
        self._nombre = validar_texto(nombre, "nombre del laboratorio")
        self._cupo = validar_entero(cupo, "cupo", 1)
        self._nivel_minimo = validar_entero(nivel_minimo, "nivel mínimo", 1, 3)
        self._ocupantes = []

    @property
    def clave(self):
        """Clave del laboratorio, solo lectura."""
        return self._clave

    def esta_lleno(self):
        """Indica si ya no cabe nadie más."""
        return len(self._ocupantes) >= self._cupo

    def admitir(self, persona):
        """Agrega a la persona si no está dentro, tiene el nivel y hay lugar."""
        if persona in self._ocupantes:
            raise DuplicadoError(f"La persona {persona.codigo} ya está asignada a {self._clave}.")
        if persona.nivel < self._nivel_minimo:
            raise AccesoDenegadoError(f"{self._clave} requiere nivel {self._nivel_minimo} "
                                      f"y {persona.codigo} tiene nivel {persona.nivel}.")
        if self.esta_lleno():
            raise CupoLlenoError(f"{self._clave} ya alcanzó su cupo máximo de {self._cupo}.")
        self._ocupantes.append(persona)

    def describir(self):
        """Regresa los datos del laboratorio y los códigos de quienes están dentro."""
        ocupantes = ", ".join(persona.codigo for persona in self._ocupantes) or "sin ocupantes"
        lugares = f"{len(self._ocupantes)}/{self._cupo}"
        return (f"[Laboratorio] {self._clave} | {self._nombre} | {lugares}"
                f" | nivel mínimo {self._nivel_minimo} | {ocupantes}")

    def a_diccionario(self):
        """Regresa los datos del laboratorio listos para guardarse."""
        return {"clave": self._clave, "nombre": self._nombre, "cupo": self._cupo,
                "nivel_minimo": self._nivel_minimo,
                "ocupantes": [persona.codigo for persona in self._ocupantes]}
