from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from ... import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/eventos/remisiones",
    tags=["eventos-remisiones"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/", response_model=List[schemas.RemisionDetailResponse])
async def get_remisiones(skip: int = 0, limit: int = 100,
                         current_user: models.Usuario = Depends(auth.get_current_user),
                         db: Session = Depends(database.get_db)):
    if current_user.rol == 'veterinario':
        return crud.get_remisiones_all(db, skip=skip, limit=limit)
    return crud.get_remisiones_by_user(db, user_id=current_user.id, skip=skip, limit=limit)

@router.get("/bovino/{bovino_id}", response_model=List[schemas.RemisionDetailResponse])
async def get_remisiones_by_bovino(bovino_id: str, skip: int = 0, limit: int = 100,
                                   current_user: models.Usuario = Depends(auth.get_current_user),
                                   db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if current_user.rol != 'veterinario' and db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_remisiones_by_bovino(db, bovino_id=bovino_id, skip=skip, limit=limit)

@router.get("/enfermedad/{enfermedad_id}", response_model=List[schemas.RemisionDetailResponse])
async def get_remisiones_by_enfermedad(enfermedad_id: str, skip: int = 0, limit: int = 100,
                                       current_user: models.Usuario = Depends(auth.get_current_user),
                                       db: Session = Depends(database.get_db)):
    evento_id = db.execute(
        text("SELECT evento_id FROM enfermedades WHERE id = :eid"),
        {"eid": enfermedad_id}
    ).scalar()
    if evento_id is None:
        raise HTTPException(status_code=404, detail="Enfermedad not found")
    enfermedad = crud.get_enfermedad_detail(db, evento_id=str(evento_id))
    if enfermedad is None:
        raise HTTPException(status_code=404, detail="Enfermedad not found")
    db_bovino = crud.get_bovino(db, bovino_id=str(enfermedad["bovino_id"]))
    if db_bovino is None or (current_user.rol != 'veterinario' and db_bovino.usuario_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    return crud.get_remisiones_by_enfermedad(db, enfermedad_id=enfermedad_id, skip=skip, limit=limit)

@router.get("/{evento_id}", response_model=schemas.RemisionDetailResponse)
async def get_remision(evento_id: str,
                       current_user: models.Usuario = Depends(auth.get_current_user),
                       db: Session = Depends(database.get_db)):
    remision = crud.get_remision_detail(db, evento_id=evento_id)
    if remision is None:
        raise HTTPException(status_code=404, detail="Remision event not found")
    db_bovino = crud.get_bovino(db, bovino_id=remision["bovino_id"])
    if current_user.rol != 'veterinario' and db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return remision
