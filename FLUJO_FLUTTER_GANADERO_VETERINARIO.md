# 📱 Flujo de Instalaciones y Predios - Flutter (Ganadero/Veterinario)

**Versión**: 1.0  
**Fecha**: Marzo 16, 2026  
**Usuarios**: Ganaderos Normales, Veterinarios  
**Plataforma**: Flutter Mobile App

---

## 🎯 Objetivos de este Documento

Este documento guía a los **ganaderos normales** (usuarios) y **veterinarios** sobre:
1. ✅ Cómo crear y gestionar **UPPs/PSGs** (como cualquier usuario normal)
2. ✅ Cómo crear y vincular **Predios** a instalaciones
3. ✅ Cómo registrar **bovinos** en sus propias instalaciones
4. ✅ Cómo registrar **eventos de salud** (privilegio extra como veterinario)
5. ✅ Limitaciones y restricciones según el tipo de instalación

**Nota Importante**: Los veterinarios son usuarios normales completos. Pueden tener instalaciones propias, crear bovinos, subir documentos, solicitar renovaciones, etc. La única diferencia es que también pueden registrar eventos de salud en CUALQUIER instalación del sistema.

---

## 📊 Arquitectura Nueva (Simplificado para Usuario)

```
┌─────────────────────────────────────────────┐
│              TU PERFIL                      │
│      (Ganadero o Veterinario)               │
└──────────────────┬──────────────────────────┘
                   │
                   ├─────────────────────────────────┐
                   │                                 │
         ┌─────────▼─────────┐          ┌────────────▼──────────┐
         │  TUS UPPs/PSGs    │          │  VES TODAS LAS UPPs   │
         │  (Privadas)       │          │  (Si eres Veterinario)│
         │ - Crear           │          │ - Puedes registrar    │
         │ - Editar          │          │   eventos de salud    │
         │ - Ver documentos  │          │ - Vacunaciones        │
         └────────┬──────────┘          │ - Desparasitaciones   │
                  │                     └───────────────────────┘
                  │
         ┌────────▼──────────┐
         │   TUS PREDIOS     │
         │ (Ligados a Instalis)
         │ - Ubicación del    │
         │   ganado          │
         │ - Documentos      │
         └─────────┬──────────┘
                  │
         ┌────────▼──────────┐
         │   TUS BOVINOS     │
         │ (Ganado)          │
         │ - Registro        │
         │ - Eventos         │
         └───────────────────┘
```

---

## 🔄 FLUJO 1: CREAR UNA UPP (Usuario Normal)

### Paso 1️⃣: Acceder a Instalaciones

```
┌─ Menú Principal
│
├─ Mis Instalaciones 🏢
│  │
│  ├─ [+ Crear Nueva]
│  │
│  └─ Listado de mis UPPs/PSGs
```

### Paso 2️⃣: Formulario de Creación de UPP

**Solo Ganaderos Normales pueden crear UPP y PSG**

```
┌─────────────────────────────────────────┐
│      CREAR NUEVA UNIDAD (UPP)           │
├─────────────────────────────────────────┤
│                                         │
│ [Nombre de la UPP]                      │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "UPP El Rancho Feliz"         │
│                                         │
│ [Código de Licencia UPP] *              │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Formato: UPP-2026-XXXXX (ÚNICO)        │
│                                         │
│ [Estado] ▼                              │
│ └─ Selecciona: Guanajuato, etc.        │
│                                         │
│ [Municipio] ▼                           │
│ └─ Selecciona: Léon, Irapuato, etc.   │
│                                         │
│ [Ubicación de la UPP] (Opcional)        │
│ ┌─────────────────────────────────────┐ │
│ │ 📍 Latitude: 20.5230...             │ │
│ │ 📍 Longitude: -101.2834...          │ │
│ │ [📍 Usar GPS] [📍 Ingresar Manual]  │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [❌ Cancelar]  [✅ Crear UPP]       │ │
│ └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### Paso 3️⃣: Confirmación y Estado

```
✅ UPP Creada Exitosamente

