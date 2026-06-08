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