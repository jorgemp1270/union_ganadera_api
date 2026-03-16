# Refactoring Arquitectónico - Sistema de Instalaciones (Marzo 16, 2026)

## 🎯 Objetivo
Mejorar la arquitectura del sistema de instalaciones y bovinos para:
1. ✅ Permitir múltiples predios por instalación y viceversa
2. ✅ Relacionar bovinos directamente a instalaciones (no a predios)
3. ✅ Implementar control granular de acceso y privacidad
4. ✅ Validar estado y vencimiento de instalaciones
5. ✅ Restringir tipos de instalación por rol de usuario

---

## 📐 Cambios Arquitectónicos

### 1. Nueva Tabla: `InstalacionPredio` (Many-to-Many Junction)

**Antes:**
```
Instalacion ← (1) facility_id
Predio ← (1) facility_id
| Una instalación tenía muchos predios
| Un predio pertenecía a UNA instalación
```

**Después:**
```
Instalacion ←→ (M:N) InstalacionPredio ←→ Predio
| Una instalación puede tener MUCHOS predios
| Un predio puede estar vinculado a MUCHAS instalaciones
```

**Nueva Tabla SQL:**
```sql
CREATE TABLE instalacion_predio (
  upp_id UUID PRIMARY KEY,
  predio_id UUID PRIMARY KEY,
  FOREIGN KEY (upp_id) REFERENCES instalaciones(id) ON DELETE CASCADE,
  FOREIGN KEY (predio_id) REFERENCES predios(id) ON DELETE CASCADE
);
```

**Modelo ORM:**
```python
class InstalacionPredio(Base):
    __tablename__ = "instalacion_predio"
    upp_id = Column(UUID, FK(instalaciones.id), primary_key=True)
    predio_id = Column(UUID, FK(predios.id), primary_key=True)
    instalacion = relationship("Instalacion", back_populates="predios")
    predio = relationship("Predio", back_populates="instalaciones")
```

---

### 2. Cambio de Relación: Bovino → Instalación

**Antes:**
```
Usuario
├── Bovino
    └── predio_id → Predio → instalacion (facility_id)
```

**Después:**
```
Usuario
├── Bovino
    └── instalacion_id → Instalacion → predios (M:N)
```

**Cambios en Model:**
- ❌ Remover: `Bovino.predio_id`
- ✅ Agregar: `Bovino.instalacion_id` (FK a instalaciones)
- ❌ Remover: `Predio.facility_id`
- ✅ Predio ahora tiene `instalaciones` (lista de InstalacionPredio)

**Cambios en Schemas:**
- ❌ Remover: `predio_id` de BovinoBase
- ✅ Agregar: `instalacion_id` a BovinoBase

---

### 3. Control de Tipos por Rol

**Usuarios Normales (usuario):**
- ✅ Pueden CREAR: `UPP`, `PSG`
- ❌ Pueden CREAR: Todos los demás tipos

**Administradores (administrador/superadministrador):**
- ✅ Pueden CREAR: TODOS los tipos incluyendo `CASETA_INSPECCION` (NUEVO)

**Validación en:**
- POST `/instalaciones/` - Valida rol y tipo solicitado

---

### 4. Nuevo Campo: `fecha_vencimiento`

**Propósito:**
- Rastrear expiración de permisos UPP/PSG
- Bloquear operaciones en instalaciones vencidas

**Detalles:**
- `Instalacion.fecha_vencimiento: Date | NULL`
- Se establece cuando se aprueba una RenovacionUPP
- NULL para tipos que no requieren renovación (RASTRO, FERIA, etc.)
- Se valida automáticamente en:
  - POST /bovinos (crear bovino)
  - POST /eventos (crear eventos)

**Flujo:**
1. User crea UPP/PSG (fecha_vencimiento = NULL)
2. User solicita renovación (POST /instalaciones/{id}/renovaciones/solicitar)
3. Admin aprueba (POST /renovaciones/{id}/aprobar) → fecha_vencimiento = hoy + 365 días
4. Si fecha_vencimiento < hoy → instalación bloqueada

---

### 5. Privacidad y Control de Acceso

#### A. Listado de Instalaciones

