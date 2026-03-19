from sqlalchemy.orm import Session
from fastapi import HTTPException
import uuid as uuid_lib
import string
import secrets
from datetime import datetime, timezone

from . import models, schemas

_REEMO_ALPHABET = string.digits

def _generate_reemo() -> str:
    """Generate a random 10-digit string for the REEMO."""
    return ''.join(secrets.choice(_REEMO_ALPHABET) for _ in range(10))

def get_movilizaciones(db: Session, skip: int = 0, limit: int = 100, usuario_id: str = None, estado: str = None):
    query = db.query(models.Movilizacion)
    if usuario_id:
        query = query.filter(models.Movilizacion.solicitante_id == usuario_id)
    if estado:
        query = query.filter(models.Movilizacion.estado == estado)
    return query.order_by(models.Movilizacion.fecha_solicitud.desc()).offset(skip).limit(limit).all()

def get_movilizacion(db: Session, movilizacion_id: str):
    return db.query(models.Movilizacion).filter(models.Movilizacion.id == movilizacion_id).first()

def create_movilizacion(db: Session, movilizacion: schemas.MovilizacionCreate, usuario_id: str):
    # Validar instalaciones
    origen = db.query(models.Instalacion).filter(models.Instalacion.id == movilizacion.origen_id).first()
    destino = db.query(models.Instalacion).filter(models.Instalacion.id == movilizacion.destino_id).first()

    if not origen or not destino:
        raise HTTPException(status_code=404, detail="Instalacion origen o destino no encontrada")
    if not origen.active or not destino.active:
        raise HTTPException(status_code=400, detail="Ambas instalaciones deben estar activas")
        
    # Check vencimiento (basic check)
    today = datetime.now().date()
    if origen.fecha_vencimiento and origen.fecha_vencimiento < today:
        raise HTTPException(status_code=400, detail="La instalación origen ha expirado")
    if destino.fecha_vencimiento and destino.fecha_vencimiento < today:
        raise HTTPException(status_code=400, detail="La instalación destino ha expirado")

    # Validar bovinos
    bovinos = db.query(models.Bovino).filter(models.Bovino.id.in_(movilizacion.bovino_ids)).all()
    if len(bovinos) != len(movilizacion.bovino_ids):
        raise HTTPException(status_code=400, detail="Algunos bovinos no fueron encontrados")

    for b in bovinos:
        if b.status == 'sacrificado' or b.status == 'muerto' or b.status == 'exportado':
             raise HTTPException(status_code=400, detail=f"Bovino {b.id} no puede moverse (status: {b.status})")
        if b.status == 'enfermo' and movilizacion.tipo != models.TipoMovilizacionEnum.cuarentena:
             raise HTTPException(status_code=400, detail=f"Bovino {b.id} está enfermo y no puede movilizarse excepto a cuarentena")
        if not b.arete_barcode and not b.arete_rfid:
             raise HTTPException(status_code=400, detail=f"Bovino {b.id} no cuenta con arete identificador")

    # Create Movilizacion
    db_mov = models.Movilizacion(
        solicitante_id=usuario_id,
        origen_id=movilizacion.origen_id,
        destino_id=movilizacion.destino_id,
        tipo=movilizacion.tipo,
        estado=models.EstadoMovilizacionEnum.REQUESTED,
        transportista_nombre=movilizacion.transportista_nombre,
        placas_vehiculo=movilizacion.placas_vehiculo,
        observaciones=movilizacion.observaciones
    )
    db.add(db_mov)
    db.commit()
    db.refresh(db_mov)

    # Link bovinos
    for b in bovinos:
        db_mb = models.MovilizacionBovino(movilizacion_id=db_mov.id, bovino_id=b.id)
        db.add(db_mb)

    # Log event
    db_event = models.MovilizacionEvento(
        movilizacion_id=db_mov.id,
        estado_nuevo=models.EstadoMovilizacionEnum.REQUESTED,
        usuario_id=usuario_id,
        observaciones="Solicitud creada"
    )
    db.add(db_event)
    
    db.commit()
    db.refresh(db_mov)
    return db_mov


def _log_evento(db: Session, mov_id: str, old_state, new_state, user_id, obs):
    db_event = models.MovilizacionEvento(
        movilizacion_id=mov_id,
        estado_viejo=old_state,
        estado_nuevo=new_state,
        usuario_id=user_id,
        observaciones=obs
    )
    db.add(db_event)


