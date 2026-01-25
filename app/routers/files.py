from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
import boto3
import os
import uuid
from .. import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(auth.get_current_user)]
)

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
)

@router.get("/", response_model=list[schemas.DocumentoResponse])
def list_documents(skip: int = 0, limit: int = 100,
                   current_user: models.Usuario = Depends(auth.get_current_user),
                   db: Session = Depends(database.get_db)):
    documentos = crud.get_documentos_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

    # Generate presigned URLs for each document (valid for 1 hour)
    result = []
    for doc in documentos:
        try:
            download_url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET_NAME, 'Key': doc.storage_key},
                ExpiresIn=3600  # 1 hour
            )
        except Exception as e:
            download_url = None

        result.append({
            "id": doc.id,
            "doc_type": doc.doc_type,
            "original_filename": doc.original_filename,
            "created_at": doc.created_at,
            "authored": doc.authored,
            "download_url": download_url
        })

    return result

@router.post("/upload", response_model=schemas.DocumentoResponse)
async def upload_file(
    doc_type: schemas.DocTypeEnum,
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    print("=== FILE UPLOAD DEBUG ===")
    print(f"doc_type received: {doc_type}")
    print(f"doc_type type: {type(doc_type)}")
    print(f"file: {file}")
    print(f"file.filename: {file.filename}")
    print(f"file.content_type: {file.content_type}")
    print(f"current_user: {current_user.id}")
    print("========================")

    file_extension = os.path.splitext(file.filename)[1]
    storage_key = f"{current_user.id}/{doc_type.value}/{uuid.uuid4()}{file_extension}"

    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            storage_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

    doc_data = {
        "usuario_id": current_user.id,
        "doc_type": doc_type,
        "storage_key": storage_key,
        "original_filename": file.filename
    }

    return crud.create_documento(db=db, documento_data=doc_data)
