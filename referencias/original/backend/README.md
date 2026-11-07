# Backend: BUZON Xpress S.R.L. API

API distribuida en tiempo real desarrollada en **Python 3.11+ (FastAPI)** siguiendo los principios de **Clean Architecture (Robert C. Martin)** y **Domain-Driven Design (Eric Evans)**.

---

## Estructura de Capas (Clean Architecture)

```
backend/
├── app/
│   ├── domain/               # Capa 1: Entidades de Dominio, Value Objects y Reglas Puras
│   │   ├── models/           # Package, LockerSlot, DeliveryPoint, CustodyEvent
│   │   ├── value_objects/    # BuyerPhone, ChromaticTag, Money
│   │   └── events/           # PackageCreatedEvent, PackageDeliveredEvent
│   ├── application/          # Capa 2: Casos de Uso y Puertos (Interfaces)
│   │   ├── use_cases/        # RegisterPackage, AllocateLocker, FastDispatch, ConsolidateOrders
│   │   └── interfaces/       # IPackageRepository, ILockerRepository, INotifier
│   ├── adapters/             # Capa 3: Controladores API, Repositorios SQLAlchemy y WebSockets
│   │   ├── api/v1/           # Endpoints REST (packages, dispatch, tracking)
│   │   ├── repositories/     # Implementación concreta de persistencia en PostgreSQL
│   │   └── websocket/        # Hub de eventos de presencia y actualización en vivo
│   └── infrastructure/       # Capa 4: Base de datos, Configuración y Frameworks
│       ├── db/               # Sesión SQLAlchemy y migraciones Alembic
│       ├── config.py         # Configuración y variables de entorno
│       └── main.py           # Instancia principal y middlewares de FastAPI
├── tests/                    # Pruebas unitarias e integración con Pytest
└── requirements.txt          # Dependencias del backend
```
