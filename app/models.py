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

class TipoMovilizacionEnum(str, enum.Enum):
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

class EstadoMovilizacionEnum(str, enum.Enum):
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
    CASETA_INSPECCION = "CASETA_INSPECCION"

class InstalacionStatusEnum(str, enum.Enum):
    pendiente_revision = "pendiente_revision"
    documentos_incompletos = "documentos_incompletos"
    documentos_rechazados = "documentos_rechazados"
    lista_operar = "lista_operar"
    activa = "activa"
    inactiva = "inactiva"

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
    instalaciones = relationship("Instalacion", back_populates="usuario", foreign_keys="[Instalacion.usuario_id]")

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
    instalacion_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id"), nullable=True)

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
    instalacion = relationship("Instalacion", back_populates="bovinos")

    madre = relationship("Bovino", remote_side=[id], foreign_keys=[madre_id])
    padre = relationship("Bovino", remote_side=[id], foreign_keys=[padre_id])

    @property
    def instalacion_nombre(self):
        return self.instalacion.nombre if self.instalacion else None

class Predio(Base):
    __tablename__ = "predios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    clave_catastral = Column(String(50), unique=True)
    superficie_total = Column(Numeric(10, 2))
    latitud = Column(Numeric(9, 6))
    longitud = Column(Numeric(9, 6))

    usuario = relationship("Usuario", back_populates="predios")
    instalaciones = relationship("InstalacionPredio", back_populates="predio", cascade="all, delete-orphan")

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
    status = Column(Enum(InstalacionStatusEnum), default=InstalacionStatusEnum.pendiente_revision)
    latitud = Column(Numeric(9, 6))
    longitud = Column(Numeric(9, 6))
    estado = Column(String(50), nullable=False)
    municipio = Column(String(50), nullable=False)
    created_by_admin = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    license_number = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=False)  # Only True when status = "activa" and approved by admin
    fecha_vencimiento = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    usuario = relationship("Usuario", back_populates="instalaciones", foreign_keys=[usuario_id])
    predios = relationship("InstalacionPredio", back_populates="instalacion", cascade="all, delete-orphan")
    bovinos = relationship("Bovino", back_populates="instalacion")
    documentos = relationship("InstalacionDocumento", back_populates="instalacion", cascade="all, delete-orphan")
    renovaciones = relationship("RenovacionUPP", back_populates="instalacion", cascade="all, delete-orphan")


class InstalacionPredio(Base):
    """Junction table for many-to-many relationship between Instalacion and Predio"""
    __tablename__ = "instalacion_predio"

    upp_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    predio_id = Column(UUID(as_uuid=True), ForeignKey("predios.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    instalacion = relationship("Instalacion", back_populates="predios")
    predio = relationship("Predio", back_populates="instalaciones")


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

class Movilizacion(Base):
    __tablename__ = "movilizaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    solicitante_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    origen_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id"), nullable=False)
    destino_id = Column(UUID(as_uuid=True), ForeignKey("instalaciones.id"), nullable=False)
    tipo = Column(Enum(TipoMovilizacionEnum), nullable=False)
    estado = Column(Enum(EstadoMovilizacionEnum), default=EstadoMovilizacionEnum.DRAFT)
    reemo = Column(String(50), unique=True, nullable=True)
    transportista_nombre = Column(String(150), nullable=False)
    placas_vehiculo = Column(String(20), nullable=False)

    fecha_solicitud = Column(DateTime(timezone=True), server_default=func.now())
    fecha_aprobacion = Column(DateTime(timezone=True), nullable=True)
    fecha_cargue = Column(DateTime(timezone=True), nullable=True)
    fecha_inspeccion = Column(DateTime(timezone=True), nullable=True)
    fecha_llegada = Column(DateTime(timezone=True), nullable=True)
    fecha_completada = Column(DateTime(timezone=True), nullable=True)
    fecha_cancelacion = Column(DateTime(timezone=True), nullable=True)

    aprobado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    inspector_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)

    documento_exportacion_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True)
    documento_sanitario_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True)
    documento_factura_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True)
    documento_compra_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True)

    observaciones = Column(Text, nullable=True)

    # Relationships
    solicitante = relationship("Usuario", foreign_keys=[solicitante_id])
    origen = relationship("Instalacion", foreign_keys=[origen_id])
    destino = relationship("Instalacion", foreign_keys=[destino_id])
    aprobado_por = relationship("Usuario", foreign_keys=[aprobado_por_id])
    inspector = relationship("Usuario", foreign_keys=[inspector_id])
    
    documento_exportacion = relationship("Documento", foreign_keys=[documento_exportacion_id])
    documento_sanitario = relationship("Documento", foreign_keys=[documento_sanitario_id])
    documento_factura = relationship("Documento", foreign_keys=[documento_factura_id])
    documento_compra = relationship("Documento", foreign_keys=[documento_compra_id])

    bovinos = relationship("MovilizacionBovino", back_populates="movilizacion", cascade="all, delete-orphan")
    eventos = relationship("MovilizacionEvento", back_populates="movilizacion", cascade="all, delete-orphan")

class MovilizacionBovino(Base):
    __tablename__ = "movilizacion_bovinos"

    movilizacion_id = Column(UUID(as_uuid=True), ForeignKey("movilizaciones.id", ondelete="CASCADE"), primary_key=True)
    bovino_id = Column(UUID(as_uuid=True), ForeignKey("bovinos.id", ondelete="CASCADE"), primary_key=True)

    movilizacion = relationship("Movilizacion", back_populates="bovinos")
    bovino = relationship("Bovino")

class MovilizacionEvento(Base):
    __tablename__ = "movilizacion_eventos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    movilizacion_id = Column(UUID(as_uuid=True), ForeignKey("movilizaciones.id", ondelete="CASCADE"), nullable=False)
    estado_viejo = Column(Enum(EstadoMovilizacionEnum), nullable=True)
    estado_nuevo = Column(Enum(EstadoMovilizacionEnum), nullable=False)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    fecha = Column(DateTime(timezone=True), server_default=func.now())
    observaciones = Column(Text, nullable=True)

    movilizacion = relationship("Movilizacion", back_populates="eventos")
    usuario = relationship("Usuario", foreign_keys=[usuario_id])
