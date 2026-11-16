from datetime import datetime


class Bitacora:
    """Lleva el registro cronológico de lo que pasa en el sistema."""

    def __init__(self):
        self._eventos = []

    def agregar(self, mensaje):
        """Guarda un evento con la hora en que ocurrió."""
        hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._eventos.append(f"[{hora}] {mensaje}")

    def listar(self):
        """Imprime los eventos en el orden en que ocurrieron."""
        for evento in self._eventos:
            print(evento)
