# 🖥️ Flujo de Instalaciones y Predios - Angular Web (Administrador)

**Versión**: 1.0  
**Fecha**: Marzo 16, 2026  
**Usuarios**: Administrador, Superadministrador, Inspector  
**Plataforma**: Angular 21 Web Dashboard

---

## 🎯 Objetivos de este Documento

Este documento guía a los **administradores** del sistema sobre:
1. ✅ Cómo gestionar todas las UPPs, PSGs y otras instalaciones
2. ✅ Cómo revisar y aprobar documentos
3. ✅ Cómo procesar renovaciones de licencia (UPP/PSG)
4. ✅ Cómo monitorear límites y restricciones del sistema
5. ✅ Cómo generar reportes y auditorías

---

## 📊 Arquitectura para Administrador

```
┌─────────────────────────────────────────────────────┐
│          🖥️ DASHBOARD ADMINISTRATIVO                │
│                                                     │
│  Total UPPs: 1,234  |  PSGs: 456  |  Otros: 89   │
│  Pendientes: 45     |  Vencidas: 12                │
│  Usuarios: 1,240 (Ganaderos + Veterinarios)        │
└──────────────────────┬──────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼────┐      ┌──────▼──────┐    ┌────▼────┐
│Gestión │      │Revisión     │    │Renovac. │
│Instala.│      │Documentos   │    │UPPs/PSGs│
│        │      │             │    │         │
│- CRUD  │      │- Aprobar    │    │- Aprobar│
│- Crear │      │- Rechazar   │    │- Rechazar
│- Admin │      │- Validar    │    │- Extender
│- Vet   │      │- Catastral  │    │365 días |
│        │      │             │    │         │
└────────┘      └─────────────┘    └─────────┘
```

---

## 📋 FLUJO 1: PANEL DE CONTROL (DASHBOARD)

### Vista General

```
┌──────────────────────────────────────────────────────────────┐
│ 🏠 DASHBOARD PRINCIPAL                     [Logout] [Perfil] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ 📊 ESTADÍSTICAS GENERALES                                   │
│ ┌────────────────────────────────────────────────────────┐  │
│ │                                                        │  │
│ │  🏢 Instalaciones Total: 1,789                         │  │
│ │     ├─ UPPs: 1,234 (68%)                             │  │
│ │     ├─ PSGs: 456  (25%)                              │  │
│ │     ├─ OTROS: 99  (5%)                               │  │
│ │     └─ CASETAS_INSPE: 89                             │  │
│ │                                                        │  │
│ │  🟢 Activas: 1,650  |  🔴 Inactivas: 139            │  │
│ │  ⏰ Vencidas: 12    |  ⏳ Próximas vencer: 78        │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ ⚠️ ALERTAS CRÍTICAS                                         │
│ ┌────────────────────────────────────────────────────────┐  │
│ │  🚨 12 UPPs vencidas esperando renovación              │  │
│ │  🟡 78 UPPs vencen en próximos 30 días                │  │
│ │  📄 45 documentos pendientes de revisión               │  │
│ │  ✋ 23 renovaciones pendientes de aprobación           │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ 🔗 ACCESOS RÁPIDOS                                          │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ [📋 Revisar Documentos]                                │  │
│ │ [✅ Aprobar Renovaciones]                              │  │
│ │ [👥 Gestionar Usuarios]                                │  │
│ │ [📊 Reportes]                                          │  │
│ │ [⚙️ Configuración]                                     │  │
│ │                                                        │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 🏢 FLUJO 2: GESTIÓN DE INSTALACIONES

### 2.1 Listar Todas las Instalaciones

**Acceso:**
```
Menú Principal
  ├─ 📋 Instalaciones
  │  ├─ [Ver Todas]
  │  ├─ [UPPs]
  │  ├─ [PSGs]
  │  ├─ [Otras]
  │  ├─ [Vencidas]
  │  └─ [Inactivas]
