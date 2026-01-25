# Union Ganadera - API Documentation for Flutter Integration

## Base URL
```
http://localhost:8000
```

For production, replace with your deployed backend URL.

---

## Authentication

### 1. User Registration

**Endpoint:** `POST /signup`

**Request Body:**
```json
{
  "curp": "DOEJ900515HDFRHN01",
  "contrasena": "SecurePass123!",
  "nombre": "John",
  "apellido_p": "Doe",
  "apellido_m": "Smith",
  "sexo": "M",
  "fecha_nac": "1990-05-15",
  "clave_elector": "DOESMJHN900515H",
  "idmex": "1234567890"
}
```

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "curp": "DOEJ900515HDFRHN01",
  "rol": "usuario",
  "created_at": "2026-01-23T10:30:00Z"
}
```

**Validation Rules:**
- `curp`: Required, unique, 18-character CURP (Mexican national ID)
- `contrasena`: Required, minimum 8 characters (recommended)
- `nombre`, `apellido_p`: Required
- `sexo`: Required, enum: "M", "F", "X"
- `fecha_nac`: Required, format: "YYYY-MM-DD"
- `clave_elector`: Required
- `idmex`: Required
- `apellido_m`: Optional

---

### 2. User Login

**Endpoint:** `POST /login`

**Request Body:**
```json
{
  "curp": "DOEJ900515HDFRHN01",
  "contrasena": "SecurePass123!"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Error Response:** `401 Unauthorized`
```json
{
  "detail": "Incorrect username or password"
}
```

**Flutter Implementation:**
```dart
// Store the token securely (use flutter_secure_storage)
await storage.write(key: 'access_token', value: response['access_token']);

// Include in all subsequent requests
headers: {
  'Authorization': 'Bearer ${token}',
  'Content-Type': 'application/json',
}
```

---

### 3. Get Current User Info

**Endpoint:** `GET /users/me`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "curp": "DOEJ900515HDFRHN01",
  "rol": "usuario",
  "created_at": "2026-01-23T10:30:00Z"
}
```

---

## Cattle Management (Bovinos)

All endpoints require authentication.

### 1. List User's Cattle

**Endpoint:** `GET /bovinos/?skip=0&limit=100`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "arete_barcode": "MX123456789",
    "arete_rfid": "RFID001122",
    "raza_dominante": "Angus",
    "fecha_nac": "2023-03-15",
    "sexo": "M",
    "peso_nac": 35.5,
    "peso_actual": 450.0,
    "proposito": "Engorda",
    "status": "activo"
  }
]
```

---

### 2. Get Single Cattle

**Endpoint:** `GET /bovinos/{bovino_id}`

**Headers:** `Authorization: Bearer {token}`

**Path Parameters:**
- `bovino_id`: UUID of the bovino

**Response:** `200 OK`
```json
{
  "id": "b7d3a8e9-1234-5678-9abc-def012345678",
  "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
  "arete_barcode": "MX123456789",
  "arete_rfid": "RFID001122",
  "raza_dominante": "Angus",
  "fecha_nac": "2023-03-15",
  "sexo": "M",
  "peso_nac": 35.5,
  "peso_actual": 450.0,
  "proposito": "Engorda",
  "status": "activo"
}
```

**Error Response:** `404 Not Found`
```json
{
  "detail": "Bovino not found"
}
```

---

### 3. Create New Cattle

**Endpoint:** `POST /bovinos/`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "arete_barcode": "MX123456789",
  "arete_rfid": "RFID001122",
  "raza_dominante": "Angus",
  "fecha_nac": "2023-03-15",
  "sexo": "M",
  "peso_nac": 35.5,
  "peso_actual": 450.0,
  "proposito": "Engorda"
}
```

**Response:** `200 OK`
```json
{
  "id": "b7d3a8e9-1234-5678-9abc-def012345678",
  "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
  "arete_barcode": "MX123456789",
  "arete_rfid": "RFID001122",
  "raza_dominante": "Angus",
  "fecha_nac": "2023-03-15",
  "sexo": "M",
  "peso_nac": 35.5,
  "peso_actual": 450.0,
  "proposito": "Engorda",
  "status": "activo"
}
```

**Validation Rules:**
- All fields are optional
- `sexo`: enum: "M", "F", "X"
- `arete_barcode`, `arete_rfid`: Must be unique if provided

---

### 4. Update Cattle

**Endpoint:** `PUT /bovinos/{bovino_id}`

**Headers:** `Authorization: Bearer {token}`

**Request Body:** (Partial update supported)
```json
{
  "peso_actual": 475.5,
  "proposito": "Reproducción"
}
```

**Response:** `200 OK` (Returns updated bovino object)

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Not authorized to update this bovino"
}
```

