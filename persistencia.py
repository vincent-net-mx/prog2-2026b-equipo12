import json
import os

from excepciones import ArchivoInvalidoError
from modelo import Becario, Investigador, Laboratorio

TIPOS = {clase.__name__: clase for clase in (Investigador, Becario)}


def guardar(sistema, ruta):
    """Escribe de forma atómica en un archivo JSON las personas y laboratorios del sistema."""
    ruta_temporal = None
    try:
        if not isinstance(ruta, (str, os.PathLike)):
            raise TypeError("Ruta inválida.")
        ruta_str = os.fspath(ruta)
        if not isinstance(ruta_str, str) or not ruta_str.strip():
            raise ValueError("Ruta vacía o inválida.")
        if os.path.isdir(ruta_str):
            raise IsADirectoryError(ruta_str)
        datos = {
            "personas": [persona.a_diccionario() for persona in sistema.personas],
            "laboratorios": [laboratorio.a_diccionario() for laboratorio in sistema.laboratorios],
        }
        directorio = os.path.dirname(ruta_str) or "."
        nombre = os.path.basename(ruta_str)
        ruta_temporal = os.path.join(directorio, f".{nombre}.{os.getpid()}.tmp")
        with open(ruta_temporal, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(ruta_temporal, ruta_str)
    except (OSError, TypeError, ValueError, AttributeError):
        if ruta_temporal and os.path.exists(ruta_temporal):
            try:
                os.remove(ruta_temporal)
            except OSError:
                pass
        raise ArchivoInvalidoError(f"No se pudo guardar en '{ruta}'.") from None


def cargar(sistema, ruta):
    """Reconstruye el sistema desde el archivo; si no existe, lo deja vacío."""
    try:
        sistema.vaciar()
        if not isinstance(ruta, (str, os.PathLike)):
            raise TypeError("Ruta inválida.")
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        if (
            not isinstance(datos, dict)
            or not isinstance(datos.get("personas"), list)
            or not isinstance(datos.get("laboratorios"), list)
        ):
            raise ValueError("Estructura de archivo inválida.")
        for persona in datos["personas"]:
            if not isinstance(persona, dict):
                raise TypeError("Registro de persona inválido.")
            copia = dict(persona)
            sistema.registrar(TIPOS[copia.pop("tipo")](**copia))
        for laboratorio in datos["laboratorios"]:
            if not isinstance(laboratorio, dict):
                raise TypeError("Registro de laboratorio inválido.")
            copia = dict(laboratorio)
            ocupantes = copia.pop("ocupantes")
            if not isinstance(ocupantes, list):
                raise TypeError("Lista de ocupantes inválida.")
            sistema.registrar(Laboratorio(**copia))
            for codigo in ocupantes:
                sistema.asignar(codigo, copia["clave"])
    except FileNotFoundError:
        return
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        if hasattr(sistema, "vaciar"):
            sistema.vaciar()
        raise ArchivoInvalidoError(f"El archivo '{ruta}' está dañado o es inválido.") from None