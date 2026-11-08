# BUZON Xpress final

**Línea base 1.1 · 7 de noviembre de 2026 · Arch WSL**

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

La base documental proviene de `../buzon-xpress-reformulado`. El código de `../buzon-xpress` es el antecedente ejecutable de paquetería, útil para evaluar componentes reutilizables. El perfil, la especificación y el contrato de esta carpeta gobiernan la implementación de custodia.

## 2. Estructura y verificación

[Mapa de archivos, límites de cada capa y orden de implementación](docs/gestion/04_estructura_de_archivos.md).

El primer incremento implementa identidad y sesiones en FastAPI, PostgreSQL y React. La revisión Alembic inicial crea cuentas, sesiones, puntos y asignaciones en una base vacía. Las operaciones de custodia se incorporan después de identidad.

### Probar identidad en WSL

Desde la raíz de este checkout:

```bash
./infra/probar-identidad.sh
cd frontend
npm ci
npm run build
```

El ensayo crea y elimina su propio PostgreSQL 16 en loopback. Aplica la migración, la revierte, la aplica de nuevo y prueba la API contra OpenAPI con datos sintéticos y un puerto de correo de prueba.

### Ejecutar el incremento

Prepara una base nueva de desarrollo. En la terminal de la API, configura `BUZON_DATABASE_URL` con una URL `postgresql+psycopg://` para esa base y ejecuta desde la raíz:

```bash
cd backend
uv sync --locked --python 3.13
export BUZON_ENV=desarrollo
export BUZON_ALLOWED_ORIGINS=http://127.0.0.1:5173
export BUZON_SESSION_SECRET="$(python -c 'from secrets import token_hex; print(token_hex(32))')"
uv run --locked alembic upgrade head
uv run --locked uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000
```

Desde la raíz en otra terminal:

```bash
cd frontend
npm ci
npm run dev
```

Abre `http://127.0.0.1:5173`. Para recibir el enlace de verificación en desarrollo, configura `BUZON_SMTP_HOST` y `BUZON_SMTP_FROM` y, si corresponde, `BUZON_SMTP_PORT`, `BUZON_SMTP_USER` y `BUZON_SMTP_PASSWORD`. El transporte usa STARTTLS. Con el correo deshabilitado, las cuentas nuevas quedan con contacto pendiente. El límite de intentos se aplica por cliente y proceso en el servidor de desarrollo.

### Verificar el diseño

Para comprobar la línea base documental, prepara el [entorno documental](herramientas/README.md) y ejecuta `./verificar.sh` desde la raíz. La comprobación valida enlaces, trazabilidad, OpenAPI y el SQL de referencia en PostgreSQL desechable. [Resultado documental](docs/validacion/03_verificacion_linea_base.md).
