from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from enum import Enum

class SanidadAlertType(str, Enum):
    OUTBREAK = "outbreak"
    RESTRICTED_ZONE = "restricted_zone"
    QUARANTINE = "quarantine"
    VACCINATION_REMINDER = "vaccination_reminder"

class SanidadSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SexoEnum(str, Enum):
    M = "M"
    F = "F"
    X = "X"

class DocTypeEnum(str, Enum):
    identificacion_frente = "identificacion_frente"
    identificacion_reverso = "identificacion_reverso"
    comprobante_domicilio = "comprobante_domicilio"
    predio = "predio"
    cedula_veterinario = "cedula_veterinario"
    fierro = "fierro"
    otro = "otro"
    clave_catastral = "clave_catastral"
    constancia_fiscal = "constancia_fiscal"
    certificado_parcelario = "certificado_parcelario"
    identificacion = "identificacion"
    rfc = "rfc"
    permiso_rastro = "permiso_rastro"
    certificado_inspecciones = "certificado_inspecciones"
    permiso_feria = "permiso_feria"
    permiso_subasta = "permiso_subasta"
    permiso_exportacion = "permiso_exportacion"
    certificado_calidad = "certificado_calidad"
    permiso_cuarentena = "permiso_cuarentena"
    permiso_laboratorio = "permiso_laboratorio"
    certificado_sanitario = "certificado_sanitario"
    factura = "factura"
    documento_compra = "documento_compra"

class TipoMovilizacionEnum(str, Enum):
    venta = "venta"
    traslado_interno = "traslado_interno"
    reproduccion = "reproduccion"
    subasta_ingreso = "subasta_ingreso"
    subasta_venta = "subasta_venta"
    subasta_salida = "subasta_salida"
    rastro = "rastro"
    feria = "feria"
    cuarentena = "cuarentena"
    exportacion = "exportacion"

class EstadoMovilizacionEnum(str, Enum):
    DRAFT = "DRAFT"
    REQUESTED = "REQUESTED"
    APPROVED = "APPROVED"
    LOADED = "LOADED"
    IN_TRANSIT = "IN_TRANSIT"
    INSPECTED = "INSPECTED"
    HELD = "HELD"
    ARRIVED = "ARRIVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class DocReviewStatusEnum(str, Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"

class InstalacionStatusEnum(str, Enum):
    pendiente_revision = "pendiente_revision"
    documentos_incompletos = "documentos_incompletos"
    documentos_rechazados = "documentos_rechazados"
    lista_operar = "lista_operar"
    activa = "activa"
    inactiva = "inactiva"

# User Schemas
class UserBase(BaseModel):
    curp: str

class UserCreate(UserBase):
    contrasena: str
    nombre: str
    apellido_p: str
    apellido_m: Optional[str] = None
    sexo: SexoEnum
    fecha_nac: date
    clave_elector: str
    idmex: str

    @field_validator('contrasena')
    @classmethod
    def validate_password_length(cls, v):
        if len(v) > 72:
            raise ValueError('Password cannot be longer than 72 characters')
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

class VeterinarioCreate(UserCreate):
    # Inherits all UserCreate fields
    cedula: str  # Professional license number
    # Cedula file (document) will be uploaded separately in the multipart form

class AdministradorCreate(UserCreate):
    # Inherits all UserCreate fields
    # Administrador can be created by superadministrador
    pass

class SuperAdministradorCreate(UserBase):
    # SuperAdministrador is only created from database
    # Only requires CURP for creation (password and other fields are set manually in DB)
    pass

class InspectorCreate(UserCreate):
    # Inherits all UserCreate fields
    # Inspector can be created by administrador or superadministrador
    pass

class UserLogin(UserBase):
    contrasena: str

