# Plan de validación de producto y servicio

Estado: protocolo propuesto. Las treinta pruebas siguientes están **pendientes de ejecución sobre una implementación**. La revisión documental realizada se registra por separado en [revisión documental](02_revision_documental.md).

## 1. Entornos y evidencia

Usar una base de pruebas aislada y datos sintéticos. Cada prueba identifica versión, entorno, responsable, entrada, resultado y evidencia. No reutilizar la conexión de la base actual: su suite existente contiene limpieza destructiva sin separación explícita.

Probar primero reglas de dominio con dobles de repositorio; después integridad y concurrencia en PostgreSQL; luego API y recorrido de interfaz. El ensayo del servicio verifica también al personal y los objetos de prueba. No se incluyen pruebas de puertas, sensores o dispositivos.

## 2. Pruebas funcionales

| ID | Requisito | Escenario | Resultado exigido |
|---|---|---|---|
| T-01 | RF-01 | Registro, comprobación de contacto, acceso, cierre y uso posterior de sesión. | La sesión revocada falla y no se permite elegir rol de personal. |
| T-02 | RF-02 | Usuario cambia ID de custodia y operador intenta actuar en otro punto. | Rechazo sin datos de terceros ni mutación. |
| T-03 | RF-03 | Registrar y cancelar antes de recibir; intentar cancelar después. | El prerregistro no ocupa espacio; la cancelación tardía se rechaza. |
| T-04 | RF-04 | Recibir con capacidad y provocar error al insertar pago o evento. | Éxito completo o reversión digital completa; sin recepción parcial. |
| T-05 | RF-05 | Asignar una ubicación ocupada o de otro punto. | Restricción de integridad y rechazo sin doble ocupación. |
| T-06 | RF-06 | Consultar públicamente y por cuenta ajena. | Sin PIN, nombre, teléfono, descripción ni ubicación interna en público. |
| T-07 | RF-07 | Emitir, reemitir y usar el código anterior, vencido o de otro objeto. | Solo una credencial vigente; las demás son rechazadas. |
| T-08 | RF-08 | Cinco intentos fallidos y dos operadores verificando simultáneamente. | Contador persistido, límite aplicado y una autorización activa. |
| T-09 | RF-09 | Confirmar retiro y repetir con otra autorización o persona. | Una salida, una liberación y comprobante único; las demás fallan. |
| T-10 | RF-10 | Solicitar y aprobar devolución, comprobar emisor y confirmar. | Estado DEVUELTA, espacio liberado y constancia distinta de retiro. |
| T-11 | RF-11 | Fallar SMTP tras recepción y ejecutar reintentos. | Custodia persiste, bandeja disponible, fallo visible y aviso sin duplicados. |
| T-12 | RF-12 | Alterar precio en navegador y cambiar tarifa tras recibir. | Servidor rechaza importe alterado y conserva condiciones históricas. |
| T-13 | RF-13 | Vencer plazo con un objeto presente y registrar prórroga. | Sigue ocupando espacio; cambia plazo solo tras operación válida. |
| T-14 | RF-14 | Solicitante intenta autoaprobar, evidencia insuficiente y cambio de destinatario. | Autoaprobación rechazada; bloqueo conservado; cambio válido revoca códigos previos. |
| T-15 | RF-15 | Modificar o borrar evento con cuenta de aplicación y revisar payload. | Rechazo de edición y ausencia de secretos. |
| T-16 | RF-16 | Retirar de servicio una ubicación ocupada o quitar personal asignado. | No pierde inventario; permisos revocados se aplican en servidor. |
| T-17 | RF-17 | Calcular reportes con una muestra conocida y fechas incompletas. | Numerador y denominador correctos; limitación de datos visible. |
| T-18 | RF-18 | Repetir confirmación con misma clave, cambiar contenido y perder respuesta tras entrega. | Sin doble efecto; conflicto si cambia contenido; recuperación sin repetir entrega humana. |

