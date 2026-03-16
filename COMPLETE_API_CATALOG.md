# Union Ganadera API - Complete Endpoint Catalog

**API Base URL**: `http://localhost:8000/api`  
**Total Endpoints**: 92 (3 nuevos endpoints de instalaciones)  
**Last Updated**: Marzo 16, 2026 - **MAJOR REFACTOR: Architecture Changes**

---

## 📋 CAMBIOS ARQUITECTÓNICOS PRINCIPALES (Marzo 16, 2026)

### ⚠️ BREAKING CHANGES

1. **Relación Bovino** (IMPORTANTE)
   - ❌ `bovino.predio_id` fue REMOVIDO
   - ✅ `bovino.instalacion_id` fue AGREGADO
   - Bovinos ahora se relacionan directamente a instalaciones

2. **Relación Predio-Instalación** (IMPORTANTE)
   - ❌ `predio.facility_id` fue REMOVIDO
   - ✅ Nueva tabla: `instalacion_predio` (many-to-many junction)
   - Una instalación puede tener múltiples predios
   - Un predio puede vincularse a múltiples instalaciones

3. **Control de Tipos por Rol** (NUEVO)
   - Usuarios normales: Solo pueden crear **UPP** y **PSG**
   - Administradores: Pueden crear TODOS los tipos
   - **Nuevo tipo**: `CASETA_INSPECCION` (solo admin)

4. **Validaciones de Estado** (NUEVO)
   - No se pueden crear bovinos si instalación no está activa
   - No se pueden crear eventos si instalación está vencida
   - Campo `fecha_vencimiento` en Instalacion

5. **Privacidad** (NUEVO)
   - Usuarios normales: Solo ven sus propias instalaciones
   - Nuevo endpoint: GET `/instalaciones/buscar/codigo/{license_number}` (público)
   - Previene búsqueda exhaustiva de instalaciones de otros usuarios

### Referencias Completas
Consulta [ARQUITECTURA_REFACTOR_MARZO_2026.md](ARQUITECTURA_REFACTOR_MARZO_2026.md) para detalles completos.

---

