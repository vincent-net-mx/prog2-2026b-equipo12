import re

from excepciones import DatoInvalidoError


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