Nombre: El Rancho Feliz
Código: UPP-2026-001234
Estado: Guanajuato / Léon
Vencimiento: ⏳ SIN VENCIMIENTO (Necesita Renovación)

⚠️ Necesitas:
┌─────────────────────────────────────────┐
│ 1. Subir DOCUMENTOS requeridos          │
│    ✅ Constancia fiscal                 │
│    ❌ Certificado parcelario            │
│    ❌ Contrato arrendamiento            │
│    ❌ Clave catastral                   │
│                                         │
│ 2. Vincular PREDIOS (tu terreno)        │
│                                         │
│ 3. Crear BOVINOS (tu ganado)            │
└─────────────────────────────────────────┘

[➡️ Continuar]
```

---

## 📄 FLUJO 2: SUBIR DOCUMENTOS REQUERIDOS

### Requisitos por Tipo

**UPP Requiere:**
1. ✅ Constancia Fiscal
2. ✅ Certificado Parcelario (del SAT)
3. ✅ Contrato de Arrendamiento (si no es tuyo)
4. ✅ Clave Catastral

**Interfaz de Documentos:**

```
┌─────────────────────────────────────────────┐
│   DOCUMENTOS DE LA UPP                      │
│   "El Rancho Feliz"                         │
├─────────────────────────────────────────────┤
│                                             │
│ 📋 Constancia Fiscal                        │
│   Estado: ⏳ Pendiente de Revisión          │
│   [📎 Subir Documento] [❌ Eliminar]       │
│                                             │
│ 📋 Certificado Parcelario                   │
│   Estado: ⏳ Pendiente de Revisión          │
│   [📎 Subir Documento] [❌ Eliminar]       │
│                                             │
│ 📋 Contrato de Arrendamiento                │
│   Estado: ⏳ Pendiente de Revisión          │
│   [📎 Subir Documento] [❌ Eliminar]       │
│                                             │
│ 📋 Clave Catastral                          │
│   Estado: ⏳ Pendiente de Revisión          │
│   [📎 Subir Documento] [❌ Eliminar]       │
│                                             │
│ Progreso: ████████░░ (80%)                 │
│ Esperando aprobación del administrador...   │
│                                             │
│ ℹ️ Nota: Los documentos se envían a        │
│    revisor administrativo. Puedes ver      │
│    comentarios de rechazo aquí.            │
└─────────────────────────────────────────────┘
```

**Flujo de Subida:**

```
[📎 Subir Documento]
        │
        ▼
┌─────────────────────────────┐
│ Selecciona Archivo del Tel  │
├─────────────────────────────┤
│ 📁 Galería                  │
│ 📷 Cámara                   │
│ 📄 Archivos                 │
└─────────────────────────────┘
        │
        ▼
   [Archivo seleccionado]
        │
        ▼
   ⏳ Subiendo... 45%
        │
        ▼
   ✅ Documento Subido
   Estado: Pendiente de Revisión
```

---

## 🌾 FLUJO 3: CREAR Y VINCULAR PREDIOS

### ¿Qué es un Predio?

**Predio** = Tu terreno/propiedad donde tienes el ganado

- Ubicación exacta (GPS)
- Clave catastral (número oficial del SAT)
- Superficie total
- Documentos de propiedad

**NOTA**: Los veterinarios también pueden crear y vincular predios a sus propias instalaciones, exactamente igual que los ganaderos normales.

### Pasos para Vincular Predio a UPP

```
┌─ Mi UPP "El Rancho Feliz"
│
├─ 📍 PREDIOS (Mis Terrenos)
│  │
│  ├─ [+ Crear o Vincular Predio]
│  │
│  └─ Listado
│     ├─ Predio 1: "Terreno Sur" ✅ Vinculado
│     ├─ Predio 2: "Terreno Norte" ❌ Sin vincular
│     └─ [➕ Agregar más predios]
```

### Crear Nuevo Predio

```
┌─────────────────────────────────────────┐
│      CREAR NUEVO PREDIO                 │
├─────────────────────────────────────────┤
│                                         │
│ [Nombre del Predio]                     │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Terreno al Sur"               │
│                                         │
│ [Clave Catastral SAT] *                 │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Debe ser ÚNICA en el sistema            │
│                                         │
│ [Superficie Total (hectáreas)]          │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: 150                            │
│                                         │
│ [Ubicación GPS] (Opcional)              │
│ ┌─────────────────────────────────────┐ │
│ │ 📍 Latitude: _______________        │ │
│ │ 📍 Longitude: ______________        │ │
│ │ [📍 Usar GPS actual]                │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Vincular a esta UPP]  ☑️ Sí            │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [❌ Cancelar]  [✅ Crear Predio]   │ │
│ └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### Resultado: Predio Vinculado

