from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import UploadFile, HTTPException
import os
import uuid as uuid_lib
import secrets
import string
from . import models, schemas, auth
from .s3 import s3_client, S3_BUCKET_NAME

def get_user_by_username(db: Session, username: str):
    return db.query(models.Usuario).filter(models.Usuario.curp == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.contrasena)

    # Using the stored procedure registrar_usuario_nuevo
    query = text("""
        SELECT registrar_usuario_nuevo(
            :curp,
            :contrasena,
            :rol,
            :nombre,
            :apellido_p,
            :apellido_m,
            :sexo,
            :fecha_nac,
            :clave_elector,
            :idmex
        )
    """)

    params = {
        "curp": user.curp,
        "contrasena": hashed_password,
        "rol": "usuario",
        "nombre": user.nombre,
        "apellido_p": user.apellido_p,
        "apellido_m": user.apellido_m,
        "sexo": user.sexo.value,
        "fecha_nac": user.fecha_nac,
        "clave_elector": user.clave_elector,
        "idmex": user.idmex
    }

    result = db.execute(query, params)
    new_user_id = result.scalar()
    db.commit()

    return db.query(models.Usuario).filter(models.Usuario.id == new_user_id).first()

def create_veterinario(db: Session, veterinario: schemas.VeterinarioCreate, cedula_file: UploadFile):
    """
    Create a new veterinario user with cedula number and upload their cedula file.
    - User will have rol='veterinario'
    - Cedula number is saved to veterinarios table
    - Cedula file is stored in S3 and referenced in documentos table
    """
    hashed_password = auth.get_password_hash(veterinario.contrasena)

    # Using the stored procedure registrar_usuario_nuevo with rol='veterinario'
    query = text("""
        SELECT registrar_usuario_nuevo(
            :curp,
            :contrasena,
            :rol,
            :nombre,
            :apellido_p,
            :apellido_m,
            :sexo,
            :fecha_nac,
            :clave_elector,
            :idmex
        )
    """)

    params = {
        "curp": veterinario.curp,
        "contrasena": hashed_password,
        "rol": "veterinario",
        "nombre": veterinario.nombre,
        "apellido_p": veterinario.apellido_p,
        "apellido_m": veterinario.apellido_m,
        "sexo": veterinario.sexo.value,
        "fecha_nac": veterinario.fecha_nac,
        "clave_elector": veterinario.clave_elector,
        "idmex": veterinario.idmex
    }

    result = db.execute(query, params)
    new_user_id = result.scalar()
    db.commit()

    # Upload cedula file to S3
    file_extension = os.path.splitext(cedula_file.filename)[1]
    storage_key = f"{new_user_id}/cedula_veterinario/{uuid_lib.uuid4()}{file_extension}"

    try:
        s3_client.upload_fileobj(
            cedula_file.file,
            S3_BUCKET_NAME,
            storage_key
        )
    except Exception as e:
        # Rollback user creation if file upload fails
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Could not upload cedula file: {str(e)}")

    # Save document metadata
    doc_data = {
        "usuario_id": new_user_id,
        "doc_type": "cedula_veterinario",
        "storage_key": storage_key,
        "original_filename": cedula_file.filename
    }
    create_documento(db=db, documento_data=doc_data)

    # Save cedula number to veterinarios table
    vet_query = text("""
        INSERT INTO veterinarios (usuario_id, cedula)
        VALUES (:usuario_id, :cedula)
    """)
    db.execute(vet_query, {"usuario_id": new_user_id, "cedula": veterinario.cedula})
    db.commit()

    return db.query(models.Usuario).filter(models.Usuario.id == new_user_id).first()

def get_bovinos(db: Session, user_id: str, skip: int = 0, limit: int = 100, predio_id: str = None):
    query = db.query(models.Bovino).filter(models.Bovino.usuario_id == user_id)
    if predio_id:
        query = query.filter(models.Bovino.predio_id == predio_id)
    return query.offset(skip).limit(limit).all()

def get_bovinos_by_predio(db: Session, predio_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.Bovino).filter(models.Bovino.predio_id == predio_id).offset(skip).limit(limit).all()

