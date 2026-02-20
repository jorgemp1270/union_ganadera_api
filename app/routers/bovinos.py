from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Annotated
import os
import uuid as uuid_lib
from .. import crud, models, schemas, auth, database
from ..s3 import s3_client, s3_public_client, S3_BUCKET_NAME

router = APIRouter(
    prefix="/bovinos",
    tags=["bovinos"],
    dependencies=[Depends(auth.get_current_user)]
)

def _with_nariz_url(bovino: models.Bovino) -> dict:
    """Convert a Bovino ORM object to a dict with a presigned nariz_url if available."""
    data = {c.name: getattr(bovino, c.name) for c in bovino.__table__.columns}
    data["nariz_url"] = None
    if bovino.nariz_storage_key:
        try:
            data["nariz_url"] = s3_public_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": S3_BUCKET_NAME, "Key": bovino.nariz_storage_key},
                ExpiresIn=3600
            )
        except Exception:
            pass
    return data

@router.get("/", response_model=List[schemas.BovinoResponse])
async def read_bovinos(skip: int = 0, limit: int = 100,
                       predio_id: str = None,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    if predio_id:
        db_predio = crud.get_predio(db, predio_id=predio_id)
        if db_predio is None:
            raise HTTPException(status_code=404, detail="Predio not found")
        if db_predio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view bovinos for this predio")
    bovinos = crud.get_bovinos(db, user_id=current_user.id, skip=skip, limit=limit, predio_id=predio_id)
    return [_with_nariz_url(b) for b in bovinos]

@router.get("/search", response_model=schemas.BovinoResponse)
async def search_bovino(
    arete_barcode: str = None,
    arete_rfid: str = None,
    nombre: str = None,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Search for a bovino by arete_barcode, arete_rfid, or nombre.
    Only accessible to veterinarians.
    """
    if current_user.rol != 'veterinario':
        raise HTTPException(status_code=403, detail="Only veterinarians can search for bovinos")

    if not any([arete_barcode, arete_rfid, nombre]):
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one search parameter: arete_barcode, arete_rfid, or nombre"
        )

    bovino = crud.search_bovino(
        db=db,
        arete_barcode=arete_barcode,
        arete_rfid=arete_rfid,
        nombre=nombre
    )

    if not bovino:
        raise HTTPException(status_code=404, detail="Bovino not found")

    return _with_nariz_url(bovino)

@router.get("/{bovino_id}", response_model=schemas.BovinoResponse)
async def read_bovino(bovino_id: str,
                      current_user: models.Usuario = Depends(auth.get_current_user),
                      db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this bovino")
    return _with_nariz_url(db_bovino)

@router.post("/", response_model=schemas.BovinoResponse)
async def create_bovino(bovino: schemas.BovinoCreate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    if bovino.predio_id:
        db_predio = crud.get_predio(db, predio_id=str(bovino.predio_id))
        if db_predio is None:
            raise HTTPException(status_code=404, detail="Predio not found")
        if db_predio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to assign this predio")
    db_bovino = crud.create_bovino(db=db, bovino=bovino, user_id=current_user.id)
    return _with_nariz_url(db_bovino)

@router.put("/{bovino_id}", response_model=schemas.BovinoResponse)
async def update_bovino(bovino_id: str, bovino: schemas.BovinoUpdate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this bovino")
    if bovino.predio_id:
        db_predio = crud.get_predio(db, predio_id=str(bovino.predio_id))
        if db_predio is None:
            raise HTTPException(status_code=404, detail="Predio not found")
        if db_predio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to assign this predio")
    db_bovino = crud.update_bovino(db=db, bovino_id=bovino_id, bovino=bovino)
    return _with_nariz_url(db_bovino)

@router.delete("/{bovino_id}", response_model=schemas.BovinoResponse)
async def delete_bovino(bovino_id: str,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this bovino")
    return crud.delete_bovino(db=db, bovino_id=bovino_id)

@router.post("/{bovino_id}/upload-nose-photo", response_model=schemas.BovinoResponse)
async def upload_nose_photo(
    bovino_id: str,
    file: UploadFile = File(...),
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    # Verify bovino exists and belongs to user
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to upload photo for this bovino")

    # Delete old nariz photo from S3 if one exists
    if db_bovino.nariz_storage_key:
        try:
            s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=db_bovino.nariz_storage_key)
        except Exception:
            pass  # Don't block the upload if old file deletion fails

    # Generate storage key: {user_id}/nariz/{bovino_id}/{uuid}.{extension}
    file_extension = os.path.splitext(file.filename)[1]
    storage_key = f"{current_user.id}/nariz/{bovino_id}/{uuid_lib.uuid4()}{file_extension}"

    # Upload to S3
    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            storage_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not upload file: {str(e)}")

    # Update bovino with storage key
    db_bovino.nariz_storage_key = storage_key
    db.commit()
    db.refresh(db_bovino)

    return db_bovino
