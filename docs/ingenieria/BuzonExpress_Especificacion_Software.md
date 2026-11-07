# Especificación de software: BUZON Xpress

Versión 1.0 · Estado: diseño propuesto. Fuente de alcance: [decisiones](../gestion/01_decisiones_y_correspondencia.md). Marcos aplicados: I01–I04, A01–A05, Q01–Q02 y P01–P03 de la [bibliografía](../metodologia/02_bibliografia_verificada.md).

## 1. Propósito y límites

La plataforma respalda la custodia de objetos en puntos atendidos. Registra recepción y ubicación, permite consultar el estado, emite credenciales de retiro y autoriza al operador a entregar. La manipulación física siempre corresponde al personal. El proyecto utiliza equipos y espacio existentes y no integra hardware externo.

El primer producto cubre una operación dentro de un solo punto. No presta transporte, ventas, COD, pagos a vendedores ni acceso físico automatizado. El prerregistro no reserva capacidad. Todas las capacidades enumeradas en esta especificación están pendientes de implementación en la nueva versión.

## 2. Actores y permisos

| Actor | Acceso autorizado |
|---|---|
| Visitante | Horarios, condiciones y seguimiento mínimo por referencia opaca. |
| Usuario | Crear custodias propias, consultar aquellas en las que participa y generar credenciales como destinatario. |
| Operador | Recibir, ubicar, verificar y entregar en puntos con asignación activa; registrar cobros e incidencias. |
| Administrador | Configurar puntos, tarifas y personal; revisar recuperaciones y aprobar excepciones sin autoaprobarse. |
| Auditor | Lectura de eventos e indicadores de puntos autorizados, sin acceso a secretos ni capacidad de entrega. |
| Servicio de tareas | Procesar avisos y vencimientos con cuenta técnica restringida. |

Emisor y destinatario son relaciones de una custodia, no tipos permanentes de persona. La identidad del actor proviene de la sesión del servidor. Un código correcto no otorga permisos administrativos.

## 3. Requisitos funcionales

P0 identifica lo necesario para una primera entrega consistente; P1 completa el piloto. Un requisito P1 no se presenta como existente en P0.

| ID | Prioridad | Comportamiento y criterio de aceptación | Caso |
|---|---|---|---|
| RF-01 | P0 | Registrar cuentas, comprobar contacto, iniciar y cerrar sesión; una sesión revocada deja de autorizar peticiones. | CU-01 |
| RF-02 | P0 | Aplicar permisos por participación, rol y punto; un usuario ajeno o un operador no asignado recibe rechazo. | CU-01 |
| RF-03 | P0 | Registrar una custodia con emisor, destinatario activo, punto, descripción y tamaño; genera una guía y referencia pública diferentes. | CU-02 |
| RF-04 | P0 | Recibir un objeto admisible y asignar ubicación con tarifa, pago y evento en una transacción; no hay recepción sin capacidad. | CU-03 |
| RF-05 | P0 | Mostrar inventario interno por ubicación y estado; una ubicación activa no puede asignarse a otra custodia. | CU-03 |
| RF-06 | P0 | Separar consulta privada y seguimiento público; la respuesta pública no incluye nombres, teléfonos, ubicación interna ni credenciales. | CU-04 |
| RF-07 | P0 | Emitir y revocar una credencial temporal para el destinatario autenticado; una reemisión invalida la anterior. | CU-05 |
| RF-08 | P0 | Verificar credencial en el punto, aplicar límites de intentos y crear autorización vinculada a un operador y custodia. | CU-06 |
| RF-09 | P0 | Confirmar entrega física con una autorización vigente; consume credencial y autorización, cierra asignación y registra comprobante una sola vez. | CU-07 |
| RF-10 | P1 | Devolver al emisor mediante solicitud y aprobación separadas; queda comprobante y se libera ubicación después de la entrega física. | CU-10 |
| RF-11 | P1 | Crear avisos en bandeja y, si está configurado, correo; registrar intentos, reintentos y fallo sin revertir una recepción válida. | CU-08 |
| RF-12 | P0 | Calcular y registrar cobros del servicio con tarifa versionada; el navegador no fija precios ni registra liquidaciones a terceros. | CU-09 |
| RF-13 | P1 | Detectar plazo vencido, avisar y proponer prórroga o devolución; el vencimiento no libera una ubicación ocupada. | CU-09 |
| RF-14 | P0 | Abrir incidencias y tramitar recuperación con evidencia mínima; las excepciones de entrega requieren un aprobador distinto del solicitante. | CU-10 |
| RF-15 | P0 | Registrar evento con actor, punto, custodia, transición y correlación, sin secretos; la cuenta de aplicación no puede editar o borrar eventos. | CU-12 |
| RF-16 | P1 | Administrar puntos, horarios, ubicaciones y asignaciones de personal; no desactivar silenciosamente un espacio ocupado. | CU-11 |
| RF-17 | P1 | Mostrar ocupación, permanencia, tiempos e incidencias con denominador y periodo; no presentar números simulados como mediciones. | CU-12 |
| RF-18 | P0 | Manejar reintentos e interrupciones sin duplicar recepción, cobro o entrega; el mismo identificador con otro contenido produce conflicto. | CU-07 |