def search_bovino(db: Session, arete_barcode: str = None, arete_rfid: str = None, nombre: str = None):
    """
    Search for a bovino by arete_barcode, arete_rfid, or nombre.
    Returns the first match found (priority: barcode > rfid > nombre).
    """
    query = db.query(models.Bovino)

    if arete_barcode:
        return query.filter(models.Bovino.arete_barcode == arete_barcode).first()
    elif arete_rfid:
        return query.filter(models.Bovino.arete_rfid == arete_rfid).first()
    elif nombre:
        return query.filter(models.Bovino.nombre.ilike(f"%{nombre}%")).first()

    return None

def get_bovino(db: Session, bovino_id: str):
    return db.query(models.Bovino).filter(models.Bovino.id == bovino_id).first()

_FOLIO_ALPHABET = string.ascii_uppercase + string.digits

def _generate_folio() -> str:
    return ''.join(secrets.choice(_FOLIO_ALPHABET) for _ in range(7))

def create_bovino(db: Session, bovino: schemas.BovinoCreate, user_id: str):
    for _ in range(10):
        folio = _generate_folio()
        if not db.query(models.Bovino).filter(models.Bovino.folio == folio).first():
            break
    db_bovino = models.Bovino(**bovino.dict(), usuario_id=user_id, usuario_original_id=user_id, folio=folio)
    db.add(db_bovino)
    db.commit()
    db.refresh(db_bovino)
    return db_bovino

def update_bovino(db: Session, bovino_id: str, bovino: schemas.BovinoCreate):
    db_bovino = db.query(models.Bovino).filter(models.Bovino.id == bovino_id).first()
    if db_bovino:
        for key, value in bovino.dict(exclude_unset=True).items():
            setattr(db_bovino, key, value)
        db.commit()
        db.refresh(db_bovino)
    return db_bovino

def delete_bovino(db: Session, bovino_id: str):
    db_bovino = db.query(models.Bovino).filter(models.Bovino.id == bovino_id).first()
    if db_bovino:
        db.delete(db_bovino)
        db.commit()
    return db_bovino

