from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ... import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/eventos/pesos",
    tags=["eventos-pesos"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.PesoDetailResponse])
async def get_pesos(skip: int = 0, limit: int = 100,
                    current_user: models.Usuario = Depends(auth.get_current_user),
                    db: Session = Depends(database.get_db)):
    """Get all peso events for user's bovinos with detailed information"""
    return crud.get_pesos_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/bovino/{bovino_id}", response_model=List[schemas.PesoDetailResponse])
async def get_pesos_by_bovino(bovino_id: str, skip: int = 0, limit: int = 100,
                               current_user: models.Usuario = Depends(auth.get_current_user),
                               db: Session = Depends(database.get_db)):
    """Get peso events for a specific bovino"""
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return crud.get_pesos_by_bovino(db, bovino_id=bovino_id, skip=skip, limit=limit)

@router.get("/{evento_id}", response_model=schemas.PesoDetailResponse)
async def get_peso(evento_id: str,
                   current_user: models.Usuario = Depends(auth.get_current_user),
                   db: Session = Depends(database.get_db)):
    """Get a specific peso event with details"""
    peso = crud.get_peso_detail(db, evento_id=evento_id)
    if peso is None:
        raise HTTPException(status_code=404, detail="Peso event not found")

    # Verify ownership through bovino
    db_bovino = crud.get_bovino(db, bovino_id=peso["bovino_id"])
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return peso
