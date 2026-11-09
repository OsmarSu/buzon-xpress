# Casos de uso de alto nivel y expandidos

Los escenarios usan la estructura de actor, meta, alcance, condiciones y extensiones descrita por Cockburn [I02] y Larman [I03]. Las asociaciones del [diagrama UML](../diagramas/casos_uso_alto_nivel.svg) se contrastaron con la API y sus permisos.

## 1. Catálogo de alto nivel

| ID | Meta de usuario | Actor principal | Requisitos |
|---|---|---|---|
| CU-01 | Acceder y gestionar el contacto. | Visitante que se registra / persona con cuenta | RF-01, RF-02 |
| CU-02 | Registrar una entrega futura. | Emisor | RF-03 |
| CU-03 | Recibir y localizar un objeto. | Operador | RF-04, RF-05 |
| CU-04 | Consultar seguimiento público o custodia privada según alcance. | Visitante / participante / personal asignado | RF-06 |
| CU-05 | Obtener código de retiro. | Destinatario | RF-07 |
| CU-06 | Verificar y preparar la entrega. | Operador | RF-08 |
| CU-07 | Confirmar una entrega real. | Operador | RF-09, RF-18 |
| CU-08 | Recibir avisos del servicio. | Participante | RF-11 |
| CU-09 | Consultar tarifa y registrar una prórroga. | Visitante / operador asignado | RF-12, RF-13 |
| CU-10 | Tramitar incidencias, excepciones y devoluciones. | Participantes / operador / administrador | RF-10, RF-14 |
| CU-11 | Mantener el punto y su capacidad. | Administrador | RF-16 |
| CU-12 | Supervisar operaciones y evidencia. | Administrador / auditor | RF-15, RF-17 |

El diagrama representa metas observables de roles externos. Emisor y destinatario son roles de una custodia concreta. La misma persona puede desempeñar uno u otro en distintas operaciones. Visitante representa la interacción pública y persona con cuenta cubre el acceso de usuarios y personal. Operador, administrador y auditor ejercen funciones según su asignación al punto.