def create_evento(db: Session, evento_request: schemas.EventoCreateRequest):
    etype = evento_request.type
    data = evento_request.data

    # Extract common fields
    bovino_id = data.get('bovino_id')
    observaciones = data.get('observaciones', '')

    eid = None

    if etype == 'peso':
        # registrar_peso(_bovino_id, _peso_nuevo, _fecha DEFAULT NOW(), _observaciones)
        peso_nuevo = data.get('peso_nuevo')
        q = text("SELECT registrar_peso(:bid, :pn, NOW(), :obs)")
        eid = db.execute(q, {"bid": bovino_id, "pn": peso_nuevo, "obs": observaciones}).scalar()

    elif etype == 'dieta':
        # registrar_dieta(_bovino_id, _alimento, _fecha, _observaciones)
        alimento = data.get('alimento')
        q = text("SELECT registrar_dieta(:bid, :ali, NOW(), :obs)")
        eid = db.execute(q, {"bid": bovino_id, "ali": alimento, "obs": observaciones}).scalar()

    elif etype == 'vacunacion':
        # registrar_vacunacion(_bovino_id, _usuario_id, _tipo, _lote, _laboratorio, _fecha_prox, _fecha, _observaciones)
        q = text("SELECT registrar_vacunacion(:bid, :uid, :tipo, :lote, :lab, :fprox, NOW(), :obs)")
        eid = db.execute(q, {
            "bid": bovino_id, "uid": data.get('usuario_id'), "tipo": data.get('tipo'),
            "lote": data.get('lote'), "lab": data.get('laboratorio'), "fprox": data.get('fecha_prox'),
            "obs": observaciones
        }).scalar()

    elif etype == 'desparasitacion':
        # registrar_desparasitacion(_bovino_id, _usuario_id, _medicamento, _dosis, _fecha_prox, _fecha, _observaciones)
        q = text("SELECT registrar_desparasitacion(:bid, :uid, :med, :dosis, :fprox, NOW(), :obs)")
        eid = db.execute(q, {
            "bid": bovino_id, "uid": data.get('usuario_id'), "med": data.get('medicamento'),
            "dosis": data.get('dosis'), "fprox": data.get('fecha_prox'), "obs": observaciones
        }).scalar()

    elif etype == 'laboratorio':
        # registrar_laboratorio(_bovino_id, _usuario_id, _tipo, _resultado, _fecha, _observaciones)
        q = text("SELECT registrar_laboratorio(:bid, :uid, :tipo, :resultado, NOW(), :obs)")
        eid = db.execute(q, {
            "bid": bovino_id, "uid": data.get('usuario_id'), "tipo": data.get('tipo'),
            "resultado": data.get('resultado'), "obs": observaciones
        }).scalar()

    elif etype == 'compraventa':
        # registrar_compraventa(_bovino_id, _comprador_id, _vendedor_id, _fecha, _observaciones)
        q = text("SELECT registrar_compraventa(:bid, :cid, :vid, NOW(), :obs)")
        eid = db.execute(q, {
            "bid": bovino_id, "cid": data.get('comprador_id'),
            "vid": data.get('vendedor_id'), "obs": observaciones
        }).scalar()

    elif etype == 'traslado':
        # registrar_traslado(_bovino_id, _predio_nuevo_id, _fecha, _observaciones)
        q = text("SELECT registrar_traslado(:bid, :pid, NOW(), :obs)")
        eid = db.execute(q, {
            "bid": bovino_id, "pid": data.get('predio_nuevo_id'), "obs": observaciones
        }).scalar()

    elif etype == 'enfermedad':
        # registrar_enfermedad(_bovino_id, _usuario_id, _tipo, _fecha, _observaciones)
        # NOTE: This returns enfermedad_id, not evento_id
        q = text("SELECT registrar_enfermedad(:bid, :uid, :tipo, NOW(), :obs)")
        enfermedad_id = db.execute(q, {
            "bid": bovino_id, "uid": data.get('usuario_id'),
            "tipo": data.get('tipo'), "obs": observaciones
        }).scalar()
        db.commit()
        # Get the evento_id from the enfermedad record
        eid = db.execute(text("SELECT evento_id FROM enfermedades WHERE id = :eid"),
                       {"eid": enfermedad_id}).scalar()

    elif etype == 'tratamiento':
        # Validate that the referenced enfermedad belongs to the same bovino
        enfermedad_id_param = data.get('enfermedad_id')
        if enfermedad_id_param:
            enf_bovino = db.execute(
                text("SELECT bovino_id FROM eventos WHERE id = (SELECT evento_id FROM enfermedades WHERE id = :eid)"),
                {"eid": enfermedad_id_param}
            ).scalar()
            if enf_bovino and str(enf_bovino) != str(bovino_id):
                raise HTTPException(status_code=400, detail="La enfermedad no pertenece al mismo bovino")
        # registrar_tratamiento(_bovino_id, _enfermedad_id, _usuario_id, _medicamento, _dosis, _periodo, _fecha, _observaciones)
        q = text("SELECT registrar_tratamiento(:bid, :eid, :uid, :med, :dosis, :periodo, NOW(), :obs)")
        eid = db.execute(q, {
            "bid": bovino_id, "eid": enfermedad_id_param, "uid": data.get('usuario_id'),
            "med": data.get('medicamento'), "dosis": data.get('dosis'),
            "periodo": data.get('periodo'), "obs": observaciones
        }).scalar()

    # fallback to generic if no match or 'general'
    else:
        db_evento = models.Evento(bovino_id=bovino_id, observaciones=observaciones)
        db.add(db_evento)
        db.commit()
        db.refresh(db_evento)
        eid = db_evento.id

    # Commit if we used a raw SQL function (which returns a UUID scalar)
    supported_types = ['peso', 'dieta', 'vacunacion', 'desparasitacion', 'laboratorio',
                      'compraventa', 'traslado', 'enfermedad', 'tratamiento']
    if etype in supported_types:
         db.commit()

    return db.query(models.Evento).filter(models.Evento.id == eid).first()

