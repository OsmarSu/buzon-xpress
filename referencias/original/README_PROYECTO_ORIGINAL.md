# BUZON Xpress S.R.L. - Entregas y Almacenamiento

> Plataforma logística de custodia temporal, casilleros cromáticos inteligentes, consolidación multitienda y despacho ultra-rápido (< 5s) para Social Commerce y Comercio Electrónico en Bolivia.

---

## 🚀 Arquitectura y Tecnologías del Sistema

* **Frontend:** React 19 + TypeScript + Vite + Tailwind CSS v4 + React Router v7 + Lucide Icons.
* **Backend:** Python 3.11+ / 3.14 + FastAPI + Clean Architecture + Domain-Driven Design (DDD) + Pydantic v2.
* **Base de Datos:** PostgreSQL 16 + SQLAlchemy 2.0 ORM + Alembic + Docker Compose (16 tablas, índices parciales B-Tree, triggers de auditoría inmutable).
* **Despliegue & Operaciones:** Soporte SPA en producción para Surge / Vercel (`200.html`), PWA Offline con sincronización idempotente.

---

## 📂 Estructura del Repositorio

```
buzon-xpress/
├── docker-compose.yml              # PostgreSQL 16 Alpine con auto-inicialización de esquema
├── README.md                       # Documentación principal del proyecto
├── docs/                           # Ingeniería y Formulación de Negocio
│   ├── negocio/
│   │   └── BuzonExpress_Formulacion_Negocio.md   # Modelos Osterwalder, Christensen, Blue Ocean
│   └── ingenieria/
│       ├── BuzonExpress_Especificacion_Software.md # SRS, Clean Architecture, C4, FURPS+
│       ├── 01_modelado_analisis_pressman.md       # Casos de Uso, Clases, CRC, Máquinas de Estado
│       ├── 02_modelado_diseno_ui.md               # Wireframes, Theo Mandel, Benchmarking
│       ├── 03_modelado_datos_arquitectura.md      # ERD, Diccionario de datos, Índices B-Tree
│       ├── 04_propuestas_wireframes_identidad.md  # Identidad visual, colores y paletas
│       ├── 05_wireframes_estructurales_bn.md      # Especificación B&W de interfaces
│       └── 06_casos_de_uso_alto_nivel_y_expandidos.md # Cockburn, Larman, Pressman (CU-AN & CU-EXP)
├── backend/                        # API FastAPI, Capa de Dominio y Aplicación
│   ├── app/
│   │   ├── domain/                 # Entidades y reglas puras
│   │   ├── application/            # Casos de uso e interfaces de repositorio
│   │   └── infrastructure/         # SQLAlchemy ORM, sesión y configuración
│   ├── database/
│   │   └── schema.sql              # DDL PostgreSQL 14+ (16 tablas, constraints, triggers)
│   └── requirements.txt            # Dependencias Python
└── frontend/                       # Aplicación Web React 19 + TypeScript
    ├── src/
    │   ├── components/             # Layout (Navbar, Footer), Landing Sections
    │   ├── context/                # AuthContext (Sesión y navegación por roles)
    │   ├── pages/                  # Landing, Login, Register, Seller, Operator POS, Admin, Tracking
    │   ├── services/               # authService (Persistencia y simulación producción)
    │   └── types/                  # Tipos TypeScript para entidades y roles
    └── package.json                # Scripts de build con soporte SPA (200.html)
```

---

## 👥 Roles del Sistema y Vistas Principales

1. **Vendedor Social Commerce** (`/seller/dashboard`): Pre-registro individual y masivo (TikTok Live / WhatsApp), métricas de ventas y liquidaciones COD.
2. **Operador de Ventanilla POS** (`/operator/terminal`): Búsqueda sub-150ms, pantalla cromática gigante asistida por color (`V-A01`, `M-E07`), cobro COD en efectivo o QR Simple BCB y despacho garantizado en < 5 segundos.
3. **Administrador / Finanzas** (`/admin/dashboard`): Red nacional de sucursales, monitoreo de casilleros, disparador de pagos masivos ACH y auditoría de SLA.
4. **Comprador Final** (`/tracking`): Búsqueda de paquete por celular o guía, consolidación multitienda, visualización de casillero y PIN/QR de retiro sin fricción.

---

## 🏛️ Referentes Teóricos y Metodológicos

* **Ingeniería de Software & CBSE:** Roger S. Pressman (*Software Engineering: A Practitioner's Approach*).
* **Modelado de Casos de Uso:** Alistair Cockburn (*Writing Effective Use Cases*) y Craig Larman (*Applying UML and Patterns*).
* **Diseño Orientado al Dominio:** Eric Evans (*Domain-Driven Design*).
* **Arquitectura de Software:** Robert C. Martin (*Clean Architecture*) y Martin Fowler (*Patterns of Enterprise Application Architecture*).
* **Estrategia de Negocio:** Clayton Christensen (*Jobs-To-Be-Done*), W. Chan Kim & Renée Mauborgne (*Blue Ocean Strategy*), Alexander Osterwalder (*Business Model Generation*).
