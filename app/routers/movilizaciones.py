from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, database, auth, models
from ..crud_movilizaciones import (
    create_movilizacion, get_movilizaciones, get_movilizacion,
    approve_movilizacion, load_movilizacion, inspect_movilizacion,
    arrive_movilizacion, complete_movilizacion, cancel_movilizacion,
    vincular_documento_movilizacion, validar_documentos_movilizacion
)

router = APIRouter(
    prefix="/movilizaciones",
    tags=["Movilizaciones"]
)

@router.post("/", response_model=schemas.MovilizacionResponse)
def create_movilizacion_endpoint(
    movilizacion: schemas.MovilizacionCreate,
    current_user: models.Usuario = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Crear una solicitud de movilización.
    """
    return create_movilizacion(db=db, movilizacion=movilizacion, usuario_id=str(current_user.id))

@router.get("/", response_model=List[schemas.MovilizacionResponse])
def read_movilizaciones(
    skip: int = 0, limit: int = 100,
    usuario_id: str = None,
    estado: str = None,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Obtener listado de movilizaciones.
    Si eres 'usuario', solo ves las tuyas a menos que especifiques lo contrario (faltaría check de rol).
    """
    # Si es usuario normal, forzar filtro a sus propias movilizaciones
    if current_user.rol == 'usuario':
        usuario_id = str(current_user.id)
        
    return get_movilizaciones(db=db, skip=skip, limit=limit, usuario_id=usuario_id, estado=estado)

@router.get("/{movilizacion_id}", response_model=schemas.MovilizacionResponse)
def read_movilizacion(
    movilizacion_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    mov = get_movilizacion(db=db, movilizacion_id=movilizacion_id)
    if not mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    return mov

@router.put("/{movilizacion_id}/approve", response_model=schemas.MovilizacionResponse)
def approve_movilizacion_endpoint(
    movilizacion_id: str,
    data: schemas.MovilizacionApprove,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Aprobar movilización y generar REEMO. Sólo administradores.
    """
    if current_user.rol not in ['administrador', 'superadministrador']:
        raise HTTPException(status_code=403, detail="Asignación de REEMO requiere privilegios de administrador")
    return approve_movilizacion(db=db, mov_id=movilizacion_id, admin_id=str(current_user.id), obs=data.observaciones)

@router.put("/{movilizacion_id}/load", response_model=schemas.MovilizacionResponse)
def load_movilizacion_endpoint(
    movilizacion_id: str,
    data: schemas.MovilizacionLoad,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Marcar movilización como cargada en el vehículo. (App ganadero)
    """
    return load_movilizacion(db=db, mov_id=movilizacion_id, caller_id=str(current_user.id), data=data)

@router.put("/{movilizacion_id}/inspect", response_model=schemas.MovilizacionResponse)
def inspect_movilizacion_endpoint(
    movilizacion_id: str,
    data: schemas.MovilizacionInspect,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Inspector verifica ganado en tránsito. 
    """
    if current_user.rol not in ['inspector', 'administrador', 'superadministrador']:
        raise HTTPException(status_code=403, detail="Requiere privilegios de inspección")
    return inspect_movilizacion(db=db, mov_id=movilizacion_id, inspector_id=str(current_user.id), data=data)

@router.put("/{movilizacion_id}/arrive", response_model=schemas.MovilizacionResponse)
def arrive_movilizacion_endpoint(
    movilizacion_id: str,
    data: schemas.MovilizacionArrive,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Reportar llegada al destino.
    """
    return arrive_movilizacion(db=db, mov_id=movilizacion_id, caller_id=str(current_user.id), data=data)

@router.put("/{movilizacion_id}/complete", response_model=schemas.MovilizacionResponse)
def complete_movilizacion_endpoint(
    movilizacion_id: str,
    data: schemas.MovilizacionComplete,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Finaliza la movilización. Ejecuta triggers de cambio de dueño/ubicación en BD.
    Sólo admins o inspectores pueden completar.
    """
    if current_user.rol not in ['administrador', 'superadministrador']:
         raise HTTPException(status_code=403, detail="Completar un flujo requiere verificación del administrador")
    return complete_movilizacion(db=db, mov_id=movilizacion_id, admin_id=str(current_user.id), data=data)

@router.put("/{movilizacion_id}/cancel", response_model=schemas.MovilizacionResponse)
def cancel_movilizacion_endpoint(
    movilizacion_id: str,
    observaciones: str = None,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Cancelar movilización.
    """
    return cancel_movilizacion(db=db, mov_id=movilizacion_id, admin_id=str(current_user.id), observaciones=observaciones)

@router.post("/{movilizacion_id}/documentos/{doc_type}", response_model=schemas.MovilizacionResponse)
def link_document_endpoint(
    movilizacion_id: str,
    doc_type: str,
    documento_id: schemas.UUID,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Vincula un documento ya subido (vía /files/upload) a una movilización.
    """
    return vincular_documento_movilizacion(
        db=db, 
        mov_id=movilizacion_id, 
        doc_id=str(documento_id), 
        doc_type=doc_type, 
        user_id=str(current_user.id)
    )

@router.get("/{movilizacion_id}/validar-documentos", response_model=schemas.ValidacionDocumentosMovilizacionResponse)
def validate_documents_endpoint(
    movilizacion_id: str,
    db: Session = Depends(database.get_db),
    current_user: models.Usuario = Depends(auth.get_current_user),
):
    """
    Retorna la lista de documentos obligatorios y opcionales para esta movilización y si ya fueron cargados.
    """
    return validar_documentos_movilizacion(db=db, mov_id=movilizacion_id)
