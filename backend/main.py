from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import boto3
import os
import re
import uuid
from urllib.parse import unquote
from botocore.config import Config



load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "archivacloud-p11eva3")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

MAX_FILE_SIZE = 100 * 1024 * 1024
ALLOWED_EXTENSIONS = [".mp4", ".mov"]
ALLOWED_CONTENT_TYPES = ["video/mp4", "video/quicktime"]

app = FastAPI(title="ArchivaCloud P-11 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


class PresignedUrlRequest(BaseModel):
    fileName: str
    fileType: str
    fileSize: int
    fileHash: str


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def sanitize_filename(filename: str) -> str:
    filename = filename.strip()
    filename = filename.replace(" ", "_")
    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)
    return filename


@app.post("/api/upload/presigned-url")
def create_presigned_url(data: PresignedUrlRequest):
    clean_name = sanitize_filename(data.fileName)

    if not clean_name:
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")

    extension = os.path.splitext(clean_name)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")

    if data.fileType not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="MIME type no permitido")

    if data.fileSize <= 0 or data.fileSize > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo supera el máximo permitido de 100 MB")

    if not data.fileHash or len(data.fileHash) != 64:
        raise HTTPException(status_code=400, detail="Hash SHA-256 inválido")

    unique_id = str(uuid.uuid4())
    key = f"uploads/{unique_id}-{clean_name}"

    try:
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

        public_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"

        return {
            "presignedUrl": presigned_url,
            "key": key,
            "publicUrl": public_url,
        }

    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo generar la URL de subida")

@app.get("/api/files")
def list_files():
    try:
        response = s3_client.list_objects_v2(
            Bucket=S3_BUCKET_NAME,
            Prefix="uploads/"
        )

        files = []
        name_counter = {}
        hash_counter = {}

        for obj in response.get("Contents", []):
            if obj["Key"].endswith("/"):
                continue

            head = s3_client.head_object(
                Bucket=S3_BUCKET_NAME,
                Key=obj["Key"]
            )

            metadata = head.get("Metadata", {})
            file_hash = metadata.get("sha256")

            stored_name = obj["Key"].replace("uploads/", "", 1)
            visible_name = stored_name

            if "-" in stored_name:
                parts = stored_name.split("-", 5)
                if len(parts) == 6:
                    visible_name = parts[5]

            normalized_name = visible_name.lower()
            name_counter[normalized_name] = name_counter.get(normalized_name, 0) + 1

            if file_hash:
                hash_counter[file_hash] = hash_counter.get(file_hash, 0) + 1

            download_url = s3_client.generate_presigned_url(
                ClientMethod="get_object",
                Params={
                    "Bucket": S3_BUCKET_NAME,
                    "Key": obj["Key"],
                    "ResponseContentDisposition": f'attachment; filename="{visible_name}"'
                },
                ExpiresIn=3600,
            )

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

        for file in files:
            normalized_name = file["name"].lower()

            if name_counter.get(normalized_name, 0) > 1:
                file["isDuplicateName"] = True

            if file["sha256"] and hash_counter.get(file["sha256"], 0) > 1:
                file["isDuplicateHash"] = True

        return {"files": files}

    except Exception as e:
        print("ERROR LISTANDO ARCHIVOS:", e)
        raise HTTPException(status_code=500, detail="No se pudo listar los archivos")
    
@app.delete("/api/files/{key:path}")
def delete_file(key: str):
    try:
        decoded_key = unquote(key)

        if not decoded_key.startswith("uploads/"):
            raise HTTPException(status_code=400, detail="Key inválida")

        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=decoded_key
        )

        return {
            "message": "Archivo eliminado correctamente",
            "key": decoded_key
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="No se pudo eliminar el archivo")