# Estructura de archivos y secuencia de desarrollo

```text
buzon-xpress/
├── README.md                         Orden de lectura y arranque de verificación
├── docs/
│   ├── perfil/ negocio/ metodologia/ Definición del servicio y antecedentes
│   ├── ingenieria/                   Casos de uso, arquitectura, UX y seguridad
│   │   └── anexos/                   Requisitos JSON, OpenAPI y SQL de referencia
│   ├── gestion/                      Decisiones, implementación y trazabilidad
│   ├── operacion/ validacion/        Manual, criterios y evidencia
│   └── diagramas/ wireframes/        Fuentes editables y láminas
├── entregables/                      Exportaciones de la edición documental 1.0
├── referencias/                       Copias históricas y hashes registrados
├── backend/
│   ├── app/
│   │   ├── domain/                   Reglas, estados y tipos de valor
│   │   ├── application/              Casos de uso y unidades de trabajo
│   │   ├── ports/                    Interfaces de repositorios, reloj y avisos
│   │   ├── adapters/{api,storage,mail}/ API, persistencia y correo
│   │   └── jobs/                     Vencimientos y reintentos de avisos
│   ├── migrations/versions/          Revisiones 0001_identity y 0002_operations
│   └── tests/                        Pruebas de identidad y operaciones
├── frontend/
│   ├── src/assets/                   Identidad visual
│   ├── src/components/               Componentes reutilizables
│   ├── src/features/                 custody, dashboard, identity, operations,
│   │                                  shared y supervision
│   ├── src/services/                 Cliente HTTP
│   └── tests/                        Pruebas del cliente de API
├── herramientas/                      Verificación documental
├── infra/                             Pruebas desechables de PostgreSQL
└── verificar.sh                       Verificación documental y del modelo SQL
```

## Estado de implementación y verificación

El producto ya tiene API FastAPI, frontend React/TypeScript, persistencia PostgreSQL y dos migraciones Alembic. Los módulos funcionales cubren identidad, custodias e inventario, retiros y devoluciones, cobros del servicio, avisos, incidencias y supervisión. Las rutas y entidades se detallan en la [arquitectura](../ingenieria/03_modelado_datos_arquitectura.md).

La última verificación automatizada se ejecutó en un clon limpio de `9405ed7`: las migraciones se aplicaron y revirtieron en PostgreSQL 16 desechable, pasaron las pruebas de backend, las pruebas del frontend y la compilación de producción. También se comprobó una restauración local. Las limitaciones por requisito están en el [registro de pruebas](../validacion/resultados_pruebas.csv).

El [plan de implementación](02_plan_implementacion.md) conserva la secuencia y los criterios originalmente propuestos; no es un tablero del trabajo pendiente. Para instalar, iniciar y verificar el entorno actual, seguir los comandos del [README](../../README.md).