def approve_movilizacion(db: Session, mov_id: str, admin_id: str, obs: str = None):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    if db_mov.estado != models.EstadoMovilizacionEnum.REQUESTED:
        raise HTTPException(status_code=400, detail="Solo se pueden aprobar movilizaciones en REQUESTED")

    # Generate REEMO
    for _ in range(10):
        reemo_candidate = _generate_reemo()
        if not db.query(models.Movilizacion).filter(models.Movilizacion.reemo == reemo_candidate).first():
            db_mov.reemo = reemo_candidate
            break

    db_mov.aprobado_por_id = admin_id
    db_mov.fecha_aprobacion = datetime.now(timezone.utc)
    db_mov.estado = models.EstadoMovilizacionEnum.APPROVED

    _log_evento(db, mov_id, models.EstadoMovilizacionEnum.REQUESTED, models.EstadoMovilizacionEnum.APPROVED, admin_id, obs)
    db.commit()
    db.refresh(db_mov)
    return db_mov


def load_movilizacion(db: Session, mov_id: str, caller_id: str, data: schemas.MovilizacionLoad):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    if db_mov.estado != models.EstadoMovilizacionEnum.APPROVED and db_mov.estado != models.EstadoMovilizacionEnum.HELD:
        raise HTTPException(status_code=400, detail="Solo se pueden cargar movilizaciones APPROVED o HELD")

    if data.placas_vehiculo:
        db_mov.placas_vehiculo = data.placas_vehiculo

    old_state = db_mov.estado
    db_mov.fecha_cargue = datetime.now(timezone.utc)
    db_mov.estado = models.EstadoMovilizacionEnum.LOADED

    _log_evento(db, mov_id, old_state, models.EstadoMovilizacionEnum.LOADED, caller_id, data.observaciones)
    db.commit()
    db.refresh(db_mov)
    return db_mov


def inspect_movilizacion(db: Session, mov_id: str, inspector_id: str, data: schemas.MovilizacionInspect):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    if db_mov.estado not in [models.EstadoMovilizacionEnum.LOADED, models.EstadoMovilizacionEnum.IN_TRANSIT]:
        raise HTTPException(status_code=400, detail="El ganado debe estar cargado o en tránsito para ser inspeccionado")

    old_state = db_mov.estado
    db_mov.inspector_id = inspector_id
    db_mov.fecha_inspeccion = datetime.now(timezone.utc)

    if data.aprobar:
        db_mov.estado = models.EstadoMovilizacionEnum.INSPECTED
    else:
        db_mov.estado = models.EstadoMovilizacionEnum.HELD

    _log_evento(db, mov_id, old_state, db_mov.estado, inspector_id, data.observaciones)
    db.commit()
    db.refresh(db_mov)
    return db_mov


def arrive_movilizacion(db: Session, mov_id: str, caller_id: str, data: schemas.MovilizacionArrive):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    # Aceptamos llegadas desde LOADED, IN_TRANSIT, INSPECTED
    valid_states = [models.EstadoMovilizacionEnum.LOADED, models.EstadoMovilizacionEnum.IN_TRANSIT, models.EstadoMovilizacionEnum.INSPECTED]
    if db_mov.estado not in valid_states:
        raise HTTPException(status_code=400, detail="Estado inválido para reportar llegada")

    old_state = db_mov.estado
    db_mov.fecha_llegada = datetime.now(timezone.utc)
    db_mov.estado = models.EstadoMovilizacionEnum.ARRIVED

    _log_evento(db, mov_id, old_state, models.EstadoMovilizacionEnum.ARRIVED, caller_id, data.observaciones)
    db.commit()
    db.refresh(db_mov)
    return db_mov


def complete_movilizacion(db: Session, mov_id: str, admin_id: str, data: schemas.MovilizacionComplete):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    if db_mov.estado != models.EstadoMovilizacionEnum.ARRIVED:
        raise HTTPException(status_code=400, detail="El ganado debe haber llegado (ARRIVED) para completarse")

    old_state = db_mov.estado
    db_mov.fecha_completada = datetime.now(timezone.utc)
    db_mov.estado = models.EstadoMovilizacionEnum.COMPLETED

    _log_evento(db, mov_id, old_state, models.EstadoMovilizacionEnum.COMPLETED, admin_id, data.observaciones)
    
    # Aquí el trigger handle_movilizacion_completed en la BD tomará acción
    # y actualizará los dueños / status de los bovinos.
    
    db.commit()
    db.refresh(db_mov)
    return db_mov

