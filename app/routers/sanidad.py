from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
from datetime import datetime, timedelta
from .. import crud, models, schemas, auth, database

router = APIRouter(
    prefix="/sanidad",
    tags=["sanidad"],
    dependencies=[Depends(auth.get_current_user)]
)

@router.get("/dashboard", response_model=schemas.SanidadDashboardResponse)
async def get_sanidad_dashboard(db: Session = Depends(database.get_db)):
    # 1. Get active outbreaks (diseases without remissions)
    outbreaks_query = text("""
        SELECT COUNT(e.id) 
        FROM enfermedades e
        LEFT JOIN remisiones r ON e.id = r.enfermedad_id
        WHERE r.id IS NULL
    """)
    active_outbreaks = db.execute(outbreaks_query).scalar() or 0

    # 2. Get quarantine count (bovines in quarantine centers or movements)
    quarantine_query = text("""
        SELECT COUNT(id) FROM bovinos 
        WHERE status = 'cuarentena' 
        OR instalacion_id IN (SELECT id FROM instalaciones WHERE facility_type = 'QUARANTINE_CENTER')
    """)
    quarantine_count = db.execute(quarantine_query).scalar() or 0

    # 3. Get recent vaccinations (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    vaccinations_query = text("""
        SELECT COUNT(v.id) 
        FROM vacunaciones v
        JOIN eventos e ON v.evento_id = e.id
        WHERE e.fecha >= :thirty_days_ago
    """)
    recent_vaccinations = db.execute(vaccinations_query, {"thirty_days_ago": thirty_days_ago}).scalar() or 0

    # 4. Mock some alerts for demonstration if none exist, or derive from data
    alerts = []
    
    # Deriving alerts from active outbreaks
    if active_outbreaks > 0:
        alerts.append(schemas.SanidadAlert(
            type=schemas.SanidadAlertType.OUTBREAK,
            severity=schemas.SanidadSeverity.HIGH,
            title=f"Brotes Activos: {active_outbreaks} casos registrados",
            description="Se han detectado enfermedades sin reporte de remisión. Se recomienda revisión inmediata.",
            date=datetime.now(),
            location="Diversas Instalaciones"
        ))

    if quarantine_count > 0:
        alerts.append(schemas.SanidadAlert(
            type=schemas.SanidadAlertType.QUARANTINE,
            severity=schemas.SanidadSeverity.MEDIUM,
            title=f"Ganado en Cuarentena: {quarantine_count} cabezas",
            description="Existen bovinos en centros de cuarentena o con estatus de restricción de movilidad.",
            date=datetime.now(),
            location="Centros de Cuarentena"
        ))

    return schemas.SanidadDashboardResponse(
        alerts=alerts,
        quarantine_count=quarantine_count,
        active_outbreaks=active_outbreaks,
        recent_vaccinations_count=recent_vaccinations,
        total_active_cases=active_outbreaks + quarantine_count
    )

@router.get("/bovino/{bovino_id}/history", response_model=schemas.SanidadBovinoHistoryResponse)
async def get_bovino_sanidad_history(bovino_id: str, db: Session = Depends(database.get_db)):
    db_bovino = crud.get_bovino(db, bovino_id=bovino_id)
    if not db_bovino:
        raise HTTPException(status_code=404, detail="Bovino no encontrado")
    
    raw_history = crud.get_bovino_full_history(db, bovino_id=bovino_id)
    
    formatted_history = []
    for item in raw_history:
        # Map item to SanidadHistoryItem
        # In raw_history, details are already flattened or nested depending on type
        formatted_history.append(schemas.SanidadHistoryItem(
            id=item["id"],
            date=item["fecha"],
            type=item["tipo"],
            title=item["tipo"].replace('_', ' ').capitalize(),
            details=item["detalles"],
            observaciones=item.get("observaciones")
        ))
        
    return schemas.SanidadBovinoHistoryResponse(
        bovino_id=db_bovino.id,
        nombre=db_bovino.nombre,
        arete_barcode=db_bovino.arete_barcode,
        history=formatted_history
    )

@router.get("/quarantine", response_model=List[schemas.SanidadQuarantineResponse])
async def get_quarantine_data(db: Session = Depends(database.get_db)):
    query = text("""
        SELECT b.id as bovino_id, b.arete_barcode, b.nombre, i.id as instalacion_id, i.nombre as instalacion_nombre, e.fecha as fecha_inicio, e.observaciones as motivo
        FROM bovinos b
        JOIN instalaciones i ON b.instalacion_id = i.id
        LEFT JOIN eventos e ON e.bovino_id = b.id
        WHERE b.status = 'cuarentena' 
        OR i.facility_type = 'QUARANTINE_CENTER'
        ORDER BY e.fecha DESC
    """)
    rows = db.execute(query).fetchall()
    
    return [schemas.SanidadQuarantineResponse(
        bovino_id=r.bovino_id,
        arete_barcode=r.arete_barcode,
        nombre=r.nombre,
        instalacion_id=r.instalacion_id,
        instalacion_nombre=r.instalacion_nombre,
        fecha_inicio=r.fecha_inicio or datetime.now(),
        motivo=r.motivo or "Bajo observación sanitaria"
    ) for r in rows]
