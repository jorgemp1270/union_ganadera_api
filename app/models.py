from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Enum, Date, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from .database import Base

class SexoEnum(str, enum.Enum):
    M = "M"
    F = "F"
    X = "X"

class RolEnum(str, enum.Enum):
    usuario = "usuario"
    veterinario = "veterinario"
    administrador = "administrador"
    superadministrador = "superadministrador"
    inspector = "inspector"
    ban = "ban"

class DocTypeEnum(str, enum.Enum):
    identificacion_frente = "identificacion_frente"
    identificacion_reverso = "identificacion_reverso"
    comprobante_domicilio = "comprobante_domicilio"
    predio = "predio"
    cedula_veterinario = "cedula_veterinario"
    fierro = "fierro"
    otro = "otro"

class DocReviewStatusEnum(str, enum.Enum):
    pendiente = "pendiente"
    aprobado = "aprobado"
    rechazado = "rechazado"

class FacilityTypeEnum(str, enum.Enum):
    UPP = "UPP"
    PSG = "PSG"
    SUBASTA = "SUBASTA"
    RASTRO = "RASTRO"
    FERIA = "FERIA"
    EXPORT_CENTER = "EXPORT_CENTER"
    QUARANTINE_CENTER = "QUARANTINE_CENTER"

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curp = Column(String, unique=True, nullable=False)
    contrasena = Column(String, nullable=False)
    rol = Column(Enum(RolEnum), default=RolEnum.usuario)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    datos = relationship("DatosUsuario", back_populates="usuario_rel", uselist=False)
    bovinos = relationship("Bovino", back_populates="usuario", foreign_keys="[Bovino.usuario_id]")
    documentos = relationship("Documento", back_populates="usuario")
    domicilios = relationship("Domicilio", back_populates="usuario")
    predios = relationship("Predio", back_populates="usuario")
    instalaciones = relationship("Instalacion", back_populates="usuario")

class Domicilio(Base):
    __tablename__ = "domicilios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    calle = Column(String(100))
    colonia = Column(String(100))
    cp = Column(String(10))
    estado = Column(String(50))
    municipio = Column(String(50))

    usuario = relationship("Usuario", back_populates="domicilios")

class DatosUsuario(Base):
    __tablename__ = "datos_usuario"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True)
    nombre = Column(String, nullable=False)
    apellido_p = Column(String, nullable=False)
    apellido_m = Column(String)
    sexo = Column(Enum(SexoEnum))
    fecha_nac = Column(Date)
    clave_elector = Column(String)
    idmex = Column(String)

    usuario_rel = relationship("Usuario", back_populates="datos")

class Veterinario(Base):
    __tablename__ = "veterinarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    cedula = Column(String(50), unique=True, nullable=False)

    usuario = relationship("Usuario")

class Administrador(Base):
    __tablename__ = "administradores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])

class SuperAdministrador(Base):
    __tablename__ = "superadministradores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario")

class Inspector(Base):
    __tablename__ = "inspectores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), unique=True, nullable=False)
    creado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    creado_por = relationship("Usuario", foreign_keys=[creado_por_id])

class Bovino(Base):
    __tablename__ = "bovinos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    predio_id = Column(UUID(as_uuid=True), ForeignKey("predios.id"), nullable=True)

    arete_barcode = Column(String, unique=True)
    arete_rfid = Column(String, unique=True)
    nariz_storage_key = Column(String, unique=True, nullable=True)
    folio = Column(String(7), unique=True, nullable=True)

    madre_id = Column(UUID(as_uuid=True), ForeignKey("bovinos.id"), nullable=True)
    padre_id = Column(UUID(as_uuid=True), ForeignKey("bovinos.id"), nullable=True)
    usuario_original_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    nombre = Column(String, nullable=True)

    raza_dominante = Column(String)
    fecha_nac = Column(Date)
    sexo = Column(Enum(SexoEnum))
    peso_nac = Column(Numeric(6, 2))
    peso_actual = Column(Numeric(6, 2))
    imc = Column(Numeric(4, 2))
    proposito = Column(String)
    status = Column(String, default="activo")

    usuario = relationship("Usuario", back_populates="bovinos", foreign_keys=[usuario_id])
    eventos = relationship("Evento", back_populates="bovino")
    predio = relationship("Predio", back_populates="bovinos")

class Predio(Base):
    __tablename__ = "predios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    facility_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id"), nullable=True)
    clave_catastral = Column(String(50), unique=True)
    superficie_total = Column(Numeric(10, 2))
    latitud = Column(Numeric(9, 6))
    longitud = Column(Numeric(9, 6))

    usuario = relationship("Usuario", back_populates="predios")
    bovinos = relationship("Bovino", back_populates="predio")
    instalacion = relationship("Instalacion", back_populates="predios")

class Evento(Base):
    __tablename__ = "eventos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bovino_id = Column(UUID(as_uuid=True), ForeignKey("bovinos.id"))
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    observaciones = Column(Text)

    bovino = relationship("Bovino", back_populates="eventos")