```

**Interfaz:**

```
┌────────────────────────────────────────────────────────────┐
│ 📋 TODAS LAS INSTALACIONES                                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ [🔍 Buscar por nombre]  [Filtro ▼] [Exportar]            │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ No  Nombre              Tipo    Propietario  Vencimiento │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ 1   El Rancho Feliz     UPP     Juan García  2026-04-15 │ │
│ │     ✅ Activa                                          │ │
│ │     [Ver] [Editar] [Documentos] [Renovar]             │ │
│ │                                                        │ │
│ │ 2   Ganadería del Norte UPP     Roberto Pérez 2026-06-20│ │
│ │     ✅ Activa                                          │ │
│ │     [Ver] [Editar] [Documentos] [Renovar]             │ │
│ │                                                        │ │
│ │ 3   PSG Los Altos        PSG    María López   2026-05-10│ │
│ │     🔴 VENCIDA ❌                                       │ │
│ │     [Ver] [Editar] [Documentos] [Renovar]             │ │
│ │                                                        │ │
│ │ 4   Rastro Municipal     RASTRO Admin        Permanente │ │
│ │     ✅ Activa                                          │ │
│ │     [Ver] [Editar] [Documentos]                       │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Página 1 de 45  [< Anterior] [1] [2] [3]... [Siguiente >] │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Crear Nueva Instalación (Admin)

**El admin PUEDE crear UPPs/PSGs/Trabajadores/Casetas para otros usuarios (ej: veterinarios):**

```
┌────────────────────────────────────────────────────────────┐
│ ➕ CREAR NUEVA INSTALACIÓN                                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ [Nombre Instalación] *                                     │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Caseta de Inspección Léon"                       │
│                                                            │
│ [Tipo de Instalación] ▼ *                                  │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ✅ UPP (Usuario Normal)                               │ │
│ │ ✅ PSG (Usuario Normal)                               │ │
│ │ ✅ RASTRO (Admin)                                     │ │
│ │ ✅ FERIA (Admin)                                      │ │
│ │ ✅ TRABAJADOR (Admin)                                 │ │
│ │ ✅ CASETA_INSPECCION (Admin)                          │ │
│ │ ✅ LABORATORIO (Admin)                                │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Código de Licencia] (Opcional)                            │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│                                                            │
│ [Estado] ▼                                                 │
│ ├─ Guanajuato                                              │
│ └─ [Seleccionar...]                                        │
│                                                            │
│ [Municipio] ▼                                              │
│ ├─ Léon                                                    │
│ └─ [Seleccionar...]                                        │
│                                                            │
│ [Ubicación GPS] (Opcional)                                 │
│ ├─ Latitude: [_______________]                             │
│ └─ Longitude: [_______________]                            │
│                                                            │
│ [¿Agregar Contacto de Referencia?] ☐                      │
│                                                            │
│ [Estado de la Instalación] ☑️ Activa                       │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [❌ Cancelar]  [✅ Crear Instalación]                 │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.3 Editar Instalación

```
┌────────────────────────────────────────────────────────────┐
│ ✏️ EDITAR INSTALACIÓN                                      │
│ "El Rancho Feliz"                                          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ [Nombre] ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  (No editable para UPP) │
│                                                            │
│ [Estado] ☑️ Activa  ☐ Inactiva                             │
│                                                            │
│ ℹ️ Cambiar a INACTIVA hará que:                            │
│    - NO se puedan crear bovinos                            │
│    - NO se puedan registrar eventos                        │
│    - Los bovinos existentes no cambian de estado           │
│                                                            │
│ [Municipio] ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬  Léon, Gto.            │
│                                                            │
│ [Ubicación GPS]                                            │
│ ├─ Latitude: 20.5230                                       │
│ └─ Longitude: -101.2834                                    │
│                                                            │
│ [Contacto]                                                 │
│ ├─ Nombre: Juan García                                     │
│ └─ Teléfono: [_______________]                             │
│                                                            │
│ 📅 Información Importante                                  │
│ ├─ Creada: 2025-03-15                                      │
│ ├─ Vencimiento: 2026-04-15                                 │
│ ├─ Última renovación: 2025-04-15                           │
│ └─ Propietario: Juan García (ID: GARC850415...)           │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [❌ Cancelar]  [✅ Guardar Cambios]  [🗑️ Eliminar]   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📄 FLUJO 3: REVISIÓN Y APROBACIÓN DE DOCUMENTOS

### 3.1 Panel de Documentos Pendientes

**Acceso:**
```
Menú Principal
  ├─ 📄 Documentos
  │  ├─ [Pendientes] ⚠️ (45)
  │  ├─ [Aprobados] ✅
  │  ├─ [Rechazados] ❌
  │  └─ [Por Tipo]
```

