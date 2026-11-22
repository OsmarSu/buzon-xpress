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
| `BUZON_MFA_ENCRYPTION_KEY` | Clave Fernet estable y separada para cifrar TOTP; obligatoria en piloto. |
| `BUZON_MAIL_PROVIDER` | `gmail`, `smtp` o `none`; Gmail requiere contraseña de aplicación y cuenta remitente. |
| `BUZON_ENV` | Distingue desarrollo, pruebas y piloto. |

La configuración se valida en `backend/app/config.py`. En piloto se exigen tres secretos distintos de al menos 32 bytes. No se guardan secretos reales en el repositorio; las pruebas usan credenciales sintéticas y una base aislada.

## 3. Entornos y datos

Desarrollo: datos sintéticos y servicios locales disponibles. Pruebas: base separada y descartable identificada explícitamente; una prueba no puede aceptar por omisión la URL del punto piloto. Ensayo: versión identificada, personal informado y bultos de prueba. Piloto: solo después de validar requisitos y procedimiento.

El [SQL de referencia](anexos/modelo_propuesto.sql) describe el esquema relacional. Las migraciones `0001_identity`, `0002_operations` y `0003_mfa` crean la estructura de la aplicación; `./infra/probar-sistema.sh` las aplica, revierte y reaplica en PostgreSQL 16 desechable. No usar este esquema para actualizar directamente la base antecedente. La primera cuenta administradora se habilita mediante el procedimiento documentado en el README, sin una contraseña universal.

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

## 8. Distribución Android de la primera fase

La app 0.2.3 en `mobile/` comparte la API publicada y sus permisos. El perfil `preview` de `eas.json` solicita un APK firmado de distribución interna; `production` solicita un AAB y no realiza una publicación en tienda. Los comandos vigentes están en el [README](../../README.md). La cuenta de Expo y su cuota se consultan antes de iniciar nuevas compilaciones; no se contrataron servicios de pago.

La carga de código se limita con `.easignore` en la raíz del repositorio y se verifica con `eas build:inspect --platform android --profile preview --stage archive`. El archivo inspeccionado incluye solo la app y sus pruebas. La contraseña de Gmail, credenciales de la base, sesiones del servidor y configuración de producción no forman parte del paquete. Expo conserva la firma Android en la cuenta propietaria; los secretos de acceso no se añaden a Git.

Antes de compartir un APK se comprueban su finalización, identificador `bo.buzonxpress.app`, versión, integridad y firma. Un APK compilado no constituye aceptación en dispositivo: aún se deben ejecutar instalación, apertura, acceso, MFA cuando corresponda, restauración y cierre de sesión, pérdida de conexión, retorno desde segundo plano, código de retiro y TalkBack. El backend publicado debe estar activo para las funciones de negocio, aunque el APK abra sin el servidor de desarrollo.

La revisión 0.2.1 reemplaza los iconos de navegación por SVG y enlaza la tipografía restante en los recursos Android, por lo que requiere un nuevo APK. Conserva el identificador y la firma de la entrega anterior y aumenta el código de versión a 3. La pantalla pública inicial consulta únicamente seguimiento; la navegación restante se presenta después de autenticar y comprueba sesión en las rutas privadas.

La actualización 0.2.2 aumenta el código Android a 4 e incorpora react-native-keyboard-controller 1.21.9, compatible con SDK 57. El cambio nativo requiere instalar el nuevo APK. Los campos dentro de pantallas y ventanas de custodia usan el mismo desplazamiento automático sobre el teclado. Puntos añade búsqueda, detalle, cotización y traslado de selección al prerregistro. Mantiene firma, paquete y API; no requiere migración de datos. La web se compila y publica por separado.

## Alojamiento de PostgreSQL y FastAPI

La web de Surge y la app 0.2.3 consumen la API de alwaysdata en `https://buzonxpress.alwaysdata.net/api/v1`. Supabase aloja PostgreSQL. FastAPI conserva identidad, MFA y permisos. El backend se conecta con un rol limitado a las tablas de la aplicación, el Session pooler en el puerto 5432 y `sslmode=verify-full` con el certificado raíz de Supabase. Las credenciales y las claves de sesión, HMAC y MFA se guardan fuera del repositorio.

El sitio de alwaysdata usa el tipo Programa de usuario, Python 3.13 y Uvicorn en la dirección y puerto asignados. Las dependencias se instalan desde una exportación con hashes de `backend/uv.lock`. El trabajo programado ejecuta `python -m app.jobs.maintenance` cada cinco minutos. Las verificaciones de despliegue incluyen `/api/v1/health`, CORS desde Surge, acceso web y Android y autenticación con Gmail. El `Dockerfile` de `backend/` permite ensayar la API y las tareas en contenedor, aparte del alojamiento compartido.

Para respaldar el origen, exporta solo el esquema de la aplicación con `pg_dump --schema=public --format=custom --no-owner --no-privileges`. Si el destino ya tiene el esquema `public`, excluye sus entradas de creación y comentario de la lista de restauración. Usa `--single-transaction --exit-on-error` y compara revisión, tablas y conteos. Durante el corte, comprueba que no hayan quedado escrituras en dos bases distintas. La API heredada en WSL sirve como puente de compatibilidad usando la misma base alojada. El trabajo local de avisos se desactiva al trasladar la operación.