**Usuarios Normales:**
- ✅ VEN: Todas sus propias instalaciones
- ❌ NO VEN: Instalaciones de otros usuarios
- 🔍 PUEDEN: Buscar instalaciones externas por código UPP

**Admins/Inspectores:**
- ✅ VEN: TODAS las instalaciones del sistema

**Endpoint:**
```
GET /instalaciones/
├── Usuarios normales: Solo suyas (usuario_id = auth_user)
└── Admins: Todas
```

#### B. Búsqueda de Instalaciones Externas

**Endpoint Público (new):**
```
GET /instalaciones/buscar/codigo/{license_number}
- No requiere autenticación (público)
- Retorna datos básicos de facility
- Permite a usuarios normales descubrir instalaciones ajenas
- PREVIENE: Búsqueda exhaustiva de instalaciones
- PROPÓSITO: Evitar delitos y extorsiones
```

**Ejemplo de Uso:**
```
# Usuario descubre UPP de otro ganadero por código
GET /instalaciones/buscar/codigo/UPP-2026-001
→ Retorna nombre, ubicación, tipo, etc.
```

---

### 6. Validaciones de Estado y Vencimiento

#### Crear Bovino
```
POST /bovino/ {instalacion_id: "uuid"}
├─ ✅ Instalación existe
├─ ✅ Usuario autorizado
├─ ✅ Instalación.active = true
├─ ✅ Instalación.facility_type ∈ {UPP, PSG}
│   → ✅ Instalación.fecha_vencimiento > hoy
└─ ERROR 409: Si alguna validación falla
```

#### Crear Evento
```
POST /eventos/ {bovino_id: "uuid"}
├─ ✅ Bovino existe
├─ ✅ Bovino.instalacion_id existe
├─ ✅ Instalación.active = true
├─ ✅ Instalación.facility_type ∈ {UPP, PSG}
│   → ✅ Instalación.fecha_vencimiento > hoy
└─ ERROR 409: Si alguna validación falla
```

**Excepciones:**
- `compraventa`: NO valida (transfiere ownership)
- `veterinary_events`: Veterinarios pueden crear para cualquier bovino

---

## 📝 Cambios en Endpoints

### NUEVOS Endpoints

#### Búsqueda por Código UPP (Público)
```
GET /instalaciones/buscar/codigo/{license_number}
- Público (no requiere auth)
- Permite a usuarios normales descubrir instalaciones externas
- Retorna: InstalacionResponse básica
- Ejemplo: GET /instalaciones/buscar/codigo/UPP-2026-001234
```

### MODIFICADOS Endpoints

#### Crear Instalación
```
POST /instalaciones/
- Valida tipo según rol:
  * usuario → Solo UPP, PSG
  * admin → Todo tipo
- Establece fecha_vencimiento = NULL (se activa en renovación)
```

#### Listar Instalaciones
```
GET /instalaciones/
- Filtrado por usuario (privacidad)
- Usuarios normales: Solo ven sus instalaciones
- Admins: Ven todas
```

#### Crear Bovino
```
POST /bovinos/
- Valida instalación.active = true
- Valida instalación.fecha_vencimiento si UPP/PSG
- ERROR 409 si instalación inactiva o vencida
```

#### Crear Evento
```
POST /eventos/
- Valida instalación.active = true
- Valida instalación.fecha_vencimiento si UPP/PSG
- ERROR 409 si instalación inactiva o vencida
- Excepciones: compraventa (transferencia de propiedad)
```

#### Aprobar Renovación UPP
```
POST /renovaciones/{renovacion_id}/aprobar
- Establece instalacion.fecha_vencimiento = hoy + 365 días
- Establece renovacion.fecha_proximo_vencimiento = hoy + 365 días
```

---

## 🔄 Cambios en CRUD

### app/crud.py

**Removidas:**
- `get_bovinos_by_predio()` → Cambia a `get_bovinos_by_instalacion()`

**Modificadas:**
- `get_bovinos()`: Parámetro `predio_id` → `instalacion_id`

---

## 🔐 Control de Acceso (ACL)

