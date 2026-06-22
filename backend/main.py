# Importación de FastAPI para crear la API REST
from fastapi import FastAPI, HTTPException

# Middleware para permitir peticiones desde el frontend (CORS)
from fastapi.middleware.cors import CORSMiddleware

# BaseModel permite definir modelos de datos para validar solicitudes
from pydantic import BaseModel

# Carga variables de entorno desde el archivo .env
from dotenv import load_dotenv

# SDK de AWS para interactuar con servicios como S3
import boto3

# Permite acceder a variables de entorno del sistema operativo
import os

# Expresiones regulares para sanitizar nombres de archivos
import re

# Generación de identificadores únicos (UUID)
import uuid

# Decodifica caracteres especiales en URLs
from urllib.parse import unquote

# Configuración avanzada para el cliente S3
from botocore.config import Config


# Carga las variables definidas en el archivo .env
load_dotenv()

# Región AWS donde se encuentra el bucket S3
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# Nombre del bucket S3 utilizado para almacenar los archivos
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "archivacloud-p11eva3")

# URL permitida para consumir la API desde el frontend
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# Tamaño máximo permitido para un archivo (100 MB)
MAX_FILE_SIZE = 100 * 1024 * 1024

# Extensiones permitidas para subir archivos
ALLOWED_EXTENSIONS = [".mp4", ".mov"]

# Tipos MIME permitidos
ALLOWED_CONTENT_TYPES = ["video/mp4", "video/quicktime"]

# Creación de la aplicación FastAPI
app = FastAPI(title="ArchivaCloud P-11 API")

# Configuración de CORS para permitir comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creación del cliente S3 utilizando las credenciales AWS
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
    config=Config(
        s3={"addressing_style": "virtual"},
        signature_version="s3v4"
    )
)

# Modelo utilizado para validar la solicitud de generación de URL prefirmada
class PresignedUrlRequest(BaseModel):
    fileName: str
    fileType: str
    fileSize: int
    fileHash: str


# Endpoint de verificación de estado de la API
@app.get("/healthz")
def healthz():
    return {"status": "ok"}


# Función para limpiar y normalizar nombres de archivos
def sanitize_filename(filename: str) -> str:

    # Elimina espacios al inicio y final
    filename = filename.strip()

    # Reemplaza espacios internos por guiones bajos
    filename = filename.replace(" ", "_")

    # Elimina caracteres no permitidos
    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)

    return filename


# Endpoint que genera una URL prefirmada para subir archivos a S3
@app.post("/api/upload/presigned-url")
def create_presigned_url(data: PresignedUrlRequest):

    # Limpia el nombre del archivo recibido
    clean_name = sanitize_filename(data.fileName)

    # Verifica que el nombre sea válido
    if not clean_name:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    # Obtiene la extensión del archivo
    extension = os.path.splitext(clean_name)[1].lower()

    # Valida que la extensión esté permitida
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")

    # Valida el MIME Type
    if data.fileType not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="MIME type no permitido")

    # Valida tamaño máximo permitido
    if data.fileSize <= 0 or data.fileSize > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el máximo permitido de 100 MB")

    # Verifica que el hash SHA-256 tenga el largo correcto
    if not data.fileHash or len(data.fileHash) != 64:
        raise HTTPException(status_code=400, detail="Hash SHA-256 inválido")

    # Genera un identificador único para evitar colisiones de nombres
    unique_id = str(uuid.uuid4())

    # Construye la key que tendrá el archivo dentro del bucket
    key = f"uploads/{unique_id}-{clean_name}"

    try:

        # Genera una URL prefirmada para subir el archivo directamente a S3
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": key,
                "ContentType": data.fileType,
                "Metadata": {
                    "sha256": data.fileHash
                }
            },
            ExpiresIn=3600,
        )

        # Construye una URL pública de referencia
        public_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"

        # Devuelve la información al frontend
        return {
            "presignedUrl": presigned_url,
            "key": key,
            "publicUrl": public_url,
        }

    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo generar la URL de subida")


# Endpoint que lista los archivos almacenados en S3
@app.get("/api/files")
def list_files():
    try:

        # Obtiene todos los objetos dentro del prefijo uploads/
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix="uploads/"
        )

        files = []

        # Diccionarios utilizados para detectar duplicados
        name_counter = {}
        hash_counter = {}

        # Recorre todos los archivos encontrados
        for obj in response.get("Contents", []):

            # Ignora carpetas virtuales
            if obj["Key"].endswith("/"):
                continue

            # Obtiene metadatos del objeto
            head = s3_client.head_object(
                Bucket=S3_BUCKET_NAME,
                Key=obj["Key"]
            )

            metadata = head.get("Metadata", {})

            # Obtiene el hash SHA-256 almacenado
            file_hash = metadata.get("sha256")

            # Obtiene el nombre almacenado en S3
            stored_name = obj["Key"].replace("uploads/", "", 1)

            visible_name = stored_name

            # Elimina el UUID para mostrar el nombre original
            if "-" in stored_name:
                parts = stored_name.split("-", 5)
                if len(parts) == 6:
                    visible_name = parts[5]

            # Normaliza el nombre para detección de duplicados
            normalized_name = visible_name.lower()

            name_counter[normalized_name] = name_counter.get(normalized_name, 0) + 1

            # Cuenta hashes repetidos
            if file_hash:
                hash_counter[file_hash] = hash_counter.get(file_hash, 0) + 1

            # Genera URL prefirmada de descarga
            download_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": S3_BUCKET_NAME,
                    "Key": obj["Key"],
                    "ResponseContentDisposition": f'attachment; filename="{visible_name}"'
                },
                ExpiresIn=3600,
            )

            # Agrega información del archivo a la lista
            files.append({
                "key": obj["Key"],
                "name": visible_name,
                "storedName": stored_name,
                "size": obj["Size"],
                "lastModified": obj["LastModified"].isoformat(),
                "url": download_url,
                "sha256": file_hash,
                "isDuplicateName": False,
                "isDuplicateHash": False
            })

        # Marca archivos duplicados por nombre o hash
        for file in files:
            normalized_name = file["name"].lower()

            if name_counter.get(normalized_name, 0) > 1:
                file["isDuplicateName"] = True

            if file["sha256"] and hash_counter.get(file["sha256"], 0) > 1:
                file["isDuplicateHash"] = True

        # Retorna listado completo
        return {"files": files}

    except Exception as e:
        print("ERROR LISTANDO ARCHIVOS:", e)

        raise HTTPException(status_code=500, detail="No se pudo listar los archivos")


# Endpoint para eliminar archivos del bucket
@app.delete("/api/files/{key:path}")
def delete_file(key: str):
    try:

        # Decodifica caracteres especiales de la URL
        decoded_key = unquote(key)

        # Verifica que el archivo pertenezca al directorio uploads
        if not decoded_key.startswith("uploads/"):
            raise HTTPException(status_code=400, detail="Key inválida")

        # Elimina el objeto del bucket
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=decoded_key
        )

        # Respuesta exitosa
        return {
            "message": "Archivo eliminado correctamente",
            "key": decoded_key
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo eliminar el archivo")