**Interfaz:**

```
┌────────────────────────────────────────────────────────────┐
│ 📄 DOCUMENTOS PENDIENTES DE REVISIÓN (45)                  │
│                                                            │
│ [🔍 Filtrar] [Por: Instalación ▼] [Por: Tipo ▼]          │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 1. Constancia Fiscal - El Rancho Feliz               │ │
│ │    Instalación: El Rancho Feliz (UPP)                │ │
│ │    Propietario: Juan García                           │ │
│ │    Enviado: 2026-03-10 15:30                          │ │
│ │    [Ver Documento] [👁️ Preview]                      │ │
│ │    [✅ Aprobar]  [❌ Rechazar]  [💬 Comentarios]      │ │
│ │                                                       │ │
│ │ 2. Clave Catastral - Ganadería del Norte            │ │
│ │    Instalación: Ganadería del Norte (UPP)           │ │
│ │    Propietario: Roberto Pérez                        │ │
│ │    Enviado: 2026-03-10 14:15                         │ │
│ │    [Ver Documento] [👁️ Preview]                     │ │
│ │    [✅ Aprobar]  [❌ Rechazar]  [💬 Comentarios]     │ │
│ │                                                       │ │
│ │ 3. Certificado Parcelario - PSG Los Altos           │ │
│ │    Instalación: PSG Los Altos (PSG)                 │ │
│ │    Propietario: María López                          │ │
│ │    Enviado: 2026-03-10 10:45                         │ │
│ │    [Ver Documento] [👁️ Preview]                     │ │
│ │    [✅ Aprobar]  [❌ Rechazar]  [💬 Comentarios]     │ │
│ │                                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Página 1 de 5  [< Anterior] [1] [2] [3]... [Siguiente >]  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.2 Revisar Documento

**Cuando haces click en "Ver Documento":**

```
┌────────────────────────────────────────────────────────────┐
│ 📄 REVISAR DOCUMENTO                                       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Instalación: El Rancho Feliz (UPP)                         │
│ Tipo: Constancia Fiscal                                    │
│ Propietario: Juan García                                   │
│ Enviado: 2026-03-10 15:30                                  │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │                                                        │ │
│ │               📄 VISTA PREVIA DEL DOCUMENTO           │ │
│ │                                                        │ │
│ │  [Imagen del PDF o archivo subido]                   │ │
│ │                                                        │ │
│ │  Nombre Archivo: Constancia_SAT_2026.pdf              │ │
│ │  Tamaño: 2.3 MB                                       │ │
│ │  [⬇️ Descargar]  [🖨️ Imprimir]  [🔗 Link Directo]   │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 📝 DECISIÓN DEL REVISOR                                   │
│                                                            │
│ [✅ APROBAR DOCUMENTO]                                     │
│                                                            │
│ [❌ RECHAZAR DOCUMENTO]                                    │
│                                                            │
│ [Razón del Rechazo] (si aplica)                            │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Documento vencido. Favor reenviar               │
│          certificado actualizado."                         │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [← Atrás]  [💾 Guardar Decisión]                      │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 3.3 Validación: Clave Catastral Única

**Cuando se aprueba un documento de Clave Catastral:**

```
El sistema automáticamente verifica:

1️⃣ ¿Existe otra UPP con la misma clave catastral?
   ├─ Si: ❌ ERROR 409 - "Clave catastral duplicada"
   └─ No: ✅ Continúa

2️⃣ ¿El documento es válido?
   ├─ Si: ✅ APROBADO
   └─ No: ❌ Se rechaza

Resultado en Admin:
┌────────────────────────────────────────┐
│ ✅ DOCUMENTO APROBADO                  │
│                                        │
│ Clave Catastral: 1234567890           │
│ UPP: El Rancho Feliz                  │
│ Estado: ÚNICA en el sistema           │
│                                        │
│ Predios Vinculados: 2                 │
│ ├─ Terreno Sur (30 hectáreas)        │
│ └─ Terreno Norte (50 hectáreas)      │
│                                        │
│ ℹ️ Claves catastrales duplicadas      │
│    se rechazan automáticamente        │
└────────────────────────────────────────┘
```

---

## 🔄 FLUJO 4: RENOVACIONES DE UPP/PSG

### 4.1 Panel de Renovaciones Pendientes