---

### 4. Delete Cattle

**Endpoint:** `DELETE /bovinos/{bovino_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK` (Returns deleted bovino object)

**Error Response:** `404 Not Found`
```json
{
  "detail": "Bovino not found"
}
```

---

## Events System

All events require authentication and ownership verification.

### Get All User Events

**Endpoint:** `GET /eventos/?skip=0&limit=100`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "evento-uuid",
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "fecha": "2026-01-23T14:30:00Z",
    "observaciones": "Control mensual"
  }
]
```

**Note:** Returns all events for all bovinos owned by the current user, ordered by date (newest first).

---

### Get Events by Bovino

**Endpoint:** `GET /eventos/bovino/{bovino_id}?skip=0&limit=100`

**Headers:** `Authorization: Bearer {token}`

**Path Parameters:**
- `bovino_id`: UUID of the bovino

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)

**Response:** `200 OK` (Same format as above)

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Not authorized to view eventos for this bovino"
}
```

---

### Get Single Event

**Endpoint:** `GET /eventos/{evento_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": "evento-uuid",
  "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
  "fecha": "2026-01-23T14:30:00Z",
  "observaciones": "Control mensual"
}
```

---

### Event Creation

**Endpoint:** `POST /eventos/`

**Headers:** `Authorization: Bearer {token}`

**General Structure:**
```json
{
  "type": "event_type",
  "data": {
    "bovino_id": "UUID",
    "observaciones": "Optional notes",
    // ... type-specific fields
  }
}
```

---

### 1. Weight Recording (Peso)

**Request:**
```json
{
  "type": "peso",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "peso_nuevo": 480.5,
    "observaciones": "Control mensual"
  }
}
```

**Response:** `200 OK`
```json
{
  "id": "evento-uuid",
  "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
  "fecha": "2026-01-23T14:30:00Z",
  "observaciones": "Control mensual"
}
```

**Note:** The `peso_actual` field in the bovino record is automatically updated by the database.

---

### 2. Diet Change (Dieta)

**Request:**
```json
{
  "type": "dieta",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "alimento": "Concentrado Premium + Forraje",
    "observaciones": "Cambio a dieta de engorda intensiva"
  }
}
```

---

### 3. Vaccination (Vacunacion)

**Request:**
```json
{
  "type": "vacunacion",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "veterinario_id": "vet-uuid",
    "tipo": "Fiebre Aftosa",
    "lote": "LOTE2024-001",
    "laboratorio": "Zoetis",
    "fecha_prox": "2027-01-23",
    "observaciones": "Primera dosis del año"
  }
}
```

**Required Fields:**
- `bovino_id`, `veterinario_id`, `tipo`, `lote`, `laboratorio`, `fecha_prox`

---

### 4. Deworming (Desparasitacion)

**Request:**
```json
{
  "type": "desparasitacion",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "veterinario_id": "vet-uuid",
    "medicamento": "Ivermectina",
    "dosis": "10ml",
    "fecha_prox": "2026-07-23",
    "observaciones": "Desparasitación semestral"
  }
}
```

---

### 5. Lab Test (Laboratorio)

**Request:**
```json
{
  "type": "laboratorio",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "veterinario_id": "vet-uuid",
    "tipo": "Análisis de Sangre",
    "resultado": "Hemoglobina: 12.5 g/dL, Leucocitos: Normal",
    "observaciones": "Resultados dentro de parámetros normales"
  }
}
```

---

### 6. Sale/Purchase (Compraventa)

**Request:**
```json
{
  "type": "compraventa",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "comprador_curp": "DOEJ900515HDFRHN01",
    "vendedor_curp": "SMIJ850320MDFRHN02",
    "observaciones": "Venta acordada en $15,000 MXN"
  }
}
```

**Required Fields:**
- `bovino_id`: UUID of the animal being sold
- `comprador_curp`: CURP (18 characters) of the buyer
- `vendedor_curp`: CURP (18 characters) of the seller

**Important:** This automatically transfers ownership to the buyer (comprador_curp) and clears the `predio_id` (location).

---

### 7. Location Transfer (Traslado)

**Request:**
```json
{
  "type": "traslado",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "predio_nuevo_id": "new-location-uuid",
    "observaciones": "Traslado a predio de engorda"
  }
}
```