```
✅ Predio Creado y Vinculado

Nombre: Terreno al Sur
Clave Catastral: 1234567890
Superficie: 150 hectáreas
Ubicación: 20.5230°N, 101.2834°W

Vinculado a UPP: "El Rancho Feliz" ✅

¡Ahora puedes crear bovinos en este predio!
```

---

## 🐄 FLUJO 4: CREAR BOVINOS EN LA UPP

### Acceso a Bovinos

```
┌─ Mi UPP "El Rancho Feliz"
│  │
│  ├─ 📍 Predios (vinculados)
│  │
│  ├─ 🐄 MIS BOVINOS
│  │  │
│  │  ├─ [+ Crear Nuevo Bovino]
│  │  │
│  │  └─ Listado
│  │     ├─ Femenil #0001 - "Belinda" ✅ Activo
│  │     ├─ Macho #0002 - "Toro Fuerte" ✅ Activo
│  │     └─ Ternera #0003 - "Princesa" ✅ Activo
```

### Formulario de Creación de Bovino

**⚠️ VALIDACIONES AUTOMÁTICAS:**
- La UPP debe estar **activa** ✅
- Si es UPP: No puede estar **vencida** ✅
- El bovino se asigna a la **instalación** (UPP), no al predio

```
┌─────────────────────────────────────────┐
│      REGISTRAR NUEVO BOVINO             │
├─────────────────────────────────────────┤
│                                         │
│ Instalación: El Rancho Feliz            │
│ ⚠️ Estado: ✅ Activa                    │
│ ⏳ Vencimiento: Sin vencimiento         │
│                                         │
│ [Nombre del Bovino] (Opcional)          │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Belinda"                      │
│                                         │
│ [Arete Barcode] (Opcional)              │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Escanea o ingresa código de barras      │
│                                         │
│ [Arete RFID] (Opcional)                 │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Escanea o ingresa código RFID           │
│                                         │
│ [Raza Dominante] ▼                      │
│ └─ Selecciona: Brahman, Cebú, etc.    │
│                                         │
│ [Sexo] ▼                                │
│ └─ Selecciona: Macho (M), Hembra (F)  │
│                                         │
│ [Fecha de Nacimiento]                   │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: 2023-05-15                     │
│                                         │
│ [Peso Actual (kg)]                      │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: 450                            │
│                                         │
│ [Propósito] ▼                           │
│ └─ Selecciona: Engorde, Reproducción... │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [❌ Cancelar] [✅ Registrar Bovino] │ │
│ └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### Validación de Creación

```
✅ Bovino Registrado Exitosamente

ID: F0E8D5C3-2B1A-4D6F-9A8B-7C4E6D5F3A2B
Nombre: Belinda
Raza: Brahman
Sexo: Hembra
Peso: 450 kg
Estado: ✅ Activo

⚡ Ahora puedes:
  ✅ Registrar eventos de salud (si eres veterinario)
  ✅ Registrar peso
  ✅ Registrar alimentación
  ✅ Transferir a otro ganadero (compraventa)
