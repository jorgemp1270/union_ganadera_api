from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta, date
from uuid import UUID
import uuid

from ..database import get_db
from ..models import Instalacion, Predio, Usuario, InstalacionDocumento, RenovacionUPP, Documento, FacilityTypeEnum, DocReviewStatusEnum, InstalacionPredio, InstalacionStatusEnum
from ..auth import get_current_user, require_admin
from ..schemas import (
    InstalacionCreate,
    InstalacionUpdate,
    InstalacionResponse,
    InstalacionDetailResponse,
    InstalacionDocumentoResponse,
    RenovacionUPPCreate,
    RenovacionUPPResponse,
    VincularPredioInstalacionRequest,
    VincularPredioInstalacionResponse,
    ValidacionDocumentosResponse,
    ApproveInstalacionRequest,
    ApproveInstalacionResponse,
    DocumentoStatusResponse,
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
    - Normal users (usuario): Can only create UPP and PSG
    - Veterinarians (veterinario): Can only create UPP and PSG (same as normal users)
    - Admins/SuperAdmins: Can create all types including CASETA_INSPECCION
    """
    
    # Validate facility type based on user role
    if current_user.rol in ["usuario", "veterinario"]:
        # Normal users and veterinarians can only create UPP and PSG
        if request.facility_type not in [FacilityTypeEnum.UPP, FacilityTypeEnum.PSG]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Users (normal and veterinarians) can only create UPP and PSG facilities"
            )
    elif current_user.rol not in ["administrador", "superadministrador"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create other facility types"
        )
    
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
        status=request.status or InstalacionStatusEnum.pendiente_revision,
        latitud=request.latitud,
        longitud=request.longitud,
        estado=request.estado,
        municipio=request.municipio,
        created_by_admin=current_user.id if current_user.rol in ["administrador", "superadministrador"] else None,
        license_number=request.license_number,
        active=False,  # Only set to True when admin approves and all docs are validated
        fecha_vencimiento=None,  # Will be set when UPP renewal is approved
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
    - Normal users (usuario): See only their own UPPs and PSGs
    - Veterinarians (veterinario): See only their own UPPs and PSGs (same as normal users)
    - Admins/Inspectors: See all
    
    Privacy Note: Normal users and veterinarians cannot see other users' facilities exhaustively.
    Use GET /instalaciones/buscar/codigo/{license_number} to search external facilities by code.
    """
    query = db.query(Instalacion)
    
    # Filter by user if not admin/inspector
    if current_user.rol not in ["administrador", "superadministrador", "inspector"]:
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
    Sets fecha_vencimiento on the installation to 365 days from today
    """
    renovacion = db.query(RenovacionUPP).filter(RenovacionUPP.id == renovacion_id).first()
    if not renovacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Renovación not found"
        )
    
    # Calculate expiration date
    expiration_date = date.today() + timedelta(days=365)
    
    renovacion.estado = "aprobada"
    renovacion.aprobada_por = current_user.id
    renovacion.fecha_aprobacion = datetime.utcnow()
    renovacion.fecha_proximo_vencimiento = expiration_date
    
    # Also update the installation's fecha_vencimiento
    instalacion = db.query(Instalacion).filter(Instalacion.id == renovacion.instalacion_id).first()
    if instalacion:
        instalacion.fecha_vencimiento = expiration_date
    
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


# SEARCH - Find by UPP code (license_number) - Public, for external facility discovery
@router.get("/buscar/codigo/{license_number}", response_model=InstalacionResponse)
def buscar_por_codigo(
    license_number: str,
    db: Session = Depends(get_db),
):
    """
    Search for a facility by its UPP/PSG license code.
    This endpoint is public and allows users to find external installations.
    Returns basic info only (no documents, no detailed predios).
    """
    instalacion = db.query(Instalacion).filter(
        Instalacion.license_number == license_number
    ).first()
    
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Facility with code '{license_number}' not found"
        )
    
    return instalacion


# PREDIO LINKING - Link a property (predio) to a facility
@router.post("/{instalacion_id}/vincular-predio", response_model=VincularPredioInstalacionResponse, status_code=status.HTTP_201_CREATED)
def vincular_predio_a_instalacion(
    instalacion_id: UUID,
    request: VincularPredioInstalacionRequest,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Link a property (predio) to a facility (instalacion).
    - User must own both predio and instalacion
    - Creates a many-to-many relationship via instalacion_predio
    - Shares ownership: facility inherits property's clave_catastral for validation
    """
    
    # Get instalacion
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    # Check authorization (owner or admin)
    if current_user.rol not in ["administrador", "superadministrador", "inspector"] and instalacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to link properties to this facility"
        )
    
    # Get predio
    predio = db.query(Predio).filter(Predio.id == request.predio_id).first()
    if not predio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predio not found"
        )
    
    # Check predio ownership
    if predio.usuario_id != instalacion.usuario_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Predio must be owned by the same user as the facility"
        )
    
    # Check if already linked
    existing_link = db.query(InstalacionPredio).filter(
        and_(
            InstalacionPredio.upp_id == instalacion_id,
            InstalacionPredio.predio_id == request.predio_id
        )
    ).first()
    if existing_link:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property is already linked to this facility"
        )
    
    # Create link
    link = InstalacionPredio(
        upp_id=instalacion_id,
        predio_id=request.predio_id
    )
    
    db.add(link)
    db.commit()
    db.refresh(link)
    
    return link