**Important:** Automatically updates the bovino's `predio_id`.

---

### 8. Disease Detection (Enfermedad)

**Request:**
```json
{
  "type": "enfermedad",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "veterinario_id": "vet-uuid",
    "tipo": "Brucelosis",
    "observaciones": "Síntomas detectados durante inspección rutinaria"
  }
}
```

**Note:** Returns an `enfermedad_id` that can be used to link treatments.

---

### 9. Treatment (Tratamiento)

**Request:**
```json
{
  "type": "tratamiento",
  "data": {
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "enfermedad_id": "disease-uuid",
    "veterinario_id": "vet-uuid",
    "medicamento": "Antibiótico X",
    "dosis": "5ml cada 12 horas",
    "periodo": "7 días",
    "observaciones": "Tratamiento inicial"
  }
}
```

**Required:** Must link to an existing `enfermedad_id`.

---

## Detailed Event Retrieval by Type

Each event type has dedicated endpoints for retrieving detailed information with concatenated base event data and type-specific fields.

### Compraventas (Sales/Purchases)

**Get all sale/purchase events for user's cattle:**
`GET /eventos/compraventas/?skip=0&limit=100`

**Get sale/purchase events for specific bovino:**
`GET /eventos/compraventas/bovino/{bovino_id}?skip=0&limit=100`

**Get single sale/purchase event:**
`GET /eventos/compraventas/{evento_id}`

**Response:** `200 OK`
```json
[
  {
    "id": "evento-uuid",
    "bovino_id": "b7d3a8e9-1234-5678-9abc-def012345678",
    "fecha": "2026-01-23T14:30:00Z",
    "observaciones": "Venta acordada en $15,000 MXN",
    "comprador_curp": "DOEJ900515HDFRHN01",
    "vendedor_curp": "SMIJ850320MDFRHN02"
  }
]
```

**Fields:**
- Base event fields: `id`, `bovino_id`, `fecha`, `observaciones`
- Sale/purchase specific: `comprador_curp` (buyer's CURP), `vendedor_curp` (seller's CURP)

**Note:** Similar GET endpoints exist for all other event types (pesos, dietas, vacunaciones, desparasitaciones, laboratorios, traslados, enfermedades, tratamientos) following the same pattern at `/eventos/{type}/`.

---

## File Upload

### 1. List User Documents

**Endpoint:** `GET /files/?skip=0&limit=100`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "doc-uuid-1",
    "doc_type": "identificacion",
    "original_filename": "INE_JohnDoe.pdf",
    "created_at": "2026-01-23T14:30:00Z",
    "authored": false,
    "download_url": "http://localhost:4566/documentos/user-uuid/identificacion/filename.pdf?X-Amz-Algorithm=..."
  },
  {
    "id": "doc-uuid-2",
    "doc_type": "predio",
    "original_filename": "Predio_Ejidal.pdf",
    "created_at": "2026-01-20T10:15:00Z",
    "authored": true,
    "download_url": "http://localhost:4566/documentos/user-uuid/predio/filename2.pdf?X-Amz-Algorithm=..."
  }
]
```

**Note:**
- Returns all documents owned by the current user, ordered by date (newest first)
- Each document includes a `download_url` - a presigned S3 URL valid for 1 hour
- Use the `download_url` to download the file directly (no authentication needed for the URL itself)
- `authored`: Boolean indicating if an admin has authorized/approved the document (default: false)

---

### 2. Upload Document

**Endpoint:** `POST /files/upload`

**Headers:**
- `Authorization: Bearer {token}`
- `Content-Type: multipart/form-data`

**Form Data:**
- `file`: The file to upload (PDF, image, etc.)
- `doc_type`: Type of document (see enum below)

**Document Types (doc_type):**
- `identificacion`
- `comprobante_domicilio`
- `predio`
- `cedula_veterinario`
- `otro`

**Response:** `200 OK`
```json
{
  "id": "doc-uuid",
  "doc_type": "identificacion",
  "original_filename": "INE_JohnDoe.pdf",
  "created_at": "2026-01-23T14:30:00Z",
  "authored": false
}
```

**Flutter Example using dio:**
```dart
FormData formData = FormData.fromMap({
  'file': await MultipartFile.fromFile(
    filePath,
    filename: 'document.pdf',
  ),
  'doc_type': 'identificacion',
});

