# Estructura de archivos y secuencia de desarrollo

```text
buzon-xpress-final/
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
│   │   ├── domain/                   Entidades, estados y reglas puras
│   │   ├── application/              Casos de uso y unidades de trabajo
│   │   ├── ports/                    Interfaces de repositorios, reloj y avisos
│   │   ├── adapters/
│   │   │   ├── api/                  Rutas FastAPI, autorización y DTO
│   │   │   ├── storage/              SQLAlchemy y transacciones PostgreSQL
│   │   │   └── mail/                 Transporte opcional de correo
│   │   └── jobs/                     Tareas de vencimientos y avisos
│   ├── migrations/versions/          Futuras revisiones Alembic
│   └── tests/{unit,integration,contract}/
├── frontend/
│   ├── src/{features,services,components}/
│   └── tests/
├── herramientas/                      Generación y verificación documental
├── infra/                             Ensayo de esquema PostgreSQL
└── verificar.sh                       Comprobación reproducible de la línea base
```

## Orden y responsabilidad de archivos

1. Congelar los requisitos de identidad, sesión y alcance. Definir los DTO y revisar el contrato OpenAPI antes de repartir la implementación. Fijar Python 3.13 y Node.js 24, disponibles en WSL, y guardar las versiones exactas al introducir dependencias del producto.
2. Crear la migración inicial con Alembic en un entorno aislado. Comparar los cambios con el [SQL de referencia](../ingenieria/anexos/modelo_propuesto.sql) y ensayar restauración. Las credenciales de base y los secretos se cargan por entorno.
3. Implementar dominio, casos de uso y adaptadores de identidad. La API define un punto de entrada, y la autorización se decide en servidor.
4. Conectar la UI de acceso al contrato real. Organizar `frontend/src/features` por identidad, custodias, operación y supervisión. `services` contiene cliente HTTP y errores comunes.
5. Completar una entrega vertical que registre, reciba, verifique y confirme la salida de un objeto sintético. Después se incorporan incidencias, recuperación, avisos y reportes.

Las carpetas del producto son el punto de partida. Los scripts que se ejecutan hoy verifican el diseño y la persistencia de referencia. El [plan de implementación](02_plan_implementacion.md) detalla los criterios de inicio.