**Acceso:**
```
Menú Principal
  ├─ 🔄 Renovaciones
  │  ├─ [Pendientes] ⚠️ (23)
  │  ├─ [Aprobadas] ✅
  │  ├─ [Rechazadas] ❌
  │  └─ [Por Fecha]
```

**Interfaz:**

```
┌────────────────────────────────────────────────────────────┐
│ 🔄 RENOVACIONES PENDIENTES (23)                            │
│                                                            │
│ [🔍 Buscar]  [Filtro: Por Vencimiento ▼]  [Exportar]     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ⚠️ URGENTES (Vencen en < 7 días)                       │ │
│ │                                                        │ │
│ │ 1. El Rancho Feliz (UPP)                              │ │
│ │    Propietario: Juan García                           │ │
│ │    Vencimiento: 2026-03-22 (HOY)  🔴                 │ │
│ │    [Ver Detalles] [✅ Aprobar] [❌ Rechazar]          │ │
│ │                                                        │ │
│ │ 2. Ganadería del Norte (UPP)                          │ │
│ │    Propietario: Roberto Pérez                         │ │
│ │    Vencimiento: 2026-03-25 (3 días)  🟠              │ │
│ │    [Ver Detalles] [✅ Aprobar] [❌ Rechazar]          │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📋 EN TIEMPO (Vencen en > 7 días)                     │ │
│ │                                                        │ │
│ │ 3. PSG Los Altos (PSG)                                │ │
│ │    Propietario: María López                           │ │
│ │    Vencimiento: 2026-04-10 (19 días)  🟡             │ │
│ │    [Ver Detalles] [✅ Aprobar] [❌ Rechazar]          │ │
│ │                                                        │ │
│ │ 4. UPP Santa Rosa (UPP)                               │ │
│ │    Propietario: Carlos Rodríguez                      │ │
│ │    Vencimiento: 2026-04-20 (29 días)  🟡             │ │
│ │    [Ver Detalles] [✅ Aprobar] [❌ Rechazar]          │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Página 1 de 3  [< Anterior] [1] [2] [3] [Siguiente >]     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 4.2 Aprobar Renovación

**Cuando haces click en "✅ Aprobar":**

```
┌────────────────────────────────────────────────────────────┐
│ ✅ APROBAR RENOVACIÓN                                      │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Instalación: El Rancho Feliz (UPP)                         │
│ Propietario: Juan García                                   │
│                                                            │
│ 📅 INFORMACIÓN DE LA RENOVACIÓN                            │
│ ├─ Vencimiento Actual: 2026-03-22                          │
│ ├─ Nuevo Vencimiento: 2027-03-22 (365 días después)      │
│ ├─ Renovaciones Previas: 2                                 │
│ └─ Última Renovación: 2025-03-22                           │
│                                                            │
│ ⚠️ AL APROBAR:                                             │
│ ├─ fecha_vencimiento = 2027-03-22                          │
│ ├─ Estado = "activa"                                       │
│ ├─ Usuarios pueden crear bovinos                           │
│ ├─ Eventos de salud se permiten                            │
│ └─ Historial se actualiza                                  │
│                                                            │
│ [Comentarios Adicionales] (Opcional)                        │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Documentación en orden. Aprobada."              │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [← Cancelar]  [✅ CONFIRMAR APROBACIÓN]               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Después de Aprobar:**

```
✅ RENOVACIÓN APROBADA

Instalación: El Rancho Feliz                        ✅
Propietario: Juan García                              
Vencimiento Anterior: 2026-03-22                      
Vencimiento Nuevo: 2027-03-22                         
Apropiador: Admin (tu usuario)                        
Fecha Aprobación: 2026-03-22 10:45                    

📧 Notificación Enviada:
   El ganadero recibió email notificando
   que su renovación fue aprobada.

[← Atrás]  [📋 Ir a Renovaciones]  [📊 Reportes]
```

### 4.3 Rechazar Renovación

**Cuando haces click en "❌ Rechazar":**

