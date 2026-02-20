from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid as uuid_lib
from .. import crud, models, schemas, auth, database
from ..s3 import s3_client, S3_BUCKET_NAME

router = APIRouter(
    prefix="/domicilios",
    tags=["domicilios"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.DomicilioResponse])
async def read_domicilios(skip: int = 0, limit: int = 100,
                          current_user: models.Usuario = Depends(auth.get_current_user),
                          db: Session = Depends(database.get_db)):
    return crud.get_domicilios_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/{domicilio_id}", response_model=schemas.DomicilioResponse)
async def read_domicilio(domicilio_id: str,
                         current_user: models.Usuario = Depends(auth.get_current_user),
                         db: Session = Depends(database.get_db)):
    db_domicilio = crud.get_domicilio(db, domicilio_id=domicilio_id)
    if db_domicilio is None:
        raise HTTPException(status_code=404, detail="Domicilio not found")
    if db_domicilio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this domicilio")
    return db_domicilio

@router.post("/", response_model=schemas.DomicilioResponse)
async def create_domicilio(domicilio: schemas.DomicilioCreate,
                           current_user: models.Usuario = Depends(auth.get_current_user),
                           db: Session = Depends(database.get_db)):
    return crud.create_domicilio(db=db, domicilio=domicilio, user_id=current_user.id)

@router.put("/{domicilio_id}", response_model=schemas.DomicilioResponse)
async def update_domicilio(domicilio_id: str, domicilio: schemas.DomicilioUpdate,
                           current_user: models.Usuario = Depends(auth.get_current_user),
                           db: Session = Depends(database.get_db)):
    db_domicilio = crud.get_domicilio(db, domicilio_id=domicilio_id)
    if db_domicilio is None:
        raise HTTPException(status_code=404, detail="Domicilio not found")
    if db_domicilio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this domicilio")
    return crud.update_domicilio(db=db, domicilio_id=domicilio_id, domicilio=domicilio)

@router.delete("/{domicilio_id}", response_model=schemas.DomicilioResponse)
async def delete_domicilio(domicilio_id: str,
                           current_user: models.Usuario = Depends(auth.get_current_user),
                           db: Session = Depends(database.get_db)):
    db_domicilio = crud.get_domicilio(db, domicilio_id=domicilio_id)
    if db_domicilio is None:
        raise HTTPException(status_code=404, detail="Domicilio not found")
    if db_domicilio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this domicilio")
    return crud.delete_domicilio(db=db, domicilio_id=domicilio_id)

@router.post("/{domicilio_id}/upload-document", response_model=schemas.DocumentoResponse)
async def upload_domicilio_document(
    domicilio_id: str,
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_domicilio = crud.get_domicilio(db, domicilio_id=domicilio_id)
    if db_domicilio is None:
        raise HTTPException(status_code=404, detail="Domicilio not found")
    if db_domicilio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload documents for this domicilio")

    # Replace existing comprobante for this domicilio if one already exists
    prefix = f"{current_user.id}/comprobante_domicilio/{domicilio_id}/"
    existing = crud.get_documento_by_storage_prefix(db, prefix=prefix)
    if existing:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=existing.storage_key)
        except Exception:
            pass
        crud.delete_documento(db=db, doc_id=str(existing.id))

    file_extension = os.path.splitext(file.filename)[1]
    storage_key = f"{current_user.id}/comprobante_domicilio/{domicilio_id}/{uuid_lib.uuid4()}{file_extension}"

    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, storage_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

    doc_data = {
        "usuario_id": current_user.id,
        "doc_type": schemas.DocTypeEnum.comprobante_domicilio,
        "storage_key": storage_key,
        "original_filename": file.filename
    }

    return crud.create_documento(db=db, documento_data=doc_data)
