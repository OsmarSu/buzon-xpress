# BUZON Xpress

**Versión de desarrollo 1.3**

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

Para correo real con Gmail configura `BUZON_MAIL_PROVIDER=gmail`, `BUZON_SMTP_USER` y `BUZON_SMTP_PASSWORD` con una contraseña de aplicación de Google. El remitente usa esa cuenta, `smtp.gmail.com` y STARTTLS en 587 (o TLS implícito en 465). Google exige verificación en dos pasos para crear una [contraseña de aplicación](https://support.google.com/accounts/answer/185833?hl=es). La cuenta y la credencial pertenecen al servidor; el navegador no las recibe.

En la instalación WSL existente puedes guardar y validar la credencial fuera del repositorio con `python3 infra/configurar-gmail.py --restart`. El comando pide la contraseña de forma oculta, autentica con Google, guarda el entorno con permisos 600 y reinicia API y avisos. No envía un mensaje de prueba. Para otro entorno, utiliza `--env-file RUTA`.

El modo `BUZON_MAIL_PROVIDER=smtp` conserva un transporte SMTP de pruebas. Ejecuta `uv run --locked python -m app.jobs.maintenance --loop` desde `backend/` con la misma configuración para procesar vencimientos y reintentos. Sin transporte, la bandeja sigue disponible y la comprobación presencial se registra por el procedimiento autorizado.

El usuario activa MFA desde «Mi cuenta» con su contraseña y una aplicación autenticadora compatible con TOTP. Debe confirmar el primer código y guardar los códigos de recuperación de un solo uso. El acceso de una cuenta con MFA no emite sesión hasta comprobar el segundo factor. La recuperación de contraseña conserva MFA.

Para un entorno HTTPS configura tres secretos distintos mediante `BUZON_SESSION_SECRET`, `BUZON_CREDENTIAL_HMAC_KEY` y `BUZON_REQUEST_HMAC_KEY`, además de una clave Fernet estable y separada en `BUZON_MFA_ENCRYPTION_KEY` para cifrar los secretos TOTP. Conservar esa clave fuera del repositorio junto con el procedimiento de recuperación de la base. Los límites por origen y cuenta en memoria corresponden a un proceso. Para un piloto con varios procesos, aplica también límites compartidos en el proxy. Excluye los códigos públicos de seguimiento de los logs de acceso.

Si publicas el frontend estático en un origen HTTPS separado, compílalo con `VITE_BUZON_API_ORIGIN` apuntando a la API. Incluye el origen exacto del frontend en `BUZON_CORS_ORIGINS` y en `BUZON_ALLOWED_ORIGINS`. El primer valor de `BUZON_ALLOWED_ORIGINS` es la dirección que se incluye en los correos. La sesión entre sitios usa cookies particionadas.

### Servicio publicado

La [web en Surge](https://buzon-xpress.surge.sh/) y Android desde 0.2.3 usan la [API en alwaysdata](https://buzonxpress.alwaysdata.net/api/v1/health). PostgreSQL se aloja en Supabase y las tareas de avisos y vencimientos se ejecutan en alwaysdata. El uso de estas versiones no requiere que la máquina de desarrollo esté encendida. Para publicar cambios en la web, compila con `VITE_BUZON_API_ORIGIN=https://buzonxpress.alwaysdata.net`.

### Verificar el diseño y consultar entregables

Prepara el [entorno documental](herramientas/README.md) y ejecuta `./verificar.sh`. Consulta el [plan y los resultados de validación](docs/validacion/01_plan_validacion.md) y los [archivos editables de Scrum y pruebas](entregables/README.md).

## 3. Aplicación Android

La versión móvil 0.2.4 vive en `mobile/` y usa Expo SDK 57 con React Native, TypeScript y Expo Router. Comparte la base publicada y los permisos del servidor. Incluye acceso, segundo factor si está activado, registro y recuperación, custodias, prerregistro, cotización, seguimiento público, avisos, cuenta y código temporal del destinatario. La gestión del segundo factor y las funciones del personal se mantienen en la web durante esta primera fase.

Desde WSL:

```bash
cd /home/oswi/Proyectos/buzon-xpress/mobile
npm ci
npm run check
npm run export:android
npm start -- --tunnel --go
```

Abre el enlace o escanea el código del servidor con una versión de [Expo Go compatible con SDK 57 para Android](https://expo.dev/go). La conexión requiere que el servidor de desarrollo y los servicios publicados estén activos. No hace falta iniciar un emulador ni usar la GPU para este recorrido.

La exportación Android genera el paquete de JavaScript y recursos; **no es un APK instalable**. El perfil `preview` de `mobile/eas.json` genera el APK firmado con Expo Build. El proyecto está vinculado a [@oswidev/buzon-xpress](https://expo.dev/accounts/oswidev/projects/buzon-xpress). Para volver a compilar desde `mobile/`:

```bash
npx --yes eas-cli@latest login --device
npx --yes eas-cli@latest build --platform android --profile preview
```

El APK 0.2.3 (código Android 5) usa la API en alwaysdata y amplía a 40 segundos el tiempo límite de la consulta para tolerar el arranque en frío. Se distribuye firmado en [GitHub Releases](https://github.com/OsmarSu/buzon-xpress/releases/tag/v0.2.3). El APK se conserva fuera del historial de Git.

El [APK 0.2.4](https://github.com/OsmarSu/buzon-xpress/releases/tag/v0.2.4) incluye Código de Paquete y asteriscos en los campos obligatorios. Usa el código Android 6 y conserva la firma para instalarse como actualización.

La cuenta debe tener cuota disponible en su plan. El perfil `production` prepara un AAB para Google Play; no publica automáticamente en la tienda. El APK incorpora el código de la app y no necesita Metro para abrirse, pero sí requiere conexión a la API publicada para consultar o modificar datos. La prueba en teléfono físico, TalkBack y los recorridos de instalación siguen pendientes antes de una distribución final.

La lista `.easignore` de la raíz limita la carga al código, recursos, configuración y pruebas de `mobile/`. Se comprobó el archivo que prepara EAS: no incluye backend, base de datos, contraseñas, archivos de entorno ni documentos. La credencial de Expo permanece en el perfil del usuario; no se guarda en el repositorio.


Para revisar la interfaz localmente sin cerrar la sesión del sitio:

```bash
cd /home/oswi/Proyectos/buzon-xpress/mobile
npm run export:web
npm run preview
```

La previsualización se sirve en `http://127.0.0.1:8082` y conecta a la API mediante un proxy local. En esa vista la sesión permanece solo en memoria; en Android se conserva con SecureStore. La contraseña y los códigos temporales no se guardan en el dispositivo. La app vuelve a consultar la cuenta al regresar del correo y oculta el código de retiro al pasar a segundo plano.

El transporte móvil usa sesiones opacas revocables de ocho horas, separadas de las cookies del navegador, y conserva los límites de intentos y MFA. Los cinco endpoints bajo `/api/v1/mobile/auth` no reciben cookies ni `Origin`, ni emiten cookies. Las operaciones de negocio comprueban el portador y sus permisos. El contrato actualizado contiene 54 operaciones.

La navegación utiliza rutas en `src/app/`. La pantalla inicial es **Consultar seguimiento**. Sin sesión se muestra solo esta consulta y el botón **Iniciar sesión** a la derecha de la cabecera. Custodias, Puntos, Avisos y Cuenta requieren sesión también al abrir enlaces directos. Después de acceder aparecen las cinco pestañas: Seguimiento, Custodias, Puntos, Avisos y Cuenta.

Los iconos de las barras se dibujan con SVG nativo y no requieren cargar una tipografía. La fuente Ionicons usada en el resto de la app queda integrada en los recursos Android como `ionicons` mediante el plugin de Expo Font. Se verificaron el archivo TTF, su definición XML y el registro nativo de la familia. Las pestañas reservan espacio para el área segura y para sus títulos completos, incluido Seguimiento a 320 píxeles.


La verificación del 15 de noviembre de 2026 aprobó doce pruebas del cliente móvil, ESLint sin advertencias, TypeScript, los 21 controles de Expo Doctor y las exportaciones Android y web. `npm ci` se comprobó desde el archivo de bloqueo y `npm audit` no informó vulnerabilidades. La revisión visual a 320 y 390 píxeles comprobó acceso, retorno a Custodias, avisos, reapertura del mismo detalle y cierre de sesión con la base publicada, sin crear operaciones de negocio. Es evidencia de la previsualización de React Native, no de ejecución física en Android.

Las sobrescrituras de `minimatch`, `uuid` y `decode-uri-component` mantienen versiones corregidas. `scripts/prepare-dependencies.mjs` adapta la importación de `query-string` 7 al decodificador corregido; se ejecuta al instalar y tiene prueba de parámetros, acentos y datos malformados. Conservar la prueba al actualizar Expo Router. El icono Android adapta el logotipo existente a un PNG cuadrado con margen, sin redibujar la identidad.

La revisión visual 0.2.2 comprobó el nombre Código público de seguimiento, cabecera sin símbolo, medidas legibles a 320 píxeles y ausencia del apartado Fotografías del recorrido en el pie web. En la previsualización móvil se verificaron búsqueda y detalle de Puntos, cotización real, traslado y reapertura del prerregistro con punto, tamaño y horas conservados, acceso y cierre de sesión. Un formulario de registro con ventana reducida permitió enfocar Repetir contraseña sin tapar el control. Esta evidencia de navegador no reproduce un teclado Android; su comprobación física y TalkBack quedan pendientes de instalar el APK actualizado.

La revisión 0.2.2 incorpora desplazamiento automático del campo enfocado sobre el teclado, también dentro de ventanas de custodia. Puntos permite buscar, consultar horarios, cotizar y abrir el prerregistro con punto, tamaño y horas conservados. En 0.2.2, el seguimiento se identificaba como **Código público de seguimiento**. Desde 0.2.4 se muestra **Código de Paquete**, separado de la guía privada y del código de retiro. La cabecera conserva solo el nombre escrito. Los tamaños declaran máximos con embalaje en largo × ancho × alto: pequeño 30 × 20 × 15 cm, mediano 50 × 40 × 30 cm y grande 70 × 50 × 50 cm. El personal confirma la categoría en recepción.