## 📋 Table of Contents
1. [Authentication](#authentication)
2. [Users](#users)
3. [Bovinos (Cattle)](#bovinos-cattle)
4. [Predios (Farms)](#predios-farms)
5. [Instalaciones (Facilities)](#instalaciones-facilities)
6. [Domicilios (Addresses)](#domicilios-addresses)
7. [Files/Documents](#filesdocuments)
8. [Eventos (Events)](#eventos-events)
   - [Pesos](#eventos---pesos)
   - [Dietas](#eventos---dietas)
   - [Vacunaciones](#eventos---vacunaciones)
   - [Desparasitaciones](#eventos---desparasitaciones)
   - [Laboratorios](#eventos---laboratorios)
   - [Compraventas](#eventos---compraventas)
   - [Traslados](#eventos---traslados)
   - [Enfermedades](#eventos---enfermedades)
   - [Tratamientos](#eventos---tratamientos)
   - [Remisiones](#eventos---remisiones)

---

## Authentication

### POST `/signup`
**Description**: Register a new user (ganadero)  
**Auth Required**: No  
**Request Body**:
```json
{
  "curp": "string",
  "contrasena": "string (8-72 chars)",
  "nombre": "string",
  "apellido_p": "string",
  "apellido_m": "string | null",
  "sexo": "M | F | X",
  "fecha_nac": "YYYY-MM-DD",
  "clave_elector": "string",
  "idmex": "string"
}
```
**Response** (201): `UserResponse`
```json
{
  "id": "uuid",
  "curp": "string",
  "rol": "ganadero",
  "created_at": "ISO-8601 datetime"
}
```

---

### POST `/signup/veterinario`
**Description**: Register a new veterinarian (requires cedula file upload)  
**Auth Required**: No  
**Request**: `multipart/form-data`
- `curp`: string
- `contrasena`: string (8-72 chars)
- `nombre`: string
- `apellido_p`: string
- `apellido_m`: string (optional)
- `sexo`: M | F | X
- `fecha_nac`: YYYY-MM-DD
- `clave_elector`: string
- `idmex`: string
- `cedula`: string (professional license number)
- `cedula_file`: file (upload document)

**Response** (201): `UserResponse`
```json
{
  "id": "uuid",
  "curp": "string",
  "rol": "veterinario",
  "created_at": "ISO-8601 datetime"
}
```

---

### POST `/login`
**Description**: Authenticate user and get access token  
**Auth Required**: No  
**Request Body**:
```json
{
  "curp": "string",
  "contrasena": "string"
}
```
**Response** (200): `Token`
```json
{
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

---

### POST `/signup/administrador`
**Description**: Create a new administrador (admin only)  
**Auth Required**: Yes (superadministrador)  
**Request Body**:
```json
{
  "curp": "string",
  "contrasena": "string",
  "nombre": "string",
  "apellido_p": "string",
  "apellido_m": "string | null",
  "sexo": "M | F | X",
  "fecha_nac": "YYYY-MM-DD",
  "clave_elector": "string",
  "idmex": "string"
}
```
**Response** (201): `UserResponse`

---

### POST `/signup/inspector`
**Description**: Create a new inspector (admin only)  
**Auth Required**: Yes (administrador or superadministrador)  
**Request Body**:
```json
{
  "curp": "string",
  "contrasena": "string",
  "nombre": "string",
  "apellido_p": "string",
  "apellido_m": "string | null",
  "sexo": "M | F | X",
  "fecha_nac": "YYYY-MM-DD",
  "clave_elector": "string",
  "idmex": "string"
}
```
**Response** (201): `UserResponse`

---

## Users

### GET `/users/me`
**Description**: Get current authenticated user info  
**Auth Required**: Yes  
**Query Parameters**: None  
**Response** (200): `UserResponse`
```json
{
  "id": "uuid",
  "curp": "string",
  "rol": "ganadero | veterinario | administrador | superadministrador",
  "created_at": "ISO-8601 datetime"
}
```

---

### GET `/administradores`
**Description**: List all administradores and superadministradores  
**Auth Required**: Yes (administrador+)  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[UserResponse]`
```json
[
  {
    "id": "uuid",
    "curp": "string",
    "rol": "administrador | superadministrador",
    "created_at": "ISO-8601 datetime"
  }
]
```

---

### GET `/inspectores`
**Description**: List all inspectors  
**Auth Required**: Yes (administrador+)  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[UserResponse]`

---

### GET `/normales-y-veterinarios`
**Description**: List all normal users (ganaderos) and veterinarians (who are users with extra health event permissions)  
**Auth Required**: Yes (administrador+)  
**Query Parameters**: None  
**Response** (200): `List[UserListResponse]`
```json
[
  {
    "id": "uuid",
    "curp": "string",
    "rol": "usuario | veterinario",
    "created_at": "ISO-8601 datetime",
    "datos": {
      "id": "uuid",
      "usuario_id": "uuid",
      "nombre": "string",
      "apellido_p": "string",
      "apellido_m": "string | null",
      "sexo": "M | F | X | null",
      "fecha_nac": "YYYY-MM-DD | null",
      "clave_elector": "string | null",
      "idmex": "string | null"
    }
  }
]
```

---

### GET `/users/{user_id}/completo`
**Description**: Get complete information about a user including addresses, documents, cattle, and properties  
**Auth Required**: Yes (administrador+)  
**Path Parameters**:
- `user_id`: UUID

**Response** (200): `UserInfoCompleto`
```json
{
  "id": "uuid",
  "curp": "string",
  "rol": "usuario | veterinario | administrador | inspector | superadministrador",
  "created_at": "ISO-8601 datetime",
  "datos": {
    "id": "uuid",
    "usuario_id": "uuid",
    "nombre": "string",
    "apellido_p": "string",
    "apellido_m": "string | null",
    "sexo": "M | F | X | null",
    "fecha_nac": "YYYY-MM-DD | null",
    "clave_elector": "string | null",
    "idmex": "string | null"
  },
  "domicilios": [
    {
      "id": "uuid",
      "usuario_id": "uuid",
      "calle": "string | null",
      "colonia": "string | null",
      "cp": "string | null",
      "estado": "string | null",
      "municipio": "string | null"
    }
  ],
  "documentos": [
    {
      "id": "uuid",
      "doc_type": "identificacion_frente | identificacion_reverso | comprobante_domicilio | predio | cedula_veterinario | fierro | otro",
      "original_filename": "string",
      "created_at": "ISO-8601 datetime",
      "authored": "boolean",
      "download_url": "presigned-url | null",
      "ultima_revision": {
        "id": "uuid",
        "documento_id": "uuid",
        "admin_id": "uuid",
        "status": "pendiente | aprobado | rechazado",
        "comentario": "string | null",
        "fecha": "ISO-8601 datetime"
      }
    }
  ],
  "bovinos": [
    {
      "id": "uuid",
      "arete_barcode": "string | null",
      "arete_rfid": "string | null",
      "nombre": "string | null",
      "folio": "string | null",
      "raza_dominante": "string | null",
      "fecha_nac": "YYYY-MM-DD | null",
      "sexo": "M | F | X | null",
      "peso_actual": "float | null",
      "status": "string",
      "predio_id": "uuid | null"
    }
  ],
  "predios": [
    {
      "id": "uuid",
      "usuario_id": "uuid",
      "clave_catastral": "string | null",
      "superficie_total": "float | null",
      "latitud": "float | null",
      "longitud": "float | null"
    }
  ]
}
```

---

## Bovinos (Cattle)

### GET `/bovinos`
**Description**: List bovinos for current user  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)
- `instalacion_id`: UUID (optional - filter by instalacion) **[CHANGED: was `predio_id`]**

**Response** (200): `List[BovinoResponse]`
```json
[
  {
    "id": "uuid",
    "usuario_id": "uuid",
    "usuario_original_id": "uuid | null",
    "arete_barcode": "string | null",
    "arete_rfid": "string | null",
    "nombre": "string | null",
    "folio": "string | null",
    "raza_dominante": "string | null",
    "fecha_nac": "YYYY-MM-DD | null",
    "sexo": "M | F | X | null",
    "peso_nac": "float | null",
    "peso_actual": "float | null",
    "proposito": "string | null",
    "status": "string",
    "madre_id": "uuid | null",
    "padre_id": "uuid | null",
    "instalacion_id": "uuid | null",
    "nariz_storage_key": "string | null",
    "nariz_url": "presigned-url | null",
    "madre": { /* BovinoParentPublic or null */ },
    "padre": { /* BovinoParentPublic or null */ }
  }
]
```

---

### GET `/bovinos/{bovino_id}`
**Description**: Get detailed info for a specific bovino (includes parent data)  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Response** (200): `BovinoResponse` (with resolved madre/padre)

---

### GET `/bovinos/search`
**Description**: Search for bovino by barcode, RFID, or name (veterinarians only)  
**Auth Required**: Yes (veterinario)  
**Query Parameters**:
- `arete_barcode`: string (optional)
- `arete_rfid`: string (optional)
- `nombre`: string (optional)

*Note: At least one parameter required*

**Response** (200): `BovinoResponse`

---

### POST `/bovinos`
**Description**: Create a new bovino  
**Auth Required**: Yes  
**Request Body**:
```json
{
  "arete_barcode": "string | null",
  "arete_rfid": "string | null",
  "nombre": "string | null",
  "madre_id": "uuid | null",
  "padre_id": "uuid | null",
  "instalacion_id": "uuid | null",
  "raza_dominante": "string | null",
  "fecha_nac": "YYYY-MM-DD | null",
  "sexo": "M | F | X | null",
  "peso_nac": "float | null",
  "peso_actual": "float | null",
  "proposito": "string | null"
}
```

**Validations** (HTTP 409 Conflict if fails):
- If `instalacion_id` provided:
  - Instalacion must exist and belong to user (or user is admin)
  - Instalacion.active must be TRUE
  - If instalacion is UPP/PSG:
    - Instalacion.fecha_vencimiento must be NULL or > today

**Response** (201): `BovinoResponse`

---

### PUT `/bovinos/{bovino_id}`
**Description**: Update bovino info (owner only)  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Request Body**: BovinoUpdate (same as create, all optional)  
**Response** (200): `BovinoResponse`

---

### DELETE `/bovinos/{bovino_id}`
**Description**: Delete bovino (owner only)  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Response** (200): `BovinoResponse`

---

### POST `/bovinos/{bovino_id}/upload-nose-photo`
**Description**: Upload nose/nariz photo for biometric identification  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Request**: `multipart/form-data`
- `file`: file (image)

**Response** (200): `BovinoResponse`

---

## Predios (Farms)

### GET `/predios`
**Description**: List predios for current user  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[PredioResponse]`
```json
[
  {
    "id": "uuid",
    "usuario_id": "uuid",
    "nombre": "string",
    "clave_catastral": "string | null",
    "municipio": "string | null",
    "ubicacion": "string | null",
    "created_at": "ISO-8601 datetime"
  }
]
```

---

### GET `/predios/{predio_id}`
**Description**: Get specific predio details  
**Auth Required**: Yes  
**Path Parameters**:
- `predio_id`: UUID

**Response** (200): `PredioResponse`

---

### POST `/predios`
**Description**: Create a new predio  
**Auth Required**: Yes  
**Request Body**:
```json
{
  "nombre": "string",
  "clave_catastral": "string | null",
  "municipio": "string | null",
  "ubicacion": "string | null"
}
```
**Response** (201): `PredioResponse`

---

### PUT `/predios/{predio_id}`
**Description**: Update predio info  
**Auth Required**: Yes  
**Path Parameters**:
- `predio_id`: UUID

**Request Body**: PredioUpdate (same as create, all optional)  
**Response** (200): `PredioResponse`

---

### DELETE `/predios/{predio_id}`
**Description**: Delete predio  
**Auth Required**: Yes  
**Path Parameters**:
- `predio_id`: UUID

**Response** (200): `PredioResponse`

---

### GET `/predios/{predio_id}/bovinos`
**Description**: List bovinos in a specific predio  
**Auth Required**: Yes  
**Path Parameters**:
- `predio_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[BovinoResponse]`

---

### POST `/predios/{predio_id}/upload-document`
**Description**: Upload predio document (replaces existing)  
**Auth Required**: Yes  
**Path Parameters**:
- `predio_id`: UUID

**Request**: `multipart/form-data`
- `file`: file

**Response** (201): `DocumentoResponse`

---

## Instalaciones (Facilities)

**Facility Types**:
- `UPP`: Unidad de Producción Pecuaria (Cattle Production Unit)
- `PSG`: Productor de Servicios Ganaderos (Livestock Service Provider)
- `SUBASTA`: Livestock Auction
- `RASTRO`: Slaughterhouse
- `FERIA`: Livestock Fair
- `EXPORT_CENTER`: Export Center
- `QUARANTINE_CENTER`: Quarantine Center

### POST `/instalaciones/`
**Description**: Create a new facility/installation  
**Auth Required**: Yes  

**Role-Based Facility Types** (HTTP 403 if unauthorized):
- **Usuario (normal users)**: Can ONLY create `UPP`, `PSG`
- **Administrador/SuperAdministrador**: Can create ALL types including `CASETA_INSPECCION`

**Request Body**:
```json
{
  "usuario_id": "uuid | null (defaults to current user)",
  "nombre": "string",
  "facility_type": "UPP | PSG | SUBASTA | RASTRO | FERIA | EXPORT_CENTER | QUARANTINE_CENTER | CASETA_INSPECCION",
  "status": "activa (default)",
  "latitud": "float | null",
  "longitud": "float | null",
  "estado": "string (state name)",
  "municipio": "string (municipality name)",
  "license_number": "string (unique)",
  "active": "boolean (default: true)"
}
```
**Response** (201): `InstalacionResponse`
```json
{
  "id": "uuid",
  "usuario_id": "uuid",
  "nombre": "string",
  "facility_type": "string",
  "status": "string",
  "latitud": "float | null",
  "longitud": "float | null",
  "estado": "string",
  "municipio": "string",
  "license_number": "string",
  "active": "boolean",
  "fecha_vencimiento": "YYYY-MM-DD | null",
  "created_at": "ISO-8601 datetime"
}
```

### GET `/instalaciones/`
**Description**: List all facilities (admins see all, users see only theirs)  
**Auth Required**: Yes  

**Privacy Rules**:
- **Normal users**: See ONLY their own instalaciones (usuario_id = authenticated user)
- **Admins/Inspectors**: See ALL instalaciones
- To find external facilities: Use `GET /instalaciones/buscar/codigo/{license_number}`

**Query Parameters**:
- `facility_type`: string (optional, filter by type)
- `estado`: string (optional, filter by state)
- `active_only`: boolean (optional, default: false)

**Response** (200): List of `InstalacionResponse`

---

### GET `/instalaciones/{instalacion_id}`
**Description**: Get specific facility with documents and related info  
**Auth Required**: Yes  
**Path Parameters**:
- `instalacion_id`: UUID

**Response** (200): `InstalacionDetailResponse`
```json
{
  "id": "uuid",
  "usuario_id": "uuid",
  "nombre": "string",
  "facility_type": "string",
  "status": "string",
  "latitud": "float | null",
  "longitud": "float | null",
  "estado": "string",
  "municipio": "string",
  "license_number": "string",
  "active": "boolean",
  "created_at": "ISO-8601 datetime",
  "documentos": [
    {
      "id": "uuid",
      "instalacion_id": "uuid",
      "documento_id": "uuid",
      "documento_tipo": "string",
      "status": "pendiente | aprobado | rechazado",
      "comentario_rechazo": "string | null",
      "review_date": "ISO-8601 datetime | null",
      "reviewed_by": "uuid | null",
      "created_at": "ISO-8601 datetime"
    }
  ],
  "predios": [
    {
      "id": "uuid",
      "usuario_id": "uuid",
      "facility_id": "uuid",
      "clave_catastral": "string",
      "superficie_total": "decimal",
      "latitud": "decimal",
      "longitud": "decimal"
    }
  ]
}
```

---

### PUT `/instalaciones/{instalacion_id}`
**Description**: Update facility information  
**Auth Required**: Yes (owner or admin)  
**Path Parameters**:
- `instalacion_id`: UUID

**Request Body** (all optional):
```json
{
  "nombre": "string | null",
  "status": "string | null",
  "latitud": "float | null",
  "longitud": "float | null",
  "estado": "string | null",
  "municipio": "string | null",
  "active": "boolean | null"
}
```
**Response** (200): `InstalacionResponse`

---

### DELETE `/instalaciones/{instalacion_id}`
**Description**: Deactivate a facility (admins only)  
**Auth Required**: Yes (admin only)  
**Path Parameters**:
- `instalacion_id`: UUID

**Response** (204): No Content

---

### POST `/instalaciones/{instalacion_id}/documentos/{documento_tipo}`
**Description**: Link a document to a facility  
**Auth Required**: Yes  
**Path Parameters**:
- `instalacion_id`: UUID
- `documento_tipo`: string (e.g., 'constancia_fiscal', 'certificado_parcelario', etc.)

**Query Parameters**:
- `documento_id`: UUID

**Response** (201):
```json
{
  "id": "uuid",
  "instalacion_id": "uuid",
  "documento_id": "uuid",
  "documento_tipo": "string",
  "status": "pendiente",
  "created_at": "ISO-8601 datetime"
}
```

---

### GET `/instalaciones/{instalacion_id}/documentos`
**Description**: Get all documents linked to a facility  
**Auth Required**: Yes  
**Path Parameters**:
- `instalacion_id`: UUID

**Response** (200): List of `InstalacionDocumentoResponse`

---

### POST `/instalaciones/{instalacion_id}/documentos/{doc_id}/aprobar`
**Description**: Approve a facility document (admins only)  
**Auth Required**: Yes (admin only)  
**Path Parameters**:
- `instalacion_id`: UUID
- `doc_id`: UUID

**Response** (200):
```json
{
  "status": "approved",
  "documento": {
    "id": "uuid",
    "instalacion_id": "uuid",
    "documento_id": "uuid",
    "documento_tipo": "string",
    "status": "aprobado",
    "review_date": "ISO-8601 datetime",
    "reviewed_by": "uuid"
  }
}
```

---

### POST `/instalaciones/{instalacion_id}/documentos/{doc_id}/rechazar`
**Description**: Reject a facility document (admins only)  
**Auth Required**: Yes (admin only)  
**Path Parameters**:
- `instalacion_id`: UUID
- `doc_id`: UUID

**Query Parameters**:
- `comentario`: string (reason for rejection)

**Response** (200):
```json
{
  "status": "rejected",
  "documento": {
    "id": "uuid",
    "instalacion_id": "uuid",
    "documento_id": "uuid",
    "documento_tipo": "string",
    "status": "rechazado",
    "comentario_rechazo": "string",
    "review_date": "ISO-8601 datetime",
    "reviewed_by": "uuid"
  }
}
```

---

### POST `/instalaciones/{instalacion_id}/renovaciones/solicitar`
**Description**: Request annual UPP renewal  
**Auth Required**: Yes  
**Path Parameters**:
- `instalacion_id`: UUID

**Response** (201): `RenovacionUPPResponse`
```json
{
  "id": "uuid",
  "instalacion_id": "uuid",
  "solicitada_por": "uuid",
  "estado": "pendiente",
  "fecha_solicitud": "ISO-8601 datetime",
  "fecha_proximo_vencimiento": "YYYY-MM-DD | null",
  "aprobada_por": "uuid | null",
  "fecha_aprobacion": "ISO-8601 datetime | null",
  "comentarios": "string | null"
}
```

---

### GET `/instalaciones/renovaciones/pendientes`
**Description**: Get all pending UPP renewals (admins/inspectors only)  
**Auth Required**: Yes (admin/inspector only)  

**Response** (200): List of `RenovacionUPPResponse`

---

### POST `/instalaciones/renovaciones/{renovacion_id}/aprobar`
**Description**: Approve UPP renewal (extends license 365 days)  
**Auth Required**: Yes (admin/inspector only)  
**Path Parameters**:
- `renovacion_id`: UUID

**Side Effects**:
- Sets `instalacion.fecha_vencimiento = today + 365 days`
- Sets `renovacion.fecha_proximo_vencimiento = today + 365 days`
- Blocks future creation of bovinos/eventos if fecha_vencimiento passes

**Response** (200): `RenovacionUPPResponse`
```json
{
  "id": "uuid",
  "instalacion_id": "uuid",
  "solicitada_por": "uuid",
  "estado": "aprobada",
  "fecha_solicitud": "ISO-8601 datetime",
  "fecha_proximo_vencimiento": "YYYY-MM-DD",
  "aprobada_por": "uuid",
  "fecha_aprobacion": "ISO-8601 datetime",
  "comentarios": "string | null"
}
```

---

### POST `/instalaciones/renovaciones/{renovacion_id}/rechazar`
**Description**: Reject UPP renewal  
**Auth Required**: Yes (admin/inspector only)  
**Path Parameters**:
- `renovacion_id`: UUID

**Query Parameters**:
- `comentarios`: string (reason for rejection)

**Response** (200): `RenovacionUPPResponse` with "rechazada" status

---

### GET `/instalaciones/buscar/municipio/{municipio}`
**Description**: Search facilities by municipality  
**Auth Required**: No  
**Path Parameters**:
- `municipio`: string

**Query Parameters**:
- `facility_type`: string (optional)

**Response** (200): List of `InstalacionResponse`

---

### GET `/instalaciones/buscar/codigo/{license_number}`
**Description**: Search for a facility by its UPP/PSG license code (public discovery)  
**Auth Required**: No  
**Path Parameters**:
- `license_number`: string (unique license code)

**Purpose**: 
- Allows users to discover and interact with external facilities
- Prevents exhaustive searches (must know exact code)
- Helps prevent crimes and extortions by controlling visibility

**Response** (200): `InstalacionResponse` (basic info only)
```json
{
  "id": "uuid",
  "usuario_id": "uuid",
  "nombre": "string",
  "facility_type": "string",
  "status": "string",
  "latitud": "float | null",
  "longitud": "float | null",
  "estado": "string",
  "municipio": "string",
  "license_number": "string",
  "active": "boolean",
  "created_at": "ISO-8601 datetime"
}
```

**Example Usage**:
```bash
# Find a specific UPP by code
GET /api/instalaciones/buscar/codigo/UPP-2026-001234
```

---

### GET `/instalaciones/tipo/{facility_type}`
**Description**: Search facilities by type  
**Auth Required**: No  
**Path Parameters**:
- `facility_type`: UPP | PSG | SUBASTA | RASTRO | FERIA | EXPORT_CENTER | QUARANTINE_CENTER

**Query Parameters**:
- `estado`: string (optional, filter by state)

**Response** (200): List of `InstalacionResponse`

---

## Domicilios (Addresses)

### GET `/domicilios`
**Description**: List domicilios for current user  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DomicilioResponse]`
```json
[
  {
    "id": "uuid",
    "usuario_id": "uuid",
    "calle": "string | null",
    "colonia": "string | null",
    "cp": "string | null",
    "estado": "string | null",
    "municipio": "string | null"
  }
]
```

---

### GET `/domicilios/{domicilio_id}`
**Description**: Get specific domicilio  
**Auth Required**: Yes  
**Path Parameters**:
- `domicilio_id`: UUID

**Response** (200): `DomicilioResponse`

---

### POST `/domicilios`
**Description**: Create new domicilio  
**Auth Required**: Yes  
**Request Body**:
```json
{
  "calle": "string | null",
  "colonia": "string | null",
  "cp": "string | null",
  "estado": "string | null",
  "municipio": "string | null"
}
```
**Response** (201): `DomicilioResponse`

---

### PUT `/domicilios/{domicilio_id}`
**Description**: Update domicilio  
**Auth Required**: Yes  
**Path Parameters**:
- `domicilio_id`: UUID

**Request Body**: DomicilioUpdate (all optional)  
**Response** (200): `DomicilioResponse`

---

### DELETE `/domicilios/{domicilio_id}`
**Description**: Delete domicilio  
**Auth Required**: Yes  
**Path Parameters**:
- `domicilio_id`: UUID

**Response** (200): `DomicilioResponse`

---

### POST `/domicilios/{domicilio_id}/upload-document`
**Description**: Upload address proof/comprobante (replaces existing)  
**Auth Required**: Yes  
**Path Parameters**:
- `domicilio_id`: UUID

**Request**: `multipart/form-data`
- `file`: file

**Response** (201): `DocumentoResponse`

---

## Files/Documents

### GET `/files/health/s3`
**Description**: Test S3 connection and get configuration  
**Auth Required**: Yes  
**Response** (200):
```json
{
  "status": "connected | error",
  "bucket": "documentos",
  "available_buckets": ["string"],
  "s3_endpoint": "url",
  "s3_public_url": "url",
  "message": "string"
}
```

---

### GET `/files`
**Description**: List documents for current user  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DocumentoResponse]`
```json
[
  {
    "id": "uuid",
    "doc_type": "identificacion_frente | identificacion_reverso | comprobante_domicilio | predio | cedula_veterinario | fierro | otro",
    "original_filename": "string",
    "created_at": "ISO-8601 datetime",
    "authored": "boolean",
    "download_url": "presigned-url | null",
    "ultima_revision": { /* DocumentoRevisionResponse or null */ }
  }
]
```

---

### GET `/files/admin/pending`
**Description**: Admin - list all pending (unapproved) documents  
**Auth Required**: Yes (admin+)  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DocumentoResponse]`

---

### GET `/files/admin/all`
**Description**: Admin - list all documents system-wide  
**Auth Required**: Yes (admin+)  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DocumentoResponse]`

---

### POST `/files/upload`
**Description**: Upload a document  
**Auth Required**: Yes  
**Request**: `multipart/form-data`
- `doc_type`: identificacion_frente | identificacion_reverso | comprobante_domicilio | predio | cedula_veterinario | fierro | otro
- `file`: file

*Note: Most types replace existing; `fierro` allows multiple uploads per user*

**Response** (201): `DocumentoResponse`

---

### GET `/files/{doc_id}/preview`
**Description**: Get presigned preview URL (1 hour validity)  
**Auth Required**: Yes  
**Path Parameters**:
- `doc_id`: UUID

**Response** (200):
```json
{
  "doc_id": "uuid",
  "filename": "string",
  "doc_type": "string",
  "preview_url": "presigned-url",
  "expires_in": 3600,
  "message": "Preview URL generated successfully"
}
```

---

### GET `/files/{doc_id}/content`
**Description**: Stream file content directly from API (no CORS issues). Returns file with proper MIME type for preview in browsers/apps.  
**Auth Required**: Yes  
**Path Parameters**:
- `doc_id`: UUID

**Response** (200): Binary file content with appropriate `Content-Type` header
- Supports: Images (JPEG, PNG, etc), PDFs, text files, all formats
- Headers: `Content-Disposition: inline; filename=...` (for preview, not download)
- Cache: 1 hour (`Cache-Control: public, max-age=3600`)

**Usage Examples**:
- Images: `<img src="/api/files/{id}/content">`
- PDFs: `<iframe src="/api/files/{id}/content">`
- Downloads: `<a href="/api/files/{id}/content">Download</a>`

---

### POST `/files/{doc_id}/review`
**Description**: Admin - approve/reject document  
**Auth Required**: Yes (admin+)  
**Path Parameters**:
- `doc_id`: UUID

**Request Body**:
```json
{
  "status": "pendiente | aprobado | rechazado",
  "comentario": "string | null"
}
```
**Response** (201): `DocumentoRevisionResponse`
```json
{
  "id": "uuid",
  "documento_id": "uuid",
  "admin_id": "uuid",
  "status": "string",
  "comentario": "string | null",
  "fecha": "ISO-8601 datetime"
}
```

---

### GET `/files/{doc_id}/reviews`
**Description**: Admin - get full revision history for document  
**Auth Required**: Yes (admin+)  
**Path Parameters**:
- `doc_id`: UUID

**Response** (200): `List[DocumentoRevisionResponse]`

---

### DELETE `/files/{doc_id}`
**Description**: Delete document (owner only)  
**Auth Required**: Yes  
**Path Parameters**:
- `doc_id`: UUID

**Response** (200): `DocumentoResponse`

---

## Eventos (Events)

### POST `/eventos`
**Description**: Create event for bovino (universal endpoint)  
**Auth Required**: Yes  
**Request Body**:
```json
{
  "type": "peso | dieta | vacunacion | desparasitacion | laboratorio | compraventa | traslado | enfermedad | tratamiento | remision",
  "data": {
    "bovino_id": "uuid",
    "observaciones": "string | null",
    // ... type-specific fields (see details below)
  }
}
```
**Response** (201): `EventoResponse` (base structure)

---

### Eventos - Pesos

#### GET `/eventos/pesos`
**Description**: List all peso events for user's bovinos  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[PesoDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "peso_actual": "float | null",
    "peso_nuevo": "float"
  }
]
```

---

#### GET `/eventos/pesos/bovino/{bovino_id}`
**Description**: List peso events for a specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[PesoDetailResponse]`

---

#### GET `/eventos/pesos/{evento_id}`
**Description**: Get specific peso event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `PesoDetailResponse`

---

**POST `/eventos` (type: "peso")**
```json
{
  "type": "peso",
  "data": {
    "bovino_id": "uuid",
    "peso_nuevo": "float",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Dietas

#### GET `/eventos/dietas`
**Description**: List all diet events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DietaDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "alimento": "string"
  }
]
```

---

#### GET `/eventos/dietas/bovino/{bovino_id}`
**Description**: List diet events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DietaDetailResponse]`

---

#### GET `/eventos/dietas/{evento_id}`
**Description**: Get specific diet event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `DietaDetailResponse`

---

**POST `/eventos` (type: "dieta")**
```json
{
  "type": "dieta",
  "data": {
    "bovino_id": "uuid",
    "alimento": "string",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Vacunaciones

#### GET `/eventos/vacunaciones`
**Description**: List all vaccination events (vet sees all, users see their bovinos only)  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[VacunacionDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "veterinario_id": "uuid | null",
    "tipo": "string | null",
    "lote": "string | null",
    "laboratorio": "string | null",
    "fecha_prox": "YYYY-MM-DD | null"
  }
]
```

---

#### GET `/eventos/vacunaciones/bovino/{bovino_id}`
**Description**: List vaccination events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[VacunacionDetailResponse]`

---

#### GET `/eventos/vacunaciones/{evento_id}`
**Description**: Get specific vaccination event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `VacunacionDetailResponse`

---

**POST `/eventos` (type: "vacunacion")**
```json
{
  "type": "vacunacion",
  "data": {
    "bovino_id": "uuid",
    "veterinario_id": "uuid",
    "tipo": "string",
    "lote": "string",
    "laboratorio": "string",
    "fecha_prox": "YYYY-MM-DD",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Desparasitaciones

#### GET `/eventos/desparasitaciones`
**Description**: List all deworming events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DesparasitacionDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "veterinario_id": "uuid | null",
    "medicamento": "string | null",
    "dosis_admin": "string | null",
    "fecha_prox": "YYYY-MM-DD | null"
  }
]
```

---

#### GET `/eventos/desparasitaciones/bovino/{bovino_id}`
**Description**: List deworming events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[DesparasitacionDetailResponse]`

---

#### GET `/eventos/desparasitaciones/{evento_id}`
**Description**: Get specific deworming event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `DesparasitacionDetailResponse`

---

**POST `/eventos` (type: "desparasitacion")**
```json
{
  "type": "desparasitacion",
  "data": {
    "bovino_id": "uuid",
    "veterinario_id": "uuid",
    "medicamento": "string",
    "dosis": "string",
    "fecha_prox": "YYYY-MM-DD",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Laboratorios

#### GET `/eventos/laboratorios`
**Description**: List all lab test events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[LaboratorioDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "veterinario_id": "uuid | null",
    "tipo": "string | null",
    "resultado": "string | null"
  }
]
```

---

#### GET `/eventos/laboratorios/bovino/{bovino_id}`
**Description**: List lab tests for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[LaboratorioDetailResponse]`

---

#### GET `/eventos/laboratorios/{evento_id}`
**Description**: Get specific lab test event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `LaboratorioDetailResponse`

---

**POST `/eventos` (type: "laboratorio")**
```json
{
  "type": "laboratorio",
  "data": {
    "bovino_id": "uuid",
    "veterinario_id": "uuid",
    "tipo": "string",
    "resultado": "string",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Compraventas

#### GET `/eventos/compraventas`
**Description**: List all purchase/sale events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[CompraventaDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "comprador_curp": "string | null",
    "vendedor_curp": "string | null"
  }
]
```

---

#### GET `/eventos/compraventas/bovino/{bovino_id}`
**Description**: List purchase/sale events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[CompraventaDetailResponse]`

---

#### GET `/eventos/compraventas/{evento_id}`
**Description**: Get specific purchase/sale event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `CompraventaDetailResponse`

---

**POST `/eventos` (type: "compraventa")**
```json
{
  "type": "compraventa",
  "data": {
    "bovino_id": "uuid",
    "comprador_curp": "string",
    "vendedor_curp": "string (must match authenticated user's CURP)",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Traslados

#### GET `/eventos/traslados`
**Description**: List all transfer events (moves between predios)  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[TrasladoDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "predio_anterior_id": "uuid | null",
    "predio_nuevo_id": "uuid | null"
  }
]
```

---

#### GET `/eventos/traslados/bovino/{bovino_id}`
**Description**: List transfer events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[TrasladoDetailResponse]`

---

#### GET `/eventos/traslados/{evento_id}`
**Description**: Get specific transfer event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `TrasladoDetailResponse`

---

**POST `/eventos` (type: "traslado")**
```json
{
  "type": "traslado",
  "data": {
    "bovino_id": "uuid",
    "predio_nuevo_id": "uuid",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Enfermedades

#### GET `/eventos/enfermedades`
**Description**: List all disease events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[EnfermedadDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "enfermedad_id": "uuid | null",
    "veterinario_id": "uuid | null",
    "tipo": "string | null"
  }
]
```

---

#### GET `/eventos/enfermedades/bovino/{bovino_id}`
**Description**: List disease events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[EnfermedadDetailResponse]`

---

#### GET `/eventos/enfermedades/{evento_id}`
**Description**: Get specific disease event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `EnfermedadDetailResponse`

---

#### GET `/eventos/enfermedades/{enfermedad_id}/tratamientos`
**Description**: List treatments for a specific disease  
**Auth Required**: Yes  
**Path Parameters**:
- `enfermedad_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[TratamientoDetailResponse]`

---

#### GET `/eventos/enfermedades/{enfermedad_id}/remisiones`
**Description**: List referrals for a specific disease  
**Auth Required**: Yes  
**Path Parameters**:
- `enfermedad_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[RemisionDetailResponse]`

---

**POST `/eventos` (type: "enfermedad")**
```json
{
  "type": "enfermedad",
  "data": {
    "bovino_id": "uuid",
    "veterinario_id": "uuid",
    "tipo": "string",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Tratamientos

#### GET `/eventos/tratamientos`
**Description**: List all treatment events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[TratamientoDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "enfermedad_id": "uuid | null",
    "veterinario_id": "uuid | null",
    "medicamento": "string | null",
    "dosis": "string | null",
    "periodo": "string | null"
  }
]
```

---

#### GET `/eventos/tratamientos/bovino/{bovino_id}`
**Description**: List treatment events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[TratamientoDetailResponse]`

---

#### GET `/eventos/tratamientos/{evento_id}`
**Description**: Get specific treatment event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `TratamientoDetailResponse`

---

**POST `/eventos` (type: "tratamiento")**
```json
{
  "type": "tratamiento",
  "data": {
    "bovino_id": "uuid",
    "enfermedad_id": "uuid",
    "veterinario_id": "uuid",
    "medicamento": "string",
    "dosis": "string",
    "periodo": "string",
    "observaciones": "string | null"
  }
}
```

---

### Eventos - Remisiones

#### GET `/eventos/remisiones`
**Description**: List all referral/remision events  
**Auth Required**: Yes  
**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[RemisionDetailResponse]`
```json
[
  {
    "id": "uuid",
    "bovino_id": "uuid",
    "fecha": "ISO-8601 datetime",
    "observaciones": "string | null",
    "enfermedad_id": "uuid | null",
    "veterinario_id": "uuid | null"
  }
]
```

---

#### GET `/eventos/remisiones/bovino/{bovino_id}`
**Description**: List referral events for specific bovino  
**Auth Required**: Yes  
**Path Parameters**:
- `bovino_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[RemisionDetailResponse]`

---

#### GET `/eventos/remisiones/enfermedad/{enfermedad_id}`
**Description**: List referrals for a specific disease  
**Auth Required**: Yes  
**Path Parameters**:
- `enfermedad_id`: UUID

**Query Parameters**:
- `skip`: int (default: 0)
- `limit`: int (default: 100)

**Response** (200): `List[RemisionDetailResponse]`

---

#### GET `/eventos/remisiones/{evento_id}`
**Description**: Get specific referral event  
**Auth Required**: Yes  
**Path Parameters**:
- `evento_id`: UUID

**Response** (200): `RemisionDetailResponse`

---

**POST `/eventos` (type: "remision")**
```json
{
  "type": "remision",
  "data": {
    "bovino_id": "uuid",
    "enfermedad_id": "uuid",
    "veterinario_id": "uuid",
    "observaciones": "string | null"
  }
}
```

---

## Root Endpoint

### GET `/`
**Description**: Welcome message  
**Auth Required**: No  
**Response** (200):
```json
{
  "message": "Welcome to the Union Ganadera API"
}
```

---

## Summary Statistics

- **Total Endpoints**: 89
- **Authentication Endpoints**: 5 (`/signup`, `/signup/veterinario`, `/signup/administrador`, `/signup/inspector`, `/login`)
- **User Endpoints**: 3 (`/users/me`, `/administradores`, `/inspectores`)
- **Bovino Endpoints**: 8 (CRUD + search + photo upload)
- **Predio Endpoints**: 7 (CRUD + bovinos list + document upload)
- **Instalaciones Endpoints**: 16 (CRUD + document management + UPP renewals + search by type/municipality)
- **Domicilio Endpoints**: 7 (CRUD + document upload)
- **File Endpoints**: 11 (list, upload, list pending/all, preview, content stream, review, delete, reviews, health check)
- **Event Endpoints**:
  - Pesos: 3 (list, by bovino, detail)
  - Dietas: 3
  - Vacunaciones: 3
  - Desparasitaciones: 3
  - Laboratorios: 3
  - Compraventas: 3
  - Traslados: 3
  - Enfermedades: 5 (list, by bovino, detail, treatments, referrals)
  - Tratamientos: 3
  - Remisiones: 4 (list, by bovino, by disease, detail)
  - Main Create: 1 (`POST /eventos`)

---

## Authorization Levels

- **No Auth Required**: Signup endpoints, login, root, public searches (`/instalaciones/buscar/municipio/`, `/instalaciones/tipo/`)
- **User Auth Required**: Most endpoints (authenticated users)
- **Owner/User Only**: View/update own instalaciones, view/link documents
- **Veterinarian Only**: `/bovinos/search`, veterinary event creation
- **Admin/Inspector Only**: Document review/approval, deactivate facilities, manage UPP renewals
- **SuperAdmin Only**: Administrator creation

---

## Common Response Structures

### Error Responses
```json
{
  "detail": "error message string"
}
```

### Pagination
All list endpoints support:
- `skip`: int (default: 0) - number of records to skip
- `limit`: int (default: 100) - max records to return

---

**Last Updated**: Marzo 16, 2026  
**API Version**: 1.0.1
**Status**: ✅ Production Ready with Major Architecture Refactor
**Breaking Changes**: Yes - See top section for details
