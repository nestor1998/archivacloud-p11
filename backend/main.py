from fastapi import FastAPI, HTTPException  # Importa FastAPI para crear la API REST y HTTPException para manejar errores HTTP
from fastapi.middleware.cors import CORSMiddleware  # Permite configurar CORS para aceptar peticiones desde el frontend
from pydantic import BaseModel  # Permite definir modelos de datos para validar solicitudes
from dotenv import load_dotenv  # Carga variables de entorno desde el archivo .env
import boto3  # SDK de AWS para interactuar con servicios como S3 y DynamoDB
import os  # Permite acceder a variables de entorno del sistema operativo
import re  # Permite usar expresiones regulares para limpiar nombres de archivos
import uuid  # Permite generar identificadores únicos
from urllib.parse import unquote  # Decodifica caracteres especiales enviados en URLs
from botocore.config import Config  # Permite configurar opciones avanzadas del cliente S3


load_dotenv()  # Carga las variables definidas en el archivo .env

AWS_REGION = os.getenv("AWS_REGION", "us-west-2")  # Define la región de AWS donde se encuentra el bucket
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "archivacloud-p11eva3")  # Define el nombre del bucket S3
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")  # Define el origen permitido del frontend

MAX_FILE_SIZE = 100 * 1024 * 1024  # Define el tamaño máximo permitido para archivos, equivalente a 100 MB
ALLOWED_EXTENSIONS = [".mp4", ".mov"]  # Define las extensiones de archivo permitidas
ALLOWED_CONTENT_TYPES = ["video/mp4", "video/quicktime"]  # Define los tipos MIME permitidos

app = FastAPI(title="ArchivaCloud P-11 API")  # Crea la aplicación FastAPI con un título identificador

app.add_middleware(  # Agrega middleware de CORS a la aplicación
    CORSMiddleware,  # Indica que se usará el middleware CORS
    allow_origins=[FRONTEND_ORIGIN],  # Permite peticiones solo desde el frontend configurado
    allow_credentials=True,  # Permite enviar credenciales si fueran necesarias
    allow_methods=["*"],  # Permite todos los métodos HTTP
    allow_headers=["*"],  # Permite todos los headers en las peticiones
)

s3_client = boto3.client(  # Crea el cliente de S3 usando boto3
    "s3",  # Indica que se usará el servicio Amazon S3
    region_name=AWS_REGION,  # Asigna la región configurada en variables de entorno
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),  # Obtiene la access key temporal desde el .env
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),  # Obtiene la secret key temporal desde el .env
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),  # Obtiene el token de sesión temporal de AWS Academy
    config=Config(  # Configura opciones avanzadas del cliente S3
        s3={"addressing_style": "virtual"},  # Usa el estilo virtual-hosted para acceder al bucket
        signature_version="s3v4"  # Usa la versión 4 de firma de AWS para URLs prefirmadas
    )
)


class PresignedUrlRequest(BaseModel):  # Modelo que valida los datos recibidos para crear la URL prefirmada
    fileName: str  # Nombre del archivo recibido desde el frontend
    fileType: str  # Tipo MIME del archivo
    fileSize: int  # Tamaño del archivo en bytes
    fileHash: str  # Hash SHA-256 calculado en el frontend


@app.get("/healthz")  # Endpoint para verificar si la API está funcionando
def healthz():  # Función que responde al endpoint de salud
    return {"status": "ok"}  # Devuelve una respuesta simple indicando que la API está activa


def sanitize_filename(filename: str) -> str:  # Función para limpiar y normalizar nombres de archivos
    filename = filename.strip()  # Elimina espacios al inicio y al final del nombre
    filename = filename.replace(" ", "_")  # Reemplaza espacios internos por guiones bajos
    filename = re.sub(r"[^a-zA-Z0-9._-]", "", filename)  # Elimina caracteres no permitidos
    return filename  # Devuelve el nombre limpio