| Operación | Usuario Normal | Admin | Inspector | Veterinario |
|-----------|---|---|---|---|
| Ver sus instalaciones | ✅ | ✅ * | ✅ * | ❌ |
| Ver todas las instalaciones | ❌ | ✅ | ✅ | ❌ |
| Buscar por código (público) | ✅ | ✅ | ✅ | ✅ |
| Crear UPP/PSG | ✅ | ✅ | ❌ | ❌ |
| Crear otros tipos | ❌ | ✅ | ❌ | ❌ |
| Aprobar documentos | ❌ | ✅ | ❌ | ❌ |
| Aprobar renovación | ❌ | ✅ | ✅ | ❌ |
| Crear eventos generales | ✅ * | ✅ | ❌ | ❌ |
| Crear eventos veterinarios | ❌ | ❌ | ❌ | ✅ |

\* _ven todas luego de cambios recientes_

---

## 🆕 Nuevo Tipo de Facilidad

**CASETA_INSPECCION**
- Tipo de instalación para casetas de inspección
- Solo puede ser creada por administradores
- Típicamente no tiene fecha_vencimiento
- Puede estar vinculada a múltiples predios

---

## 📊 Impacto en Base de Datos

### Migration Steps (Manual)

1. Crear tabla `instalacion_predio`:
```sql
CREATE TABLE instalacion_predio (
  upp_id UUID PRIMARY KEY,
  predio_id UUID PRIMARY KEY,
  FOREIGN KEY (upp_id) REFERENCES instalaciones(id) ON DELETE CASCADE,
  FOREIGN KEY (predio_id) REFERENCES predios(id) ON DELETE CASCADE
);
```

2. Transferir datos (si existen):
```sql
INSERT INTO instalacion_predio (upp_id, predio_id)
SELECT id, facility_id FROM instalaciones WHERE facility_id IS NOT NULL;
```

3. Actualizar columnas en `bovinos`:
```sql
ALTER TABLE bovinos DROP COLUMN predio_id;
ALTER TABLE bovinos ADD COLUMN instalacion_id uuid REFERENCES instalaciones(id);
```

4. Actualizar columnas en `predios`:
```sql
ALTER TABLE predios DROP COLUMN facility_id;
```

5. Agregar columna a `instalaciones`:
```sql
ALTER TABLE instalaciones ADD COLUMN fecha_vencimiento DATE;
```

6. Actualizar índices:
```sql
DROP INDEX idx_bovinos_predio;
CREATE INDEX idx_bovinos_instalacion ON bovinos(instalacion_id);
```

---

## ✅ Validación de Cambios

### Checklist de Testing

- [ ] Usuario normal crea UPP exitosamente
- [ ] Usuario normal NO puede crear RASTRO
- [ ] Admin puede crear CASETA_INSPECCION
- [ ] Usuario normal NO ve instalaciones de otros
- [ ] Búsqueda pública por código funciona sin auth
- [ ] Crear bovino valida instalacion.active
- [ ] Crear bovino valida fecha_vencimiento si UPP/PSG
- [ ] Crear evento valida instalacion.active
- [ ] Aprobar renovación establece fecha_vencimiento correctamente
- [ ] Bovino con instalacion_id vencida bloquea eventos

---

## 📌 Notas Importantes

### Compatibilidad
- Los cambios ROMPEN compatibilidad backward con clientes antiguos
- Parámetro `predio_id` → `instalacion_id` en endpoints
- Schema response de bovinos ahora usa `instalacion_id`

### Datos Existentes
- Requiere migración manual de datos (ver sección DB)
- Los predios existentes necesitan ser vinculados a instalaciones

### Privacidad
- El sistema ahora previene que usuarios normales vean instalaciones ajenas
- PREVIENE: búsquedas exhaustivas que podrían facilitar delitos
- PERMITE: búsqueda pública por código para transacciones legítimas

### Vencimiento
- Las instalaciones creadas sin renovación aprobada NO tienen fecha_vencimiento
- Esto permite crear UPPs/PSGs sin bloqueo inmediato
- El bloqueo solo ocurre DESPUÉS de 365 días si no se renueva

---

**Versión:** 1.0  
**Fecha:** Marzo 16, 2026  
**Autores:** Sistema automatizado + Revisión manual
