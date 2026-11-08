# Contratos API y controles de seguridad

El contrato 1.2 documenta la API de desarrollo. [OpenAPI 3.1.0](anexos/openapi.yaml) enumera operaciones, peticiones, respuestas y seguridad. Referentes: T01 y S01–S03 de la [bibliografía](../metodologia/02_bibliografia_verificada.md).

## 1. Convenciones

Prefijo `/api/v1`. JSON UTF-8; identificadores UUID; fechas ISO 8601 con zona UTC; importes BOB como cadenas decimales de dos posiciones. La UI convierte fechas a la zona publicada del punto. Las entidades privadas no incluyen secretos de sesión o retiro.

El servidor obtiene actor desde cookie de sesión protegida. Las mutaciones incluyen `X-CSRF-Token`; el navegador lo obtiene mediante `/auth/csrf`, ligado a su contexto. Se valida origen y contexto también en acceso y registro. La autenticación web no reside en `localStorage`.

La referencia pública se muestra al crear la custodia y solo se conserva su hash. Si se pierde, un participante puede rotarla mediante la operación privada correspondiente; la referencia anterior deja de funcionar. Una repetición idempotente de creación devuelve la custodia existente sin volver a mostrar una referencia que ya no se conserva en texto.

## 2. Contratos principales

| Operación | Permiso y efecto |
|---|---|
| `POST /auth/register`, `/auth/login`, `/auth/logout` | Cuenta general, sesión y revocación. El registro público no concede rol de personal. |
| `POST /auth/verify-contact` | Consume enlace de verificación de correo; la alternativa presencial queda registrada por personal autorizado. |
| `POST /auth/password-reset/request`, `/complete` | Respuesta genérica al solicitar; enlace breve de uso único y revocación de sesiones al cambiar contraseña. |
| `GET /points`, `/points/{point_id}/quote` | Horarios y cotización por tamaño/plazo. Una cotización no reserva capacidad. |
| `POST /custodies` | Cuenta activa y comprobada; participantes y punto válidos. |
| `GET /custodies`, `/custodies/{custody_id}` | Participantes o personal dentro de su alcance. |
| `POST /custodies/{custody_id}/cancel` | Emisor; únicamente mientras esté registrada y sin recepción. |
| `POST /custodies/{custody_id}/receive` | Operador del punto; registra condición externa, ubicación, tarifa aceptada y pago. |
| `POST /custodies/{custody_id}/credentials` | Destinatario; código de una sola visualización y vigencia limitada. |
| `POST /custodies/{custody_id}/verify` | Operador del punto; exige código presentado, versión y comprobación visual. |
| `POST /custodies/{custody_id}/handover` | Mismo operador de autorización; confirma un acto físico ya realizado. |
| `POST /custodies/{custody_id}/abort-handover` | Declara que no hubo entrega; revoca preparación y credencial. Si hubo entrega, requiere conciliación. |
| `POST /custodies/{custody_id}/extend` | Operador; prórroga y cobro conforme a condiciones históricas. |
| `POST /custodies/{custody_id}/incidents` | Participante o personal según alcance; el servidor determina bloqueo efectivo. |
| `POST /recovery-requests`, `/{request_id}/decision` | Solicitud con evidencia y decisión de otra persona autorizada. |
| `POST /custodies/{custody_id}/return-authorization`, `/return-handover` | Devolución aprobada y confirmación de entrega al emisor. |
| `GET /inventory` | Personal asignado al punto; ubicación interna nunca pública. |
| `/admin/points`, `/admin/locations`, `/admin/staff-assignments`, `/admin/tariffs` | Administración con auditoría; deshabilitar no elimina inventario. |
| `GET /notifications`, `POST /notifications/{notification_id}/read` | Bandeja propia, sin códigos. |
| `GET /audit/events`, `/reports` | Auditor o administrador con alcance y periodo. |
| `GET /public-tracking/{reference}` | Información mínima por referencia aleatoria independiente de la guía. |

El YAML especifica las rutas de comprobación presencial, consulta y resolución de incidencias, consulta de expedientes y cambio de estado de ubicaciones. El detalle de expedientes requiere un administrador asignado al punto. La matriz funcional enlaza los caminos principales; las operaciones auxiliares conservan los mismos permisos.

