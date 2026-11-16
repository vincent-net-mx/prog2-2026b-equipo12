class ErrorAccesos(ValueError):
    """Error base de todo lo que el sistema de accesos rechaza."""


class DatoInvalidoError(ErrorAccesos):
    """Un dato está vacío, tiene mal formato o está fuera de rango."""


class DuplicadoError(ErrorAccesos):
    """Se intenta registrar o asignar algo que ya existe."""


class NoEncontradoError(ErrorAccesos):
    """La persona o el laboratorio buscado no está registrado."""


class CupoLlenoError(ErrorAccesos):
    """El laboratorio ya alcanzó su cupo máximo."""


class AccesoDenegadoError(ErrorAccesos):
    """La persona no tiene el nivel que pide el laboratorio."""


class ArchivoInvalidoError(ErrorAccesos):
    """El archivo de datos no se pudo leer o escribir."""
