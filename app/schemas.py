from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime
from uuid import UUID
from enum import Enum

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
    predio_id: Optional[UUID] = None
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
    arete_barcode: Optional[str] = None
    arete_rfid: Optional[str] = None
    nombre: Optional[str] = None
    madre_id: Optional[UUID] = None
    padre_id: Optional[UUID] = None
    predio_id: Optional[UUID] = None
    raza_dominante: Optional[str] = None
    fecha_nac: Optional[date] = None
    sexo: Optional[SexoEnum] = None
    peso_nac: Optional[float] = None
    peso_actual: Optional[float] = None
    proposito: Optional[str] = None

class BovinoResponse(BovinoBase):
    id: UUID
    usuario_id: UUID
    usuario_original_id: Optional[UUID] = None
    nariz_storage_key: Optional[str] = None
    nariz_url: Optional[str] = None
    folio: Optional[str] = None
    status: str

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

# Document Schemas
class DocumentoResponse(BaseModel):
    id: UUID
    doc_type: DocTypeEnum
    original_filename: str
    created_at: datetime
    authored: bool
    download_url: Optional[str] = None

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
