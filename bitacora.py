from datetime import datetime

from excepciones import DatoInvalidoError


class Bitacora:
    """Lleva el registro cronológico de lo que pasa en el sistema."""

    def __init__(self):
        self._eventos = []

    def agregar(self, mensaje):
        """Guarda un evento con la hora en que ocurrió."""
        if not isinstance(mensaje, str) or not mensaje.strip():
            raise DatoInvalidoError("El mensaje de la bitácora es obligatorio y debe ser texto.")
        limpio = mensaje.replace("\r", " ").replace("\n", " ").strip()
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._eventos.append(f"[{hora}] {limpio}")

    def listar(self):
        """Imprime los eventos en el orden en que ocurrieron."""
        for evento in self._eventos:
            print(evento)

    def limpiar(self):
        """Elimina todos los eventos registrados en la bitácora."""
        self._eventos.clear()
