# Control de Acceso para Laboratorio de Ciberseguridad

**Autores:** Vicente Isidro Amezcua Fuentes e Iván Alejandro García Arteaga.
Programación II, Ciclo 2026B. Opción B: control de accesos.

## ¿Qué hace?

Administra quién puede trabajar en los laboratorios de investigación en ciberseguridad. Registra investigadores y becarios con un nivel de autorización de 1 a 3, registra laboratorios con un cupo máximo y un nivel mínimo, y asigna personas a laboratorios validando que exista lugar, que el nivel alcance y que no estén asignadas dos veces. Todo lo que pasa queda en una bitácora y la información se guarda en `datos.json` para que siga ahí al volver a abrir el programa.

## ¿Cómo se corre?

Se necesita Python 3.10 o más reciente, sin librerías externas. Desde la carpeta del proyecto:

```
python main.py
```

Se abre un menú para registrar, asignar, listar y ver la bitácora. Los datos se guardan después de cada operación. Si `datos.json` no existe, el programa arranca vacío.

También se puede usar importando las clases:

```python
from modelo import Investigador, Becario, Laboratorio
from sistema import SistemaAccesos

sistema = SistemaAccesos()
SistemaAccesos.cargar(sistema, "datos.json")
sistema.registrar(Investigador("123456789", "Ana Ruiz", 3, "Análisis de malware"))
sistema.registrar(Becario("987654321", "Luis Paz", 1, "Ciberseguridad", 3))
sistema.registrar(Laboratorio("MAL-01", "Laboratorio de malware", 5, 2))
sistema.asignar("123456789", "MAL-01")
sistema.listar()
SistemaAccesos.guardar(sistema, "datos.json")
```

`guardar` y `cargar` también existen como funciones del módulo `persistencia` con los mismos parámetros.

## ¿Qué hay en cada archivo?

| Archivo | De qué se encarga |
|---|---|
| `excepciones.py` | Errores propios del sistema, todos heredan de `ErrorAccesos` (que a su vez hereda de `ValueError`) |
| `modelo.py` | Clases `Persona`, `Investigador`, `Becario` y `Laboratorio`, con sus validaciones |
| `bitacora.py` | Clase `Bitacora`, el registro cronológico de eventos |
| `sistema.py` | Clase `SistemaAccesos` con `registrar` (personas y laboratorios), `asignar`, `listar`, `guardar` y `cargar` |
| `persistencia.py` | Escribe y lee el estado del sistema en formato JSON |
| `main.py` | Menú de consola para probar el sistema |
| `tests/` | Suite de pruebas unitarias y de manejo de errores con `unittest` |

## ¿Qué rechaza?

Todo rechazo lanza una excepción con un mensaje que dice qué estuvo mal:

- Código vacío o que no tenga exactamente 9 dígitos, nombre vacío, nivel fuera de 1 a 3, área o carrera vacías, semestre fuera de 1 a 12.
- Registrar algo que no sea una persona o un laboratorio, un código de persona que ya existe o una clave de laboratorio repetida.
- Laboratorio con clave o nombre vacíos, cupo menor a 1, nivel mínimo fuera de 1 a 3 o clave repetida.
- Asignar una persona no registrada, a un laboratorio que no existe, sin el nivel suficiente, a un laboratorio lleno o dos veces al mismo.
- Cargar un archivo dañado: se avisa y el sistema queda vacío.

## Cambios respecto al hito 1

Al programar nos dimos cuenta de que el proyecto pide que el sistema tenga la bitácora y le delegue el registro de lo que pasa, así que la `Bitacora` pasó de `Laboratorio` a `SistemaAccesos`; ahora también registra los intentos de asignación rechazados. `guardar` y `cargar` siguen en `persistencia.py`, pero `SistemaAccesos` también los tiene como métodos estáticos con los mismos parámetros para respetar el contrato. Se agregaron `vaciar()` y `ver_bitacora()` al sistema, propiedades de solo lectura (`codigo`, `nivel`, `clave`, `personas`, `laboratorios`) y `a_diccionario()` en `Laboratorio`. Se quitó `listar_ocupantes()` porque `describir()` ya muestra los ocupantes.

## Correcciones respecto al hito 2

La revisión del hito 2 señaló que `registrar()` rechazaba los laboratorios y que estos se daban de alta con otro método que no está en el contrato (`agregar_laboratorio`). Se corrigió así:

- `registrar(objeto)` ahora acepta personas (`Investigador`, `Becario`) y también laboratorios (`Laboratorio`), como pide el contrato: un solo método para dar de alta cualquiera de los dos tipos de objeto.
- Un laboratorio con una clave que ya existe se rechaza con `DuplicadoError`, igual que una persona con un código repetido. Cualquier otro tipo de objeto (por ejemplo `None` o un texto) se sigue rechazando con `DatoInvalidoError`. Cada alta de laboratorio también queda en la bitácora.
- Se eliminó el método `agregar_laboratorio()`, que ya no hacía falta. El contrato vuelve a ser exactamente de cinco métodos: `registrar`, `asignar`, `listar`, `guardar` y `cargar`.
- `cargar` en `persistencia.py` reconstruye los laboratorios con `registrar`, y la opción 2 del menú de `main.py` ahora se llama "Registrar laboratorio" y usa el mismo método.
- Se actualizaron el ejemplo de uso, la lista de lo que se rechaza y el diagrama de este README para que coincidan con el código.