class UserResponse(UserBase):
    id: UUID
    rol: str
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Bovino Schemas
class BovinoBase(BaseModel):
    arete_barcode: Optional[str] = None
    arete_rfid: Optional[str] = None
    nombre: Optional[str] = None
    madre_id: Optional[UUID] = None
    padre_id: Optional[UUID] = None
    instalacion_id: Optional[UUID] = None
    raza_dominante: Optional[str] = None
    fecha_nac: Optional[date] = None
    sexo: Optional[SexoEnum] = None
    peso_nac: Optional[float] = None
    peso_actual: Optional[float] = None
    proposito: Optional[str] = None

class BovinoCreate(BovinoBase):
    pass

class BovinoUpdate(BaseModel):
    # Only allow updating user-modifiable fields
    # instalacion_id is managed through traslado events
    arete_barcode: Optional[str] = None
    arete_rfid: Optional[str] = None
    nombre: Optional[str] = None
    madre_id: Optional[UUID] = None
    padre_id: Optional[UUID] = None
    raza_dominante: Optional[str] = None
    fecha_nac: Optional[date] = None
    sexo: Optional[SexoEnum] = None
    peso_nac: Optional[float] = None
    peso_actual: Optional[float] = None
    proposito: Optional[str] = None

class BovinoParentPublic(BaseModel):
    """Minimal public-safe projection for a parent bovino owned by a different user."""
    id: UUID
    folio: Optional[str] = None
    raza_dominante: Optional[str] = None
    fecha_nac: Optional[date] = None
    sexo: Optional[SexoEnum] = None

    class Config:
        from_attributes = True

class BovinoResponse(BovinoBase):
    id: UUID
    usuario_id: UUID
    usuario_original_id: Optional[UUID] = None
    nariz_storage_key: Optional[str] = None
    nariz_url: Optional[str] = None
    folio: Optional[str] = None
    status: str
    # Resolved parent projections — None when not requested (list endpoints)
    # Full BovinoResponse if owned by requesting user, BovinoParentPublic otherwise
    madre: Optional[BovinoParentPublic] = None
    padre: Optional[BovinoParentPublic] = None
    instalacion_nombre: Optional[str] = None

    class Config:
        from_attributes = True

# Event Schemas
class EventoBase(BaseModel):
    bovino_id: UUID
    observaciones: Optional[str] = ''

class EventoPesoCreate(EventoBase):
    peso_nuevo: float

class EventoDietaCreate(EventoBase):
    alimento: str

class EventoVacunacionCreate(EventoBase):
    veterinario_id: UUID
    tipo: str
    lote: str
    laboratorio: str
    fecha_prox: date

class EventoDesparasitacionCreate(EventoBase):
    veterinario_id: UUID
    medicamento: str
    dosis: str
    fecha_prox: date

class EventoLaboratorioCreate(EventoBase):
    veterinario_id: UUID
    tipo: str
    resultado: str

class EventoCompraventaCreate(EventoBase):
    comprador_curp: str
    vendedor_curp: str

class EventoTrasladoCreate(EventoBase):
    predio_nuevo_id: UUID

class EventoEnfermedadCreate(EventoBase):
    veterinario_id: UUID
    tipo: str

class EventoTratamientoCreate(EventoBase):
    enfermedad_id: UUID
    veterinario_id: UUID
    medicamento: str
    dosis: str
    periodo: str

class EventoRemisionCreate(EventoBase):
    enfermedad_id: UUID
    veterinario_id: UUID

class EventoCreateGeneral(EventoBase):
    pass

class EventoCreateRequest(BaseModel):
    type: str # 'peso', 'dieta', etc.
    data: dict # unstructured for now to avoid strict union issues, or use Union

class EventoResponse(BaseModel):
    id: UUID
    bovino_id: UUID
    fecha: datetime
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True

# Detailed Event Response Schemas (evento + specific event data)
class PesoDetailResponse(EventoResponse):
    peso_actual: Optional[float] = None
    peso_nuevo: Optional[float] = None

class DietaDetailResponse(EventoResponse):
    alimento: Optional[str] = None

class VacunacionDetailResponse(EventoResponse):
    veterinario_id: Optional[UUID] = None
    tipo: Optional[str] = None
    lote: Optional[str] = None
    laboratorio: Optional[str] = None
    fecha_prox: Optional[date] = None