# VALIDATION - Check document completeness for a facility
@router.get("/{instalacion_id}/validar-documentos", response_model=ValidacionDocumentosResponse)
def validar_documentos_instalacion(
    instalacion_id: UUID,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Validate if all required documents for a facility are present and approved.
    Returns:
    - Total documents uploaded
    - Aprobados/Pendientes/Rechazados counts
    - List of missing required documents
    - Recommended status change
    """
    
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    # Check authorization
    if current_user.rol not in ["administrador", "superadministrador", "inspector"] and instalacion.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )
    
    # Get all documents for this facility
    documentos = db.query(InstalacionDocumento).filter(
        InstalacionDocumento.instalacion_id == instalacion_id
    ).all()
    
    # Define required documents based on facility type
    documentos_requeridos = {
        FacilityTypeEnum.UPP: {
            "clave_catastral": "Clave Catastral del terreno",
            "constancia_fiscal": "Constancia de Situación Fiscal",
            "certificado_parcelario": "Certificado Parcelario (si aplica)",
        },
        FacilityTypeEnum.PSG: {
            "constancia_fiscal": "Constancia de Situación Fiscal",
            "registro_veterinario": "Registro/Cédula Veterinario",
        },
        FacilityTypeEnum.RASTRO: {
            "permiso_ambiental": "Permiso Ambiental",
            "constancia_fiscal": "Constancia de Situación Fiscal",
        },
    }
    
    requeridos = documentos_requeridos.get(instalacion.facility_type, {})
    
    # Count status
    docs_aprobados = sum(1 for d in documentos if d.status == DocReviewStatusEnum.aprobado)
    docs_pendientes = sum(1 for d in documentos if d.status == DocReviewStatusEnum.pendiente)
    docs_rechazados = sum(1 for d in documentos if d.status == DocReviewStatusEnum.rechazado)
    
    # Find missing documents
    doc_tipos_presentes = {d.documento_tipo for d in documentos}
    documentos_faltantes = [
        DocumentoStatusResponse(
            documento_tipo=tipo,
            status=DocReviewStatusEnum.pendiente,
            requerido=True,
            descripcion=desc
        )
        for tipo, desc in requeridos.items()
        if tipo not in doc_tipos_presentes
    ]
    
    # Determine completeness and recommended status
    validacion_completa = len(documentos_faltantes) == 0 and docs_rechazados == 0 and docs_pendientes == 0
    
    if validacion_completa:
        status_recomendado = InstalacionStatusEnum.lista_operar
    elif docs_rechazados > 0:
        status_recomendado = InstalacionStatusEnum.documentos_rechazados
    elif docs_pendientes > 0 or len(documentos_faltantes) > 0:
        status_recomendado = InstalacionStatusEnum.documentos_incompletos
    else:
        status_recomendado = InstalacionStatusEnum.pendiente_revision
    
    return ValidacionDocumentosResponse(
        instalacion_id=instalacion_id,
        documentos_totales=len(documentos),
        documentos_aprobados=docs_aprobados,
        documentos_pendientes=docs_pendientes,
        documentos_rechazados=docs_rechazados,
        documentos_faltantes=documentos_faltantes,
        validacion_completa=validacion_completa,
        status_recomendado=status_recomendado,
    )


# APPROVAL - Admin approves facility and makes it operational
@router.post("/{instalacion_id}/aprobar-operacion", response_model=ApproveInstalacionResponse)
def aprobar_operacion_instalacion(
    instalacion_id: UUID,
    request: ApproveInstalacionRequest,
    current_user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    ADMIN ONLY: Approve facility operation.
    Prerequisites:
    - All required documents must be approved
    - No rejected documents
    - Facility must be in "lista_operar" status
    
    After approval:
    - status = "activa"
    - active = True
    - Facility can now perform cattle movements and events
    """
    
    instalacion = db.query(Instalacion).filter(Instalacion.id == instalacion_id).first()
    if not instalacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Instalación not found"
        )
    
    # Get all documents
    documentos = db.query(InstalacionDocumento).filter(
        InstalacionDocumento.instalacion_id == instalacion_id
    ).all()
    
    # Check if all documents are approved
    tiene_pendientes = any(d.status == DocReviewStatusEnum.pendiente for d in documentos)
    tiene_rechazados = any(d.status == DocReviewStatusEnum.rechazado for d in documentos)
    
    if tiene_pendientes or tiene_rechazados:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot approve: pending or rejected documents exist. Solve them first."
        )
    
    # Validate using the validation endpoint logic
    # Get facility type required documents
    documentos_requeridos = {
        FacilityTypeEnum.UPP: ["clave_catastral", "constancia_fiscal"],
        FacilityTypeEnum.PSG: ["constancia_fiscal"],
        FacilityTypeEnum.RASTRO: ["permiso_ambiental", "constancia_fiscal"],
    }
    
    requeridos = documentos_requeridos.get(instalacion.facility_type, [])
    doc_tipos_presentes = {d.documento_tipo for d in documentos}
    
    # Check all required documents exist and are approved
    for tipo_requerido in requeridos:
        if tipo_requerido not in doc_tipos_presentes:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot approve: required document '{tipo_requerido}' is missing"
            )
        
        doc = next(d for d in documentos if d.documento_tipo == tipo_requerido)
        if doc.status != DocReviewStatusEnum.aprobado:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot approve: required document '{tipo_requerido}' is not approved"
            )
    
    # Approve the facility
    instalacion.status = InstalacionStatusEnum.activa
    instalacion.active = True
    instalacion.created_by_admin = current_user.id
    
    db.commit()
    db.refresh(instalacion)
    
    return ApproveInstalacionResponse(
        id=instalacion.id,
        status=instalacion.status,
        active=instalacion.active,
        mensaje="Instalación approved and operational. Cattle movements allowed.",
        fecha_aprobacion=datetime.utcnow(),
    )
