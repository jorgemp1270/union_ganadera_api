from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from .. import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/eventos",
    tags=["eventos"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.post("/", response_model=schemas.EventoResponse)
async def create_evento(evento: schemas.EventoCreateRequest,
                        current_user: models.Usuario = Depends(auth.get_current_user),
                        db: Session = Depends(database.get_db)):
    # Verify bovino belongs to user
    bovino_id = evento.data.get('bovino_id')
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")
    if db_bovino.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to add events to this bovino")

    return crud.create_evento(db=db, evento_request=evento)
