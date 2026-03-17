from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Annotated
from datetime import date
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
    """Convert a Bovino ORM object to a dict with a presigned nariz_url. No parent resolution."""
    data = {c.name: getattr(bovino, c.name) for c in bovino.__table__.columns}
    data["nariz_url"] = None
    data["madre"] = None
    data["padre"] = None
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


def _resolve_parent(db: Session, parent_id, current_user_id) -> dict | None:
    """Resolve a madre_id/padre_id to a BovinoParentPublic projection.

    Always returns only the public-safe minimal fields regardless of ownership.
    If the parent belongs to a different user, only the safe fields are returned.
    If owned by the requesting user, still returns the same minimal shape here —
    the full detail is available via GET /bovinos/{parent_id}.
    Returns None if parent_id is None or the parent no longer exists.
    """
    if parent_id is None:
        return None
    parent = crud.get_bovino(db, bovino_id=str(parent_id))
    if parent is None:
        return None
    # Return minimal projection — includes an ownership flag so the client
    # knows whether to offer a navigation link to the full record
    return {
        "id": parent.id,
        "folio": parent.folio,
        "raza_dominante": parent.raza_dominante,
        "fecha_nac": parent.fecha_nac,
        "sexo": parent.sexo,
    }


def _with_parents(bovino: models.Bovino, db: Session, current_user_id) -> dict:
    """Full detail response: nariz_url + resolved madre/padre projections."""
    data = _with_nariz_url(bovino)
    data["madre"] = _resolve_parent(db, bovino.madre_id, current_user_id)
    data["padre"] = _resolve_parent(db, bovino.padre_id, current_user_id)
    return data

@router.get("/", response_model=List[schemas.BovinoResponse])
async def read_bovinos(skip: int = 0, limit: int = 100,
                       instalacion_id: str = None,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    if instalacion_id:
        db_instalacion = db.query(models.Instalacion).filter(models.Instalacion.id == instalacion_id).first()
        if db_instalacion is None:
            raise HTTPException(status_code=404, detail="Instalacion not found")
        if db_instalacion.usuario_id != current_user.id and current_user.rol not in ["administrador", "superadministrador", "inspector"]:
            raise HTTPException(status_code=403, detail="Not authorized to view bovinos for this instalacion")
    bovinos = crud.get_bovinos(db, user_id=current_user.id, skip=skip, limit=limit, instalacion_id=instalacion_id)
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
    return _with_parents(db_bovino, db, current_user.id)

@router.post("/", response_model=schemas.BovinoResponse)
async def create_bovino(bovino: schemas.BovinoCreate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    """
    Create a new bovino.
    If instalacion_id is provided, validates:
    - Instalacion exists and belongs to user
    - Instalacion is approved (status = 'activa' AND active = True)
    - Instalacion is not expired (fecha_vencimiento > today or null for non-UPP/PSG)
    """
    if bovino.instalacion_id:
        db_instalacion = db.query(models.Instalacion).filter(
            models.Instalacion.id == bovino.instalacion_id
        ).first()
        if db_instalacion is None:
            raise HTTPException(status_code=404, detail="Instalacion not found")
        if db_instalacion.usuario_id != current_user.id and current_user.rol not in ["administrador", "superadministrador", "inspector"]:
            raise HTTPException(status_code=403, detail="Not authorized to use this instalacion")
        
        # Validate instalacion is active and approved
        if db_instalacion.status != models.InstalacionStatusEnum.activa or not db_instalacion.active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot create bovino: Instalacion is not active or not approved by admin"
            )
        
        # Validate instalacion is not expired (for UPP/PSG types)
        if db_instalacion.facility_type in [models.FacilityTypeEnum.UPP, models.FacilityTypeEnum.PSG]:
            if db_instalacion.fecha_vencimiento and db_instalacion.fecha_vencimiento < date.today():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Cannot create bovino: Instalacion license has expired"
                )
    
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
    # instalacion_id updates are not accepted here — use a traslado event instead
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