```

---

## ⚡ FLUJO 5: REGISTRAR EVENTOS (Privilegio Veterinario)

### Tipos de Eventos Disponibles SOLO para Veterinarios

**Privilegio Exclusivo**: Solo los veterinarios pueden registrar eventos de salud. Esto aplica a:

| Evento | Quien Puede | Requerimientos |
|--------|-----------|---|
| 💉 Vacunación | Solo Veterinario | Bovino en UPP/PSG activa |
| 💊 Desparasitación | Solo Veterinario | Bovino en UPP/PSG activa |
| 🔬 Laboratorio | Solo Veterinario | Bovino en UPP/PSG activa |
| 🤒 Enfermedad | Solo Veterinario | Bovino en UPP/PSG activa |
| 🩺 Tratamiento | Solo Veterinario | Enfermedad registrada |
| ➡️ Remisión | Solo Veterinario | Enfermedad registrada |

**En cualquier instalación del sistema** (no solo las propias del veterinario)

### Interfaz para Veterinarios

**Los veterinarios pueden buscar y registrar eventos en CUALQUIER bovino del sistema:**

```
┌─ EVENTOS 📋
│
├─ [🔍 Buscar Bovino en el Sistema]
│  │
│  ├─ Arete Barcode: [__________]
│  ├─ Arete RFID: [__________]
│  └─ Nombre/ID: [__________]
│
└─ Resultados (de CUALQUIER PROPIETARIO)
   │
   ├─ 🐄 Belinda (ID: F0E8...)
   │  Raza: Brahman | Peso: 450 kg
   │  Propietario: Juan García
   │  Instalación: El Rancho Feliz ✅ Activa
   │  [➕ Registrar Evento para Belinda]
   │
   ├─ 🐄 Toro Fuerte (ID: A2B3...)
   │  Raza: Cebú | Peso: 650 kg  
   │  Propietario: Roberto Pérez
   │  Instalación: Ganadería del Norte ✅ Activa
   │  [➕ Registrar Evento para Toro Fuerte]
```

⭐ **Diferencia clave**: Los veterinarios NO están limitados a sus propias instalaciones para registrar eventos.

### Registrar Vacunación

```
┌─────────────────────────────────────────┐
│      REGISTRAR VACUNACIÓN               │
│      Bovino: Belinda                    │
├─────────────────────────────────────────┤
│                                         │
│ [Tipo de Vacuna] ▼                      │
│ └─ Fiebre Aftosa, Brucelosis, etc.    │
│                                         │
│ [Laboratorio]                           │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Laboratorios Agropecuarios"  │
│                                         │
│ [Lote/Número de Lote]                   │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│                                         │
│ [Fecha de Próxima Dosis]                │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: 2026-05-16                     │
│                                         │
│ [Observaciones]                         │
│ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬            │
│ Ejemplo: "Buena respuesta inmune"      │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ [❌ Cancelar] [✅ Registrar Evento] │ │
│ └─────────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

---

## 🚫 LIMITACIONES Y RESTRICCIONES

### ❌ NO PUEDES CREAR SI:

#### 1️⃣ Bovino - UPP No Está Activa
```
Error HTTP 409:
┌─────────────────────────────────────────┐
│ ⚠️ ERROR                                │
│                                         │
│ No se puede crear bovino:               │
│ La instalación (UPP) NO está activa     │
│                                         │
│ Estado: ❌ Inactiva                     │
│ Razón: Desactivada por administrador   │
│                                         │
│ [Contacta al administrador]             │
└─────────────────────────────────────────┘
```

#### 2️⃣ Bovino - UPP Está Vencida
```
Error HTTP 409:
┌─────────────────────────────────────────┐
│ ⚠️ ERROR                                │
│                                         │
│ No se puede crear bovino:               │
│ La licencia UPP ha expirado             │
│                                         │
│ Vencimiento: 2025-03-16 ❌             │
│ Hoy: 2026-03-20                        │
│                                         │
│ ℹ️ Solicita renovación de tu UPP       │
│    al administrador                     │
│                                         │
│ [Solicitar Renovación]                  │
└─────────────────────────────────────────┘
```

