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
│   ├── migrations/versions/          0001_identity, 0002_operations y 0003_mfa
│   └── tests/                        Pruebas de identidad y operaciones
├── frontend/
│   ├── src/assets/                   Identidad visual
│   ├── src/components/               Componentes reutilizables
│   ├── src/features/                 custody, dashboard, identity, operations,
│   │                                  shared y supervision
│   ├── src/services/                 Cliente HTTP
│   └── tests/                        Pruebas del cliente de API
├── mobile/                           Aplicación Android con Expo / React Native
│   ├── src/app/                      Rutas y pestañas de Expo Router
│   ├── src/api/                      Transporte nativo y tipos del servicio
│   ├── src/auth/                     Acceso, MFA y sesión protegida
│   ├── src/components/               Interfaz y estilos reutilizables
│   ├── src/screens/                  Seguimiento, custodias, puntos, avisos y cuenta
│   ├── src/navigation/               Destinos internos e identificadores válidos
│   ├── scripts/                      Arranque, compatibilidad y previsualización
│   ├── eas.json                      Perfiles APK interno y AAB para tienda
│   └── tests/                        Diez casos de transporte, rutas y compatibilidad
├── herramientas/                      Verificación documental
├── infra/                             Pruebas desechables de PostgreSQL
└── verificar.sh                       Verificación documental y del modelo SQL
```

## Estado de implementación y verificación

El producto ya tiene API FastAPI, frontend React/TypeScript, persistencia PostgreSQL y tres migraciones Alembic. Los módulos funcionales cubren identidad, custodias e inventario, retiros y devoluciones, cobros del servicio, avisos, incidencias y supervisión. Las rutas y entidades se detallan en la [arquitectura](../ingenieria/03_modelado_datos_arquitectura.md).

La verificación del árbol de trabajo basado en `196af44` (2026-11-13) aprobó 43 pruebas de backend con migración, reversión, carga y restauración local, cinco pruebas del cliente y la compilación de producción. El recorrido de acceso MFA también se comprobó en navegador con datos sintéticos. Las limitaciones por requisito están en el [registro de pruebas](../validacion/resultados_pruebas.csv).

El [plan de implementación](02_plan_implementacion.md) conserva la secuencia y los criterios originalmente propuestos; no es un tablero del trabajo pendiente. Para instalar, iniciar y verificar el entorno actual, seguir los comandos del [README](../../README.md).

La primera fase Android añade cinco operaciones de identidad nativa al contrato (54 en total), sin una migración adicional de tablas. La exportación de recursos Android no sustituye la compilación del APK ni la validación en un dispositivo físico.

La versión móvil 0.2.2 usa Expo Router y mantiene las funciones del personal en la web. La lista `.easignore` de la raíz limita la compilación en Expo al código y recursos móviles. Las verificaciones técnicas y el estado del APK se registran en el [README](../../README.md); la ejecución física Android y TalkBack requieren un dispositivo.
