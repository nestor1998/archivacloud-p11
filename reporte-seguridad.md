# Reporte de Seguridad – ArchivaCloud P-11

## Introducción

El presente documento describe los controles de seguridad implementados en el proyecto ArchivaCloud P-11 para proteger la gestión y almacenamiento de archivos en Amazon S3.

---

## SEC-01: Secretos fuera del repositorio

**Estado:** Cumplido

Se utiliza un archivo `.env` para almacenar credenciales AWS temporales. El archivo se encuentra excluido mediante `.gitignore`.

```gitignore
.env
```

Esto evita la exposición accidental de credenciales dentro del repositorio Git.

---

## SEC-02: CORS Restrictivo

**Estado:** Cumplido

El backend y el bucket S3 permiten solicitudes únicamente desde:

```text
http://localhost:5173
```

No se utiliza el comodín `*` como origen permitido.

Esta configuración reduce el riesgo de que aplicaciones externas no autorizadas interactúen con la API o con los recursos almacenados.

---

## SEC-03: Validación de Entrada

**Estado:** Cumplido

Se implementaron validaciones para:

* Nombre de archivo.
* Extensión permitida.
* Tipo MIME.
* Hash SHA-256.
* Tamaño máximo.

Además, los nombres de archivo son sanitizados mediante expresiones regulares para evitar caracteres no deseados.

---

## SEC-04: Límite de Tamaño

**Estado:** Cumplido

Se estableció un tamaño máximo de:

```text
100 MB
```

Los archivos que superan este límite son rechazados antes de ser procesados.

Esta medida ayuda a prevenir cargas excesivas y abuso de recursos.

---

## SEC-05: Principio de Mínimo Privilegio

**Estado:** Cumplido

El proyecto utiliza credenciales temporales proporcionadas por AWS Academy Learner Lab.

Los permisos disponibles fueron administrados por el entorno educativo de AWS Academy, evitando el uso de credenciales permanentes dentro del proyecto.

Además, las credenciales utilizadas se almacenan mediante variables de entorno y nunca son expuestas al cliente.

---

## SEC-06: Bucket Cerrado al Público

**Estado:** Cumplido

Se mantiene habilitada la opción:

```text
Block all public access
```

Esta configuración impide que los objetos almacenados puedan ser accedidos públicamente sin autorización.

---

## SEC-07: Errores sin Información Sensible

**Estado:** Cumplido

La aplicación entrega mensajes controlados al usuario y evita exponer información sensible o detalles internos del sistema.

Ejemplo:

```text
No se pudo generar la URL de subida
```

Esto reduce el riesgo de filtración de información útil para un atacante.

---

## SEC-08: Encriptación en Reposo

**Estado:** Cumplido

El bucket S3 tiene habilitado el cifrado predeterminado mediante Amazon S3 Managed Keys (SSE-S3).

Todos los objetos almacenados son cifrados automáticamente por Amazon S3 antes de ser persistidos.

Configuración observada:

* Cifrado del servidor con claves administradas de Amazon S3 (SSE-S3).
* Clave de bucket activada.
* Cifrado SSE-C bloqueado.

Esta configuración protege la información almacenada frente a accesos no autorizados a nivel de almacenamiento.

---

## SEC-09: Auditoría de Dependencias

**Estado:** Cumplido

Se realizó una auditoría de dependencias utilizando las herramientas:

```bash
pip-audit
npm audit
```

### Frontend

Durante la revisión inicial se detectó una vulnerabilidad asociada al paquete `form-data`.

Se aplicó la corrección recomendada mediante:

```bash
npm audit fix
```

Posteriormente se verificó nuevamente el estado de las dependencias obteniendo:

```text
found 0 vulnerabilities
```

### Backend

La herramienta `pip-audit` identificó vulnerabilidades conocidas en dependencias de terceros:

| Paquete   | Versión | Vulnerabilidad | Versión corregida |
| --------- | ------- | -------------- | ----------------- |
| pip       | 26.1.1  | PYSEC-2026-196 | 26.1.2            |
| starlette | 1.2.1   | CVE-2026-54283 | 1.3.1             |
| starlette | 1.2.1   | CVE-2026-54282 | 1.3.0             |

Estas vulnerabilidades fueron identificadas y documentadas durante la auditoría de seguridad.

La ejecución de las herramientas permitió detectar riesgos potenciales asociados a dependencias externas y mantener un registro de futuras actualizaciones requeridas.

---

## SEC-10: Uso de HTTPS

**Estado:** Cumplido

Las URLs prefirmadas generadas por Amazon S3 utilizan HTTPS para la transferencia segura de archivos.

Asimismo, las comunicaciones con servicios AWS se realizan mediante TLS, garantizando confidencialidad e integridad durante la transmisión de datos.

---

## Feature Extra de Seguridad

La pareja P-11 implementó detección de archivos duplicados mediante:

* Comparación de nombre.
* Comparación de hash SHA-256.

Esta funcionalidad ayuda a evitar redundancia de información y facilita la identificación de contenido repetido dentro del sistema.

---

## Conclusión

ArchivaCloud P-11 implementa controles de seguridad orientados a la protección de credenciales, validación de archivos, control de acceso y protección de la información almacenada en Amazon S3.

Durante el desarrollo se aplicaron medidas como URLs prefirmadas, cifrado SSE-S3, restricción CORS, validaciones de entrada, auditoría de dependencias y almacenamiento seguro de credenciales mediante variables de entorno.

Las medidas implementadas permiten reducir riesgos asociados al almacenamiento de archivos en la nube y cumplir con los requisitos de seguridad definidos para la evaluación.