#### 3️⃣ Evento - Mismas Restricciones
```
Al intentar registrar evento de salud
(vacunación, desparasitación, etc.):

❌ No puedes si:
   - UPP no está activa
   - UPP está vencida (UPP/PSG)

✅ Puedes si:
   - UPP está activa
   - UPP no está vencida
   - Eres veterinario para eventos de salud
```

### ✅ QUÉ SÍ PUEDES HACER SIEMPRE

Como **Usuario Normal**:
- ✅ Ver tus propias UPPs/PSGs
- ✅ Crear UPPs y PSGs (no otros tipos)
- ✅ Subir documentos de renovación
- ✅ Crear predios
- ✅ Crear bovinos (si UPP activa y no vencida)
- ✅ Registrar peso y dieta
- ✅ Vender bovino (compraventa)
- ❌ NO puedes registrar eventos de salud

Como **Veterinario** (Usuario Normal + Permisos Extra):
- ✅ Ver SOLO tus propias UPPs/PSGs (como usuario normal)
- ✅ Crear TUS PROPIAS UPPs y PSGs
- ✅ Crear TUS PROPIOS bovinos
- ✅ Subir documentos de renovación en tus instalaciones
- ✅ Registrar eventos de salud EN CUALQUIER instalación:
  - Vacunaciones
  - Desparasitaciones
  - Laboratorios
  - Enfermedades
  - Tratamientos
  - Remisiones
- ✅ Buscar bovino por código en cualquier UPP
- ✅ Buscar UPPs externas por código/identificador para registrar eventos
- ❌ NO puedes ver UPPs/PSGs de otros ganaderos sin su código
- ❌ NO puedes crear/eliminar instalaciones (solo usuarios normales de admin)

---

## 📡 MANEJO DE SOLICITUD DE RENOVACIÓN

### Cuando tu UPP se va a Vencer

```
┌─ Notificación 📬
│
├─ ⏰ Tu UPP vence en 30 días
│
├─ UPP: "El Rancho Feliz"
│  Vencimiento: 2026-04-15
│
└─ [🔄 Solicitar Renovación Ahora]
```

### Flujo de Solicitud

```
[🔄 Solicitar Renovación]
        │
        ▼
┌─────────────────────────────────────────┐
│ ¿Deseas renovar tu UPP por 1 año más?  │
│                                         │
│ Instalación: El Rancho Feliz            │
│ Vencimiento Actual: 2026-04-15          │
│ Nuevo Vencimiento: 2027-04-15 (si aprueba) │
│                                         │
│ [❌ Cancelar]  [✅ Solicitar]          │
└─────────────────────────────────────────┘
        │
        ▼
✅ Solicitud Enviada

Estado: ⏳ Pendiente de Aprobación
El administrador revisará tu solicitud
en los próximos 3-5 días hábiles.

📧 Te notificaremos por correo cuando
se apruebe o se rechace.
```

---

## 📱 RESUMEN DE PERMISOS POR ROL

| Acción | Usuario Normal | Veterinario |
|--------|---|---|
| Ver propias instalaciones | ✅ | ✅ |
| Crear UPP | ✅ | ✅ |
| Crear PSG | ✅ | ✅ |
| Crear bovino en propias instalaciones | ✅* | ✅* |
| Registrar peso | ✅ | ✅ |
| Registrar dieta | ✅ | ✅ |
| Transferir bovino (compraventa) | ✅ | ✅ |
| Buscar UPPs externas por código | ✅ | ✅ |
| Vacunar bovino | ❌ | ✅** |
| Desparasitar | ❌ | ✅** |
| Registrar laboratorio | ❌ | ✅** |
| Registrar enfermedad | ❌ | ✅** |
| Registrar tratamiento | ❌ | ✅** |
| Registrar remisión | ❌ | ✅** |

