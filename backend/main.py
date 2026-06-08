from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import boto3
import os
import re
import uuid

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
)


class PresignedUrlRequest(BaseModel):
    fileName: str
    fileType: str
    fileSize: int


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

    unique_id = str(uuid.uuid4())
    key = f"uploads/{unique_id}-{clean_name}"

    try:
        presigned_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": key,
                "ContentType": data.fileType,
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