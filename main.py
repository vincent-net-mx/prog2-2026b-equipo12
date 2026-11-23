from modelo import Becario, Investigador, Laboratorio
from sistema import SistemaAccesos

RUTA = "datos.json"
MENU = """
1. Registrar persona
2. Registrar laboratorio
3. Asignar persona a laboratorio
4. Listar
5. Ver bitácora
6. Salir"""


def pedir_entero(mensaje):
    """Pide un número entero y avisa con claridad si lo escrito no lo es."""
    try:
        return int(input(mensaje))
    except ValueError:
        raise ValueError("Se esperaba un número entero.") from None


def pedir_persona():
    """Pide los datos de una persona y crea el objeto del tipo elegido."""
    tipo = input("Tipo (1 investigador, 2 becario): ").strip()
    if tipo not in ("1", "2"):
        raise ValueError("El tipo debe ser 1 o 2.")
    codigo = input("Código (9 dígitos): ")
    nombre = input("Nombre: ")
    nivel = pedir_entero("Nivel de autorización (1-3): ")
    if tipo == "1":
        return Investigador(codigo, nombre, nivel, input("Área de investigación: "))
    return Becario(codigo, nombre, nivel, input("Carrera: "), pedir_entero("Semestre: "))


def pedir_laboratorio():
    """Pide los datos de un laboratorio y crea el objeto."""
    clave = input("Clave: ")
    nombre = input("Nombre: ")
    return Laboratorio(clave, nombre, pedir_entero("Cupo: "), pedir_entero("Nivel mínimo (1-3): "))


def main():
    """Carga los datos, muestra el menú y guarda después de cada operación."""
    sistema = SistemaAccesos()
    try:
        sistema.cargar(sistema, RUTA)
    except ValueError as error:
        print(f"Error: {error}")
    while True:
        print(MENU)
        try:
            opcion = input("Opción: ").strip()
            if opcion == "1":
                sistema.registrar(pedir_persona())
                sistema.guardar(sistema, RUTA)
            elif opcion == "2":
                sistema.registrar(pedir_laboratorio())
                sistema.guardar(sistema, RUTA)
            elif opcion == "3":
                sistema.asignar(input("Código de la persona: "), input("Clave del laboratorio: "))
                sistema.guardar(sistema, RUTA)
            elif opcion == "4":
                sistema.listar()
            elif opcion == "5":
                sistema.ver_bitacora()
            elif opcion == "6":
                break
            else:
                print("Opción inválida.")
        except ValueError as error:
            print(f"Error: {error}")
        except (EOFError, KeyboardInterrupt):
            break


if __name__ == "__main__":
    main()