def get_evento(db: Session, evento_id: str):
    return db.query(models.Evento).filter(models.Evento.id == evento_id).first()

def get_eventos_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.Evento).filter(models.Evento.bovino_id == bovino_id).offset(skip).limit(limit).all()

def get_eventos_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    # Get all eventos for all bovinos owned by the user
    return db.query(models.Evento).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(
        models.Evento.fecha.desc()
    ).offset(skip).limit(limit).all()

def create_documento(db: Session, documento_data: dict):
    db_documento = models.Documento(**documento_data)
    db.add(db_documento)
    db.commit()
    db.refresh(db_documento)
    return db_documento

def get_documento(db: Session, doc_id: str):
    return db.query(models.Documento).filter(models.Documento.id == doc_id).first()

def delete_documento(db: Session, doc_id: str):
    db_documento = db.query(models.Documento).filter(models.Documento.id == doc_id).first()
    if db_documento:
        db.delete(db_documento)
        db.commit()
    return db_documento

def get_documento_by_user_and_type(db: Session, user_id: str, doc_type):
    """Return the single document a user has of a given type, or None."""
    return db.query(models.Documento).filter(
        models.Documento.usuario_id == user_id,
        models.Documento.doc_type == doc_type
    ).first()

def get_documento_by_storage_prefix(db: Session, prefix: str):
    """Return the document whose storage_key starts with the given prefix, or None."""
    return db.query(models.Documento).filter(
        models.Documento.storage_key.like(f"{prefix}%")
    ).first()

def get_documentos_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.Documento).filter(
        models.Documento.usuario_id == user_id
    ).order_by(
        models.Documento.created_at.desc()
    ).offset(skip).limit(limit).all()

# Domicilio CRUD
def get_domicilios_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(models.Domicilio).filter(
        models.Domicilio.usuario_id == user_id
    ).offset(skip).limit(limit).all()

def get_domicilio(db: Session, domicilio_id: str):
    return db.query(models.Domicilio).filter(models.Domicilio.id == domicilio_id).first()

def create_domicilio(db: Session, domicilio: schemas.DomicilioCreate, user_id: str):
    db_domicilio = models.Domicilio(**domicilio.dict(), usuario_id=user_id)
    db.add(db_domicilio)
    db.commit()
    db.refresh(db_domicilio)
    return db_domicilio

def update_domicilio(db: Session, domicilio_id: str, domicilio: schemas.DomicilioUpdate):
    db_domicilio = db.query(models.Domicilio).filter(models.Domicilio.id == domicilio_id).first()
    if db_domicilio:
        for key, value in domicilio.dict(exclude_unset=True).items():
            setattr(db_domicilio, key, value)
        db.commit()
        db.refresh(db_domicilio)
    return db_domicilio

def delete_domicilio(db: Session, domicilio_id: str):
    db_domicilio = db.query(models.Domicilio).filter(models.Domicilio.id == domicilio_id).first()
    if db_domicilio:
        db.delete(db_domicilio)
        db.commit()
    return db_domicilio

# Predio CRUD
def get_predios(db: Session, skip: int = 0, limit: int = 100, usuario_id: str = None):
    query = db.query(models.Predio)
    if usuario_id:
        query = query.filter(models.Predio.usuario_id == usuario_id)
    return query.offset(skip).limit(limit).all()

def get_predio(db: Session, predio_id: str):
    return db.query(models.Predio).filter(models.Predio.id == predio_id).first()

def create_predio(db: Session, predio: schemas.PredioCreate, usuario_id: str):
    db_predio = models.Predio(**predio.dict(), usuario_id=usuario_id)
    db.add(db_predio)
    db.commit()
    db.refresh(db_predio)
    return db_predio

def update_predio(db: Session, predio_id: str, predio: schemas.PredioUpdate):
    db_predio = db.query(models.Predio).filter(models.Predio.id == predio_id).first()
    if db_predio:
        for key, value in predio.dict(exclude_unset=True).items():
            setattr(db_predio, key, value)
        db.commit()
        db.refresh(db_predio)
    return db_predio

