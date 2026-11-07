# Modelo de Análisis de Software: Buzzon Express
**Fase de Modelado según Roger S. Pressman (*Ingeniería del Software: Un Enfoque Práctico*)**

---

## 1. Introducción y Principios del Modelado (Pressman)

De acuerdo con Roger S. Pressman, el modelo de análisis debe lograr tres objetivos primordiales:
1. **Describir lo que requiere el cliente.**
2. **Establecer una base para la creación del diseño de software.**
3. **Definir un conjunto de requerimientos que puedan validarse una vez que se construya el software.**

El modelado se estructura en cuatro dimensiones analíticas:
* **Modelado basado en escenarios:** Casos de uso y diagramas de actividades.
* **Modelado basado en clases:** Clases de análisis, diagramas de clases y tarjetas CRC.
* **Modelado del comportamiento:** Diagramas de transición de estados y secuencias de interacción.
* **Modelado orientado al flujo:** Diagramas de Flujo de Datos (DFD Nivel 0 y Nivel 1).

---

## 2. Modelado Basado en Escenarios (Scenario-Based Modeling)

### 2.1. Perfiles de Actores del Sistema
* **Act-01 Vendedor (Emprendedor Social Commerce):** Emite ventas en TikTok Live / WhatsApp. Requiere pre-registrar envíos en segundos sin llenar campos innecesarios.
* **Act-02 Operador de Punto (Ventanilla / Local Aliado):** Atiende físicamente el mostrador. Requiere una interfaz táctil ergonómica y reconocimiento visual inmediato para evitar filas.
* **Act-03 Comprador Final (Cliente):** Recoge los paquetes. Requiere visibilidad sin fricciones técnicas (sin contraseñas complejas) y presentación de credencial digital (QR).
* **Act-04 Sistema / Tareas Asíncronas (Daemon):** Procesa consolidaciones automáticas, caducidad de custodia (>48h) y alertas de estado.

### 2.2. Diagrama de Casos de Uso (UML Use Case)

```mermaid
flowchart LR
    Vendedor["Vendedor (TikTok/Marketplace)"]
    Operador["Operador de Ventanilla"]
    Comprador["Comprador Final"]
    Sistema["Daemon / Sistema"]

    subgraph CasosDeUso ["Sistema Buzzon Express"]
        UC01["UC-01: Pre-registrar Paquete(s)"]
        UC02["UC-02: Confirmar Ingesta en Ventanilla"]
        UC03["UC-03: Asignar y Consolidar Casillero"]
        UC04["UC-04: Búsqueda y Despacho Cromático (<5s)"]
        UC05["UC-05: Consultar Estado y QR de Retiro"]
        UC06["UC-06: Liquidar Cobro Contra Entrega (COD)"]
        UC07["UC-07: Gestionar Alerta de Paquete Expirado"]
    end

    Vendedor --> UC01
    Operador --> UC02
    Operador --> UC04
    Operador --> UC06
    Comprador --> UC05
    Sistema --> UC03
    Sistema --> UC07
    UC02 -.->|<<include>>| UC03
```

### 2.3. Especificaciones Formales de Casos de Uso (Plantilla Pressman)

#### Caso de Uso: UC-04 Búsqueda y Despacho Cromático en Ventanilla (<5 seg)
* **Actor Primario:** Operador de Punto (Act-02).
* **Precondiciones:**
  1. El operador ha iniciado sesión en su terminal de punto autorizado.
  2. Uno o más paquetes se encuentran físicamente en estado `LISTO_PARA_RETIRO`.
* **Disparador (Trigger):** El comprador se presenta en la ventanilla y dicta su número de celular o presenta su código QR en pantalla.
* **Flujo Principal (Escenario de Éxito):**
  1. El operador ingresa los dígitos del teléfono o escanea el QR con la cámara del dispositivo.
  2. El sistema consulta en memoria/caché y localiza los registros de custodia asociados en tiempo de respuesta < 150 ms.
  3. El sistema proyecta la pantalla de **Despacho Cromático**: el fondo completo adopta el color del bloque asignado (ej. Verde Esmeralda, Rojo Pasión, Azul Cobalto) y muestra en tipografía gigante el código de celda (ej. `V-A03`) y la cantidad de paquetes (`2 paquetes consolidados`).
  4. El operador visualiza el color, extrae los paquetes correspondientes de la estantería física sin leer etiquetas pequeñas y valida el nombre del destinatario.
  5. Si el paquete requiere Cobro Contra Entrega (COD), el sistema muestra el monto exacto a cobrar en Bs y habilita cobro en efectivo o QR interoperable (Simple).
  6. El operador presiona el botón físico/táctil "Confirmar Entrega".
  7. El sistema transacciona atómicamente el estado de los paquetes a `ENTREGADO`, marca la celda física como `VACIA` y emite eventos de notificación trilateral.