def get_dynamodb_table():  # Función que obtiene la tabla DynamoDB
    dynamodb = boto3.resource(  # Crea un recurso DynamoDB usando boto3
        "dynamodb",  # Indica que se usará el servicio DynamoDB
        region_name=AWS_REGION,  # Usa la misma región configurada para AWS
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),  # Usa la access key temporal
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),  # Usa la secret key temporal
        aws_session_token=os.getenv("AWS_SESSION_TOKEN")  # Usa el token de sesión temporal
    )

    return dynamodb.Table("database_dynamo")  # Retorna la tabla DynamoDB llamada database_dynamo


def upload_dynamodb(item):  # Función que guarda información del archivo en DynamoDB
    table = get_dynamodb_table()  # Obtiene la tabla DynamoDB

    table.put_item(  # Inserta un nuevo registro en DynamoDB
        Item={  # Define los atributos que se guardarán
            "id_tabla": item["id_tabla"],  # Guarda la key del archivo como identificador principal
            "nombre_proyecto": item["nombre_proyecto"],  # Guarda el nombre del proyecto
            "descripcion": item["descripcion"],  # Guarda una descripción del archivo
            "presigned_url": item["presigned_url"],  # Guarda la URL prefirmada generada
            "key_s3": item["key_s3"]  # Guarda la key real del archivo en S3
        }
    )


def delete_dynamodb(id_tabla):  # Función que elimina un registro de DynamoDB
    table = get_dynamodb_table()  # Obtiene la tabla DynamoDB

    table.delete_item(  # Elimina un registro de la tabla
        Key={  # Define la clave primaria compuesta del registro a eliminar
            "id_tabla": id_tabla,  # Usa la key del archivo como clave de partición
            "nombre_proyecto": "ArchivaCloud P-11"  # Usa el nombre del proyecto como clave de ordenación
        }
    )


@app.post("/api/upload/presigned-url")  # Endpoint que genera una URL prefirmada para subir archivos a S3
def create_presigned_url(data: PresignedUrlRequest):  # Recibe y valida los datos enviados desde el frontend
    clean_name = sanitize_filename(data.fileName)  # Limpia el nombre del archivo recibido

    if not clean_name:  # Verifica que el nombre limpio no esté vacío
        raise HTTPException(status_code=400, detail="Nombre de archivo inválido")  # Devuelve error si el nombre es inválido

    extension = os.path.splitext(clean_name)[1].lower()  # Obtiene la extensión del archivo en minúsculas

    if extension not in ALLOWED_EXTENSIONS:  # Verifica si la extensión está permitida
        raise HTTPException(status_code=400, detail="Tipo de archivo no permitido")  # Devuelve error si la extensión no es válida

    if data.fileType not in ALLOWED_CONTENT_TYPES:  # Verifica si el tipo MIME está permitido
        raise HTTPException(status_code=400, detail="MIME type no permitido")  # Devuelve error si el MIME type no es válido

    if data.fileSize <= 0 or data.fileSize > MAX_FILE_SIZE:  # Valida que el archivo no esté vacío ni supere los 100 MB
        raise HTTPException(status_code=400, detail="El archivo supera el máximo permitido de 100 MB")  # Devuelve error por tamaño inválido

    if not data.fileHash or len(data.fileHash) != 64:  # Verifica que el hash SHA-256 tenga 64 caracteres
        raise HTTPException(status_code=400, detail="Hash SHA-256 inválido")  # Devuelve error si el hash no es válido

    unique_id = str(uuid.uuid4())  # Genera un identificador único para evitar colisiones de nombres
    key = f"uploads/{unique_id}-{clean_name}"  # Construye la ruta final que tendrá el archivo dentro del bucket S3

    try:  # Intenta generar la URL prefirmada y guardar los datos
        presigned_url = s3_client.generate_presigned_url(  # Genera una URL temporal para subir el archivo directamente a S3
            ClientMethod="put_object",  # Define que la URL permitirá subir un objeto
            Params={  # Parámetros necesarios para crear la URL prefirmada
                "Bucket": S3_BUCKET_NAME,  # Indica el bucket donde se subirá el archivo
                "Key": key,  # Indica la ruta/nombre del archivo dentro del bucket
                "ContentType": data.fileType,  # Asocia el tipo MIME correcto al archivo
                "Metadata": {  # Agrega metadatos personalizados al objeto
                    "sha256": data.fileHash  # Guarda el hash SHA-256 como metadata del archivo
                }
            },
            ExpiresIn=3600,  # Define que la URL expira en 3600 segundos, es decir, 1 hora
        )

        public_url = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"  # Construye una URL de referencia al objeto en S3

        upload_dynamodb({  # Guarda la información del archivo en DynamoDB
            "id_tabla": key,  # Usa la key S3 como identificador
            "nombre_proyecto": "ArchivaCloud P-11",  # Guarda el nombre del proyecto
            "descripcion": f"Archivo {clean_name} con URL prefirmada de S3",  # Guarda una descripción del archivo
            "presigned_url": presigned_url,  # Guarda la URL prefirmada generada
            "key_s3": key  # Guarda la key del archivo en S3
        })

        return {  # Devuelve la información necesaria al frontend
            "presignedUrl": presigned_url,  # URL temporal que el frontend usará para subir el archivo
            "key": key,  # Key del archivo dentro del bucket
            "publicUrl": public_url,  # URL de referencia del archivo
        }

    except Exception:  # Captura cualquier error ocurrido durante la generación de URL o guardado en DynamoDB
        raise HTTPException(status_code=500, detail="No se pudo generar la URL de subida")  # Devuelve error interno al frontend