def delete_predio(db: Session, predio_id: str):
    db_predio = db.query(models.Predio).filter(models.Predio.id == predio_id).first()
    if db_predio:
        db.delete(db_predio)
        db.commit()
    return db_predio

# Event detail CRUD functions with joined data
def get_pesos_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Peso).join(
        models.Peso, models.Evento.id == models.Peso.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "peso_actual": p.peso_actual, "peso_nuevo": p.peso_nuevo} for e, p in results]

def get_pesos_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Peso).join(
        models.Peso, models.Evento.id == models.Peso.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "peso_actual": p.peso_actual, "peso_nuevo": p.peso_nuevo} for e, p in results]

def get_peso_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Peso).join(
        models.Peso, models.Evento.id == models.Peso.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, p = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "peso_actual": p.peso_actual, "peso_nuevo": p.peso_nuevo}

def get_dietas_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Dieta).join(
        models.Dieta, models.Evento.id == models.Dieta.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "alimento": d.alimento} for e, d in results]

def get_dietas_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Dieta).join(
        models.Dieta, models.Evento.id == models.Dieta.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "alimento": d.alimento} for e, d in results]

def get_dieta_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Dieta).join(
        models.Dieta, models.Evento.id == models.Dieta.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, d = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "alimento": d.alimento}

def get_vacunaciones_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Vacunacion).join(
        models.Vacunacion, models.Evento.id == models.Vacunacion.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "veterinario_id": v.veterinario_id, "tipo": v.tipo, "lote": v.lote,
             "laboratorio": v.laboratorio, "fecha_prox": v.fecha_prox} for e, v in results]

def get_vacunaciones_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Vacunacion).join(
        models.Vacunacion, models.Evento.id == models.Vacunacion.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "veterinario_id": v.veterinario_id, "tipo": v.tipo, "lote": v.lote,
             "laboratorio": v.laboratorio, "fecha_prox": v.fecha_prox} for e, v in results]

def get_vacunacion_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Vacunacion).join(
        models.Vacunacion, models.Evento.id == models.Vacunacion.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, v = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "veterinario_id": v.veterinario_id, "tipo": v.tipo, "lote": v.lote,
            "laboratorio": v.laboratorio, "fecha_prox": v.fecha_prox}

def get_desparasitaciones_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Desparasitacion).join(
        models.Desparasitacion, models.Evento.id == models.Desparasitacion.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "veterinario_id": d.veterinario_id, "medicamento": d.medicamento,
             "dosis_admin": d.dosis_admin, "fecha_prox": d.fecha_prox} for e, d in results]

def get_desparasitaciones_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Desparasitacion).join(
        models.Desparasitacion, models.Evento.id == models.Desparasitacion.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "veterinario_id": d.veterinario_id, "medicamento": d.medicamento,
             "dosis_admin": d.dosis_admin, "fecha_prox": d.fecha_prox} for e, d in results]

def get_desparasitacion_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Desparasitacion).join(
        models.Desparasitacion, models.Evento.id == models.Desparasitacion.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, d = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "veterinario_id": d.veterinario_id, "medicamento": d.medicamento,
            "dosis_admin": d.dosis_admin, "fecha_prox": d.fecha_prox}

def get_laboratorios_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Laboratorio).join(
        models.Laboratorio, models.Evento.id == models.Laboratorio.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "veterinario_id": l.veterinario_id, "tipo": l.tipo, "resultado": l.resultado} for e, l in results]

def get_laboratorios_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Laboratorio).join(
        models.Laboratorio, models.Evento.id == models.Laboratorio.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "veterinario_id": l.veterinario_id, "tipo": l.tipo, "resultado": l.resultado} for e, l in results]

def get_laboratorio_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Laboratorio).join(
        models.Laboratorio, models.Evento.id == models.Laboratorio.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, l = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "veterinario_id": l.veterinario_id, "tipo": l.tipo, "resultado": l.resultado}

def get_compraventas_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Compraventa).join(
        models.Compraventa, models.Evento.id == models.Compraventa.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "comprador_curp": c.comprador_curp, "vendedor_curp": c.vendedor_curp} for e, c in results]