## 3. Calidad, recuperación y seguridad

| ID | Requisito | Procedimiento y aceptación |
|---|---|---|
| T-19 | RNF-01 | Cinco participantes realizan tareas; al menos cuatro completan las críticas sin ayuda y se registra toda falla crítica. |
| T-20 | RNF-02 | Registrar equipo, base, 10 000 custodias y 20 usuarios concurrentes; medir P95 de consultas y comparar con 500 ms. |
| T-21 | RNF-03 | Revisar cookie, expiración, CSRF, origen, sesión revocada y recuperación de contraseña; cada acceso indebido previsto se rechaza. |
| T-22 | RNF-04 | Inyectar fallas antes de cada confirmación de transacción; consultar todas las tablas afectadas y comprobar ausencia de estados parciales. |
| T-23 | RNF-05 | Restaurar una copia en entorno vacío; medir antigüedad y duración y contrastar con RPO 24 h / RTO 4 h propuestos. |
| T-24 | RNF-06 | Ejecutar reglas de dominio sin framework, ORM o correo; comprobar responsabilidades y dependencias. |
| T-25 | RNF-07 | Recorrer con teclado, revisar foco, etiquetas, anuncios y contraste de criterios seleccionados. Documentar cualquier incumplimiento. |
| T-26 | RNF-08 | Trazar una operación desde petición a evento e incidencia; inspeccionar logs para detectar secretos o datos innecesarios. |
| T-27 | RNF-09 | Confirmar transacción y comprobar aviso interno y primer intento de correo dentro de dos minutos en entorno controlado. |
| T-28 | RNF-10 | Lanzar veinte recepciones sobre una ubicación; exactamente una ocupa el espacio y el resto recibe conflicto sin efectos parciales. |
| T-29 | RNF-11 | Completar flujo con entrada manual y navegador en equipo disponible, sin periféricos o hardware conectado. |
| T-30 | RNF-12 | Revisar consultas, exportaciones y conservación; cuenta ajena no ve datos y los secretos no se exportan. |

Un porcentaje de cobertura de código no sustituye estas evidencias. La regla de no doble entrega y la privacidad se comprueban con escenarios de abuso, no solo con el camino feliz.

## 4. Ensayo operativo propuesto

Treinta ciclos con bultos de prueba identificados y sin dinero real. Variar tamaños, plazos, usuarios y operadores. Incluir: punto lleno, destinatario incorrecto, objeto en otra ubicación, código perdido, plazo vencido y corte después de una entrega real simulada.

Por ciclo registrar referencia de ensayo, inicio, recepción, verificación, entrega física declarada, confirmación persistida, ayuda y diferencia de inventario. Al terminar cotejar todos los bultos y ubicaciones. No afirmar “cero errores” sin indicar muestra, condiciones y tipos de error examinados.

El objetivo es detectar problemas y decidir ajustes. Treinta ciclos y cinco participantes no estiman una tasa poblacional de pérdida o fraude. El piloto público requiere los controles críticos aprobados y condiciones operativas definidas.

## 5. Métricas y criterios de salida

Tiempo de recepción y retiro: distinguir espera, atención y respuesta de software. Medir con observación y fechas reales, sin números aleatorios. Ocupación: asignaciones activas divididas por ubicaciones utilizables durante el periodo; informar bloqueos. Permanencia: tiempo recibido–salida de operaciones completadas; las activas se reportan separadamente.

Criterios críticos: ningún acceso no autorizado en los casos negativos planificados; ninguna asignación o salida duplicada; ningún secreto público; ningún incidente bloqueante que permita entrega ordinaria; conciliación practicable por personal. Estos son criterios del ensayo, no garantías universales de seguridad.

Guardar evidencia de pruebas aprobadas y fallidas, correcciones y repetición de los casos afectados. El informe final debe describir demanda y costos levantados, límites de muestra y decisión de continuidad. La [plantilla de resultados](resultados_pruebas.csv) comienza sin resultados.