## 4. Reglas de negocio

| ID | Regla |
|---|---|
| RN-01 | Toda mutación sensible obtiene actor y alcance desde la sesión; los identificadores enviados por el cliente no sustituyen autorización. |
| RN-02 | Una custodia tiene como máximo una asignación activa y una ubicación como máximo una custodia activa. |
| RN-03 | `REGISTRADA` no ocupa ni reserva espacio. La capacidad se confirma en recepción. |
| RN-04 | Credencial propuesta: seis dígitos aleatorios, quince minutos de vigencia, cinco intentos fallidos por ventana de quince minutos y controles adicionales por cuenta y origen. Una autorización dura dos minutos; son parámetros de piloto. |
| RN-05 | La guía y el teléfono no autorizan retiro. Ninguna consulta pública o bitácora devuelve el código de retiro. |
| RN-06 | La tarifa y sus reglas se calculan en servidor; la custodia conserva versión y condiciones aceptadas. El servicio se paga al recibir y las prórrogas antes de entregar. |
| RN-07 | Un plazo vencido mantiene la custodia y su ubicación. No se elimina ni se dispone automáticamente del objeto. |
| RN-08 | Recuperaciones y devoluciones requieren solicitud, evidencia y aprobación por otra persona con permiso. |
| RN-09 | Verificar permite preparar la entrega; confirmar registra que el operador ya entregó físicamente. Son pasos separados y visibles. |
| RN-10 | Sin conexión no se inician mutaciones operativas. Una entrega humana sin confirmación digital se trata como incidencia y no se repite. |
| RN-11 | Los eventos son adiciones históricas. Una corrección crea otro evento; no reescribe el anterior. |
| RN-12 | Una incidencia bloqueante, deuda del servicio o discrepancia de inventario impide una entrega ordinaria. |
| RN-13 | Emisor y destinatario tienen cuenta activa y contacto comprobado por correo o comprobación presencial registrada. |
| RN-14 | Se registra la comprobación visual del destinatario y nombre del operador; no se exige fotografía o número completo de documento. El periodo de conservación debe definirse antes del piloto público. |

La credencial se conserva mediante un verificador HMAC con secreto de servidor, propósito y custodia asociados; el secreto del servidor no reside en la base de datos. Las contraseñas utilizan un algoritmo adaptativo apropiado y configuración verificada al implementar [S01–S03]. No se reutiliza un PIN de retiro como contraseña.

## 5. Calidad y restricciones: clasificación FURPS+

| ID | Categoría | Meta o condición verificable |
|---|---|---|
| RNF-01 | Usabilidad | Cuatro de cinco participantes completan las tareas críticas sin ayuda; registrar errores y limitaciones de la muestra. |
| RNF-02 | Desempeño | P95 de consultas privadas menor o igual a 500 ms en servidor de prueba identificado, con 10 000 custodias sintéticas y 20 usuarios concurrentes. No incluye trabajo humano ni entrega de correo. |
| RNF-03 | Seguridad | Cookies de sesión HttpOnly, Secure en HTTPS y SameSite, defensa CSRF en mutaciones, expiración, autorización y límites de intentos probados. |
| RNF-04 | Confiabilidad | En pruebas de falla de persistencia, ningún retiro o recepción queda parcialmente confirmado en la base de datos. |
| RNF-05 | Recuperación | Metas propuestas RPO 24 horas y RTO 4 horas, sujetas a un ensayo real de copia y restauración. |
| RNF-06 | Mantenibilidad | Casos de uso comprobables con repositorios en memoria; el dominio no importa FastAPI ni SQLAlchemy. |
| RNF-07 | Accesibilidad | Navegación crítica por teclado, foco visible, etiquetas y estados con texto; contraste revisado contra criterios seleccionados de WCAG 2.2. |
| RNF-08 | Observabilidad | Correlación entre petición, evento e incidencia, sin códigos, contraseñas o sesiones en logs. |
| RNF-09 | Comunicaciones | Aviso interno creado en la transacción; primer intento de correo en dos minutos en entorno controlado, con estado de error visible. |
| RNF-10 | Concurrencia | Veinte solicitudes simultáneas sobre una única ubicación disponible producen una sola asignación exitosa. |
| RNF-11 | Restricción | Uso desde navegador y equipos existentes; ningún flujo exige periférico o dispositivo externo. |
| RNF-12 | Privacidad | Vistas por participación y punto, información pública mínima y exportaciones sin secretos. Política de conservación documentada antes del piloto. |

