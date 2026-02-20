from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import os
import uuid as uuid_lib
from .. import crud, models, schemas, auth, database
from ..s3 import s3_client, S3_BUCKET_NAME

router = APIRouter(
    prefix="/predios",
    tags=["predios"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.PredioResponse])
async def read_predios(skip: int = 0, limit: int = 100,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    return crud.get_predios(db, skip=skip, limit=limit, usuario_id=str(current_user.id))

@router.get("/{predio_id}", response_model=schemas.PredioResponse)
async def read_predio(predio_id: str,
                      current_user: models.Usuario = Depends(auth.get_current_user),
                      db: Session = Depends(database.get_db)):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")
    if db_predio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this predio")
    return db_predio

@router.post("/", response_model=schemas.PredioResponse)
async def create_predio(predio: schemas.PredioCreate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    return crud.create_predio(db=db, predio=predio, usuario_id=str(current_user.id))

@router.put("/{predio_id}", response_model=schemas.PredioResponse)
async def update_predio(predio_id: str, predio: schemas.PredioUpdate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")
    if db_predio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this predio")
    return crud.update_predio(db=db, predio_id=predio_id, predio=predio)

@router.delete("/{predio_id}", response_model=schemas.PredioResponse)
async def delete_predio(predio_id: str,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")
    if db_predio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this predio")
    return crud.delete_predio(db=db, predio_id=predio_id)

@router.get("/{predio_id}/bovinos", response_model=List[schemas.BovinoResponse])
async def get_bovinos_by_predio(
    predio_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")
    if db_predio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view bovinos for this predio")
    return crud.get_bovinos_by_predio(db, predio_id=predio_id, skip=skip, limit=limit)

@router.post("/{predio_id}/upload-document", response_model=schemas.DocumentoResponse)
async def upload_predio_document(
    predio_id: str,
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")
    if db_predio.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload documents for this predio")

    # Replace existing document for this predio if one already exists
    prefix = f"{current_user.id}/predio/{predio_id}/"
    existing = crud.get_documento_by_storage_prefix(db, prefix=prefix)
    if existing:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=existing.storage_key)
        except Exception:
            pass
        crud.delete_documento(db=db, doc_id=str(existing.id))

    file_extension = os.path.splitext(file.filename)[1]
    storage_key = f"{current_user.id}/predio/{predio_id}/{uuid_lib.uuid4()}{file_extension}"

    try:
        s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, storage_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

    doc_data = {
        "usuario_id": current_user.id,
        "doc_type": schemas.DocTypeEnum.predio,
        "storage_key": storage_key,
        "original_filename": file.filename
    }

    return crud.create_documento(db=db, documento_data=doc_data)
