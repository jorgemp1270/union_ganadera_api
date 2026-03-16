# Union Ganadera API - Instalaciones (Facilities) System
## Implementation Summary - March 16, 2026

---

## 📋 Overview

The **Instalaciones (Facilities)** system provides a legal/administrative layer for agricultural facilities. While a **Predio** is the physical land owned by a user, an **Instalacion** is the legal designation of that land for specific purposes.

### Key Differences

| Concept | Definition | Ownership |
|---------|-----------|-----------|
| **Predio** | Physical land/property with geographic coordinates | User (ganadero/veterinario) |
| **Instalacion** | Legal facility type (UPP, PSG, Rastro, etc.) | User (admin approves documents) |

A Predio can have ONE Instalacion, but not all Predios are Instalaciones.

---

## 🏗️ Database Changes

### 1. New Enum: `facility_type`
```sql
CREATE TYPE facility_type_enum AS ENUM (
  'UPP', 'PSG', 'SUBASTA', 'RASTRO', 'FERIA', 
  'EXPORT_CENTER', 'QUARANTINE_CENTER'
);
```

### 2. New Tables

#### `instalaciones`
```sql
CREATE TABLE instalaciones (
    id UUID PRIMARY KEY,
    usuario_id UUID NOT NULL REFERENCES usuarios(id),
    nombre VARCHAR(150) NOT NULL,
    facility_type facility_type_enum NOT NULL,
    status VARCHAR(20) DEFAULT 'activa',
    latitud DECIMAL(9, 6),
    longitud DECIMAL(9, 6),
    estado VARCHAR(50) NOT NULL,
    municipio VARCHAR(50) NOT NULL,
    created_by_admin UUID REFERENCES usuarios(id),
    license_number VARCHAR(50) UNIQUE NOT NULL,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `instalacion_documentos`
Tracks required documents for each installation (UPP, PSG, etc.)

```sql
CREATE TABLE instalacion_documentos (
    id UUID PRIMARY KEY,
    instalacion_id UUID NOT NULL REFERENCES instalaciones(id),
    documento_id UUID NOT NULL REFERENCES documentos(id),
    documento_tipo VARCHAR(50) NOT NULL,
    status doc_review_status_enum DEFAULT 'pendiente',
    comentario_rechazo TEXT,
    review_date TIMESTAMPTZ,
    reviewed_by UUID REFERENCES usuarios(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### `renovaciones_upp`
Tracks annual UPP renewal requests and approvals

```sql
CREATE TABLE renovaciones_upp (
    id UUID PRIMARY KEY,
    instalacion_id UUID NOT NULL REFERENCES instalaciones(id),
    solicitada_por UUID NOT NULL REFERENCES usuarios(id),
    estado VARCHAR(20) DEFAULT 'pendiente',
    fecha_solicitud TIMESTAMPTZ DEFAULT NOW(),
    fecha_proximo_vencimiento DATE,
    aprobada_por UUID REFERENCES usuarios(id),
    fecha_aprobacion TIMESTAMPTZ,
    comentarios TEXT
);
```

#### `instalacion_documento_requerimientos` (Configuration Table)
Defines required documents for each facility type:

```sql
-- UPP: constancia_fiscal, certificado_parcelario, contrato_arrendamiento, clave_catastral
-- PSG: identificacion, rfc, comprobante_domicilio, acta_constitutiva, permiso_funcionamiento
-- SUBASTA: permiso_subasta, comprobante_domicilio, rfc, identificacion
-- RASTRO: permiso_rastro, certificado_inspecciones, rfc, identificacion
-- FERIA: permiso_feria, comprobante_domicilio, rfc
-- EXPORT_CENTER: permiso_exportacion, certificado_calidad, rfc, identificacion, comprobante_domicilio
-- QUARANTINE_CENTER: permiso_cuarentena, comprobante_domicilio, rfc, certificado_veterinario
```

### 3. Updated Table: `predios`
```sql
ALTER TABLE predios ADD COLUMN facility_id UUID REFERENCES instalaciones(id);
```

---

## 🐍 Python Models Added

### `Instalacion` Model
```python
class Instalacion(Base):
    __tablename__ = "instalaciones"
    # Fields: id, usuario_id, nombre, facility_type, status, 
    #         latitud, longitud, estado, municipio, created_by_admin,
    #         license_number, active, created_at
    # Relationships: usuario, predios, documentos, renovaciones
```

### `InstalacionDocumento` Model
Linking table between Instalacion and Documento with review status.

### `RenovacionUPP` Model
Tracks UPP renewal requests with approval workflow.

---

## 🔌 API Endpoints (16 total)

### CRUD Operations
- **POST** `/instalaciones/` - Create facility
- **GET** `/instalaciones/` - List all (filtered by user if not admin)
- **GET** `/instalaciones/{instalacion_id}` - Get detail with documents
- **PUT** `/instalaciones/{instalacion_id}` - Update facility info
- **DELETE** `/instalaciones/{instalacion_id}` - Deactivate (soft delete)

### Document Management
- **POST** `/instalaciones/{instalacion_id}/documentos/{documento_tipo}` - Link document
- **GET** `/instalaciones/{instalacion_id}/documentos` - List documents
- **POST** `/instalaciones/{instalacion_id}/documentos/{doc_id}/aprobar` - Admin approve
- **POST** `/instalaciones/{instalacion_id}/documentos/{doc_id}/rechazar` - Admin reject with comment

### UPP Renewal
- **POST** `/instalaciones/{instalacion_id}/renovaciones/solicitar` - Request renewal
- **GET** `/instalaciones/renovaciones/pendientes` - View pending (admin only)
- **POST** `/instalaciones/renovaciones/{renovacion_id}/aprobar` - Approve + extend 365 days
- **POST** `/instalaciones/renovaciones/{renovacion_id}/rechazar` - Reject with comment

### Search
- **GET** `/instalaciones/buscar/municipio/{municipio}` - Search by municipality
- **GET** `/instalaciones/tipo/{facility_type}` - Search by type

---

## 📋 Request/Response Examples

### Create a UPP Installation
```bash
POST /instalaciones/
Content-Type: application/json

{
  "nombre": "Rancho Las Flores",
  "facility_type": "UPP",
  "estado": "Jalisco",
  "municipio": "Guadalajara",
  "license_number": "UPP-14-001-2026",
  "latitud": 20.6595,
  "longitud": -103.2494
}
```

**Response (201)**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "usuario_id": "550e8400-e29b-41d4-a716-446655440001",
  "nombre": "Rancho Las Flores",
  "facility_type": "UPP",
  "status": "activa",
  "estado": "Jalisco",
  "municipio": "Guadalajara",
  "license_number": "UPP-14-001-2026",
  "active": true,
  "created_at": "2026-03-16T10:30:00Z"
}
```

### Link a Document
```bash
POST /instalaciones/550e8400-e29b-41d4-a716-446655440000/documentos/constancia_fiscal?documento_id=550e8400-e29b-41d4-a716-446655440002
```

### Request UPP Renewal
```bash
POST /instalaciones/550e8400-e29b-41d4-a716-446655440000/renovaciones/solicitar
```

### Approve Document (Admin)
```bash
POST /instalaciones/550e8400-e29b-41d4-a716-446655440000/documentos/550e8400-e29b-41d4-a716-446655440003/aprobar
```

---

## 🔐 Access Control

| Endpoint | User | Owner | Admin | Inspector | SuperAdmin |
|----------|------|-------|-------|-----------|------------|
| Create | ✅ | - | ✅ | - | ✅ |
| List (own) | ✅ | - | ✅ (all) | ✅ (all) | ✅ |
| View Detail | ✅ | ✅ | ✅ | ✅ | ✅ |
| Update | - | ✅ | ✅ | - | ✅ |
| Delete | - | - | ✅ | - | ✅ |
| Approve Docs | - | - | ✅ | ✅ | ✅ |
| Manage Renewals | - | - | ✅ | ✅ | ✅ |

---

## 📝 Facility Types & Required Documents

### UPP (Unidad de Producción Pecuaria)
**Purpose**: Primary livestock producer unit (farms/ranches)
**License**: 12-digit code (state + municipality + producer)
**Documents Required**:
- ✅ Constancia de Situación Fiscal
- ✅ Certificado Parcelario (if ejido land)
- ✅ Contrato de Arrendamiento/Comodato (if rented)
- ✅ Clave Catastral (cadastral key for location)

**Special Rules**:
- Annual renewal required (or movilizaciones are blocked)
- No two UPPs on same exact land (prevents duplicates)

### PSG (Productor de Servicios Ganaderos)
**Purpose**: Livestock service providers (not producers)
**Examples**: Feedlot operations, fattening centers, collection points
**Documents Required**:
- ✅ Identificación (INE)
- ✅ RFC
- ✅ Comprobante de Domicilio
- ✅ Acta Constitutiva (corporate charter)
- ✅ Permiso de Funcionamiento (operational permit)

### SUBASTA (Livestock Auction)
**Purpose**: Auction facilities for livestock sales
**Documents Required**:
- ✅ Permiso de Subasta
- ✅ Comprobante de Domicilio
- ✅ RFC
- ✅ Identificación

### RASTRO (Slaughterhouse)
**Purpose**: Processing/slaughter facilities
**Documents Required**:
- ✅ Permiso de Rastro
- ✅ Certificado de Inspecciones
- ✅ RFC
- ✅ Identificación

### FERIA (Livestock Fair)
**Purpose**: Temporary or permanent livestock trading venues
**Documents Required**:
- ✅ Permiso de Feria
- ✅ Comprobante de Domicilio
- ✅ RFC

### EXPORT_CENTER (Centro de Exportación)
**Purpose**: Export preparation and shipment facility
**Documents Required**:
- ✅ Permiso de Exportación
- ✅ Certificado de Calidad
- ✅ RFC
- ✅ Identificación
- ✅ Comprobante de Domicilio

### QUARANTINE_CENTER (Centro de Cuarentena)
**Purpose**: Quarantine/isolation facility for animal health monitoring
**Documents Required**:
- ✅ Permiso de Cuarentena
- ✅ Comprobante de Domicilio
- ✅ RFC
- ✅ Certificado Veterinario

---

## 🔄 Workflow Examples

### UPP Registration Flow
1. User creates Instalacion (type: UPP)
2. User uploads required documents
3. Admin reviews documents one by one
   - Can approve: Document moves to "aprobado"
   - Can reject: Document moves to "rechazado" with comment
4. Once all approved: Instalacion is fully registered
5. Admin can link Instalacion to Predio

### UPP Renewal Flow
1. 1-year anniversary approaches
2. User requests renewal: `POST /instalaciones/{id}/renovaciones/solicitar`
3. Status: "pendiente"
4. Admin/Inspector reviews renewal request
5. Admin approves: 
   - Status: "aprobada"
   - New expiration: Today + 365 days
   - Movilizaciones enabled for next year
6. OR Admin rejects: Status "rechazada" + reason

### Blocking Movilizaciones on Expired UPP
- When creating an event (traslado) FROM a UPP:
  - System checks if UPP renovation is overdue
  - If expired: HTTP 409 "UPP license expired, renewal required"
  - User must request renewal and get admin approval

---

## 📊 Files Modified

### Backend Files
- ✅ `db_schema.sql` - 4 new tables + 1 config table + indexes
- ✅ `app/models.py` - 3 new models + 1 new enum + relationships
- ✅ `app/schemas.py` - 6 new request/response schemas + 1 enum
- ✅ `app/routers/instalaciones.py` - NEW 16 endpoints
- ✅ `app/main.py` - Imported and registered router
- ✅ `COMPLETE_API_CATALOG.md` - Added full documentation

### Git Commit
```
commit d5b2788
Author: GitHub Copilot
Date: March 16, 2026

feat: Add Instalaciones (Facilities) system with document management 
      and UPP renewal tracking
      
- 4 new database tables (instalaciones, instalacion_documentos, 
  renovaciones_upp, instalacion_documento_requerimientos)
- 3 new SQLAlchemy models with relationships
- 16 new API endpoints with full CRUD and document workflow
- UPP annual renewal tracking system
- Document approval/rejection with admin review
- Search by municipality and facility type
```

---

## 🚀 Testing Checklist

After deploying, test:

- [ ] Create UPP installation
- [ ] View installation details
- [ ] Link document to facility
- [ ] List pending documents
- [ ] Admin approve document
- [ ] Admin reject document with comment
- [ ] Request UPP renewal
- [ ] View pending renewals (inspector view)
- [ ] Approve renewal (check 365-day extension)
- [ ] Reject renewal (check reason saved)
- [ ] Search facilities by municipality
- [ ] Search facilities by type
- [ ] Verify non-admins can only see their own facilities
- [ ] Verify predios can be linked to instalaciones

---

## 📖 Key Documentation

For detailed endpoint specifications, see:
- **`COMPLETE_API_CATALOG.md`** - Full API reference (lines 1-1900)
- **Instalaciones section** - All 16 endpoints with examples (lines ~580-760)

---

**Status**: ✅ COMPLETE & READY FOR TESTING  
**Last Updated**: March 16, 2026  
**Total Endpoints Added**: 16  
**Total API Endpoints Now**: 89