def get_compraventas_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Compraventa).join(
        models.Compraventa, models.Evento.id == models.Compraventa.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "comprador_curp": c.comprador_curp, "vendedor_curp": c.vendedor_curp} for e, c in results]

def get_compraventa_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Compraventa).join(
        models.Compraventa, models.Evento.id == models.Compraventa.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, c = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "comprador_curp": c.comprador_curp, "vendedor_curp": c.vendedor_curp}

def get_traslados_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Traslado).join(
        models.Traslado, models.Evento.id == models.Traslado.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "predio_anterior_id": t.predio_anterior_id, "predio_nuevo_id": t.predio_nuevo_id} for e, t in results]

def get_traslados_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Traslado).join(
        models.Traslado, models.Evento.id == models.Traslado.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "predio_anterior_id": t.predio_anterior_id, "predio_nuevo_id": t.predio_nuevo_id} for e, t in results]

def get_traslado_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Traslado).join(
        models.Traslado, models.Evento.id == models.Traslado.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, t = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "predio_anterior_id": t.predio_anterior_id, "predio_nuevo_id": t.predio_nuevo_id}

def get_enfermedades_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Enfermedad).join(
        models.Enfermedad, models.Evento.id == models.Enfermedad.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "enfermedad_id": enf.id, "veterinario_id": enf.veterinario_id, "tipo": enf.tipo} for e, enf in results]

def get_enfermedades_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Enfermedad).join(
        models.Enfermedad, models.Evento.id == models.Enfermedad.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "enfermedad_id": enf.id, "veterinario_id": enf.veterinario_id, "tipo": enf.tipo} for e, enf in results]

def get_enfermedad_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Enfermedad).join(
        models.Enfermedad, models.Evento.id == models.Enfermedad.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, enf = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "enfermedad_id": enf.id, "veterinario_id": enf.veterinario_id, "tipo": enf.tipo}

def get_tratamientos_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Tratamiento).join(
        models.Tratamiento, models.Evento.id == models.Tratamiento.evento_id
    ).join(
        models.Bovino, models.Evento.bovino_id == models.Bovino.id
    ).filter(
        models.Bovino.usuario_id == user_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "enfermedad_id": t.enfermedad_id, "veterinario_id": t.veterinario_id,
             "medicamento": t.medicamento, "dosis": t.dosis, "periodo": t.periodo} for e, t in results]

def get_tratamientos_by_bovino(db: Session, bovino_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Tratamiento).join(
        models.Tratamiento, models.Evento.id == models.Tratamiento.evento_id
    ).filter(
        models.Evento.bovino_id == bovino_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "enfermedad_id": t.enfermedad_id, "veterinario_id": t.veterinario_id,
             "medicamento": t.medicamento, "dosis": t.dosis, "periodo": t.periodo} for e, t in results]

def get_tratamiento_detail(db: Session, evento_id: str):
    result = db.query(models.Evento, models.Tratamiento).join(
        models.Tratamiento, models.Evento.id == models.Tratamiento.evento_id
    ).filter(models.Evento.id == evento_id).first()

    if not result:
        return None
    e, t = result
    return {"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
            "enfermedad_id": t.enfermedad_id, "veterinario_id": t.veterinario_id,
            "medicamento": t.medicamento, "dosis": t.dosis, "periodo": t.periodo}

def get_tratamientos_by_enfermedad(db: Session, enfermedad_id: str, skip: int = 0, limit: int = 100):
    results = db.query(models.Evento, models.Tratamiento).join(
        models.Tratamiento, models.Evento.id == models.Tratamiento.evento_id
    ).filter(
        models.Tratamiento.enfermedad_id == enfermedad_id
    ).order_by(models.Evento.fecha.desc()).offset(skip).limit(limit).all()

    return [{"id": e.id, "bovino_id": e.bovino_id, "fecha": e.fecha, "observaciones": e.observaciones,
             "enfermedad_id": t.enfermedad_id, "veterinario_id": t.veterinario_id,
             "medicamento": t.medicamento, "dosis": t.dosis, "periodo": t.periodo} for e, t in results]