class DesparasitacionDetailResponse(EventoResponse):
    veterinario_id: Optional[UUID] = None
    medicamento: Optional[str] = None
    dosis_admin: Optional[str] = None
    fecha_prox: Optional[date] = None

class LaboratorioDetailResponse(EventoResponse):
    veterinario_id: Optional[UUID] = None
    tipo: Optional[str] = None
    resultado: Optional[str] = None

class CompraventaDetailResponse(EventoResponse):
    comprador_curp: Optional[str] = None
    vendedor_curp: Optional[str] = None

class TrasladoDetailResponse(EventoResponse):
    predio_anterior_id: Optional[UUID] = None
    predio_nuevo_id: Optional[UUID] = None

class EnfermedadDetailResponse(EventoResponse):
    enfermedad_id: Optional[UUID] = None
    veterinario_id: Optional[UUID] = None
    tipo: Optional[str] = None

class TratamientoDetailResponse(EventoResponse):
    enfermedad_id: Optional[UUID] = None
    veterinario_id: Optional[UUID] = None
    medicamento: Optional[str] = None
    dosis: Optional[str] = None
    periodo: Optional[str] = None

class RemisionDetailResponse(EventoResponse):
    enfermedad_id: Optional[UUID] = None
    veterinario_id: Optional[UUID] = None

# Document Schemas
class DocumentoRevisionCreate(BaseModel):
    status: DocReviewStatusEnum
    comentario: Optional[str] = None

class DocumentoRevisionResponse(BaseModel):
    id: UUID
    documento_id: UUID
    admin_id: UUID
    status: DocReviewStatusEnum
    comentario: Optional[str] = None
    fecha: datetime

    class Config:
        from_attributes = True

class DocumentoResponse(BaseModel):
    id: UUID
    doc_type: DocTypeEnum
    original_filename: str
    created_at: datetime
    authored: bool
    download_url: Optional[str] = None
    ultima_revision: Optional[DocumentoRevisionResponse] = None

    class Config:
        from_attributes = True

# Domicilio Schemas
class DomicilioBase(BaseModel):
    calle: Optional[str] = None
    colonia: Optional[str] = None
    cp: Optional[str] = None
    estado: Optional[str] = None
    municipio: Optional[str] = None

class DomicilioCreate(DomicilioBase):
    pass

class DomicilioUpdate(DomicilioBase):
    pass

class DomicilioResponse(DomicilioBase):
    id: UUID
    usuario_id: UUID

    class Config:
        from_attributes = True

# Predio Schemas
class PredioBase(BaseModel):
    clave_catastral: Optional[str] = None
    superficie_total: Optional[float] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class PredioCreate(PredioBase):
    pass

class PredioUpdate(PredioBase):
    pass

class PredioResponse(PredioBase):
    id: UUID
    usuario_id: UUID

    class Config:
        from_attributes = True

# DatosUsuario Schemas
class DatosUsuarioResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    nombre: str
    apellido_p: str
    apellido_m: Optional[str] = None
    sexo: Optional[SexoEnum] = None
    fecha_nac: Optional[date] = None
    clave_elector: Optional[str] = None
    idmex: Optional[str] = None

    class Config:
        from_attributes = True

# BovinoListResponse - Simplified version for listings
class BovinoListResponse(BaseModel):
    id: UUID
    arete_barcode: Optional[str] = None
    arete_rfid: Optional[str] = None
    nombre: Optional[str] = None
    folio: Optional[str] = None
    raza_dominante: Optional[str] = None
    fecha_nac: Optional[date] = None
    sexo: Optional[SexoEnum] = None
    peso_actual: Optional[float] = None
    status: str
    predio_id: Optional[UUID] = None
    instalacion_nombre: Optional[str] = None

    class Config:
        from_attributes = True

# UserInfoCompleto - Complete user information with all related data
class UserInfoCompleto(BaseModel):
    id: UUID
    curp: str
    rol: str
    created_at: datetime
    datos: Optional[DatosUsuarioResponse] = None
    domicilios: list[DomicilioResponse] = []
    documentos: list[DocumentoResponse] = []
    bovinos: list[BovinoListResponse] = []
    predios: list[PredioResponse] = []

    class Config:
        from_attributes = True