## Cambios para el hito 3

A partir de una auditoría de calidad y seguridad sobre todos los módulos, se reforzaron validaciones, integridad de estado y manejo de errores:

- **`modelo.py`:** `validar_texto()` ahora rechaza saltos de línea (`\n`, `\r`) para prevenir inyección de registros en la bitácora (CWE-117); se corrigió el mensaje de rango en `validar_entero()` cuando `maximo == 0`; `Persona` implementa `__eq__` y `__hash__` por `codigo` para evitar duplicados entre instancias distintas; y `Laboratorio.admitir()` valida que el argumento sea una `Persona` válida lanzando `DatoInvalidoError`.
- **`bitacora.py`:** `agregar()` valida que el mensaje sea texto no vacío y neutraliza saltos de línea en una sola entrada; se añadió `limpiar()` para vaciar los eventos de forma encapsulada.
- **`sistema.py`:** `registrar()` restringe el alta estrictamente a `Investigador`, `Becario` y `Laboratorio` (rechazando instancias base de `Persona` y laboratorios que ya incluyan ocupantes externos), y `vaciar()` ahora limpia también la bitácora para evitar eventos fantasma tras una carga fallida.
- **`persistencia.py`:** `guardar()` realiza escritura atómica mediante archivo temporal y `os.replace()` (preservando el archivo previo ante fallos de escritura), valida el tipo de ruta y encapsula errores de `sistema` o rutas inválidas en `ArchivoInvalidoError`; `cargar()` valida estrictamente la estructura de listas (`personas`, `laboratorios` y `ocupantes`), protege `sistema.vaciar()` dentro del bloque `try` y restringe `TIPOS` a `Investigador` y `Becario`.
- **`main.py`:** `pedir_persona()` valida inmediatamente que el tipo sea `1` o `2` antes de solicitar el resto de los campos, y `main()` solo guarda en `datos.json` tras operaciones de escritura (`1`, `2` y `3`), evitando sobrescribir un archivo dañado al listar, ver la bitácora o elegir una opción inválida.

## Pruebas unitarias (`unittest`)

Se implementó una suite de **111 pruebas unitarias y de manejo de errores** usando exclusivamente el módulo estándar `unittest` y `unittest.mock`, sin dependencias externas ni efectos secundarios sobre `datos.json` (se emplean directorios temporales y mocks para entradas de consola, fecha/hora y fallos de disco/permisos):

- `tests/test_excepciones.py`: verifica la jerarquía de `ErrorAccesos` y la preservación de mensajes.
- `tests/test_modelo.py`: valida tipos, rangos límite, encapsulamiento, igualdad por código, reglas de admisión y prioridad de errores en `Laboratorio`.
- `tests/test_bitacora.py`: comprueba formato con marca de tiempo, orden cronológico, soporte Unicode y mitigación de inyección de logs.
- `tests/test_sistema.py`: prueba altas, duplicados, asignaciones exitosas y rechazadas con auditoría en bitácora, vaciado completo y delegación a persistencia.
- `tests/test_persistencia.py`: cubre ciclos guardar/cargar, escritura atómica, archivos inexistentes, vacíos, UTF-8 corrupto, esquemas malformados y errores simulados de permisos o escritura.
- `tests/test_main.py`: prueba el menú interactivo y las funciones de lectura simulando `input`, `EOFError`, `KeyboardInterrupt` y archivos dañados al inicio.

Para ejecutar la suite completa desde la raíz del proyecto:

```bash
python3 -m unittest discover -s tests -v
```

## Diagrama

```mermaid
classDiagram
    direction TB

    class SistemaAccesos {
        -dict _personas
        -dict _laboratorios
        -Bitacora _bitacora
        +personas list
        +laboratorios list
        +registrar(objeto)
        +asignar(identificador, clave)
        +listar()
        +ver_bitacora()
        +vaciar()
        +guardar(sistema, ruta)$
        +cargar(sistema, ruta)$
    }

    class Persistencia {
        <<módulo>>
        +guardar(sistema, ruta)
        +cargar(sistema, ruta)
    }

    class Bitacora {
        -list _eventos
        +agregar(mensaje)
        +listar()
        +limpiar()
    }

    class Persona {
        -str _codigo
        -str _nombre
        -int _nivel
        +codigo str
        +nivel int
        +describir() str
        +a_diccionario() dict
    }

    class Investigador {
        -str _area
        +describir() str
        +a_diccionario() dict
    }

    class Becario {
        -str _carrera
        -int _semestre
        +describir() str
        +a_diccionario() dict
    }

    class Laboratorio {
        -str _clave
        -str _nombre
        -int _cupo
        -int _nivel_minimo
        -list _ocupantes
        +clave str
        +admitir(persona)
        +esta_lleno() bool
        +describir() str
        +a_diccionario() dict
    }

    Investigador --|> Persona : ES-UNA
    Becario --|> Persona : ES-UNA
    SistemaAccesos *-- Bitacora : TIENE-UNA
    SistemaAccesos o-- Persona : GESTIONA
    SistemaAccesos o-- Laboratorio : GESTIONA
    Laboratorio o-- Persona : ALOJA
    SistemaAccesos ..> Persistencia : USA
```