Response response = await dio.post(
  '/files/upload',
  data: formData,
  options: Options(
    headers: {'Authorization': 'Bearer $token'},
  ),
);
```

**Storage Structure:**
Files are stored in S3 with the following key pattern:
```
{user_id}/{doc_type}/{uuid}.{extension}
```

**Document Authorization:**
- Documents are created with `authored: false` by default
- In future releases, admin users will be able to review and authorize documents
- The `authored` field tracks whether an admin has verified/approved the document

---

## Domicilios (Addresses)

All domicilio operations require authentication and ownership verification.

### 1. List User Addresses

**Endpoint:** `GET /domicilios/?skip=0&limit=100`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "dom-uuid-1",
    "usuario_id": "user-uuid",
    "calle": "Av. Reforma 123",
    "colonia": "Centro",
    "cp": "06000",
    "estado": "CDMX",
    "municipio": "Cuauhtémoc"
  }
]
```

---

### 2. Get Single Address

**Endpoint:** `GET /domicilios/{domicilio_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Not authorized to view this domicilio"
}
```

---

### 3. Create Address

**Endpoint:** `POST /domicilios/`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "calle": "Av. Reforma 123",
  "colonia": "Centro",
  "cp": "06000",
  "estado": "CDMX",
  "municipio": "Cuauhtémoc"
}
```

**Response:** `200 OK` (Returns created domicilio object)

**Note:** All fields are optional.

---

### 4. Update Address

**Endpoint:** `PUT /domicilios/{domicilio_id}`

**Headers:** `Authorization: Bearer {token}`

**Request Body:** (Partial update supported)
```json
{
  "cp": "06010",
  "colonia": "Juárez"
}
```

**Response:** `200 OK` (Returns updated domicilio object)

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Not authorized to update this domicilio"
}
```

---

### 5. Delete Address

**Endpoint:** `DELETE /domicilios/{domicilio_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK` (Returns deleted domicilio object)

**Note:** This will cascade delete associated predios.

---

## Predios (Properties)

All predio operations require authentication. Predios are linked to domicilios, and ownership is verified through the associated domicilio.

### 1. List Predios

**Endpoint:** `GET /predios/?skip=0&limit=100&domicilio_id={uuid}`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Number of records (default: 100)
- `domicilio_id`: Optional filter by domicilio UUID

**Response:** `200 OK`
```json
[
  {
    "id": "predio-uuid-1",
    "domicilio_id": "dom-uuid",
    "clave_catastral": "CAT123456",
    "superficie_total": 150.5,
    "latitud": 19.432608,
    "longitud": -99.133209
  }
]
```

---

### 2. Get Single Predio

**Endpoint:** `GET /predios/{predio_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Not authorized to view this predio"
}
```

---

### 3. Create Predio

**Endpoint:** `POST /predios/`

**Headers:** `Authorization: Bearer {token}`

**Request Body:**
```json
{
  "domicilio_id": "dom-uuid",
  "clave_catastral": "CAT123456",
  "superficie_total": 150.5,
  "latitud": 19.432608,
  "longitud": -99.133209
}
```

**Response:** `200 OK` (Returns created predio object)

**Validation:**
- If `domicilio_id` is provided, it must belong to the current user
- All fields are optional

---

### 4. Update Predio

**Endpoint:** `PUT /predios/{predio_id}`

**Headers:** `Authorization: Bearer {token}`

**Request Body:** (Partial update supported)
```json
{
  "superficie_total": 160.0,
  "latitud": 19.432700
}
```

**Response:** `200 OK` (Returns updated predio object)

**Error Response:** `403 Forbidden`
```json
{
  "detail": "Not authorized to update this predio"
}
```

---

### 5. Delete Predio

