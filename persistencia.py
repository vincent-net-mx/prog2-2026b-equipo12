import json

from excepciones import ArchivoInvalidoError
from modelo import Becario, Investigador, Laboratorio, Persona

TIPOS = {clase.__name__: clase for clase in (Persona, Investigador, Becario)}


def guardar(sistema, ruta):
    """Escribe en un archivo JSON las personas y los laboratorios del sistema."""
    datos = {
        "personas": [persona.a_diccionario() for persona in sistema.personas],
        "laboratorios": [laboratorio.a_diccionario() for laboratorio in sistema.laboratorios],
    }
    try:
        with open(ruta, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
    except (OSError, TypeError):
        raise ArchivoInvalidoError(f"No se pudo guardar en '{ruta}'.") from None


def cargar(sistema, ruta):
    """Reconstruye el sistema desde el archivo; si no existe, lo deja vacío."""
    sistema.vaciar()
    try:
        with open(ruta, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        for persona in datos["personas"]:
            sistema.registrar(TIPOS[persona.pop("tipo")](**persona))
        for laboratorio in datos["laboratorios"]:
            ocupantes = laboratorio.pop("ocupantes")
            sistema.registrar(Laboratorio(**laboratorio))
            for codigo in ocupantes:
                sistema.asignar(codigo, laboratorio["clave"])
    except FileNotFoundError:
        return
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        sistema.vaciar()
        raise ArchivoInvalidoError(f"El archivo '{ruta}' está dañado o es inválido.") from None