# Event Detail Models
class Peso(Base):
    __tablename__ = "pesos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    peso_actual = Column(Numeric(6, 2))
    peso_nuevo = Column(Numeric(6, 2))

class Dieta(Base):
    __tablename__ = "dietas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    alimento = Column(String(100), nullable=False)

class Vacunacion(Base):
    __tablename__ = "vacunaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    veterinario_id = Column(UUID(as_uuid=True))
    tipo = Column(String(100))
    lote = Column(String(50))
    laboratorio = Column(String(100))
    fecha_prox = Column(Date)

class Desparasitacion(Base):
    __tablename__ = "desparasitaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    veterinario_id = Column(UUID(as_uuid=True))
    medicamento = Column(String(100))
    dosis_admin = Column(String(50))
    fecha_prox = Column(Date)

class Laboratorio(Base):
    __tablename__ = "laboratorios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    veterinario_id = Column(UUID(as_uuid=True))
    tipo = Column(String(100))
    resultado = Column(Text)

class Compraventa(Base):
    __tablename__ = "compraventas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    comprador_curp = Column(String(18))
    vendedor_curp = Column(String(18))

class Traslado(Base):
    __tablename__ = "traslado"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    predio_anterior_id = Column(UUID(as_uuid=True))
    predio_nuevo_id = Column(UUID(as_uuid=True))

class Enfermedad(Base):
    __tablename__ = "enfermedades"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    veterinario_id = Column(UUID(as_uuid=True))
    tipo = Column(String(100))

class Tratamiento(Base):
    __tablename__ = "tratamientos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    enfermedad_id = Column(UUID(as_uuid=True), ForeignKey("enfermedades.id"), nullable=True)
    veterinario_id = Column(UUID(as_uuid=True))
    medicamento = Column(String(100))
    dosis = Column(String(50))
    periodo = Column(String(50))

class Remision(Base):
    __tablename__ = "remisiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"))
    enfermedad_id = Column(UUID(as_uuid=True), ForeignKey("enfermedades.id"), nullable=True)
    veterinario_id = Column(UUID(as_uuid=True))

class Documento(Base):
    __tablename__ = "documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"))
    doc_type = Column(Enum(DocTypeEnum), nullable=False)
    storage_key = Column(Text, nullable=False)
    original_filename = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    authored = Column(Boolean, default=False)

    usuario = relationship("Usuario", back_populates="documentos")
    revisiones = relationship(
        "DocumentoRevision",
        back_populates="documento",
        cascade="all, delete-orphan"
    )


class DocumentoRevision(Base):
    __tablename__ = "documento_revisiones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    status = Column(Enum(DocReviewStatusEnum), nullable=False)
    comentario = Column(Text, nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())

    documento = relationship("Documento", back_populates="revisiones")
    admin = relationship("Usuario", foreign_keys=[admin_id])


class Instalacion(Base):
    __tablename__ = "instalaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    nombre = Column(String(150), nullable=False)
    facility_type = Column(Enum(FacilityTypeEnum), nullable=False)
    status = Column(String(20), default="activa")
    latitud = Column(Numeric(9, 6))
    longitud = Column(Numeric(9, 6))
    estado = Column(String(50), nullable=False)
    municipio = Column(String(50), nullable=False)
    created_by_admin = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    license_number = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="instalaciones", foreign_keys=[usuario_id])
    predios = relationship("Predio", back_populates="instalacion")
    documentos = relationship("InstalacionDocumento", back_populates="instalacion", cascade="all, delete-orphan")
    renovaciones = relationship("RenovacionUPP", back_populates="instalacion", cascade="all, delete-orphan")


class InstalacionDocumento(Base):
    __tablename__ = "instalacion_documentos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instalacion_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id", ondelete="CASCADE"), nullable=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id", ondelete="CASCADE"), nullable=False)
    documento_tipo = Column(String(50), nullable=False)
    status = Column(Enum(DocReviewStatusEnum), default=DocReviewStatusEnum.pendiente)
    comentario_rechazo = Column(Text, nullable=True)
    review_date = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    instalacion = relationship("Instalacion", back_populates="documentos")
    documento = relationship("Documento")
    reviewer = relationship("Usuario", foreign_keys=[reviewed_by])


class RenovacionUPP(Base):
    __tablename__ = "renovaciones_upp"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instalacion_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id", ondelete="CASCADE"), nullable=False)
    solicitada_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estado = Column(String(20), default="pendiente")
    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    fecha_proximo_vencimiento = Column(Date, nullable=True)
    aprobada_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha_aprobacion = Column(DateTime(timezone=True), nullable=True)
    comentarios = Column(Text, nullable=True)

    instalacion = relationship("Instalacion", back_populates="renovaciones")
    solicitante = relationship("Usuario", foreign_keys=[solicitada_por])
    aprobador = relationship("Usuario", foreign_keys=[aprobada_por])