```
┌────────────────────────────────────────────────────────────┐
│ ❌ RECHAZAR RENOVACIÓN                                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ Instalación: El Rancho Feliz (UPP)                         │
│ Propietario: Juan García                                   │
│ Vencimiento Actual: 2026-03-22                             │
│                                                            │
│ [Razón del Rechazo] ▼ *                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ ☐ Documentos incompletos                              │ │
│ │ ☐ Documentos vencidos                                 │ │
│ │ ☐ Incongruencias en datos                             │ │
│ │ ☐ Bajo investigación SAGARPA                          │ │
│ │ ☐ Deuda pendiente                                     │ │
│ │ ☐ Otra razón                                          │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [Detalles de la Razón] *                                   │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Los certificados de los predios                 │
│          están vencidos desde 2025. Favor                 │
│          actualizar ante el SAT."                         │
│                                                            │
│ ⚠️ EFECTO DEL RECHAZO:                                     │
│ ├─ fecha_vencimiento NO se actualiza                       │
│ ├─ fecha_vencimiento sigue siendo 2026-03-22              │
│ ├─ Usuarios SEGUIRÁN SIN PODER crear bovinos              │
│ ├─ Renovación vuelve a estado "rechazada"                  │
│ └─ Se enviará notificación al ganadero                     │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [← Cancelar]  [✅ CONFIRMAR RECHAZO]                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 👥 FLUJO 5: GESTIÓN DE USUARIOS

### 5.1 Listar Usuarios

**Acceso:**
```
Menú Principal
  ├─ 👥 Usuarios
  │  ├─ [Todos]
  │  ├─ [Ganaderos Normales]
  │  ├─ [Veterinarios]
  │  ├─ [Administradores]
  │  └─ [Por Estado]
```

**Interfaz:**

```
┌────────────────────────────────────────────────────────────┐
│ 👥 GESTIÓN DE USUARIOS                                     │
│                                                            │
│ [🔍 Buscar por nombre/email] [Filtro ▼] [➕ Nuevo]       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ No  Nombre       Rol          Instalaciones  Activo    │ │
│ ├────────────────────────────────────────────────────────┤ │
│ │ 1   Juan García  Ganadero     2 UPPs        ✅ Sí      │ │
│ │     [Ver] [Editar]  [Documentos]  [Historial]         │ │
│ │                                                       │ │
│ │ 2   Roberto Pérez Ganadero    1 UPP         ✅ Sí      │ │
│ │     [Ver] [Editar]  [Documentos]  [Historial]         │ │
│ │                                                       │ │
│ │ 3   Dr. Felipe   Veterinario  N/A           ✅ Sí      │ │
│ │     [Ver] [Editar]  [Auditoría]  [Historial]          │ │
│ │                                                       │ │
│ │ 4   María López  Ganadero     1 PSG         🔴 No      │ │
│ │     [Ver] [Editar]  [Reactivar]  [Historial]          │ │
│ │                                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Total: 1,240 usuarios  |  Activos: 1,189  |  Inactivos: 51│
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 5.2 Ver Perfil Completo de Usuario

**Cuando haces click en "Ver":**

```
┌────────────────────────────────────────────────────────────┐
│ 👤 PERFIL COMPLETO: Juan García                           │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 📋 DATOS PERSONALES                                        │
│ ├─ Nombre: Juan García Rodríguez                           │
│ ├─ Email: juan.garcia@email.com                            │
│ ├─ Teléfono: +52 477 1234567                               │
│ ├─ RFC: GARJ850415ABC                                      │
│ ├─ Cédula: 123456789                                       │
│ ├─ Fecha de Nacimiento: 1985-04-15                         │
│ └─ Rol: GANADERO_NORMAL                                    │
│                                                            │
│ 📍 DOMICILIOS (2)                                          │
│ ├─ Domicilio 1 (Principal)                                 │
│ │  └─ Calle Principal 123, Apt 4B, Léon, Gto.            │
│ ├─ Domicilio 2 (Alternativo)                               │
│ │  └─ Carretera a Silao km 5, Léon, Gto.                 │
│                                                            │
│ 📄 DOCUMENTOS (4)                                          │
│ ├─ Credencial INE: ✅ Aprobado                           │
│ ├─ Comprobante Domicilio: ✅ Aprobado                    │
│ ├─ RFC: ⏳ Pendiente                                       │
│ └─ Cédula de Ganadero: ✅ Aprobado                        │
│                                                            │
│ 🏢 INSTALACIONES (2)                                       │
│ ├─ El Rancho Feliz (UPP)                                  │
│ │  └─ ✅ Activa | Vencimiento: 2026-04-15               │
│ ├─ Terreno Extra (UPP)                                    │
│ │  └─ ✅ Activa | Vencimiento: 2026-06-20               │
│                                                            │
│ 🐄 BOVINOS (47)                                            │
│ ├─ Total: 47 cabezas de ganado                             │
│ ├─ Hembras: 28  |  Machos: 19                              │
│ └─ En El Rancho Feliz: 30  |  En Terreno Extra: 17        │
│                                                            │
│ 📊 HISTORIAL Y AUDITORÍA                                   │
│ ├─ Creado: 2024-01-15 10:30                                │
│ ├─ Última actividad: 2026-03-20 14:20                      │
│ ├─ Renovaciones: 2 totales                                 │
│ ├─ Documentos subidos: 15 totales                          │
│ └─ [📋 Ver Auditoría Completa]                             │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [← Atrás]  [✏️ Editar]  [🔒 Cambiar Contraseña]       │ │
│ │ [🚫 Desactivar Usuario]                                │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📊 FLUJO 6: REPORTES Y ANALÍTICA

### 6.1 Panel de Reportes

**Acceso:**
```
Menú Principal
  ├─ 📊 Reportes
  │  ├─ [Instalaciones]
  │  ├─ [Renovaciones]
  │  ├─ [Documentos]
  │  ├─ [Bovinos]
  │  ├─ [Eventos de Salud]
  │  └─ [Auditoría]