**Endpoint:** `DELETE /predios/{predio_id}`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK` (Returns deleted predio object)

**Note:** Bovinos linked to this predio will have their `predio_id` set to NULL.

---

## Error Handling

### Common HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid data format |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Not authorized for this resource |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server-side error |

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Validation Error (422)
```json
{
  "detail": [
    {
      "loc": ["body", "usuario"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Data Models

### Enums

**SexoEnum:**
- `M` - Male
- `F` - Female
- `X` - Other

**RolEnum:**
- `usuario` - Regular user
- `veterinario` - Veterinarian
- `admin` - Administrator
- `ban` - Banned

**DocTypeEnum:**
- `identificacion` - ID document
- `comprobante_domicilio` - Proof of address
- `predio` - Property document
- `cedula_veterinario` - Veterinary license
- `otro` - Other

---

## Flutter Integration Tips

### 1. HTTP Client Setup

```dart
import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  final Dio _dio = Dio(BaseOptions(
    baseUrl: 'http://localhost:8000',
    connectTimeout: Duration(seconds: 5),
    receiveTimeout: Duration(seconds: 3),
  ));

  final storage = FlutterSecureStorage();

  ApiClient() {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          // Token expired, redirect to login
          await storage.delete(key: 'access_token');
          // Navigate to login screen
        }
        return handler.next(error);
      },
    ));
  }
}
```

### 2. Model Classes

```dart
class Bovino {
  final String id;
  final String usuarioId;
  final String? areteBarcode;
  final String? areteRfid;
  final String? razaDominante;
  final DateTime? fechaNac;
  final String? sexo;
  final double? pesoNac;
  final double? pesoActual;
  final String? proposito;
  final String status;

  Bovino({
    required this.id,
    required this.usuarioId,
    this.areteBarcode,
    this.areteRfid,
    this.razaDominante,
    this.fechaNac,
    this.sexo,
    this.pesoNac,
    this.pesoActual,
    this.proposito,
    required this.status,
  });

  factory Bovino.fromJson(Map<String, dynamic> json) {
    return Bovino(
      id: json['id'],
      usuarioId: json['usuario_id'],
      areteBarcode: json['arete_barcode'],
      areteRfid: json['arete_rfid'],
      razaDominante: json['raza_dominante'],
      fechaNac: json['fecha_nac'] != null
          ? DateTime.parse(json['fecha_nac'])
          : null,
      sexo: json['sexo'],
      pesoNac: json['peso_nac']?.toDouble(),
      pesoActual: json['peso_actual']?.toDouble(),
      proposito: json['proposito'],
      status: json['status'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'arete_barcode': areteBarcode,
      'arete_rfid': areteRfid,
      'raza_dominante': razaDominante,
      'fecha_nac': fechaNac?.toIso8601String().split('T')[0],
      'sexo': sexo,
      'peso_nac': pesoNac,
      'peso_actual': pesoActual,
      'proposito': proposito,
    }..removeWhere((key, value) => value == null);
  }
}
```

### 3. API Service Example

```dart
class BovinoService {
  final ApiClient _client;

  BovinoService(this._client);

  Future<List<Bovino>> getBovinos({int skip = 0, int limit = 100}) async {
    final response = await _client._dio.get(
      '/bovinos/',
      queryParameters: {'skip': skip, 'limit': limit},
    );
    return (response.data as List)
        .map((json) => Bovino.fromJson(json))
        .toList();
  }

  Future<Bovino> createBovino(Bovino bovino) async {
    final response = await _client._dio.post(
      '/bovinos/',
      data: bovino.toJson(),
    );
    return Bovino.fromJson(response.data);
  }

  Future<void> deleteBovino(String id) async {
    await _client._dio.delete('/bovinos/$id');
  }
}
```

### 4. Domicilio Service Example

```dart
class Domicilio {
  final String id;
  final String usuarioId;
  final String? calle;
  final String? colonia;
  final String? cp;
  final String? estado;
  final String? municipio;

  Domicilio({
    required this.id,
    required this.usuarioId,
    this.calle,
    this.colonia,
    this.cp,
    this.estado,
    this.municipio,
  });

  factory Domicilio.fromJson(Map<String, dynamic> json) {
    return Domicilio(
      id: json['id'],
      usuarioId: json['usuario_id'],
      calle: json['calle'],
      colonia: json['colonia'],
      cp: json['cp'],
      estado: json['estado'],
      municipio: json['municipio'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'calle': calle,
      'colonia': colonia,
      'cp': cp,
      'estado': estado,
      'municipio': municipio,
    }..removeWhere((key, value) => value == null);
  }
}

class DomicilioService {
  final ApiClient _client;

  DomicilioService(this._client);

  Future<List<Domicilio>> getDomicilios({int skip = 0, int limit = 100}) async {
    final response = await _client._dio.get(
      '/domicilios/',
      queryParameters: {'skip': skip, 'limit': limit},
    );
    return (response.data as List)
        .map((json) => Domicilio.fromJson(json))
        .toList();
  }

  Future<Domicilio> createDomicilio(Domicilio domicilio) async {
    final response = await _client._dio.post(
      '/domicilios/',
      data: domicilio.toJson(),
    );
    return Domicilio.fromJson(response.data);
  }

  Future<Domicilio> updateDomicilio(String id, Map<String, dynamic> updates) async {
    final response = await _client._dio.put(
      '/domicilios/$id',
      data: updates,
    );
    return Domicilio.fromJson(response.data);
  }

  Future<void> deleteDomicilio(String id) async {
    await _client._dio.delete('/domicilios/$id');
  }
}
```

### 5. Predio Service Example

```dart
class Predio {
  final String id;
  final String? domicilioId;
  final String? claveCatastral;
  final double? superficieTotal;
  final double? latitud;
  final double? longitud;

  Predio({
    required this.id,
    this.domicilioId,
    this.claveCatastral,
    this.superficieTotal,
    this.latitud,
    this.longitud,
  });

  factory Predio.fromJson(Map<String, dynamic> json) {
    return Predio(
      id: json['id'],
      domicilioId: json['domicilio_id'],
      claveCatastral: json['clave_catastral'],
      superficieTotal: json['superficie_total']?.toDouble(),
      latitud: json['latitud']?.toDouble(),
      longitud: json['longitud']?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'domicilio_id': domicilioId,
      'clave_catastral': claveCatastral,
      'superficie_total': superficieTotal,
      'latitud': latitud,
      'longitud': longitud,
    }..removeWhere((key, value) => value == null);
  }
}

class PredioService {
  final ApiClient _client;

  PredioService(this._client);

  Future<List<Predio>> getPredios({
    int skip = 0,
    int limit = 100,
    String? domicilioId,
  }) async {
    final params = {'skip': skip, 'limit': limit};
    if (domicilioId != null) {
      params['domicilio_id'] = domicilioId;
    }

    final response = await _client._dio.get(
      '/predios/',
      queryParameters: params,
    );
    return (response.data as List)
        .map((json) => Predio.fromJson(json))
        .toList();
  }

  Future<Predio> createPredio(Predio predio) async {
    final response = await _client._dio.post(
      '/predios/',
      data: predio.toJson(),
    );
    return Predio.fromJson(response.data);
  }

  Future<Predio> updatePredio(String id, Map<String, dynamic> updates) async {
    final response = await _client._dio.put(
      '/predios/$id',
      data: updates,
    );
    return Predio.fromJson(response.data);
  }

  Future<void> deletePredio(String id) async {
    await _client._dio.delete('/predios/$id');
  }
}
```

### 6. Event Creation Example

```dart
class EventoService {
  final ApiClient _client;

  EventoService(this._client);

  Future<Map<String, dynamic>> createPesoEvent({
    required String bovinoId,
    required double pesoNuevo,
    String? observaciones,
  }) async {
    final response = await _client._dio.post(
      '/eventos/',
      data: {
        'type': 'peso',
        'data': {
          'bovino_id': bovinoId,
          'peso_nuevo': pesoNuevo,
          'observaciones': observaciones ?? '',
        },
      },
    );
    return response.data;
  }

  Future<Map<String, dynamic>> createVacunacionEvent({
    required String bovinoId,
    required String veterinarioId,
    required String tipo,
    required String lote,
    required String laboratorio,
    required DateTime fechaProx,
    String? observaciones,
  }) async {
    final response = await _client._dio.post(
      '/eventos/',
      data: {
        'type': 'vacunacion',
        'data': {
          'bovino_id': bovinoId,
          'veterinario_id': veterinarioId,
          'tipo': tipo,
          'lote': lote,
          'laboratorio': laboratorio,
          'fecha_prox': fechaProx.toIso8601String().split('T')[0],
          'observaciones': observaciones ?? '',
        },
      },
    );
    return response.data;
  }
}
```

---

## Testing with Swagger UI

Interactive API documentation is available at:
```
http://localhost:8000/docs
```

This provides:
- Complete API reference
- Request/response examples
- "Try it out" functionality
- Schema definitions

---

## Security Notes

1. **Token Storage:** Always use `flutter_secure_storage` for storing JWT tokens
2. **HTTPS:** Use HTTPS in production
3. **Token Expiration:** Handle 401 responses by redirecting to login
4. **Input Validation:** Validate user inputs on the Flutter side before sending
5. **File Upload:** Validate file types and sizes before uploading

---

## Rate Limiting & Performance

- No rate limiting is currently implemented
- Pagination is supported on list endpoints (use `skip` and `limit`)
- Token expires after 30 minutes (configurable in `.env`)

---

## Support

For issues or questions, refer to the main README.md or check the Swagger documentation at `/docs`.
