from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, date
from uuid import UUID
import uuid

from ..database import get_db
from ..models import Instalacion, Predio, Usuario, InstalacionDocumento, RenovacionUPP, Documento, FacilityTypeEnum, DocReviewStatusEnum
from ..auth import get_current_user, require_admin
from ..schemas import (
    InstalacionCreate,
    InstalacionUpdate,
    InstalacionResponse,
    InstalacionDetailResponse,
    InstalacionDocumentoResponse,
    RenovacionUPPCreate,
    RenovacionUPPResponse,
)

router = APIRouter(prefix="/instalaciones", tags=["instalaciones"])


# CREATE - Create a new facility (installation)
@router.post("/", response_model=InstalacionResponse, status_code=status.HTTP_201_CREATED)
def crear_instalacion(
    request: InstalacionCreate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a new facility/installation (UPP, PSG, Rastro, etc.)
    Only admins or the owner can create.
    """
    
    # Check if license_number is already taken
    existing = db.query(Instalacion).filter(
        Instalacion.license_number == request.license_number
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="License number (numero_licencia) already exists"
        )
    
    new_instalacion = Instalacion(
        usuario_id=request.usuario_id or current_user.id,
        nombre=request.nombre,
        facility_type=request.facility_type,
        status=request.status or "activa",
        latitud=request.latitud,
        longitud=request.longitud,
        estado=request.estado,
        municipio=request.municipio,
        created_by_admin=current_user.id if current_user.rol == "admin" or current_user.rol == "superadmin" else None,
        license_number=request.license_number,
        active=request.active or True,
    )
    
    db.add(new_instalacion)
    db.commit()
    db.refresh(new_instalacion)
    return new_instalacion


# GET - List all facilities (filtered by user if not admin)
@router.get("/", response_model=list[InstalacionResponse])
def listar_instalaciones(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
    facility_type: str = None,
    estado: str = None,
    active_only: bool = False,
):
    """
    List all installations. 
    - Admins see all
    - Users only see their own
    """
    query = db.query(Instalacion)
    
    # Filter by user if not admin
    if current_user.rol not in ["admin", "superadmin", "inspector"]:
        query = query.filter(Instalacion.usuario_id == current_user.id)
    
    # Additional filters
    if facility_type:
        query = query.filter(Instalacion.facility_type == facility_type)
    if estado:
        query = query.filter(Instalacion.estado == estado)
    if active_only:
        query = query.filter(Instalacion.active == True)
    
    return query.all()


# GET - Get specific facility with all documents
@router.get("/{instalacion_id}", response_model=InstalacionDetailResponse)
def obtener_instalacion(
    instalacion_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific facility with all documents and latest renewal status"""
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    # Check access (user or admin)
    if current_user.rol not in ["admin", "superadmin", "inspector"] and instalacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this facility"
        )
    
    return instalacion


