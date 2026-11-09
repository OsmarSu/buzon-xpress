# BUZON Xpress

**Versión de desarrollo 1.2**

Base documental 1.1.

BUZON Xpress organiza la custodia temporal y el intercambio asíncrono de objetos. El emisor registra y deja el objeto, el operador lo guarda en una ubicación interna y el destinatario lo recoge tras la comprobación digital y presencial. El punto usa su espacio y sus equipos existentes. El personal realiza la recepción y la entrega.

## 1. Documentación

| Para consultar | Fuente |
| --- | --- |
| Alcance, objetivos y justificación | [Perfil](docs/perfil/Perfil_Proyecto_BUZON_Xpress.md) y [decisiones](docs/gestion/01_decisiones_y_correspondencia.md) |
| Negocio, demanda y costos | [Formulación](docs/negocio/BuzonExpress_Formulacion_Negocio.md) y [evaluación](docs/negocio/02_demanda_costos_y_evaluacion.md) |
| Requisitos y reglas | [Especificación](docs/ingenieria/BuzonExpress_Especificacion_Software.md) y [trazabilidad](docs/gestion/03_matriz_trazabilidad.md) |
| Flujos y pantallas | [Casos de uso](docs/ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md), [diseño UI](docs/ingenieria/02_modelado_diseno_ui.md) y [wireframes](docs/wireframes/README.md) |
| Contratos y persistencia | [OpenAPI](docs/ingenieria/anexos/openapi.yaml), [SQL](docs/ingenieria/anexos/modelo_propuesto.sql) y [diccionario](docs/ingenieria/03_modelado_datos_arquitectura.md) |
| Operación y aceptación | [Manual](docs/operacion/01_manual_operativo.md), [plan de validación](docs/validacion/01_plan_validacion.md) y [plan de implementación](docs/gestion/02_plan_implementacion.md) |
| Documentos para presentar | [Perfil y dossier de la edición 1.0 en Word, PDF y HTML](entregables/README.md) |

El repositorio incluye [copias de referencia del sistema original](referencias/original/README.md), que gestionaba paquetería. El perfil, la especificación y el contrato documentan la reformulación para custodia temporal.

## 2. Estructura y verificación

[Mapa de archivos, límites de cada capa y orden de implementación](docs/gestion/04_estructura_de_archivos.md).

La aplicación integra identidad, registro y recepción, inventario, retiro, incidencias y devoluciones, avisos y supervisión. El contrato de [OpenAPI](docs/ingenieria/anexos/openapi.yaml) documenta la API y las consultas de expedientes por punto.

### Requisitos para ejecutar el proyecto

Usa una terminal Bash en Linux o WSL con Git, uv, Node.js 24 y npm. El backend usa Python 3.13, que uv puede instalar. Para ejecutar la aplicación necesitas PostgreSQL 16. Las pruebas de integración crean su propia base con Docker y la prueba de correo requiere OpenSSL.

### Pruebas reproducibles

Desde la raíz del repositorio ejecuta:

```bash
BUZON_PRUEBA_CARGA=1 BUZON_PROBAR_RESTAURACION=1 ./infra/probar-sistema.sh
cd frontend
npm ci
npm test
npm run build
```

El ensayo crea PostgreSQL 16 desechable en loopback y ejecuta migración, reversión, migración y pruebas con datos sintéticos. Las variables opcionales activan la carga concurrente y la restauración local. El ensayo STARTTLS usa un receptor en loopback con certificado efímero. La [matriz de validación](docs/validacion/resultados_pruebas.csv) distingue aprobados, parciales y pendientes.

### Arrancar la aplicación

Crea una base PostgreSQL de desarrollo y un usuario con permisos para crear tablas en ella. En una terminal, desde la raíz del repositorio, reemplaza `USUARIO`, `CONTRASENA` y `BASE` por tus valores. Ajusta el puerto si tu PostgreSQL usa otro y codifica en la URL los caracteres especiales de la contraseña.

```bash
cd backend
uv sync --locked --python 3.13
export BUZON_DATABASE_URL="postgresql+psycopg://USUARIO:CONTRASENA@127.0.0.1:5432/BASE"
export BUZON_ENV=desarrollo
export BUZON_ALLOWED_ORIGINS=http://127.0.0.1:5173
export BUZON_SESSION_SECRET="$(uv run --locked python -c 'from secrets import token_hex; print(token_hex(32))')"
uv run --locked alembic upgrade head
uv run --locked uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --no-access-log
```

Comprueba la API en `http://127.0.0.1:8000/api/v1/health`. En otra terminal, desde la raíz del repositorio, inicia el frontend:

```bash
cd frontend
npm ci
npm run dev
```

Abre `http://127.0.0.1:5173`. Registra la primera cuenta y obtén su ID en «Mi cuenta». Con el contacto comprobado, habilita la primera administración con `uv run --locked python -m app.jobs.bootstrap_admin UUID_DE_LA_CUENTA` desde `backend/` y con la misma URL de base. Para una comprobación presencial documentada, agrega `--comprobacion-presencial`. El comando exige acceso a la base, se permite una sola vez mientras exista un administrador activo y revoca las sesiones previas de la cuenta. Inicia sesión de nuevo y crea punto, ubicaciones, tarifa y asignaciones.

Configura `BUZON_SMTP_HOST` y `BUZON_SMTP_FROM`, con `BUZON_SMTP_PORT`, `BUZON_SMTP_USER` y `BUZON_SMTP_PASSWORD` según el transporte. Ejecuta `uv run --locked python -m app.jobs.maintenance --loop` desde `backend/` con la misma configuración para procesar vencimientos y reintentos de correo. Sin transporte configurado, los avisos quedan disponibles en la bandeja y el contacto se comprueba por procedimiento presencial.

Para un entorno HTTPS configura tres secretos distintos mediante `BUZON_SESSION_SECRET`, `BUZON_CREDENTIAL_HMAC_KEY` y `BUZON_REQUEST_HMAC_KEY`. Los límites por origen y cuenta en memoria corresponden a un proceso. Para un piloto con varios procesos, aplica también límites compartidos en el proxy. Excluye las referencias públicas de los logs de acceso.

Si publicas el frontend estático en un origen HTTPS separado, compílalo con `VITE_BUZON_API_ORIGIN` apuntando a la API. Incluye el origen exacto del frontend en `BUZON_CORS_ORIGINS` y en `BUZON_ALLOWED_ORIGINS`. El primer valor de `BUZON_ALLOWED_ORIGINS` es la dirección que se incluye en los correos. La sesión entre sitios usa cookies particionadas.

### Verificar el diseño y consultar entregables

Prepara el [entorno documental](herramientas/README.md) y ejecuta `./verificar.sh`. Consulta el [plan y los resultados de validación](docs/validacion/01_plan_validacion.md) y los [archivos editables de Scrum y pruebas](entregables/README.md).
