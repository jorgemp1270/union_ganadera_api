from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/predios",
    tags=["predios"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.PredioResponse])
async def read_predios(skip: int = 0, limit: int = 100,
                       domicilio_id: Optional[str] = None,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    # If domicilio_id is provided, verify it belongs to the user
    if domicilio_id:
        db_domicilio = crud.get_domicilio(db, domicilio_id=domicilio_id)
        if db_domicilio is None:
            raise HTTPException(status_code=404, detail="Domicilio not found")
        if db_domicilio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view predios for this domicilio")

    return crud.get_predios(db, skip=skip, limit=limit, domicilio_id=domicilio_id)

@router.get("/{predio_id}", response_model=schemas.PredioResponse)
async def read_predio(predio_id: str,
                      current_user: models.Usuario = Depends(auth.get_current_user),
                      db: Session = Depends(database.get_db)):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")

    # Verify predio belongs to user through domicilio
    if db_predio.domicilio_id:
        db_domicilio = crud.get_domicilio(db, domicilio_id=db_predio.domicilio_id)
        if db_domicilio and db_domicilio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to view this predio")

    return db_predio

@router.post("/", response_model=schemas.PredioResponse)
async def create_predio(predio: schemas.PredioCreate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    # Verify domicilio belongs to user if provided
    if predio.domicilio_id:
        db_domicilio = crud.get_domicilio(db, domicilio_id=str(predio.domicilio_id))
        if db_domicilio is None:
            raise HTTPException(status_code=404, detail="Domicilio not found")
        if db_domicilio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to create predio for this domicilio")

    return crud.create_predio(db=db, predio=predio)

@router.put("/{predio_id}", response_model=schemas.PredioResponse)
async def update_predio(predio_id: str, predio: schemas.PredioUpdate,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")

    # Verify ownership through domicilio
    if db_predio.domicilio_id:
        db_domicilio = crud.get_domicilio(db, domicilio_id=db_predio.domicilio_id)
        if db_domicilio and db_domicilio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to update this predio")

    # If updating domicilio_id, verify new domicilio belongs to user
    if predio.domicilio_id:
        db_new_domicilio = crud.get_domicilio(db, domicilio_id=str(predio.domicilio_id))
        if db_new_domicilio is None:
            raise HTTPException(status_code=404, detail="New domicilio not found")
        if db_new_domicilio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to assign predio to this domicilio")

    return crud.update_predio(db=db, predio_id=predio_id, predio=predio)

@router.delete("/{predio_id}", response_model=schemas.PredioResponse)
async def delete_predio(predio_id: str,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    db_predio = crud.get_predio(db, predio_id=predio_id)
    if db_predio is None:
        raise HTTPException(status_code=404, detail="Predio not found")

    # Verify ownership through domicilio
    if db_predio.domicilio_id:
        db_domicilio = crud.get_domicilio(db, domicilio_id=db_predio.domicilio_id)
        if db_domicilio and db_domicilio.usuario_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this predio")

    return crud.delete_predio(db=db, predio_id=predio_id)