@app.get("/api/files")  # Endpoint que lista los archivos almacenados en S3
def list_files():  # Función que obtiene archivos desde el bucket
    try:  # Intenta listar los archivos del bucket
        response = s3_client.list_objects_v2(  # Solicita a S3 los objetos almacenados
            Bucket=S3_BUCKET_NAME,  # Indica el bucket que se va a consultar
            Prefix="uploads/"  # Filtra solo los archivos dentro del prefijo uploads/
        )

        files = []  # Lista donde se guardará la información de los archivos
        name_counter = {}  # Diccionario para contar nombres repetidos
        hash_counter = {}  # Diccionario para contar hashes repetidos

        for obj in response.get("Contents", []):  # Recorre cada objeto encontrado en S3
            if obj["Key"].endswith("/"):  # Verifica si el objeto corresponde a una carpeta virtual
                continue  # Omite carpetas virtuales y continúa con el siguiente objeto

            head = s3_client.head_object(  # Obtiene metadatos del archivo en S3
                Bucket=S3_BUCKET_NAME,  # Indica el bucket donde está el archivo
                Key=obj["Key"]  # Indica la key específica del archivo
            )

            metadata = head.get("Metadata", {})  # Obtiene los metadatos personalizados del archivo
            file_hash = metadata.get("sha256")  # Obtiene el hash SHA-256 guardado como metadata

            stored_name = obj["Key"].replace("uploads/", "", 1)  # Obtiene el nombre almacenado quitando el prefijo uploads/
            visible_name = stored_name  # Define inicialmente el nombre visible como el nombre almacenado

            if "-" in stored_name:  # Verifica si el nombre contiene guiones
                parts = stored_name.split("-", 5)  # Separa el nombre para intentar quitar el UUID
                if len(parts) == 6:  # Verifica que la separación coincida con el formato del UUID
                    visible_name = parts[5]  # Deja solo el nombre original del archivo

            normalized_name = visible_name.lower()  # Normaliza el nombre a minúsculas para detectar duplicados
            name_counter[normalized_name] = name_counter.get(normalized_name, 0) + 1  # Cuenta cuántas veces aparece ese nombre

            if file_hash:  # Verifica si el archivo tiene hash guardado
                hash_counter[file_hash] = hash_counter.get(file_hash, 0) + 1  # Cuenta cuántas veces aparece ese hash

            download_url = s3_client.generate_presigned_url(  # Genera una URL temporal para descargar el archivo
                ClientMethod="get_object",  # Define que la URL permitirá obtener/descargar un objeto
                Params={  # Parámetros para generar la URL de descarga
                    "Bucket": S3_BUCKET_NAME,  # Indica el bucket donde está el archivo
                    "Key": obj["Key"],  # Indica la key del archivo a descargar
                    "ResponseContentDisposition": f'attachment; filename="{visible_name}"'  # Fuerza descarga con el nombre visible
                },
                ExpiresIn=3600,  # Define que la URL de descarga expira en 1 hora
            )

            files.append({  # Agrega el archivo procesado a la lista de respuesta
                "key": obj["Key"],  # Key real del archivo en S3
                "name": visible_name,  # Nombre visible para mostrar en el frontend
                "storedName": stored_name,  # Nombre real almacenado en S3
                "size": obj["Size"],  # Tamaño del archivo en bytes
                "lastModified": obj["LastModified"].isoformat(),  # Fecha de última modificación en formato ISO
                "url": download_url,  # URL temporal para descargar el archivo
                "sha256": file_hash,  # Hash SHA-256 del archivo
                "isDuplicateName": False,  # Indicador inicial de duplicado por nombre
                "isDuplicateHash": False  # Indicador inicial de duplicado por hash
            })

        for file in files:  # Recorre nuevamente la lista para marcar duplicados
            normalized_name = file["name"].lower()  # Normaliza el nombre del archivo

            if name_counter.get(normalized_name, 0) > 1:  # Verifica si el nombre aparece más de una vez
                file["isDuplicateName"] = True  # Marca el archivo como duplicado por nombre

            if file["sha256"] and hash_counter.get(file["sha256"], 0) > 1:  # Verifica si el hash aparece más de una vez
                file["isDuplicateHash"] = True  # Marca el archivo como duplicado por contenido/hash

        return {"files": files}  # Devuelve la lista completa de archivos al frontend

    except Exception as e:  # Captura errores al listar archivos
        print("ERROR LISTANDO ARCHIVOS:", e)  # Muestra el error en consola para depuración
        raise HTTPException(status_code=500, detail="No se pudo listar los archivos")  # Devuelve error interno al frontend


