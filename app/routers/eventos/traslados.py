from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ... import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/eventos/traslados",
    tags=["eventos-traslados"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.TrasladoDetailResponse])
async def get_traslados(skip: int = 0, limit: int = 100,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    return crud.get_traslados_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/bovino/{bovino_id}", response_model=List[schemas.TrasladoDetailResponse])
async def get_traslados_by_bovino(bovino_id: str, skip: int = 0, limit: int = 100,
                                   current_user: models.Usuario = Depends(auth.get_current_user),
                                   db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_traslados_by_bovino(db, bovino_id=bovino_id, skip=skip, limit=limit)

@router.get("/{evento_id}", response_model=schemas.TrasladoDetailResponse)
async def get_traslado(evento_id: str,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    traslado = crud.get_traslado_detail(db, evento_id=evento_id)
    if traslado is None:
        raise HTTPException(status_code=404, detail="Traslado event not found")
    db_bovino = crud.get_bovino(db, bovino_id=traslado["bovino_id"])
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return traslado
