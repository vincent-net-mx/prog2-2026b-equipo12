from bitacora import Bitacora
from excepciones import DatoInvalidoError, DuplicadoError, ErrorAccesos, NoEncontradoError
from modelo import Laboratorio, Persona


class SistemaAccesos:
    """Coordina todas las operaciones del control de accesos."""

    def __init__(self):
        self._personas = {}
        self._laboratorios = {}
        self._bitacora = Bitacora()

    @property
    def personas(self):
        """Lista de personas registradas, solo lectura."""
        return list(self._personas.values())

    @property
    def laboratorios(self):
        """Lista de laboratorios registrados, solo lectura."""
        return list(self._laboratorios.values())

    def registrar(self, objeto):
        """Da de alta a un investigador o becario si su código no existe."""
        if not isinstance(objeto, Persona):
            raise DatoInvalidoError("Solo se pueden registrar investigadores o becarios.")
        if objeto.codigo in self._personas:
            raise DuplicadoError(f"El código {objeto.codigo} ya está registrado.")
        self._personas[objeto.codigo] = objeto
        self._bitacora.agregar(f"Registrado {objeto.describir()}")

    def agregar_laboratorio(self, laboratorio):
        """Da de alta un laboratorio si su clave no existe."""
        if not isinstance(laboratorio, Laboratorio):
            raise DatoInvalidoError("Solo se pueden agregar laboratorios.")
        if laboratorio.clave in self._laboratorios:
            raise DuplicadoError(f"La clave {laboratorio.clave} ya está registrada.")
        self._laboratorios[laboratorio.clave] = laboratorio
        self._bitacora.agregar(f"Agregado {laboratorio.describir()}")

    def asignar(self, identificador, clave):
        """Asigna una persona registrada a un laboratorio existente."""
        codigo = str(identificador).strip()
        clave = str(clave).strip().upper()
        if codigo not in self._personas:
            raise NoEncontradoError(f"El código {codigo} no está registrado, primero regístralo.")
        if clave not in self._laboratorios:
            raise NoEncontradoError(f"El laboratorio {clave} no está registrado.")
        try:
            self._laboratorios[clave].admitir(self._personas[codigo])
        except ErrorAccesos as error:
            self._bitacora.agregar(f"Rechazado {codigo} en {clave}: {error}")
            raise
        self._bitacora.agregar(f"Asignado {codigo} a {clave}")

    def listar(self):
        """Imprime cada registro pidiéndole que se describa."""
        registros = self.personas + self.laboratorios
        if not registros:
            print("No hay registros.")
        for registro in registros:
            print(registro.describir())

    def ver_bitacora(self):
        """Imprime los eventos de la bitácora."""
        self._bitacora.listar()