* **Flujos Alternativos:**
  * *4a. Teléfono no registrado o sin paquetes activos:* El sistema emite una señal sonora suave de error y muestra mensaje "Sin paquetes pendientes de retiro para este número".
  * *6a. Pérdida de conexión a internet:* La aplicación del operador conmuta a modo local (IndexedDB), almacena la confirmación con timestamp e id criptográfico, y proyecta la confirmación en pantalla. La sincronización se realiza automáticamente en segundo plano al recuperar enlace.
* **Postcondiciones:** Los paquetes pasan a estado `ENTREGADO`; el casillero queda disponible para una nueva asignación; el vendedor ve actualizada su consola en tiempo real.

---

## 3. Modelado Basado en Clases (Class-Based Modeling)

Pressman clasifica las clases de análisis en: **Límite (Boundary)**, **Control (Control)** y **Entidad (Entity)**.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           CLASIFICACIÓN DE CLASES DE ANÁLISIS                                   │
├─────────────────────┬─────────────────────────────────────┬─────────────────────────────────────┤
│ Clase de Límite     │ Clase de Control                    │ Clase de Entidad                    │
├─────────────────────┼─────────────────────────────────────┼─────────────────────────────────────┤
│ • PreRegisterView   │ • IngestionController               │ • Package                           │
│ • DispatchView (UX) │ • LockerAllocationController        │ • LockerSlot                        │
│ • TrackingPortalView│ • FastDispatchController            │ • CustodyEvent                      │
│ • QRScannerBoundary │ • NotificationDispatcher            │ • DeliveryPoint                     │
│                     │                                     │ • Seller / BuyerProfile             │
└─────────────────────┴─────────────────────────────────────┴─────────────────────────────────────┘
```

### 3.1. Tarjetas CRC (Class-Responsibility-Collaborator - Ward Cunningham / Pressman)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Clase: LockerSlot (Entidad)                                                                     │
├───────────────────────────────────────────────────┬─────────────────────────────────────────────┤
│ Responsabilidades:                                │ Colaboradores:                              │
│ 1. Conocer su código alfanumérico y color asignado│ • DeliveryPoint                             │
│ 2. Mantener la lista de paquetes contenidos.      │ • Package                                   │
│ 3. Evaluar su capacidad disponible de volumen.    │ • ChromaticTag (Value Object)               │
│ 4. Permitir u ordenar la consolidación por cliente│                                             │
│ 5. Transicionar estado: Vacio -> Ocupado -> Vacio │                                             │
└───────────────────────────────────────────────────┴─────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ Clase: FastDispatchController (Control)                                                         │
├───────────────────────────────────────────────────┬─────────────────────────────────────────────┤
│ Responsabilidades:                                │ Colaboradores:                              │
│ 1. Resolver paquetes activos dado un teléfono/QR. │ • PackageRepository                         │
│ 2. Calcular los códigos cromáticos para UI.       │ • LockerSlotRepository                      │
│ 3. Coordinar la entrega atómica multidestino.     │ • CustodyEventLogger                        │
│ 4. Disparar notificaciones a vendedor y comprador.│ • RealtimeNotificationGateway               │
└───────────────────────────────────────────────────┴─────────────────────────────────────────────┘
```

### 3.2. Diagrama de Clases del Dominio

```mermaid
classDiagram
    class DeliveryPoint {
        +UUID id
        +String name
        +String address
        +String city
        +Boolean isActive
        +getAvailableSlots() List~LockerSlot~
    }

    class LockerSlot {
        +UUID id
        +String slotCode
        +ChromaticColor color
        +LockerStatus status
        +String currentBuyerPhone
        +assignPackage(Package pkg)
        +releaseSlot()
        +isAvailableFor(String phone) Boolean
    }

    class Package {
        +UUID id
        +String trackingNumber
        +UUID sellerId
        +String buyerPhone
        +String buyerName
        +Decimal priceToCollectCOD
        +PackageState state
        +DateTime createdAt
        +DateTime updatedAt
        +transitionTo(PackageState newState)
    }

    class CustodyEvent {
        +UUID id
        +UUID packageId
        +PackageState eventType
        +DateTime timestamp
        +String operatorNotes
    }

    class ChromaticColor {
        <<enumeration>>
        EMERALD_GREEN
        CRIMSON_RED
        COBALT_BLUE
        AMBER_YELLOW
    }

    class LockerStatus {
        <<enumeration>>
        EMPTY
        PARTIALLY_OCCUPIED
        FULL
        BLOCKED
    }

    class PackageState {
        <<enumeration>>
        PRE_REGISTERED
        RECEIVED_AT_POINT
        READY_FOR_PICKUP
        DELIVERED
        EXPIRED
        RETURNED_TO_SELLER
    }

    DeliveryPoint "1" *-- "many" LockerSlot : contiene
    LockerSlot "1" o-- "0..*" Package : custodia
    Package "1" *-- "1..*" CustodyEvent : registra historial
    LockerSlot --> ChromaticColor : codificado visualmente por
    LockerSlot --> LockerStatus : estado
    Package --> PackageState : estado actual
```

---

## 4. Modelado del Comportamiento (Behavioral Modeling)

### 4.1. Diagrama de Máquina de Estados del Paquete (Pressman Statechart)