# UserListResponse - Simple user info for listing
class UserListResponse(BaseModel):
    id: UUID
    curp: str
    rol: str
    created_at: datetime
    datos: Optional[DatosUsuarioResponse] = None

    class Config:
        from_attributes = True

# FacilityTypeEnum for installation types
class FacilityTypeEnum(str, Enum):
    UPP = "UPP"
    PSG = "PSG"
    SUBASTA = "SUBASTA"
    RASTRO = "RASTRO"
    FERIA = "FERIA"
    EXPORT_CENTER = "EXPORT_CENTER"
    QUARANTINE_CENTER = "QUARANTINE_CENTER"

# Instalacion Schemas
class InstalacionCreate(BaseModel):
    usuario_id: Optional[UUID] = None
    nombre: str
    facility_type: str
    status: Optional[InstalacionStatusEnum] = InstalacionStatusEnum.pendiente_revision
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: str
    municipio: str
    license_number: str
    active: Optional[bool] = False

class InstalacionUpdate(BaseModel):
    nombre: Optional[str] = None
    status: Optional[InstalacionStatusEnum] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: Optional[str] = None
    municipio: Optional[str] = None
    active: Optional[bool] = None

class InstalacionResponse(BaseModel):
    id: UUID
    usuario_id: UUID
    nombre: str
    facility_type: str
    status: InstalacionStatusEnum
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    estado: str
    municipio: str
    license_number: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class InstalacionDocumentoResponse(BaseModel):
    id: UUID
    instalacion_id: UUID
    documento_id: UUID
    documento_tipo: str
    status: DocReviewStatusEnum
    comentario_rechazo: Optional[str] = None
    review_date: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Instalacion - Predio Linking (DEFINIR ANTES DE InstalacionDetailResponse)
class VincularPredioInstalacionRequest(BaseModel):
    predio_id: UUID

class VincularPredioInstalacionResponse(BaseModel):
    upp_id: UUID
    predio_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

class PredioInstalacionEnriquecida(BaseModel):
    """Predio vinculado a una instalación con información completa del predio"""
    id: UUID
    usuario_id: UUID
    nombre: Optional[str] = None
    municipio: Optional[str] = None
    clave_catastral: Optional[str] = None
    superficie_total: Optional[float] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    linked_at: datetime

    class Config:
        from_attributes = True

class InstalacionDetailResponse(InstalacionResponse):
    documentos: list[InstalacionDocumentoResponse] = []
    predios: list[PredioInstalacionEnriquecida] = []

class RenovacionUPPCreate(BaseModel):
    comentarios: Optional[str] = None

class RenovacionUPPResponse(BaseModel):
    id: UUID
    instalacion_id: UUID
    solicitada_por: UUID
    estado: str
    fecha_solicitud: datetime
    fecha_proximo_vencimiento: Optional[date] = None
    aprobada_por: Optional[UUID] = None
    fecha_aprobacion: Optional[datetime] = None
    comentarios: Optional[str] = None

    class Config:
        from_attributes = True

# Validacion de documentos
class DocumentoStatusResponse(BaseModel):
    documento_tipo: str
    status: DocReviewStatusEnum
    requerido: bool
    descripcion: str

class ValidacionDocumentosResponse(BaseModel):
    instalacion_id: UUID
    documentos_totales: int
    documentos_aprobados: int
    documentos_pendientes: int
    documentos_rechazados: int
    documentos_faltantes: list[DocumentoStatusResponse]
    validacion_completa: bool
    status_recomendado: InstalacionStatusEnum

# Aprobacion de instalacion
class ApproveInstalacionRequest(BaseModel):
    comentarios: Optional[str] = None

class ApproveInstalacionResponse(BaseModel):
    id: UUID
    status: InstalacionStatusEnum
    active: bool
    mensaje: str
    fecha_aprobacion: datetime

    class Config:
        from_attributes = True