Son metas de diseño, no resultados obtenidos ni acuerdos de nivel de servicio ya ofrecidos. FURPS+ se usa como clasificación; no implica certificación ISO.

## 6. Estados y vocabulario normativos

Estados de custodia: `REGISTRADA`, `EN_CUSTODIA`, `RETIRO_EN_CURSO`, `RETIRADA`, `DEVOLUCION_EN_CURSO`, `DEVUELTA`, `CANCELADA`. El vencimiento se deriva de `due_at` y la permanencia; las incidencias son registros independientes.

Ubicaciones: `DISPONIBLE`, `OCUPADA`, `BLOQUEADA`, `FUERA_SERVICIO`. Una ubicación bloqueada puede conservar una asignación activa; no se ofrece para recibir otro objeto.

Credenciales: `ACTIVA`, `RETENIDA`, `CONSUMIDA`, `REVOCADA`. La expiración se comprueba con fecha de servidor. Autorizaciones: `VALIDADA`, `CONSUMIDA`, `ANULADA`; una autorización expirada no permite confirmar.

La recuperación de un retiro en curso no es una tarea automática: el operador debe indicar si entregó físicamente. Si no puede determinarse, se abre incidencia bloqueante y un administrador reconcilia con evidencia.

## 7. Historias y mapa de entregas

| Actividad | Corte P0 | Corte P1 |
|---|---|---|
| Acceder | Cuenta y sesión, permisos y contacto. | Mejoras de recuperación y auditoría de sesiones. |
| Dejar | Registrar, recibir, cobrar y ubicar. | Configuración completa del punto y tarifas. |
| Conocer estado | Consulta privada y pública mínima. | Bandeja y correo con reintentos. |
| Recoger | Credencial, verificación, entrega y comprobante. | Vencimiento y prórroga asistida. |
| Resolver | Incidencia y bloqueo para evitar repetición. | Recuperación aprobada, devolución y conciliación. |
| Aprender | Eventos de pruebas. | Indicadores del piloto y evaluación. |

US-01: como emisor, quiero dejar un objeto sin coincidir con el destinatario. Dada una custodia registrada y espacio disponible, cuando el operador recibe y registra el pago, entonces existe una asignación y un evento persistidos; si falla un paso, la recepción no se confirma digitalmente.

US-02: como destinatario, quiero recoger solo el objeto autorizado. Dada una credencial vigente y una cuenta habilitada, cuando el operador verifica y después confirma la entrega real, entonces la custodia queda retirada y la ubicación disponible; repetir la confirmación devuelve el resultado existente.

US-03: como responsable del punto, quiero reconstruir una diferencia. Dada una incidencia, cuando consulto el historial permitido, entonces identifico actor, fecha y operación sin revelar secretos ni editar el pasado.

## 8. Interfaz y aceptación global

Los contratos se definen en [API y seguridad](07_contratos_api_y_seguridad.md), el modelo en [datos](03_modelado_datos_arquitectura.md) y las pantallas en [UI](02_modelado_diseno_ui.md). El [plan de validación](../validacion/01_plan_validacion.md) y la [matriz de trazabilidad](../gestion/03_matriz_trazabilidad.md) relacionan cada requisito con evidencia prevista.

La aceptación del diseño exige consistencia entre esos artefactos. La aceptación de una futura implementación exige pruebas ejecutadas y un ensayo del servicio; producir estos documentos no equivale a aprobar el software.