```mermaid
stateDiagram-v2
    [*] --> PRE_REGISTERED : Vendedor crea orden web
    PRE_REGISTERED --> RECEIVED_AT_POINT : Operador escanea en ventanilla
    RECEIVED_AT_POINT --> READY_FOR_PICKUP : Asignación de casillero (Consolidado o Nuevo)
    
    state READY_FOR_PICKUP {
        [*] --> CustodiaNormal
        CustodiaNormal --> EnRiesgoExpiracion : t > 36 horas
        EnRiesgoExpiracion --> Expirado : t > 48 horas
    }

    READY_FOR_PICKUP --> DELIVERED : Retiro en ventanilla (<5s)
    Expirado --> RETURNED_TO_SELLER : Devolución a vendedor
    DELIVERED --> [*]
    RETURNED_TO_SELLER --> [*]
```

### 4.2. Diagrama de Secuencia: Despacho Asistido por Color en Mostrador (<5s)

```mermaid
sequenceDiagram
    autonumber
    actor C as Comprador Final
    actor O as Operador Ventanilla
    participant UI as App Ventanilla (Tablet)
    participant API as FastAPI DispatchController
    participant Cache as Cache / DB
    participant WS as WebSocket Hub
    actor V as Vendedor (TikTok Live)

    C->>O: Dicta teléfono (ej. 70012345) o muestra QR
    O->>UI: Ingresa teléfono / escanea QR
    UI->>API: GET /v1/dispatch/lookup?phone=70012345
    API->>Cache: Buscar paquetes activos y celdas
    Cache-->>API: Slot: V-A03, Color: VERDE, Paquetes: [Pkg1, Pkg2], TotalCOD: 0 Bs
    API-->>UI: 200 OK (Payload cromático)
    Note over UI: Pantalla se tiñe de VERDE ESMERALDA<br/>Texto Gigante: "V-A03 (2 PAQUETES)"
    O->>O: Extrae paquetes de celda verde sin leer letras chicas
    O->>UI: Clic en "Confirmar Entrega"
    UI->>API: POST /v1/dispatch/confirm {slotId: "V-A03"}
    API->>Cache: Transacción atómica: Pkgs -> DELIVERED, Slot -> EMPTY
    API->>WS: Broadcast Evento PackageDelivered(Pkg1, Pkg2)
    WS-->>V: Notificación en vivo: "Tus 2 pedidos fueron entregados"
    API-->>UI: 200 OK (Despacho Exitoso)
    UI-->>O: Pantalla lista para el siguiente cliente en <1s
```

---

## 5. Modelado Orientado al Flujo (Flow-Oriented Modeling)

### 5.1. DFD Nivel 0 (Diagrama de Contexto de Pressman)

```
                           ┌────────────────────────────────────────────────────────┐
                           │                                                        │
                           │                    SISTEMA CENTRAL                     │
                           │                    BUZZON EXPRESS                      │
                           │                                                        │
                           └───────────────────────────┬────────────────────────────┘
                                                       │
               ┌───────────────────────────────────────┼───────────────────────────────────────┐
               │                                       │                                       │
     Datos de pre-registro                    Lectura QR / Búsqueda                  Consulta estado
               ▲                                       ▲                                       ▲
               │                                       │                                       │
               ▼                                       ▼                                       ▼
    [ ENTIDAD EXTERNA: ]                    [ ENTIDAD EXTERNA: ]                    [ ENTIDAD EXTERNA: ]
    [ Vendedor Social  ]                    [ Operador Punto   ]                    [ Comprador Final  ]
    [ (Emprendedor)    ]                    [ (Ventanilla)     ]                    [ (Destinatario)   ]
```

### 5.2. DFD Nivel 1 (Descomposición en Procesos Principales)

```mermaid
flowchart TD
    E1["Vendedor Social"]
    E2["Operador Ventanilla"]
    E3["Comprador Final"]

    P1["1.0 Ingesta y Pre-registro"]
    P2["2.0 Asignación y Consolidación"]
    P3["3.0 Despacho Cromático"]
    P4["4.0 Trazabilidad y Eventos"]

    D1[("D1: Almacén de Paquetes")]
    D2[("D2: Estado de Casilleros")]
    D3[("D3: Bitácora de Eventos")]

    E1 -->|"Datos de paquete"| P1
    P1 -->|"Guarda orden pre-registrada"| D1
    
    E2 -->|"Confirma ingreso en punto"| P2
    P2 <-->|"Verifica celda de comprador existente"| D2
    P2 -->|"Actualiza ubicación y estado"| D1
    P2 -->|"Emite evento de llegada"| P4

    E3 -->|"Muestra QR / Dicta Teléfono"| P3
    P3 <-->|"Lee paquete y casillero"| D1
    P3 <-->|"Lee configuración cromática"| D2
    P3 -->|"Registra entrega"| D3
    P3 -->|"Libera casillero a VACIO"| D2
    P3 -->|"Emite evento de entrega"| P4

    P4 -->|"Actualización en vivo"| E1
    P4 -->|"Recibo digital de retiro"| E3
```
