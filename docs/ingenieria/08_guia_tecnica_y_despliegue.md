# Guía técnica, entornos y despliegue

La implementación de desarrollo se ejecuta con el [README](../../README.md). Esta guía conserva los criterios de entorno y preparación del piloto.

## 1. Base tecnológica y estructura prevista

Se conserva la familia tecnológica ya utilizada: React y TypeScript para interfaz, FastAPI para API, SQLAlchemy y PostgreSQL para persistencia y Alembic para migraciones. La implementación deberá fijar versiones compatibles y archivos de dependencias reproducibles; este documento no ordena actualizar a las últimas versiones.

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

## 2. Configuración prevista

| Parámetro propuesto | Uso y control |
|---|---|
| `BUZON_DATABASE_URL` | Conexión del entorno; sin credenciales predeterminadas de producción. |
| `BUZON_SESSION_SECRET` | Protección del contexto de sesión; fuera del código y los exportables. |
| `BUZON_CREDENTIAL_HMAC_KEY` | Verificador de códigos de retiro, separado de la base. |
| `BUZON_REQUEST_HMAC_KEY` | Resumen protegido de peticiones idempotentes. |
| `BUZON_ALLOWED_ORIGINS` | Orígenes explícitos para la interfaz desplegada. |
| `BUZON_SMTP_HOST` y credenciales asociadas | Correo opcional; nunca obligatorio para operar la bandeja. |
| `BUZON_TIMEZONE` | Presentación horaria; persistencia en UTC. |
| `BUZON_ENV` | Distinguir desarrollo, pruebas y piloto. |

Los nombres son convenciones propuestas para el nuevo código. No se proporciona un archivo con secretos de ejemplo que pueda confundirse con configuración real. El entorno de prueba no usa cuentas o contactos de usuarios reales.

## 3. Entornos y datos

Desarrollo: datos sintéticos y servicios locales disponibles. Pruebas: base separada y descartable identificada explícitamente; una prueba no puede aceptar por omisión la URL del punto piloto. Ensayo: versión identificada, personal informado y bultos de prueba. Piloto: solo después de validar requisitos y procedimiento.

El [SQL de referencia](anexos/modelo_propuesto.sql) describe un esquema inicial vacío. Se transforma en una migración revisada y se comprueba en una base aislada. No ejecutar como actualización de la base antecedente. Las cuentas iniciales se crean mediante un procedimiento controlado, sin contraseñas universales publicadas.

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

## 7. Evidencia requerida antes de afirmar implementación

Código y dependencias reproducibles; migraciones ejecutadas en prueba; contratos verificados; pruebas funcionales y negativas; ensayo operativo; copia restaurada; configuración sin secretos en repositorio; y documentación de fallas. Estos entregables pertenecen al trabajo futuro del [plan](../gestion/02_plan_implementacion.md).