## 3. Recepción y precio

Antes de confirmar, la terminal obtiene tarifa y cotización. La recepción envía `tariff_id`, `accepted_amount`, `duration_hours`, `location_id` y versión esperada. El servidor recalcula; una discrepancia de precio o tarifa requiere nueva aceptación, no se cobra silenciosamente el valor actualizado.

El importe recibido se registra como cobro del servicio, no como pago de una compra o transferencia ejecutada por el sistema. `REFERENCIA_MANUAL` significa que el operador comprobó una referencia; no acredita integración bancaria.

## 4. Verificación y confirmación

Una verificación exige un código ligado a custodia y propósito, vigencia e intentos permitidos, destinatario comprobado, punto correcto y saldo del servicio conciliado. Devuelve una autorización breve, descripción y ubicación para el operador. La credencial queda retenida y el objeto sigue bajo custodia.

La confirmación ordinaria exige `authorization_id`, versión y declaración `physically_delivered=true`. Solo consume una autorización del mismo operador y punto, vigente y sin bloqueo nuevo. La declaración es evidencia del responsable; el software no observa el acto físico.

Si la autorización caducó tras una entrega humana, el endpoint ordinario rechaza. La recuperación aprobada registra conciliación y referencia a la autorización original, conservando evidencia de ambas fechas. Una decisión de recuperación con propósito `CAMBIAR_DESTINATARIO` exige cuenta nueva activa y comprobada y revoca credenciales previas. Sus cambios propuestos se conservan en el expediente.

## 5. Idempotencia y errores

Las mutaciones operativas señaladas en OpenAPI requieren `Idempotency-Key`. Alcance: actor, operación y clave; el contenido canónico se resume con HMAC y secreto de servidor para evitar conservar un hash simple que permita enumerar códigos breves. Una repetición idéntica devuelve el recurso existente. Si el contenido cambia, se responde conflicto. Una operación aún en curso no permite repetir sus efectos. Claves y resultado se confirman junto a la transacción de negocio.

La emisión de código tiene un tratamiento separado: no se almacena el código dentro de respuestas de idempotencia. Una respuesta perdida se resuelve mediante reemisión explícita que revoca la anterior. Los logs y el historial tampoco conservan el secreto.

| HTTP | Significado |
|---|---|
| 400 / 422 | Petición o regla inválida. |
| 401 | Falta sesión válida. |
| 403 / 404 | Acceso no permitido o recurso no visible, según política uniforme. |
| 409 | Conflicto de versión, capacidad, estado o idempotencia. |
| 429 | Límite de intentos o tasa. |
| 503 | Dependencia operativa no disponible. |

El cuerpo tiene código estable, mensaje y correlación. No se devuelven trazas, consultas SQL, PIN o datos ajenos en errores. Una falla real nunca se sustituye por una respuesta simulada.

## 6. Matriz de amenazas y evidencia

| Amenaza | Control diseñado | Evidencia prevista |
|---|---|---|
| Consulta por teléfono revela objeto y PIN. | Referencia pública separada, datos mínimos y tasa limitada. | T-06, T-30. |
| Cambiar identificador accede a custodia ajena. | Autorización por participación y punto en servidor. | T-02. |
| Fuerza bruta de código. | HMAC, vigencia, contador persistido y límites por cuenta y origen. | T-07, T-08. |
| Dos operadores entregan el mismo bulto. | Autorización retenida, estado en curso y comprobante único. | T-09, T-18, T-28. |
| Autoaprobación de excepción. | Solicitante y decisor distintos; evidencia y evento. | T-14. |
| Suplantación de petición desde otra web. | Sesión protegida, CSRF y validación de origen. | T-21. |
| Falla de correo se interpreta como entrega de aviso. | Estados separados y reintentos; aceptación SMTP no equivale a lectura. | T-11, T-27. |
| Operador omite confirmar tras entregar. | Estado en curso, bloqueo y conciliación supervisada. | T-18, ensayo operativo. |
| Exposición por auditoría. | Historial sin secretos y exportación restringida. | T-15, T-26, T-30. |

La seguridad física del espacio y la conducta del personal quedan en el manual. No se promete impedir materialmente una extracción realizada al margen del proceso.