```

**Interfaz:**

```
┌────────────────────────────────────────────────────────────┐
│ 📊 REPORTES                                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 📈 REPORTE DE INSTALACIONES                               │
│                                                            │
│ [Tipo ▼] [Estado ▼] [Municipio ▼] [Fecha Inicio] [Fin]   │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Total Instalaciones: 1,789                             │ │
│ │                                                        │ │
│ │ Por Tipo:                                              │ │
│ │  ├─ UPP: 1,234 (68%)                                  │ │
│ │  ├─ PSG: 456 (25%)                                    │ │
│ │  ├─ RASTRO: 45 (2%)                                   │ │
│ │  ├─ LABORATORIO: 34 (2%)                              │ │
│ │  ├─ TRABAJADOR: 15 (1%)                               │ │
│ │  └─ OTROS: 5 (<1%)                                    │ │
│ │                                                        │ │
│ │ Por Estado:                                            │ │
│ │  ├─ Activas: 1,650 (92%)                              │ │
│ │  ├─ Inactivas: 139 (8%)                               │ │
│ │                                                        │ │
│ │ Vencimiento:                                           │ │
│ │  ├─ Vencidas: 12 (0.7%)                               │ │
│ │  ├─ Próximas a vencer (< 30d): 78 (4.4%)              │ │
│ │  └─ Activas: 1,699 (94.9%)                            │ │
│ │                                                        │ │
│ │ [📥 Descargar PDF]  [📊 Excel]  [🖨️ Imprimir]         │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ 🔄 REPORTE DE RENOVACIONES (Últimos 90 días)             │
│                                                            │
│ [Tipo ▼] [Estado ▼] [Municipio ▼] [Fecha Inicio] [Fin]   │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ Total Renovaciones: 345                                │ │
│ │                                                        │ │
│ │ Aprobadas: 310 (90%)  📈 Tendencia positiva           │ │
│ │ Rechazadas: 35 (10%)  📉 Razones comunes:             │ │
│ │                       - Documentos incompletos (60%)    │ │
│ │                       - Documentos vencidos (25%)       │ │
│ │                       - Otros (15%)                     │ │
│ │                                                        │ │
│ │ Tiempo promedio de aprobación: 2.3 días               │ │
│ │ Tasa de primera aprobación: 85%                        │ │
│ │                                                        │ │
│ │ [📥 Descargar PDF]  [📊 Excel]  [🖨️ Imprimir]         │ │
│ │                                                        │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ [➕ Crear Reporte Personalizado]                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 6.2 Reporte de Auditoría

