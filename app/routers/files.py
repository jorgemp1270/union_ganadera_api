from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
import os
import uuid
from .. import crud, models, schemas, auth, database
from ..s3 import s3_client, s3_public_client, S3_BUCKET_NAME

router = APIRouter(
    prefix="/files",
    tags=["files"],
    dependencies=[Depends(auth.get_current_user)]
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
            download_url = s3_public_client.generate_presigned_url(
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
    doc_type: schemas.DocTypeEnum = Form(...),
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Replace existing document of the same type if one already exists
    existing = crud.get_documento_by_user_and_type(db, user_id=str(current_user.id), doc_type=doc_type)
    if existing:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=existing.storage_key)
        except Exception:
            pass
        crud.delete_documento(db=db, doc_id=str(existing.id))

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

@router.delete("/{doc_id}", response_model=schemas.DocumentoResponse)
async def delete_document(
    doc_id: str,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_doc = crud.get_documento(db, doc_id=doc_id)
    if db_doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    if db_doc.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this document")

    # Delete from S3
    try:
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=db_doc.storage_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not delete file from storage: {str(e)}")

    return crud.delete_documento(db=db, doc_id=doc_id)
