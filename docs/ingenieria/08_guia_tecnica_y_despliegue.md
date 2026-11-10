# Guía técnica, entornos y despliegue

El [README](../../README.md) contiene los comandos para instalar, probar y ejecutar la aplicación. Esta guía describe la arquitectura desplegada en desarrollo y separa esa evidencia de los requisitos que faltan para un piloto operativo.

## 1. Base tecnológica y estructura implementada

La aplicación usa React y TypeScript, FastAPI, SQLAlchemy, PostgreSQL y Alembic. El backend requiere Python 3.13; el frontend se instala con Node.js 24 y npm. `backend/uv.lock` y `frontend/package-lock.json` registran las dependencias reproducibles; las restricciones de versión también se declaran en los manifiestos.

```text
backend/app/
  domain/             reglas, estados y tipos de valor
  application/        casos de uso, permisos y unidad de trabajo
  ports/              repositorios, reloj, avisos y verificadores
  adapters/api/       rutas y DTO sin secretos innecesarios
  adapters/storage/   repositorios y transacciones SQLAlchemy
  adapters/mail/      correo configurable
  jobs/               avisos y plazos
backend/migrations/   revisiones versionadas
backend/tests/        unidad, integración y contratos
frontend/src/
  features/           acceso, custodias, operación y supervisión
  services/           cliente tipado y errores
  components/         elementos compartidos
```

La estructura separa reglas, aplicación, persistencia e interfaz. Una carpeta por cada libro o patrón no aporta valor por sí sola; la revisión debe comprobar dependencias y responsabilidades.

## 2. Configuración implementada

| Parámetro | Uso y control |
|---|---|
| `BUZON_DATABASE_URL` | Conexión PostgreSQL con el controlador `psycopg`; obligatoria. |
| `BUZON_SESSION_SECRET` | Secreto de sesión de al menos 32 bytes, fuera del código. |
| `BUZON_CREDENTIAL_HMAC_KEY` | Clave HMAC independiente para credenciales de retiro. |
| `BUZON_REQUEST_HMAC_KEY` | Clave HMAC independiente para solicitudes idempotentes. |
| `BUZON_ALLOWED_ORIGINS` | Orígenes HTTPS permitidos; en desarrollo, HTTP solo en loopback. El primero se usa como origen público. |
| `BUZON_CORS_ORIGINS` | Orígenes HTTPS adicionales para el frontend estático separado. |
| `BUZON_SMTP_HOST`, `BUZON_SMTP_PORT`, `BUZON_SMTP_FROM`, `BUZON_SMTP_USER`, `BUZON_SMTP_PASSWORD` | Transporte de correo opcional; la bandeja de avisos sigue disponible sin SMTP. |
| `BUZON_ENV` | Distingue desarrollo, pruebas y piloto. |

La configuración se valida en `backend/app/config.py`. En piloto se exigen tres secretos distintos de al menos 32 bytes. No se guardan secretos reales en el repositorio; las pruebas usan credenciales sintéticas y una base aislada.

## 3. Entornos y datos

Desarrollo: datos sintéticos y servicios locales disponibles. Pruebas: base separada y descartable identificada explícitamente; una prueba no puede aceptar por omisión la URL del punto piloto. Ensayo: versión identificada, personal informado y bultos de prueba. Piloto: solo después de validar requisitos y procedimiento.

El [SQL de referencia](anexos/modelo_propuesto.sql) describe el esquema relacional. Las migraciones `0001_identity` y `0002_operations` crean la estructura de la aplicación; `./infra/probar-sistema.sh` las aplica, revierte y reaplica en PostgreSQL 16 desechable. No usar este esquema para actualizar directamente la base antecedente. La primera cuenta administradora se habilita mediante el procedimiento documentado en el README, sin una contraseña universal.

La cuenta de aplicación tiene permisos mínimos; la de migración se usa solo para cambios controlados. Los eventos son de adición y se protegen además con trigger. Documentar quién puede administrar o restaurar la base: la protección no impide que su propietario deshabilite controles.

## 4. Secuencia de despliegue a ensayar

1. Identificar versión de código y dependencias y completar la configuración del entorno.
2. Comprobar copia recuperable y disponibilidad de una base de ensayo.
3. Aplicar migraciones en ensayo y ejecutar pruebas relevantes.
4. Compilar frontend y revisar que la configuración apunte a la API correcta.
5. Publicar la aplicación con HTTPS y orígenes permitidos.
6. Habilitar tareas de avisos y vencimientos, con un solo control de concurrencia por trabajo.
7. Verificar salud real de base, sesión, permisos, recepción y retiro de prueba.
8. Registrar versión, responsable y procedimiento de recuperación.

No se incluyen comandos contra servicios inexistentes ni se presenta un archivo Docker como despliegue terminado. La infraestructura de alojamiento puede ser local o un servicio disponible; no exige dispositivo conectado al almacenamiento.

## 5. Observabilidad, avisos y diagnóstico

Cada petición operativa tiene correlación y resultado. Registrar tiempos del servidor por separado de atención humana. Las métricas del tablero derivan de operaciones persistidas, no de valores constantes o aleatorios.

La comprobación de salud consulta las dependencias que declara. Un endpoint que responde “database connected” sin consultar la base no satisface el requisito. El correo distingue pendiente, aceptado por canal y fallido; la bandeja permanece como evidencia interna.

Ante falla, el personal utiliza la referencia de operación para abrir incidencia. Evitar contraseñas, códigos, cookies y enlaces secretos en logs. Las exportaciones identifican periodo y calidad de los datos.

## 6. Copias, recuperación y cambios de secretos

Definir frecuencia de copia, ubicación protegida y responsable. Ensayar restauración en un entorno vacío y medir RPO/RTO. Conservar evidencia de inventario inicial y conteos tras recuperar.

Una restauración puede retroceder registros respecto a una entrega humana ya realizada: se suspende operación, se concilia físicamente y se revisan autorizaciones antes de abrir el punto. No se considera resuelto el servicio solo porque la API vuelve a responder.

La rotación de claves de códigos y sesión requiere invalidar o gestionar credenciales afectadas de forma explícita. Las revisiones de base no se revierten borrando evidencia; se planifica un cambio compatible o una restauración controlada y conciliada.

## 7. Estado técnico y condiciones previas al piloto

La implementación y su configuración reproducible están comprobadas en el entorno local. `./verificar.sh` valida el esquema en PostgreSQL 16 y revisa la línea base documental; el [registro de pruebas](../validacion/resultados_pruebas.csv) conserva los resultados por caso. El ensayo actual incluye restauración local, pero no establece recuperación ante desastres para una operación real.

Antes de un piloto quedan pendientes la aceptación con participantes, confirmar punto, horario y responsables reales, validar SMTP del punto, definir política de conservación de datos y medir copia, RPO y RTO en la infraestructura que se vaya a usar. El [plan de implementación](../gestion/02_plan_implementacion.md) conserva la secuencia propuesta y los criterios de transición.