_* Solo si su UPP/PSG está activa y no vencida_  
_** En CUALQUIER UPP/PSG del sistema (no solo las propias)_

---

## 🔐 PRIVACIDAD Y SEGURIDAD

### ¿Quién Ve Qué?

```
USUARIO NORMAL (Ganadero):
├─ ✅ VES: Tus UPPs/PSGs propias
├─ ❌ NO VES: UPPs de otros ganaderos
├─ ✅ PUEDES: Buscar UPPs externas por código
│   (Ej: Para vender bovinos)
└─ ❌ NO PUEDES: Registrar eventos de salud

VETERINARIO (Usuario Normal + Permisos Extra):
├─ ✅ VES: Tus UPPs/PSGs propias (como usuario normal)
├─ ❌ NO VES: UPPs de otros ganaderos exhaustivamente
├─ ✅ PUEDES: Buscar UPPs externas por código
│   (Para registrar eventos de salud)
├─ ✅ PUEDES: Registrar eventos en CUALQUIER UPP encontrada
├─ ✅ PUEDES: Ver bovinos de otros propietarios
│   (Solo cuando buscas para registrar evento)
└─ ❌ NO PUEDES: Ver documentos privados de otros

DIFERENCIA CLAVE:
Ganaderos: Solo ven sus propias instalaciones
Veterinarios: Solo ven las suyas PERO pueden trabajar con todas las demás
             (no pueden verlas exhaustivamente, pero sí acceder si conocen código)
```

### Búsqueda de UPPs Externas

Tanto **ganaderos normales** como **veterinarios** pueden buscar UPPs externas por código:

```
┌─ BUSCAR UPP EXTERNA 🔍
│
├─ [Ingresa código de UPP]
│  ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬
│  Ejemplo: UPP-2026-001234
│
├─ [Buscar]
│
└─ Resultado:
   ┌─────────────────────────────┐
   │ UPP: "Ganadería Del Norte"  │
   │ Código: UPP-2026-001234     │
   │ Municipio: Léon,Gto.        │
   │ Propietario: Roberto Pérez  │
   │ Estado: ✅ Activa          │
   │ Vencimiento: 2026-06-20     │
   │                             │
   │ [✅ Puedo venderle bovinos] │
   │ (Ganadero)                  │
   │                             │
   │ [✅ Registrar evento aquí]  │
   │ (Veterinario)               │
   └─────────────────────────────┘
```

**Diferencia**:
- **Ganadero**: Busca para transferir/vender bovinos
- **Veterinario**: Busca para registrar eventos de salud en esa UPP

---

## 🆘 TROUBLESHOOTING

### Problema: "No puedo crear bovino"

**Causa Posible 1: UPP No Activa**
```
Solución:
1. Ve a Mis Instalaciones
2. Verifica que tu UPP esté con ✅ Activa
3. Si está ❌ Inactiva, contacta al admin
```

**Causa Posible 2: UPP Vencida**
```
Solución:
1. Ve a Mis Instalaciones
2. Busca "Solicitar Renovación"
3. El admin debe aprobarla (1-5 días)
```

### Problema: "No puedo ver documentos que subí"

```
Solución:
1. Recarga la pantalla (pull to refresh)
2. Ve a la UPP → Documentos
3. Verifica que se hayan subido
4. Si ves "❌ Error", reintenta
```

### Problema: "Veterinario no me ve para vacunar"

```
Solución:
1. Verifica que tu UPP esté ACTIVA ✅
2. Verifica que NO esté vencida
3. El veterinario debe estar registrado
   en el sistema
4. Contacta al administrador
```

---

## 📞 SOPORTE Y AYUDA

**Si tienes problemas:**

1. Recarga la app
2. Verifica conexión a internet
3. Contacta al administrador
4. Email: soporte@unionganadera.gob.mx

---

**Versión**: 1.0  
**Última actualización**: Marzo 16, 2026