@app.delete("/api/files/{key:path}")  # Endpoint que elimina un archivo según su key
def delete_file(key: str):  # Recibe la key del archivo enviada desde el frontend
    try:  # Intenta eliminar el archivo de S3 y DynamoDB
        decoded_key = unquote(key)  # Decodifica la key para recuperar caracteres especiales

        if not decoded_key.startswith("uploads/"):  # Valida que la key pertenezca al directorio permitido
            raise HTTPException(status_code=400, detail="Key inválida")  # Devuelve error si la key no es válida

        s3_client.delete_object(  # Elimina el objeto desde el bucket S3
            Bucket=S3_BUCKET_NAME,  # Indica el bucket donde está el archivo
            Key=decoded_key  # Indica la key del archivo a eliminar
        )

        delete_dynamodb(decoded_key)  # Elimina de DynamoDB el registro asociado al archivo

        return {  # Devuelve respuesta exitosa al frontend
            "message": "Archivo eliminado correctamente de S3 y DynamoDB",  # Mensaje de confirmación
            "key": decoded_key  # Devuelve la key eliminada
        }

    except HTTPException:  # Captura errores HTTP lanzados manualmente
        raise  # Relanza el error HTTP original

    except Exception:  # Captura cualquier otro error inesperado
        raise HTTPException(status_code=500, detail="No se pudo eliminar el archivo")  # Devuelve error interno al frontend