def cancel_movilizacion(db: Session, mov_id: str, admin_id: str, observaciones: str = None):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    if db_mov.estado in [models.EstadoMovilizacionEnum.COMPLETED, models.EstadoMovilizacionEnum.CANCELLED]:
        raise HTTPException(status_code=400, detail="No se puede cancelar una movilización completada o ya cancelada")

    old_state = db_mov.estado
    db_mov.fecha_cancelacion = datetime.now(timezone.utc)
    db_mov.estado = models.EstadoMovilizacionEnum.CANCELLED

    _log_evento(db, mov_id, old_state, models.EstadoMovilizacionEnum.CANCELLED, admin_id, observaciones)
    
    db.commit()
    db.refresh(db_mov)
    return db_mov

def vincular_documento_movilizacion(db: Session, mov_id: str, doc_id: str, doc_type: str, user_id: str):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")
    
    # Check authorization (owner or admin)
    if str(db_mov.solicitante_id) != user_id:
        user = db.query(models.Usuario).filter(models.Usuario.id == user_id).first()
        if user.rol not in ['administrador', 'superadministrador']:
            raise HTTPException(status_code=403, detail="No autorizado para modificar esta movilización")

    # Verify document exists
    doc = db.query(models.Documento).filter(models.Documento.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Map doc_type to column
    column_map = {
        "certificado_sanitario": "documento_sanitario_id",
        "factura": "documento_factura_id",
        "documento_compra": "documento_compra_id",
        "documento_exportacion": "documento_exportacion_id"
    }

    if doc_type not in column_map:
        raise HTTPException(status_code=400, detail=f"Tipo de documento {doc_type} no válido para movilizaciones")

    setattr(db_mov, column_map[doc_type], doc_id)
    db.commit()
    db.refresh(db_mov)
    return db_mov

def get_required_docs_for_mov(tipo: models.TipoMovilizacionEnum):
    """Returns a list of (doc_type, description, is_required)"""
    common = [("certificado_sanitario", "Certificado Zoosanitario de Movilización", True)]
    
    if tipo in [models.TipoMovilizacionEnum.venta, models.TipoMovilizacionEnum.subasta_venta, 
                models.TipoMovilizacionEnum.subasta_ingreso, models.TipoMovilizacionEnum.subasta_salida]:
        return common + [
            ("factura", "Factura de la transacción", False),
            ("documento_compra", "Documento de compra-venta", False)
        ]
    elif tipo == models.TipoMovilizacionEnum.rastro:
        return common + [("permiso_rastro", "Permiso de sacrificio", False)]
    elif tipo == models.TipoMovilizacionEnum.exportacion:
        return common + [("documento_exportacion", "Pedimento de exportación", True)]
    elif tipo == models.TipoMovilizacionEnum.feria:
        return common + [("permiso_feria", "Permiso de participación en feria", True)]
    elif tipo == models.TipoMovilizacionEnum.cuarentena:
        return common + [("permiso_cuarentena", "Orden de cuarentena", True)]
    
    return common

def validar_documentos_movilizacion(db: Session, mov_id: str):
    db_mov = get_movilizacion(db, mov_id)
    if not db_mov:
        raise HTTPException(status_code=404, detail="Movilizacion no encontrada")

    required_configs = get_required_docs_for_mov(db_mov.tipo)
    
    status_list = []
    present_count = 0
    all_required_present = True

    column_map = {
        "certificado_sanitario": db_mov.documento_sanitario_id,
        "factura": db_mov.documento_factura_id,
        "documento_compra": db_mov.documento_compra_id,
        "documento_exportacion": db_mov.documento_exportacion_id
    }

    for doc_type, desc, is_req in required_configs:
        present = column_map.get(doc_type) is not None
        if present:
            present_count += 1
        elif is_req:
            all_required_present = False
        
        status_list.append(schemas.DocumentoStatusMovilizacionResponse(
            documento_tipo=doc_type,
            requerido=is_req,
            presente=present,
            descripcion=desc
        ))

    return schemas.ValidacionDocumentosMovilizacionResponse(
        movilizacion_id=db_mov.id,
        documentos_totales_requeridos=sum(1 for _, _, req in required_configs if req),
        documentos_presentes=present_count,
        documentos_faltantes=status_list,
        validacion_completa=all_required_present
    )