```
┌────────────────────────────────────────────────────────────┐
│ 🔐 AUDITORÍA COMPLETA - Juan García                       │
│                                                            │
│ [Tipo ▼] [Período ▼] [Acción ▼] [Usuario▼] [Buscar]     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 2026-03-20 14:20 | Creó Bovino                            │
│                  | Bovino: Ternera #0003 "Princesa"       │
│                  | IP: 192.168.1.45                       │
│                                                            │
│ 2026-03-19 10:15 | Renovación Solicitada                  │
│                  | Instalación: Terreno Extra             │
│                  | Estado: Pendiente                      │
│                  | IP: 192.168.1.45                       │
│                                                            │
│ 2026-03-18 15:45 | Documento Subido                       │
│                  | Tipo: Constancia Fiscal                │
│                  | Instalación: El Rancho Feliz           │
│                  | IP: 192.168.1.45                       │
│                                                            │
│ 2026-03-17 09:30 | Cambio de Contraseña                  │
│                  | Usuario: juan.garcia@email.com         │
│                  | IP: 192.168.1.40                       │
│                                                            │
│ 2026-03-10 14:30 | Bovino Transferido (Compraventa)       │
│                  | Bovino: Macho #0002 "Toro Fuerte"      │
│                  | Destino: Roberto Pérez                 │
│                  | IP: 192.168.1.45                       │
│                                                            │
│ [< Anterior] [Página 1 de 34] [Siguiente >]              │
│                                                            │
│ [📥 Descargar Auditoría Completa]                         │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🚨 VALIDACIONES AUTOMÁTICAS QUE ADMINISTRADOR DEBE CONOCER

### Validación 1: Clave Catastral Única

```
CUANDO: Admin aprueba documento de Clave Catastral
VERIFICA: ¿Existe otra UPP con misma clave?

SI EXISTE:
├─ Error HTTP 409
├─ Documento rechazado automáticamente
└─ Notification: "Clave catastral ya registrada"

NUNCA:
└─ Se permite duplicados
```

### Validación 2: UPP/PSG Vencida = Bloqueada

```
CUANDO: Ganadero intenta crear bovino en UPP/PSG vencida

CHEQUEA:
├─ instalacion.fecha_vencimiento < HOY?
├─ instalacion.estado != 'activa'?

SI FALLA:
├─ Error HTTP 409
├─ Bovino no se crea
├─ Mensaje: "UPP vencida. Solicita renovación."
└─ Usuario puede solicitar renovación desde app

SI PASA:
└─ Bovino se crea normalmente
```

### Validación 3: Instalación Inactiva = Bloqueada

```
CUANDO: Ganadero intenta crear bovino en UPP inactiva

CHEQUEA:
├─ instalacion.estado == 'activa'?

SI NO ESTÁ ACTIVA (Admin la desactivó):
├─ Error HTTP 409
├─ Bovino no se crea / Evento no se registra
└─ No se permite ninguna actividad

SI ESTÁ ACTIVA:
└─ Operación continúa (si no hay otra validación)
```

---

## 🔧 CONFIGURACIÓN Y AJUSTES (Superadministrador)

### Acceso a Configuración

```
Menú Principal
  ├─ ⚙️ Configuración
  │  ├─ [Sistema]
  │  ├─ [Seguridad]
  │  ├─ [Roles y Permisos]
  │  ├─ [Integraciones]
  │  └─ [Backup y Recuperación]
```

### Panel de Configuración

```
┌────────────────────────────────────────────────────────────┐
│ ⚙️ CONFIGURACIÓN DEL SISTEMA                               │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ 🔒 SEGURIDAD                                               │
│ ├─ Contraseña mínima: 12 caracteres                        │
│ ├─ Requisire 2FA: ☑️ Habilitado                           │
│ ├─ Expiración de sesión: 30 minutos                        │
│ ├─ Max intentos de login: 5                                │
│ └─ Bloqueo temporal: 15 minutos                            │
│                                                            │
│ 📧 CORREOS Y NOTIFICACIONES                                │
│ ├─ Email de soporte: soporte@unionganadera.gob.mx         │
│ ├─ Recordatorio vencimiento: ☑️ 30 días antes              │
│ ├─ Notificación documento aprobado: ☑️ Sí                 │
│ └─ Notificación renovación rechazada: ☑️ Sí               │
│                                                            │
│ 🐄 VALIDACIONES DE GANADO                                  │
│ ├─ Permitir transferencia entre municipios: ☑️            │
│ ├─ Verificación de genealogía: ☐                          │
│ └─ Número máximo de animales por UPP: 5000                │
│                                                            │
│ 📄 DOCUMENTOS                                              │
│ ├─ Tipos requeridos por UPP: Catastral, Fiscal, Parcel.   │
│ ├─ Tamaño máximo de archivo: 25 MB                         │
│ ├─ Formatos aceptados: PDF, JPG, PNG                       │
│ └─ Días para renovar antes de vencer: 30                   │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ [💾 Guardar Cambios]  [↩️ Reset a Valores Iniciales]   │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 📱 CAMBIOS Breaking PARA ANGULAR (Desarrolladores)