# Movilizacion Eventos
class MovilizacionEventoResponse(BaseModel):
    id: UUID
    movilizacion_id: UUID
    estado_viejo: Optional[EstadoMovilizacionEnum] = None
    estado_nuevo: EstadoMovilizacionEnum
    usuario_id: Optional[UUID] = None
    fecha: datetime
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True

# Movilizaciones Schemas
class MovilizacionCreate(BaseModel):
    origen_id: UUID
    destino_id: UUID
    tipo: TipoMovilizacionEnum
    bovino_ids: list[UUID]
    transportista_nombre: str
    placas_vehiculo: str
    observaciones: Optional[str] = None

class MovilizacionApprove(BaseModel):
    observaciones: Optional[str] = None

class MovilizacionLoad(BaseModel):
    placas_vehiculo: Optional[str] = None
    observaciones: Optional[str] = None

class MovilizacionInspect(BaseModel):
    aprobar: bool
    observaciones: Optional[str] = None

class MovilizacionArrive(BaseModel):
    observaciones: Optional[str] = None

class MovilizacionComplete(BaseModel):
    observaciones: Optional[str] = None

class MovilizacionResponse(BaseModel):
    id: UUID
    solicitante_id: UUID
    origen_id: UUID
    destino_id: UUID
    tipo: TipoMovilizacionEnum
    estado: EstadoMovilizacionEnum
    reemo: Optional[str] = None
    transportista_nombre: str
    placas_vehiculo: str

    fecha_solicitud: datetime
    fecha_aprobacion: Optional[datetime] = None
    fecha_cargue: Optional[datetime] = None
    fecha_inspeccion: Optional[datetime] = None
    fecha_llegada: Optional[datetime] = None
    fecha_completada: Optional[datetime] = None
    fecha_cancelacion: Optional[datetime] = None

    aprobado_por_id: Optional[UUID] = None
    inspector_id: Optional[UUID] = None

    documento_exportacion_id: Optional[UUID] = None
    documento_sanitario_id: Optional[UUID] = None
    documento_factura_id: Optional[UUID] = None
    documento_compra_id: Optional[UUID] = None

    observaciones: Optional[str] = None

    # We can include bovine ids
    bovinos: list[BovinoListResponse] = []
    eventos: list[MovilizacionEventoResponse] = []

    class Config:
        from_attributes = True

# Validacion Documentos Movilizacion
class DocumentoStatusMovilizacionResponse(BaseModel):
    documento_tipo: str
    requerido: bool
    presente: bool
    descripcion: str

class ValidacionDocumentosMovilizacionResponse(BaseModel):
    movilizacion_id: UUID
    documentos_totales_requeridos: int
    documentos_presentes: int
    documentos_faltantes: list[DocumentoStatusMovilizacionResponse]
    validacion_completa: bool
# Sanidad Schemas
class SanidadAlert(BaseModel):
    type: SanidadAlertType
    severity: SanidadSeverity
    title: str
    description: str
    location: Optional[str] = None
    date: datetime
    active: bool = True

class SanidadHistoryItem(BaseModel):
    id: UUID
    date: datetime
    type: str # 'peso', 'vacunacion', 'enfermedad', etc.
    title: str
    details: dict
    observaciones: Optional[str] = None
    veterinario: Optional[str] = None

class SanidadDashboardResponse(BaseModel):
    alerts: list[SanidadAlert]
    quarantine_count: int
    active_outbreaks: int
    recent_vaccinations_count: int
    total_active_cases: int

class SanidadBovinoHistoryResponse(BaseModel):
    bovino_id: UUID
    nombre: Optional[str]
    arete_barcode: Optional[str]
    history: list[SanidadHistoryItem]

class SanidadQuarantineResponse(BaseModel):
    bovino_id: UUID
    arete_barcode: Optional[str]
    nombre: Optional[str]
    instalacion_id: UUID
    instalacion_nombre: str
    fecha_inicio: datetime
    motivo: str
