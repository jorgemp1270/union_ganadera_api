-- 1. SETUP & EXTENSIONS
-- ---------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum for Sex ('M' = Male, 'F' = Female, 'X' = Other)
CREATE TYPE sexo_enum AS ENUM ('M', 'F', 'X');

-- Enum for User Roles
CREATE TYPE rol_enum AS ENUM ('usuario', 'veterinario', 'administrador', 'superadministrador', 'inspector', 'ban');

-- Enum for document types
CREATE TYPE doc_type_enum AS ENUM ('identificacion_frente', 'identificacion_reverso', 'comprobante_domicilio', 'predio', 'cedula_veterinario', 'nariz', 'fierro', 'otro');

-- Enum for document review status
CREATE TYPE doc_review_status_enum AS ENUM ('pendiente', 'aprobado', 'rechazado');

-- Enum for facility types
CREATE TYPE facility_type_enum AS ENUM ('UPP', 'PSG', 'SUBASTA', 'RASTRO', 'FERIA', 'EXPORT_CENTER', 'QUARANTINE_CENTER', 'CASETA_INSPECCION');

-- 2. BASE TABLES
-- ---------------------------------------------------------

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    curp VARCHAR(18) NOT NULL UNIQUE,
    contrasena TEXT NOT NULL,
    rol rol_enum DEFAULT 'usuario',

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE domicilios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    calle VARCHAR(100),
    colonia VARCHAR(100),
    cp VARCHAR(10),
    estado VARCHAR(50),
    municipio VARCHAR(50)
);

CREATE TABLE datos_usuario (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL UNIQUE REFERENCES usuarios(id) ON DELETE CASCADE,
    nombre VARCHAR(100) NOT NULL,
    apellido_p VARCHAR(100) NOT NULL,
    apellido_m VARCHAR(100),
    sexo sexo_enum NOT NULL,
    fecha_nac DATE NOT NULL,
    clave_elector VARCHAR(20) NOT NULL,
    idmex VARCHAR(20) NOT NULL
);

CREATE TABLE veterinarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL UNIQUE REFERENCES usuarios(id),
    cedula VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE administradores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL UNIQUE REFERENCES usuarios(id),
    creado_por_id UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE superadministradores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL UNIQUE REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE inspectores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL UNIQUE REFERENCES usuarios(id),
    creado_por_id UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE instalaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    nombre VARCHAR(150) NOT NULL,
    facility_type facility_type_enum NOT NULL,
    status VARCHAR(20) DEFAULT 'activa',
    latitud DECIMAL(9, 6),
    longitud DECIMAL(9, 6),
    estado VARCHAR(50) NOT NULL,
    municipio VARCHAR(50) NOT NULL,
    created_by_admin UUID REFERENCES usuarios(id),
    license_number VARCHAR(50) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    fecha_vencimiento DATE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE predios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    clave_catastral VARCHAR(50) UNIQUE,
    superficie_total DECIMAL(10, 2),
    latitud DECIMAL(9, 6),
    longitud DECIMAL(9, 6)
);

-- Junction table for many-to-many relationship between Instalacion and Predio
CREATE TABLE instalacion_predio (
    upp_id UUID NOT NULL REFERENCES instalaciones(id) ON DELETE CASCADE,
    predio_id UUID NOT NULL REFERENCES predios(id) ON DELETE CASCADE,
    PRIMARY KEY (upp_id, predio_id)
);

-- 3. FILE STORAGE
-- ---------------------------------------------------------
CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id),
    doc_type doc_type_enum NOT NULL,
    storage_key TEXT NOT NULL,
    original_filename TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    authored BOOLEAN DEFAULT FALSE
);

CREATE TABLE instalacion_documentos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instalacion_id UUID NOT NULL REFERENCES instalaciones(id) ON DELETE CASCADE,
    documento_id UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    documento_tipo VARCHAR(50) NOT NULL,
    status doc_review_status_enum DEFAULT 'pendiente',
    comentario_rechazo TEXT,
    review_date TIMESTAMPTZ,
    reviewed_by UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE instalacion_documento_requerimientos (
    id SERIAL PRIMARY KEY,
    facility_type facility_type_enum NOT NULL UNIQUE,
    documentos_requeridos TEXT[] NOT NULL,
    descripcion TEXT
);