# UPDATE - Update facility info
@router.put("/{instalacion_id}", response_model=InstalacionResponse)
def actualizar_instalacion(
    instalacion_id: UUID,
    request: InstalacionUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update facility information"""
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    # Check authorization
    if current_user.rol not in ["admin", "superadmin"] and instalacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this facility"
        )
    
    # Update fields
    if request.nombre:
        instalacion.nombre = request.nombre
    if request.status:
        instalacion.status = request.status
    if request.latitud is not None:
        instalacion.latitud = request.latitud
    if request.longitud is not None:
        instalacion.longitud = request.longitud
    if request.estado:
        instalacion.estado = request.estado
    if request.municipio:
        instalacion.municipio = request.municipio
    if request.active is not None:
        instalacion.active = request.active
    
    db.commit()
    db.refresh(instalacion)
    return instalacion


# DELETE - Soft delete (deactivate)
@router.delete("/{instalacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_instalacion(
    instalacion_id: UUID,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete/deactivate a facility (admins only)"""
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    instalacion.active = False
    db.commit()


# DOCUMENTS - Upload document for facility
@router.post("/{instalacion_id}/documentos/{documento_tipo}", status_code=status.HTTP_201_CREATED)
def vincular_documento_instalacion(
    instalacion_id: UUID,
    documento_tipo: str,
    documento_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Link a document to a facility
    documento_tipo: 'constancia_fiscal', 'certificado_parcelario', 'contrato_arrendamiento', etc.
    """
    
    # Verify facility exists and user has access
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    if current_user.rol not in ["admin", "superadmin"] and instalacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Verify document exists
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Documento not found"
        )
    
    # Check if already linked
    existing = db.query(InstalacionDocumento).filter(
        and_(
            InstalacionDocumento.instalacion_id == instalacion_id,
            InstalacionDocumento.documento_id == documento_id
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Document already linked to this facility"
        )
    
    new_doc = InstalacionDocumento(
        instalacion_id=instalacion_id,
        documento_id=documento_id,
        documento_tipo=documento_tipo,
        status=DocReviewStatusEnum.pendiente,
    )
    
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)
    
    return {
        "id": new_doc.id,
        "instalacion_id": new_doc.instalacion_id,
        "documento_id": new_doc.documento_id,
        "documento_tipo": new_doc.documento_tipo,
        "status": new_doc.status.value,
        "created_at": new_doc.created_at,
    }


# DOCUMENTS - Get all documents for a facility
@router.get("/{instalacion_id}/documentos", response_model=list[InstalacionDocumentoResponse])
def obtener_documentos_instalacion(
    instalacion_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all documents linked to a facility"""
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    if current_user.rol not in ["admin", "superadmin", "inspector"] and instalacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    documentos = db.query(InstalacionDocumento).filter(
        InstalacionDocumento.instalacion_id == instalacion_id
    ).all()
    
    return documentos


# DOCUMENTS - Approve/Reject facility document
@router.post("/{instalacion_id}/documentos/{doc_id}/aprobar", status_code=status.HTTP_200_OK)
def aprobar_documento_instalacion(
    instalacion_id: UUID,
    doc_id: UUID,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Approve a facility document (admins only)"""
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    doc_record = db.query(InstalacionDocumento).filter(
        and_(
            InstalacionDocumento.instalacion_id == instalacion_id,
            InstalacionDocumento.id == doc_id
        )
    ).first()
    if not doc_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc_record.status = DocReviewStatusEnum.aprobado
    doc_record.review_date = datetime.utcnow()
    doc_record.reviewed_by = current_user.id
    
    db.commit()
    db.refresh(doc_record)
    
    return {"status": "approved", "documento": doc_record}


@router.post("/{instalacion_id}/documentos/{doc_id}/rechazar", status_code=status.HTTP_200_OK)
def rechazar_documento_instalacion(
    instalacion_id: UUID,
    doc_id: UUID,
    comentario: str,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reject a facility document with comment (admins only)"""
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    doc_record = db.query(InstalacionDocumento).filter(
        and_(
            InstalacionDocumento.instalacion_id == instalacion_id,
            InstalacionDocumento.id == doc_id
        )
    ).first()
    if not doc_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    doc_record.status = DocReviewStatusEnum.rechazado
    doc_record.comentario_rechazo = comentario
    doc_record.review_date = datetime.utcnow()
    doc_record.reviewed_by = current_user.id
    
    db.commit()
    db.refresh(doc_record)
    
    return {"status": "rejected", "documento": doc_record}


# UPP RENEWAL - Request renewal
@router.post("/{instalacion_id}/renovaciones/solicitar", response_model=RenovacionUPPResponse, status_code=status.HTTP_201_CREATED)
def solicitar_renovacion_upp(
    instalacion_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Request UPP renewal (annual requirement)
    Only for UPP type facilities
    """
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    # Check facility is UPP type
    if instalacion.facility_type != FacilityTypeEnum.UPP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Renewal only applicable to UPP type facilities"
        )
    
    # Check authorization
    if current_user.id != instalacion.usuario_id and current_user.rol not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Check if there's already a pending renewal
    existing_pending = db.query(RenovacionUPP).filter(
        and_(
            RenovacionUPP.instalacion_id == instalacion_id,
            RenovacionUPP.estado == "pendiente"
        )
    ).first()
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already pending renewal approval"
        )
    
    renovacion = RenovacionUPP(
        instalacion_id=instalacion_id,
        solicitada_por=current_user.id,
        estado="pendiente",
    )
    
    db.add(renovacion)
    db.commit()
    db.refresh(renovacion)
    
    return renovacion


# UPP RENEWAL - Get pending renewals (inspector/admin)
@router.get("/renovaciones/pendientes", response_model=list[RenovacionUPPResponse])
def obtener_renovaciones_pendientes(
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get all pending UPP renewals (admins/inspectors only)"""
    renovaciones = db.query(RenovacionUPP).filter(
        RenovacionUPP.estado == "pendiente"
    ).all()
    
    return renovaciones


# UPP RENEWAL - Approve renewal
@router.post("/renovaciones/{renovacion_id}/aprobar", response_model=RenovacionUPPResponse)
def aprobar_renovacion_upp(
    renovacion_id: UUID,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Approve UPP renewal (extends license for 365 days)
    Admins/Inspectors only
    """
    renovacion = db.query(RenovacionUPP).filter(RenovacionUPP.id == renovacion_id).first()
    if not renovacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Renovación not found"
        )
    
    renovacion.estado = "aprobada"
    renovacion.aprobada_por = current_user.id
    renovacion.fecha_aprobacion = datetime.utcnow()
    renovacion.fecha_proximo_vencimiento = date.today() + timedelta(days=365)
    
    db.commit()
    db.refresh(renovacion)
    
    return renovacion


# UPP RENEWAL - Reject renewal
@router.post("/renovaciones/{renovacion_id}/rechazar", response_model=RenovacionUPPResponse)
def rechazar_renovacion_upp(
    renovacion_id: UUID,
    comentarios: str,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Reject UPP renewal
    Admins/Inspectors only
    """
    renovacion = db.query(RenovacionUPP).filter(RenovacionUPP.id == renovacion_id).first()
    if not renovacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Renovación not found"
        )
    
    renovacion.estado = "rechazada"
    renovacion.aprobada_por = current_user.id
    renovacion.fecha_aprobacion = datetime.utcnow()
    renovacion.comentarios = comentarios
    
    db.commit()
    db.refresh(renovacion)
    
    return renovacion


# SEARCH - Find facilities by municipality
@router.get("/buscar/municipio/{municipio}", response_model=list[InstalacionResponse])
def buscar_por_municipio(
    municipio: str,
    facility_type: str = None,
    db: Session = Depends(get_db),
):
    """Search facilities by municipality"""
    query = db.query(Instalacion).filter(Instalacion.municipio == municipio)
    
    if facility_type:
        query = query.filter(Instalacion.facility_type == facility_type)
    
    return query.all()


# SEARCH - Find by facility type
@router.get("/tipo/{facility_type}", response_model=list[InstalacionResponse])
def buscar_por_tipo(
    facility_type: str,
    estado: str = None,
    db: Session = Depends(get_db),
):
    """Search facilities by type"""
    try:
        ft = FacilityTypeEnum[facility_type]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid facility type. Use one of: {', '.join([t.name for t in FacilityTypeEnum])}"
        )
    
    query = db.query(Instalacion).filter(Instalacion.facility_type == ft)
    
    if estado:
        query = query.filter(Instalacion.estado == estado)
    
    return query.all()
