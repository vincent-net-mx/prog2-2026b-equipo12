# Control de Acceso para Laboratorio de Ciberseguridad

**Autores:** Vicente Amezcua y Alejandro García.

## 1. ¿Qué es esto?

Es la propuesta y diseño de un sistema en Python para administrar el control de acceso a laboratorios de investigación en ciberseguridad. El sistema registrará personal (**investigadores** y **becarios**) con niveles de autorización (`1` a `3`) y espacios de trabajo (**laboratorios**) con cupo máximo y nivel de seguridad mínimo, validando cada asignación mediante excepciones personalizadas, llevando una bitácora por laboratorio y conservando los datos entre ejecuciones.

> **Estado actual:** En fase de diseño (aún no hay código implementado en este repositorio).

## 2. ¿Cómo lo corro?

*Pendiente.* El código fuente y el punto de entrada (`main.py`) aún no han sido desarrollados.

## 3. ¿Qué hay aquí dentro?

Por el momento, el repositorio solo contiene la documentación inicial del proyecto (`README.md`). Conforme avance el desarrollo, contendrá los siguientes módulos planeados:

* **Modelo de dominio:** Clases `Persona`, `Investigador`, `Becario`, `Laboratorio` y `Bitacora`.
* **Controlador:** Clase `SistemaAccesos` para gestionar altas, asignaciones y listados.
* **Excepciones:** Jerarquía propia derivada de `ErrorAccesos` (`DatoInvalidoError`, `DuplicadoError`, `NoEncontradoError`, `CupoLlenoError`, `AccesoDenegadoError`, `ArchivoInvalidoError`).
* **Persistencia:** Módulo `persistencia.py` para guardar y cargar el estado del sistema.
* **Interfaz:** Archivo `main.py` con el menú de consola para pruebas.

## 4. ¿Qué produce?

*Pendiente.* Una vez implementado, generará listados en consola sobre el personal registrado, la ocupación y bitácoras de los laboratorios, mensajes de validación ante intentos de acceso no autorizados y un archivo de datos local para persistir la información entre ejecuciones.