CREATE TABLE renovaciones_upp (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instalacion_id UUID NOT NULL REFERENCES instalaciones(id) ON DELETE CASCADE,
    solicitada_por UUID NOT NULL REFERENCES usuarios(id),
    estado VARCHAR(20) DEFAULT 'pendiente',
    fecha_solicitud TIMESTAMPTZ DEFAULT NOW(),
    fecha_proximo_vencimiento DATE,
    aprobada_por UUID REFERENCES usuarios(id),
    fecha_aprobacion TIMESTAMPTZ,
    comentarios TEXT
);

-- 4. LIVESTOCK CORE
-- ---------------------------------------------------------

CREATE TABLE bovinos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id),
    instalacion_id UUID REFERENCES instalaciones(id),

    arete_barcode VARCHAR(50) UNIQUE,
    arete_rfid VARCHAR(50) UNIQUE,
    nariz_storage_key TEXT UNIQUE,
    folio VARCHAR(7) UNIQUE NOT NULL,

    madre_id UUID REFERENCES bovinos(id),
    padre_id UUID REFERENCES bovinos(id),
    usuario_original_id UUID REFERENCES usuarios(id),

    nombre VARCHAR(50),

    raza_dominante VARCHAR(50),
    fecha_nac DATE,
    sexo sexo_enum,
    peso_nac DECIMAL(6, 2),
    peso_actual DECIMAL(6, 2),
    imc DECIMAL(4, 2),
    proposito VARCHAR(50),
    status VARCHAR(20) DEFAULT 'activo'
);

-- 4b. DOCUMENT REVIEW
-- ---------------------------------------------------------
CREATE TABLE documento_revisiones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    documento_id UUID NOT NULL REFERENCES documentos(id) ON DELETE CASCADE,
    admin_id UUID NOT NULL REFERENCES usuarios(id),
    status doc_review_status_enum NOT NULL,
    comentario TEXT,
    fecha TIMESTAMPTZ DEFAULT NOW()
);

-- 5. EVENTS SYSTEM
-- ---------------------------------------------------------
CREATE TABLE eventos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bovino_id UUID NOT NULL REFERENCES bovinos(id) ON DELETE CASCADE,
    fecha TIMESTAMPTZ DEFAULT NOW(),
    observaciones TEXT
);

-- 6. EVENT DETAILS
-- ---------------------------------------------------------

CREATE TABLE dietas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    alimento VARCHAR(100) NOT NULL
);

CREATE TABLE pesos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    peso_actual DECIMAL(6, 2),
    peso_nuevo DECIMAL(6, 2)
);

CREATE TABLE vacunaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    veterinario_id UUID REFERENCES veterinarios(id),
    tipo VARCHAR(100),
    lote VARCHAR(50),
    laboratorio VARCHAR(100),
    fecha_prox DATE
);

CREATE TABLE desparasitaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    veterinario_id UUID REFERENCES veterinarios(id),
    medicamento VARCHAR(100),
    dosis_admin VARCHAR(50),
    fecha_prox DATE
);

CREATE TABLE laboratorios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    veterinario_id UUID REFERENCES veterinarios(id),
    tipo VARCHAR(100),
    resultado TEXT
);

CREATE TABLE compraventas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    comprador_curp VARCHAR(18) REFERENCES usuarios(curp),
    vendedor_curp VARCHAR(18) REFERENCES usuarios(curp)
);

CREATE TABLE traslado (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    predio_anterior_id UUID REFERENCES predios(id), -- NULL when bovino had no predio assigned at time of transfer
    predio_nuevo_id UUID REFERENCES predios(id)
);

-- 7. MEDICAL / PATHOLOGY
-- ---------------------------------------------------------
CREATE TABLE enfermedades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id) ON DELETE CASCADE,
    veterinario_id UUID REFERENCES veterinarios(id),
    tipo VARCHAR(100)
);

