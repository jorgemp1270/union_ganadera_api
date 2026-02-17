from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Annotated
import boto3
import os
import uuid as uuid_lib
from .. import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/bovinos",
    tags=["bovinos"],
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

@router.get("/", response_model=List[schemas.BovinoResponse])
async def read_bovinos(skip: int = 0, limit: int = 100,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    return crud.get_bovinos(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/search", response_model=schemas.BovinoResponse)
async def search_bovino(
    arete_barcode: str = None,
    arete_rfid: str = None,
    nariz_storage_key: str = None,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Search for a bovino by arete_barcode, arete_rfid, or nariz_storage_key.
    Only accessible to veterinarians.
    """
    if current_user.rol != 'veterinario':
        raise HTTPException(status_code=403, detail="Only veterinarians can search for bovinos")

    if not any([arete_barcode, arete_rfid, nariz_storage_key]):
        raise HTTPException(
            status_code=400,
            detail="Must provide at least one search parameter: arete_barcode, arete_rfid, or nariz_storage_key"
        )

    bovino = crud.search_bovino(
        db=db,
        arete_barcode=arete_barcode,
        arete_rfid=arete_rfid,
        nariz_storage_key=nariz_storage_key
    )

    if not bovino:
        raise HTTPException(status_code=404, detail="Bovino not found")

    return bovino

@router.get("/{bovino_id}", response_model=schemas.BovinoResponse)
async def read_bovino(bovino_id: str,
                      current_user: models.Usuario = Depends(auth.get_current_user),
                      db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this bovino")
    return db_bovino

@router.post("/", response_model=schemas.BovinoResponse)
async def create_bovino(bovino: schemas.BovinoCreate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    return crud.create_bovino(db=db, bovino=bovino, user_id=current_user.id)

@router.put("/{bovino_id}", response_model=schemas.BovinoResponse)
async def update_bovino(bovino_id: str, bovino: schemas.BovinoUpdate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this bovino")
    return crud.update_bovino(db=db, bovino_id=bovino_id, bovino=bovino)

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
