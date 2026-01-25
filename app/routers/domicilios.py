from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, models, schemas, auth, database

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