**Todos los endpoints que usaban `predio_id` ahora usan `instalacion_id`:**

### Endpoints Afectados

```javascript
// ❌ OLD (Ya no funciona)
POST /api/bovinos/
{
  "predio_id": "UUID",
  ... otros campos
}

// ✅ NEW (Usar esto)
POST /api/bovinos/
{
  "instalacion_id": "UUID",  // ← Cambio
  ... otros campos
}

// ❌ OLD
GET /api/bovinos/?predio_id=UUID

// ✅ NEW
GET /api/bovinos/?instalacion_id=UUID

// ❌ OLD
GET /api/bovinos/listar_por_predio/{predio_id}

// ✅ NEW
GET /api/bovinos/listar_por_instalacion/{instalacion_id}
```

### Actualizar en Angular

**En services/bovinos.service.ts:**

```typescript
// Cambiar queryParams
get(instalacion_id: string) {
  return this.http.get(`${this.apiUrl}?instalacion_id=${instalacion_id}`);
}

// Cambiar modelo
interface Bovino {
  id: string;
  nombre: string;
  // ❌ predio_id: string;  // ELIMINAR
  instalacion_id: string;  // ✅ AGREGAR
  // ... otros campos
}

// Cambiar formularios
form.controls['instalacion_id'].setValue(value);
// ❌ form.controls['predio_id'].setValue(value);
```

**En componentes HTML:**

```html
<!-- ❌ OLD -->
<input [(ngModel)]="bovino.predio_id" />

<!-- ✅ NEW -->
<input [(ngModel)]="bovino.instalacion_id" />

<!-- Cambiar en selects -->
<select [(ngModel)]="bovino.instalacion_id" formControlName="instalacion_id">
  <option *ngFor="let inst of instalaciones" [value]="inst.id">
    {{inst.nombre}}
  </option>
</select>
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN PARA ADMIN

### Dashboard
- [ ] Ver estadísticas de instalaciones activas/inactivas
- [ ] Ver alertas de renovaciones vencidas
- [ ] Ver documentos pendientes de revisión

### Gestión de Instalaciones
- [ ] Crear casetas de inspección (solo admin)
- [ ] Crear trabajadores (solo admin)
- [ ] Desactivar instalaciones cuando sea necesario
- [ ] Ver historial de cambios de estado

### Documentos
- [ ] Revisar documentos de clave catastral
- [ ] Rechazar documentos incompletos con razones
- [ ] Aprobar documentos válidos
- [ ] Verificar que claves catastrales no se dupliquen

### Renovaciones
- [ ] Procesar renovaciones pendientes
- [ ] Aprobar renovaciones con verificación de documentos
- [ ] Rechazar renovaciones con razones claras
- [ ] Notificar a ganaderos del resultado

### Usuarios
- [ ] Ver perfil completo de ganaderos
- [ ] Revisar instalaciones de cada usuario
- [ ] Ver bovinos asociados
- [ ] Desactivar usuarios si es necesario

### Reportes
- [ ] Generar reporte semanal de renovaciones
- [ ] Exportar datos de instalaciones por municipio
- [ ] Revisar auditoría de cambios
- [ ] Identificar patrones de rechazos

---

## 📞 SOPORTE TÉCNICO

**Errores Comunes:**

| Problema | Solución |
|----------|----------|
| "Clave catastral duplicada" | Verificar que no exista otra UPP con esa clave |
| Usuario no puede crear bovino | Verificar que UPP esté activa y no vencida |
| Documento no se sube | Verificar tamaño (máx 25MB) y formato (PDF/JPG/PNG) |
| Renovación pendiente no aparece | Recargar página o verificar filtros |
| Usuario no ve su instalación | Verificar que sea propietario de la instalación |

---

**Versión**: 1.0  
**Última actualización**: Marzo 16, 2026  
**Compatibilidad**: Angular 21, API Union Ganadera v1.0.1
