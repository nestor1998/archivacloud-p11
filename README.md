# ArchivaCloud P-11

Portal de carga de archivos a Amazon S3.

## Pareja
P-11

## Parámetros únicos
- Tipos permitidos: MP4, MOV
- Tamaño máximo: 100 MB
- Bucket: archivacloud-p11
- Región: us-west-2
- Feature extra: detectar archivos duplicados por mismo nombre o mismo hash

## Stack
- Backend: FastAPI
- Frontend: React + Vite
- Almacenamiento: Amazon S3


El nombre asignado era archivacloud-p11, pero AWS S3 exige nombres globalmente únicos. Como el nombre ya estaba ocupado, se utilizó archivacloud-p11eva3 manteniendo la pareja P-11 y la región us-west-2.

No se creó usuario IAM porque AWS Academy no permite iam:CreateUser.
Se usaron credenciales temporales del laboratorio voclabs.