CREATE TABLE tratamientos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id),
    enfermedad_id UUID REFERENCES enfermedades(id),
    veterinario_id UUID REFERENCES veterinarios(id),
    medicamento VARCHAR(100),
    dosis VARCHAR(50),
    periodo VARCHAR(50)
);

CREATE TABLE remisiones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    evento_id UUID NOT NULL REFERENCES eventos(id),
    enfermedad_id UUID REFERENCES enfermedades(id),
    veterinario_id UUID REFERENCES veterinarios(id)
);

-- C. Register Remission (Disease resolved, linked to a specific Disease case)
CREATE OR REPLACE FUNCTION registrar_remision(
    _bovino_id UUID,
    _enfermedad_id UUID, -- Must link to an existing disease case
    _usuario_id UUID,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _vet_id UUID;
BEGIN
    SELECT id INTO _vet_id FROM veterinarios WHERE usuario_id = _usuario_id;
    IF _vet_id IS NULL THEN
        RAISE EXCEPTION 'No veterinarian profile found for usuario_id %', _usuario_id;
    END IF;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO remisiones (evento_id, enfermedad_id, veterinario_id)
    VALUES (_evento_id, _enfermedad_id, _vet_id);

    UPDATE bovinos SET status = 'activo' WHERE id = _bovino_id;

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;

-- 8. INDEXES
-- ---------------------------------------------------------
CREATE INDEX idx_usuarios_rol ON usuarios(rol);

CREATE INDEX idx_documento_revisiones_doc ON documento_revisiones(documento_id);
CREATE INDEX idx_documento_revisiones_admin ON documento_revisiones(admin_id);

CREATE INDEX idx_bovinos_usuario ON bovinos(usuario_id);
CREATE INDEX idx_bovinos_instalacion ON bovinos(instalacion_id);
CREATE INDEX idx_bovinos_madre ON bovinos(madre_id);
CREATE INDEX idx_bovinos_padre ON bovinos(padre_id);

CREATE INDEX idx_eventos_bovino ON eventos(bovino_id);
CREATE INDEX idx_eventos_fecha ON eventos(fecha);

CREATE INDEX idx_pesos_evento ON pesos(evento_id);
CREATE INDEX idx_vacunas_evento ON vacunaciones(evento_id);
CREATE INDEX idx_vacunas_vet ON vacunaciones(veterinario_id);
CREATE INDEX idx_enfermedades_evento ON enfermedades(evento_id);

CREATE INDEX idx_instalaciones_usuario ON instalaciones(usuario_id);
CREATE INDEX idx_instalaciones_facility_type ON instalaciones(facility_type);
CREATE INDEX idx_instalaciones_active ON instalaciones(active);
CREATE INDEX idx_instalaciones_fecha_vencimiento ON instalaciones(fecha_vencimiento);

CREATE INDEX idx_predios_facility ON predios(usuario_id);
CREATE INDEX idx_instalacion_predio_upp ON instalacion_predio(upp_id);
CREATE INDEX idx_instalacion_predio_predio ON instalacion_predio(predio_id);

CREATE INDEX idx_instalacion_documentos_instalacion ON instalacion_documentos(instalacion_id);
CREATE INDEX idx_instalacion_documentos_documento ON instalacion_documentos(documento_id);
CREATE INDEX idx_instalacion_documentos_status ON instalacion_documentos(status);

CREATE INDEX idx_renovaciones_upp_instalacion ON renovaciones_upp(instalacion_id);
CREATE INDEX idx_renovaciones_upp_estado ON renovaciones_upp(estado);

-- 9. TRIGGERS & FUNCTIONS (Automation)
-- ---------------------------------------------------------

-- C. Document Review Automation
-- Automatically syncs documentos.authored when a revision is inserted
CREATE OR REPLACE FUNCTION sync_documento_authored()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'aprobado' THEN
        UPDATE documentos SET authored = TRUE WHERE id = NEW.documento_id;
    ELSE
        UPDATE documentos SET authored = FALSE WHERE id = NEW.documento_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_authored
AFTER INSERT ON documento_revisiones
FOR EACH ROW
EXECUTE FUNCTION sync_documento_authored();


-- A. Weight Automation
-- Automatically updates the cow's current weight when a 'peso' event is added
CREATE OR REPLACE FUNCTION update_cow_current_weight()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE bovinos
    SET peso_actual = NEW.peso_nuevo
    FROM eventos
    WHERE bovinos.id = eventos.bovino_id
    AND eventos.id = NEW.evento_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_auto_update_weight
AFTER INSERT ON pesos
FOR EACH ROW
EXECUTE FUNCTION update_cow_current_weight();


-- B. Transfer Ownership Automation (NEW)
-- Automatically changes owner and clears location when a 'compraventa' event is added
CREATE OR REPLACE FUNCTION handle_compraventa_transfer()
RETURNS TRIGGER AS $$
DECLARE
    _comprador_id UUID;
BEGIN
    -- Convert comprador CURP to UUID
    SELECT id INTO _comprador_id FROM usuarios WHERE curp = NEW.comprador_curp;

    -- Update the cow linked to this event:
    -- 1. Set new owner (comprador_id from CURP)
    -- 2. Clear the location (predio_id) so the new owner can assign one later
    UPDATE bovinos
    SET
        usuario_id = _comprador_id,
        predio_id = NULL
    FROM eventos
    WHERE bovinos.id = eventos.bovino_id
    AND eventos.id = NEW.evento_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_transfer_ownership
AFTER INSERT ON compraventas
FOR EACH ROW
EXECUTE FUNCTION handle_compraventa_transfer();

CREATE OR REPLACE FUNCTION registrar_usuario_nuevo(
    -- 1. Login Credentials
    _curp VARCHAR,
    _contrasena TEXT, -- Must be hashed BEFORE sending here
    _rol rol_enum,

    -- 2. Personal Data
    _nombre VARCHAR,
    _apellido_p VARCHAR,
    _apellido_m VARCHAR,
    _sexo sexo_enum,
    _fecha_nac DATE,
    _clave_elector VARCHAR,
    _idmex VARCHAR
) RETURNS UUID AS $$
DECLARE
    _new_user_id UUID;
BEGIN
    -- Step 1: Create the User (Login)
    INSERT INTO usuarios (curp, contrasena, rol)
    VALUES (_curp, _contrasena, _rol)
    RETURNING id INTO _new_user_id;

    -- Step 2: Create the Profile Data
    INSERT INTO datos_usuario (
        usuario_id,
        nombre,
        apellido_p,
        apellido_m,
        sexo,
        fecha_nac,
        clave_elector,
        idmex
    )
    VALUES (
        _new_user_id,
        _nombre,
        _apellido_p,
        _apellido_m,
        _sexo,
        _fecha_nac,
        _clave_elector,
        _idmex
    );

    -- Step 3: Return the UUID to the API
    RETURN _new_user_id;
END;
$$ LANGUAGE plpgsql;

-- ==============================================================================
-- 1. PRODUCTION EVENTS (Weights, Diets)
-- ==============================================================================

-- A. Register Weight (Auto-updates cow weight via Trigger)
CREATE OR REPLACE FUNCTION registrar_peso(
    _bovino_id UUID,
    _peso_nuevo DECIMAL,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _peso_anterior DECIMAL;
BEGIN
    -- 1. Get current weight for history
    SELECT peso_actual INTO _peso_anterior FROM bovinos WHERE id = _bovino_id;

    -- 2. Create Event
    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    -- 3. Create Detail
    INSERT INTO pesos (evento_id, peso_actual, peso_nuevo)
    VALUES (_evento_id, COALESCE(_peso_anterior, 0), _peso_nuevo);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- B. Register Diet Change
CREATE OR REPLACE FUNCTION registrar_dieta(
    _bovino_id UUID,
    _alimento VARCHAR,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
BEGIN
    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO dietas (evento_id, alimento)
    VALUES (_evento_id, _alimento);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- ==============================================================================
-- 2. HEALTH EVENTS (Vaccines, Deworming, Labs)
-- ==============================================================================

-- A. Register Vaccination
CREATE OR REPLACE FUNCTION registrar_vacunacion(
    _bovino_id UUID,
    _usuario_id UUID,
    _tipo VARCHAR, -- e.g. "Fiebre Aftosa"
    _lote VARCHAR,
    _laboratorio VARCHAR,
    _fecha_prox DATE,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _vet_id UUID;
BEGIN
    SELECT id INTO _vet_id FROM veterinarios WHERE usuario_id = _usuario_id;
    IF _vet_id IS NULL THEN
        RAISE EXCEPTION 'No veterinarian profile found for usuario_id %', _usuario_id;
    END IF;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO vacunaciones (evento_id, veterinario_id, tipo, lote, laboratorio, fecha_prox)
    VALUES (_evento_id, _vet_id, _tipo, _lote, _laboratorio, _fecha_prox);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- B. Register Deworming (Desparasitación)
CREATE OR REPLACE FUNCTION registrar_desparasitacion(
    _bovino_id UUID,
    _usuario_id UUID,
    _medicamento VARCHAR,
    _dosis VARCHAR,
    _fecha_prox DATE,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _vet_id UUID;
BEGIN
    SELECT id INTO _vet_id FROM veterinarios WHERE usuario_id = _usuario_id;
    IF _vet_id IS NULL THEN
        RAISE EXCEPTION 'No veterinarian profile found for usuario_id %', _usuario_id;
    END IF;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO desparasitaciones (evento_id, veterinario_id, medicamento, dosis_admin, fecha_prox)
    VALUES (_evento_id, _vet_id, _medicamento, _dosis, _fecha_prox);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- C. Register Lab Test
CREATE OR REPLACE FUNCTION registrar_laboratorio(
    _bovino_id UUID,
    _usuario_id UUID,
    _tipo VARCHAR, -- e.g. "Sangre"
    _resultado TEXT,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _vet_id UUID;
BEGIN
    SELECT id INTO _vet_id FROM veterinarios WHERE usuario_id = _usuario_id;
    IF _vet_id IS NULL THEN
        RAISE EXCEPTION 'No veterinarian profile found for usuario_id %', _usuario_id;
    END IF;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO laboratorios (evento_id, veterinario_id, tipo, resultado)
    VALUES (_evento_id, _vet_id, _tipo, _resultado);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- ==============================================================================
-- 3. MOVEMENT & SALES (Transfers, Sales)
-- ==============================================================================

-- A. Register Sale (Triggers ownership transfer automatically)
CREATE OR REPLACE FUNCTION registrar_compraventa(
    _bovino_id UUID,
    _comprador_curp VARCHAR(18),
    _vendedor_curp VARCHAR(18),
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _comprador_id UUID;
BEGIN
    -- Get comprador UUID from CURP
    SELECT id INTO _comprador_id FROM usuarios WHERE curp = _comprador_curp;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    -- This INSERT will fire the 'trg_transfer_ownership' trigger
    INSERT INTO compraventas (evento_id, comprador_curp, vendedor_curp)
    VALUES (_evento_id, _comprador_curp, _vendedor_curp);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- B. Register Movement (Traslado)
CREATE OR REPLACE FUNCTION registrar_traslado(
    _bovino_id UUID,
    _predio_nuevo_id UUID,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _predio_anterior_id UUID;
BEGIN
    -- 1. Get current location
    SELECT predio_id INTO _predio_anterior_id FROM bovinos WHERE id = _bovino_id;

    -- 2. Create Event
    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    -- 3. Create Detail
    INSERT INTO traslado (evento_id, predio_anterior_id, predio_nuevo_id)
    VALUES (_evento_id, _predio_anterior_id, _predio_nuevo_id);

    -- 4. Update the cow's location (Manual update required here, unlike Sales)
    UPDATE bovinos SET predio_id = _predio_nuevo_id WHERE id = _bovino_id;

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;


-- ==============================================================================
-- 4. MEDICAL CHAIN (Disease -> Treatment -> Remission)
-- ==============================================================================

-- A. Register Disease Detection (Start of chain)
CREATE OR REPLACE FUNCTION registrar_enfermedad(
    _bovino_id UUID,
    _usuario_id UUID,
    _tipo VARCHAR, -- Diagnosis
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _enfermedad_id UUID;
    _vet_id UUID;
BEGIN
    SELECT id INTO _vet_id FROM veterinarios WHERE usuario_id = _usuario_id;
    IF _vet_id IS NULL THEN
        RAISE EXCEPTION 'No veterinarian profile found for usuario_id %', _usuario_id;
    END IF;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO enfermedades (evento_id, veterinario_id, tipo)
    VALUES (_evento_id, _vet_id, _tipo)
    RETURNING id INTO _enfermedad_id;

    UPDATE bovinos SET status = 'enfermo' WHERE id = _bovino_id;

    -- Return Disease ID so the frontend can immediately link a treatment to it
    RETURN _enfermedad_id;
END;
$$ LANGUAGE plpgsql;


-- B. Register Treatment (Linked to a specific Disease)
CREATE OR REPLACE FUNCTION registrar_tratamiento(
    _bovino_id UUID,
    _enfermedad_id UUID, -- Must link to an existing disease case
    _usuario_id UUID,
    _medicamento VARCHAR,
    _dosis VARCHAR,
    _periodo VARCHAR,
    _fecha TIMESTAMPTZ DEFAULT NOW(),
    _observaciones TEXT DEFAULT ''
) RETURNS UUID AS $$
DECLARE
    _evento_id UUID;
    _vet_id UUID;
BEGIN
    SELECT id INTO _vet_id FROM veterinarios WHERE usuario_id = _usuario_id;
    IF _vet_id IS NULL THEN
        RAISE EXCEPTION 'No veterinarian profile found for usuario_id %', _usuario_id;
    END IF;

    INSERT INTO eventos (bovino_id, fecha, observaciones)
    VALUES (_bovino_id, _fecha, _observaciones)
    RETURNING id INTO _evento_id;

    INSERT INTO tratamientos (evento_id, enfermedad_id, veterinario_id, medicamento, dosis, periodo)
    VALUES (_evento_id, _enfermedad_id, _vet_id, _medicamento, _dosis, _periodo);

    RETURN _evento_id;
END;
$$ LANGUAGE plpgsql;

-- 10. INITIALIZATION DATA
-- ---------------------------------------------------------

-- Document requirements for each facility type
INSERT INTO instalacion_documento_requerimientos (facility_type, documentos_requeridos, descripcion) VALUES
('UPP', ARRAY['constancia_fiscal', 'certificado_parcelario', 'contrato_arrendamiento', 'clave_catastral'], 'Unidad de Producción Pecuaria - Productor ganadero'),
('PSG', ARRAY['identificacion', 'rfc', 'comprobante_domicilio', 'acta_constitutiva', 'permiso_funcionamiento'], 'Productor de Servicios Ganaderos - Centro de servicios'),
('SUBASTA', ARRAY['permiso_subasta', 'comprobante_domicilio', 'rfc', 'identificacion'], 'Subasta ganadera'),
('RASTRO', ARRAY['permiso_rastro', 'certificado_inspecciones', 'rfc', 'identificacion'], 'Centro de sacrificio'),
('FERIA', ARRAY['permiso_feria', 'comprobante_domicilio', 'rfc'], 'Feria ganadera'),
('EXPORT_CENTER', ARRAY['permiso_exportacion', 'certificado_calidad', 'rfc', 'identificacion', 'comprobante_domicilio'], 'Centro de exportación'),
('QUARANTINE_CENTER', ARRAY['permiso_cuarentena', 'comprobante_domicilio', 'rfc', 'certificado_veterinario'], 'Centro de cuarentena');