# ArchivaCloud P-11

## Equipo

**Pareja:** P-11


# Descripción

ArchivaCloud es una aplicación web desarrollada como parte de la Evaluación Sumativa 3 de AWS Cloud Foundations.

La solución permite cargar, listar, descargar y eliminar archivos almacenados en Amazon S3 utilizando URLs prefirmadas generadas por un backend desarrollado con FastAPI.

El sistema incorpora validaciones de seguridad, control de tipos de archivo, límite de tamaño y detección de archivos duplicados mediante nombre e identificación por hash SHA-256.

---

# Objetivo

Desarrollar una solución de almacenamiento de archivos en la nube utilizando Amazon S3 y una arquitectura cliente-servidor moderna, incorporando buenas prácticas de seguridad, validación de datos y control de acceso.

---

# Parámetros de la Pareja P-11

| Parámetro         | Valor                            |
| ----------------- | -------------------------------- |
| Código de pareja  | P-11                             |
| Tipos permitidos  | MP4, MOV                         |
| Tamaño máximo     | 100 MB                           |
| Región AWS        | us-west-2                        |
| Bucket S3         | archivacloud-p11eva3             |
| Feature adicional | Detección de archivos duplicados |

---

# Arquitectura

```text
Usuario
   ↓
Frontend React/Vite
   ↓
Backend FastAPI
   ↓
Amazon S3
```

---

# Tecnologías Utilizadas

## Frontend

* React
* Vite
* JavaScript
* Axios
* CSS

## Backend

* Python
* FastAPI
* Boto3
* Uvicorn
* Pydantic
* Python-dotenv

## Cloud

* Amazon S3
* AWS Academy Learner Lab
* Credenciales temporales AWS
* Presigned URLs

---

# Funcionalidades Implementadas

## Sprint 1

* Generación de URLs prefirmadas.
* Integración FastAPI con Amazon S3.
* Carga de archivos a S3.

## Sprint 2

* Listado de archivos almacenados.
* Descarga de archivos.
* Eliminación de archivos.
* Mejoras de interfaz.

## Sprint 3

* Detección de archivos duplicados por nombre.
* Detección de archivos duplicados mediante hash SHA-256.
* Validaciones de seguridad.
* Documentación y comentarios del código.

## Sprint 4

* Elaboración de documentación final.
* Reporte de seguridad.
* Declaración de uso de Inteligencia Artificial.
* Preparación de defensa y entrega final.

---

# Variables de Entorno

El backend utiliza las siguientes variables:

```env
AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
AWS_SESSION_TOKEN=YOUR_SESSION_TOKEN
AWS_REGION=us-west-2
S3_BUCKET_NAME=archivacloud-p11eva3
FRONTEND_ORIGIN=http://localhost:5173
```

---

# Validaciones Implementadas

## Frontend

* Validación de archivos MP4 y MOV.
* Validación de tamaño máximo de 100 MB.
* Cálculo de hash SHA-256 utilizando Web Crypto API.
* Validación previa antes de solicitar la URL prefirmada.

## Backend

* Validación de nombre de archivo.
* Sanitización de caracteres especiales.
* Validación de extensiones permitidas.
* Validación de Content-Type.
* Validación de tamaño máximo permitido.
* Validación de hash SHA-256.
* Manejo controlado de errores.

---

# Seguridad Implementada

* Uso de URLs prefirmadas para acceso temporal a Amazon S3.
* Protección de credenciales AWS mediante variables de entorno.
* Restricción de acceso mediante configuración CORS.
* Bucket protegido mediante Block Public Access.
* Cifrado SSE-S3 habilitado.
* Validación de tipos de archivos.
* Validación de tamaño máximo permitido.
* Validación de hash SHA-256.
* Detección de archivos duplicados.

---

# Configuración CORS del Bucket

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "GET", "HEAD"],
    "AllowedOrigins": ["http://localhost:5173"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

---

# Feature Adicional Implementada

La pareja P-11 implementó detección de archivos duplicados utilizando dos mecanismos:

## Duplicados por Nombre

El sistema identifica archivos que poseen el mismo nombre visible para el usuario.

## Duplicados por Hash SHA-256

Antes de subir un archivo se calcula un hash SHA-256 en el navegador utilizando Web Crypto API.

El hash es enviado al backend y almacenado como metadata del objeto en Amazon S3.

Posteriormente, durante el listado de archivos, el sistema compara los hashes almacenados y marca visualmente los archivos que contienen exactamente el mismo contenido.

---

# Instalación

## Backend

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

## Frontend

```bash
npm install
npm run dev
```

---

# Auditoría de Dependencias

## Frontend

Se ejecutó:

```bash
npm audit
```

Se detectó una vulnerabilidad asociada al paquete `form-data`.

Posteriormente se ejecutó:

```bash
npm audit fix
```

Resultado final:

```text
found 0 vulnerabilities
```

## Backend

Se ejecutó:

```bash
pip-audit
```

Las vulnerabilidades encontradas fueron documentadas en el reporte de seguridad para futuras actualizaciones del proyecto.

---


# Asignatura

AWS Cloud Foundations

---

# Estado del Proyecto

Versión final entregable:

**v1.0.0**
