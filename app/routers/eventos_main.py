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
    # Verify bovino exists
    bovino_id = evento.data.get('bovino_id')
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if db_bovino is None:
        raise HTTPException(status_code=404, detail="Bovino not found")

    # Define which events require veterinarian credentials
    veterinary_events = ['vacunacion', 'desparasitacion', 'laboratorio', 'enfermedad', 'tratamiento']

    if evento.type in veterinary_events:
        # Veterinary events: ONLY veterinarians can create, for ANY bovino
        if current_user.rol != 'veterinario':
            raise HTTPException(
                status_code=403,
                detail=f"Only users with role 'veterinario' can create {evento.type} events"
            )
        # Pass usuario_id; the DB function resolves it to veterinarios.id internally
        evento.data['usuario_id'] = str(current_user.id)
    else:
        # Non-veterinary events (peso, dieta, compraventa, traslado):
        # Only the owner can create these events for their bovinos
        if db_bovino.usuario_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to add events to this bovino. Only the owner can create this event type."
            )

    db_evento = crud.create_evento(db, evento)
    if db_evento is None:
        raise HTTPException(status_code=500, detail="Failed to create event")
    return db_evento
