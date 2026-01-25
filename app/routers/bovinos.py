from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Annotated
from .. import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/bovinos",
    tags=["bovinos"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.BovinoResponse])
async def read_bovinos(skip: int = 0, limit: int = 100,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    return crud.get_bovinos(db, user_id=current_user.id, skip=skip, limit=limit)

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
async def update_bovino(bovino_id: str, bovino: schemas.BovinoCreate,
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