Los módulos internos y sus dependencias están en la [vista de componentes](../diagramas/c4_componentes.svg). El [diagrama de secuencia](01_modelado_analisis_pressman.md#6-secuencia-de-retiro-asistido) muestra el orden del retiro.

| Caso en el diagrama | Alcance |
|---|---|
| CU-04a | Seguimiento público mediante referencia opaca. Muestra estado general, punto y horario. |
| CU-04b | Consulta privada para el emisor, el destinatario o el operador, administrador o auditor asignado al punto. |
| CU-09a | Cualquier visitante puede consultar puntos y pedir una cotización inicial. |
| CU-09b | El operador asignado cotiza la extensión según la tarifa histórica y registra el pago y el nuevo plazo. |
| CU-10a | Los participantes pueden abrir incidencias propias y solicitar reemisión o devolución. El operador y el administrador asignados pueden registrar incidencias y solicitar los expedientes autorizados. |
| CU-10b | El administrador del punto revisa el expediente, decide una excepción solicitada por otra persona o resuelve una incidencia. Una incidencia bloqueante requiere un administrador distinto de quien la abrió. |
| CU-10c | El operador asignado prepara una devolución aprobada y confirma la entrega física al emisor. |

Los sufijos conservan la trazabilidad de los doce casos expandidos. La notación de las figuras, asociaciones, óvalos y límite del sistema sigue las secciones 18.1.3 y 18.1.4 de [OMG UML 2.5.1](https://www.omg.org/spec/UML/2.5.1/).

## 2. CU-01 — Acceder con permisos apropiados

**Actor y alcance:** usuario o personal, plataforma web. Meta: establecer una sesión que permita solo sus operaciones. **Precondiciones:** acceso al navegador; para una cuenta existente, habilitación activa. **Disparador:** solicitar registro o acceso.

**Escenario principal:**

1. La persona introduce datos de cuenta general o credenciales.
2. El servidor valida formato y condiciones y comprueba el verificador de contraseña.
3. Para registro, asigna rol de usuario; el contacto se comprueba por correo o procedimiento presencial registrado.
4. Se crea una sesión con token aleatorio, vencimiento y cookie protegida.
5. La plataforma muestra las tareas permitidas; cada petición posterior vuelve a verificar sesión, participación y punto.
6. Al cerrar sesión se revoca el registro de servidor.

**Garantía de éxito:** una sesión válida y permisos limitados. **Garantía mínima:** un fallo no habilita privilegios ni revela si una cuenta ajena existe.

**Extensiones:** credenciales inválidas o demasiados intentos: rechazo; contacto pendiente: permitir completar verificación sin autorizar custodia; cuenta inactiva: no abrir sesión; usuario intenta elegir rol de personal: ignorar o rechazar el campo. **Pruebas:** T-01, T-02 y T-21.

## 3. CU-02 — Registrar una entrega futura

**Actor y alcance:** emisor autenticado, plataforma. **Precondiciones:** cuenta y contacto comprobados, destinatario activo identificado mediante contacto exacto y punto activo. **Disparador:** “Registrar objeto”.

**Escenario principal:**

1. El emisor selecciona punto e indica destinatario, tamaño y descripción externa.
2. El servidor comprueba la relación y evita exponer un directorio de cuentas.
3. La pantalla explica que la capacidad se confirma al recibir y muestra condiciones.
4. El emisor confirma los datos.
5. El servidor crea custodia `REGISTRADA`, guía privada, referencia pública independiente y evento.
6. El emisor recibe constancia del registro y puede consultar o cancelar antes de recepción.

**Garantía de éxito:** existe una operación pendiente sin asignación de espacio. **Garantía mínima:** un error no inventa una guía ni muestra recepción exitosa.

**Extensiones:** destinatario no comprobado: explicar cómo completar la cuenta; punto inactivo: impedir creación; cancelación previa a recibir: estado `CANCELADA`; intento de editar destinatario después de recibir: tramitar recuperación. **Prueba:** T-03.

## 4. CU-03 — Recibir y localizar un objeto

**Actor y alcance:** operador asignado al punto, servicio asistido y plataforma. **Precondiciones:** conexión, custodia registrada y bulto físicamente presente. **Disparador:** el emisor llega al punto.

**Escenario principal:**

1. El operador busca la guía y comprueba emisor, destinatario y bulto.
2. Revisa tamaño, condición aparente y admisibilidad; informa cualquier diferencia antes de aceptar.
3. Consulta una ubicación disponible y confirma tarifa y plazo con el emisor.
4. Recibe el pago del servicio según el medio admitido y registra la comprobación.
5. El servidor bloquea custodia y ubicación y registra asignación, cobro, inicio, vencimiento, estado `EN_CUSTODIA`, evento y aviso.
6. Tras confirmar la transacción, el operador coloca el bulto en la ubicación comprobada y muestra constancia. Si colocación y registro discrepan, abre incidencia de inmediato.

**Garantía de éxito:** una recepción y una asignación activa. **Garantía mínima:** un fallo digital no confirma parcialmente la recepción; el operador resuelve material y cobro con el emisor.

**Extensiones:** sin capacidad: rechazar admisión antes de aceptar; conflicto concurrente: revisar nueva ubicación; error tras recibir dinero: devolver o reconciliar sin nuevo cobro ficticio; objeto no admisible: no recibir. **Pruebas:** T-04 y T-05.

## 5. CU-04 — Conocer el estado permitido

**Actor y alcance:** el visitante consulta el seguimiento público. El emisor, el destinatario y el personal asignado consultan el detalle privado dentro de su alcance. **Precondiciones:** sesión autorizada para el detalle privado o referencia pública aleatoria para el seguimiento. **Disparador:** consultar estado.

**Escenario principal:**

1. El servidor distingue consulta privada de pública.
2. En privada comprueba participación o alcance del personal.
3. Devuelve el estado, el plazo y los datos autorizados de la custodia. El administrador y el auditor consultan los eventos de su punto en CU-12.
4. En pública devuelve solo estado general y punto/horario, sin nombre, teléfono, descripción o ubicación interna.
5. La pantalla muestra el resultado o una falla real.

**Garantía de éxito:** información pertinente y limitada. **Garantía mínima:** no se crea una custodia de ejemplo ni se revela si un teléfono tiene objetos.

**Extensiones:** referencia inexistente: respuesta genérica; tasa excesiva: limitar; sesión ajena: 403 o 404 según política uniforme; servicio caído: mostrar indisponibilidad. **Prueba:** T-06.

## 6. CU-05 — Obtener credencial de retiro

**Actor y alcance:** destinatario autenticado, plataforma. **Precondiciones:** custodia en posesión del punto, sin entrega en curso ni incidencia bloqueante; cuenta activa. **Disparador:** “Generar código”.

**Escenario principal:**

1. El servidor comprueba propiedad, estado y límites de emisión.
2. Revoca una credencial activa anterior si se solicitó reemisión explícita.
3. Genera código aleatorio y conserva solo un HMAC ligado a custodia y propósito.
4. Devuelve el código una sola vez por la conexión autenticada y la hora de expiración.
5. La pantalla informa vigencia y uso exclusivo para esa entrega.

**Garantía de éxito:** existe una única credencial activa. **Garantía mínima:** no se devuelve secreto a emisor, consulta pública, logs o avisos.

**Extensiones:** si se pierde la respuesta se reemite con confirmación y se invalida la anterior; no se recupera el código desde la base. Una autorización retenida impide reemisión hasta resolver la entrega. **Prueba:** T-07.

## 7. CU-06 — Verificar y preparar entrega

**Actor y alcance:** operador asignado, plataforma y comprobación presencial. **Precondiciones:** destinatario presente, código y guía, custodia disponible para retiro y servicio conciliado. **Disparador:** “Verificar autorización”.

**Escenario principal:**

1. El operador comprueba visualmente al destinatario y registra esa comprobación sin imagen documental.
2. Envía guía, código y versión esperada.
3. El servidor comprueba sesión, punto, estado, saldo, bloqueo e intentos.
4. Bajo transacción valida el HMAC y la vigencia, retiene credencial y crea autorización breve para ese operador.
5. Cambia a `RETIRO_EN_CURSO` y registra evento.
6. Devuelve “Autorizado para entregar”, descripción y ubicación interna al operador.

**Garantía de éxito:** una sola preparación activa. **Garantía mínima:** la verificación no registra entrega física ni libera espacio.

**Extensiones:** código incorrecto, vencido o de otro objeto: rechazo genérico e intento persistido; demasiados intentos: bloqueo; deuda: resolver prórroga; objeto no localizado: incidencia. **Prueba:** T-08.

## 8. CU-07 — Confirmar una entrega real

**Actor y alcance:** operador que verificó, servicio y plataforma. **Precondiciones:** autorización vigente del mismo operador y constatación del bulto correcto. **Disparador:** el operador entrega físicamente y pulsa la confirmación.

**Escenario principal:**

1. El operador entrega al destinatario y confirma que ya lo hizo.
2. La terminal envía autorización y clave de idempotencia.
3. El servidor comprueba permiso, estado, vigencia y ausencia de bloqueo nuevo.
4. En una transacción consume credencial y autorización, registra comprobante, cierra asignación, libera ubicación y marca `RETIRADA`.
5. Agrega evento y avisos y devuelve constancia.
6. Una repetición idéntica recupera el mismo resultado.

**Garantía de éxito:** una salida documentada. **Garantía mínima:** un error no confirma parcialmente el registro ni autoriza una segunda entrega.

**Extensiones:** si no se entregó se anula preparación con razón y credencial revocada; si se entregó y falló la confirmación, no repetir acto físico y abrir conciliación; clave repetida con otro contenido: conflicto; autorización expirada: recuperación, no confirmación ordinaria. **Pruebas:** T-09 y T-18.

## 9. CU-08 — Recibir avisos

**Actor y alcance:** participante, bandeja y correo configurable. **Precondiciones:** evento de recepción, plazo, salida o incidencia notificable. **Disparador:** confirmación de la transacción relevante.

**Escenario principal:**

1. La operación crea avisos únicos en su misma transacción.
2. El destinatario ve el aviso en su bandeja al consultar.
3. Un proceso toma correos pendientes, envía un mensaje sin secreto y registra intento.
4. Si el servidor de correo acepta, se marca envío aceptado; esto no acredita lectura humana.
5. La lectura en bandeja se registra separadamente.

**Garantía de éxito:** aviso interno persistido y resultado del canal rastreable. **Garantía mínima:** una falla de correo no revierte una recepción o entrega válidas ni informa envío exitoso falso.

**Extensiones:** reintentar con espera creciente; tras el límite marcar fallido y mostrar al personal; deduplicar por evento, persona y canal. Sin correo configurado se informa que solo funciona la bandeja. **Prueba:** T-11.

## 10. CU-09 — Contratar plazo y resolver vencimiento

**Actor y alcance:** el visitante consulta puntos y cotiza el plazo inicial. El operador asignado registra el cobro y la prórroga. **Precondiciones:** tarifa vigente para la cotización inicial o condiciones históricas para una prórroga. **Disparador:** cotizar, recibir o registrar una extensión.

**Escenario principal:**

1. El servidor calcula el precio por tamaño y plazo.
2. El operador informa el importe y registra aceptación y pago comprobado.
3. Se conservan versión, reglas y vencimiento.
4. Una tarea identifica custodias vencidas y crea avisos sin mover inventario.
5. Si corresponde prórroga, se calcula bajo las condiciones aceptadas, se informa y registra el nuevo pago y plazo.
6. Antes de autorizar retiro se comprueba conciliación del servicio.

**Garantía de éxito:** precio y pagos reconstruibles, sin fondos de ventas a terceros. **Garantía mínima:** una nueva tarifa no cambia operaciones históricas.

**Extensiones:** precio cero o negativo no admitido por el producto tarifario; pago no comprobado: no confirmar cobro; disputa: incidencia; plazo vencido: conservar ubicación; devolución de dinero: registro de reembolso con auditoría. **Pruebas:** T-12 y T-13.

## 11. CU-10 — Resolver diferencias y devoluciones

**Actor y alcance:** el participante o el personal autorizado registra la solicitud. El administrador asignado decide la excepción y el operador ejecuta la devolución aprobada. **Precondiciones:** custodia identificada y hechos registrados. **Disparador:** pérdida de acceso, diferencia, cambio o devolución.

**Escenario principal:**

1. Un participante o un miembro del personal autorizado abre una incidencia. El bloqueo protege la custodia si existe riesgo de duplicación o destinatario incierto.
2. El solicitante autorizado registra el propósito y la evidencia mínima de la excepción.
3. Un administrador asignado, distinto del solicitante, revisa participantes, estado físico declarado y eventos.
4. Aprueba o rechaza con fundamento; la persona solicitante no se autoaprueba.
5. La acción aprobada revoca secretos anteriores y aplica el cambio correspondiente con auditoría.
6. Para devolver, se genera autorización al operador, se entrega físicamente al emisor comprobado y se confirma comprobante `DEVOLUCION` y estado `DEVUELTA`.

**Garantía de éxito:** excepción reconstruible, salida única y conservación de evidencia. **Garantía mínima:** incertidumbre mantiene bloqueo y ubicación.

**Extensiones:** no hay segundo responsable disponible: mantener custodia y programar revisión; conciliación de entrega ya realizada permite completar el registro con expediente, sin nueva entrega; evidencia insuficiente: no entregar. **Pruebas:** T-10 y T-14.

## 12. CU-11 — Mantener punto y capacidad

**Actor y alcance:** administrador autorizado para el punto. **Precondiciones:** sesión y alcance. **Disparador:** configurar horario, tarifa, personal o ubicación.

**Escenario principal:**

1. El administrador consulta configuración y ocupación actuales.
2. Registra el cambio y su fecha de aplicación.
3. El servidor valida coherencia y evita eliminar referencias usadas.
4. Una tarifa se publica como nueva versión; no altera contratos anteriores.
5. Una ubicación libre puede salir de servicio; una ocupada exige traslado controlado o resolución documentada.
6. Se conserva evento de quién cambió qué.

**Garantía de éxito:** configuración coherente con la operación. **Garantía mínima:** desactivar un punto no elimina objetos ni historial.

**Extensiones:** rol sin alcance: rechazo; cambio concurrente: conflicto; última cuenta administrativa: procedimiento de recuperación documentado. No se da capacidad a un usuario mediante un selector público de registro. **Prueba:** T-16.

## 13. CU-12 — Supervisar operaciones y evidencia

**Actor y alcance:** administrador o auditor autorizado. **Precondiciones:** periodo y punto definidos. **Disparador:** consultar o exportar reportes.

**Escenario principal:**

1. El servidor valida alcance y filtros.
2. Devuelve eventos con actor, fecha y correlación sin secretos.
3. Calcula ocupación con ubicaciones utilizables y asignaciones activas.
4. Calcula tiempos y permanencia usando fechas reales y muestra denominadores.
5. Distingue datos del piloto de datos sintéticos y registra la exportación.
6. El responsable documenta interpretación y acciones de mejora.

**Garantía de éxito:** evidencia reproducible y limitada al alcance. **Garantía mínima:** no se reescribe la bitácora ni se atribuyen métricas simuladas a usuarios reales.

**Extensiones:** muestra insuficiente: indicarlo; fechas faltantes: reportar calidad; intento de editar evento: rechazo; restauración: realizar ensayo aislado con registro de resultado. **Pruebas:** T-15 y T-17.

## 14. Contratos comunes

Las referencias de datos, API, pantallas y pruebas se reúnen en la [matriz de trazabilidad](../gestion/03_matriz_trazabilidad.md). Todos los casos conservan el horario del punto y la ausencia de hardware externo. Los pasos de aceptación del bulto y entrega al destinatario son hechos humanos que el software registra, no hechos comprobados automáticamente.
