# Diseño de interfaz y navegación

La interfaz implementada aplica los principios de Mandel [U01] recogidos por Pressman y Maxim [I01]. WCAG 2.2 [U02] orienta la revisión de foco, contraste y reflujo.

## 1. Principios aplicados

| Principio | Decisión visible | Comprobación |
|---|---|---|
| Control del usuario | Permitir cancelar el prerregistro antes de recibir y confirmar explícitamente las acciones operativas. | El usuario identifica qué puede corregir sin ayuda. |
| Reducir carga de memoria | Mostrar punto, plazo y siguiente paso en el detalle; conservar filtros tras errores. | No exige memorizar guía ni nombres de estados técnicos. |
| Consistencia | “Registrar”, “Recibir”, “Autorizar entrega” y “Confirmar entrega realizada” conservan su sentido. | No hay botón “Entregado” antes de la entrega física. |
| Accesibilidad | Texto e icono junto al color, foco visible, etiquetas y navegación por teclado. | Tareas críticas ejecutables sin ratón; contraste revisado. |
| Información mínima | La consulta pública muestra estado general y horario. | No expone personas, códigos o ubicaciones internas. |

La reducción de pasos no reemplaza la verificación. Las restricciones de autorización se presentan con instrucciones claras y una vía de recuperación. No se usan mensajes de “cero filas”, “24/7” o “seguridad garantizada”.

## 2. Arquitectura de información y rutas propuestas

La portada organiza acceso, recorrido del servicio, puntos, cotización y seguimiento público. El espacio autenticado agrupa custodias, avisos, terminal y supervisión según el rol. La tabla conserva las rutas previstas en el diseño de información.

| ID | Ruta | Audiencia | Contenido |
|---|---|---|---|
| UI-01 | `/` | Pública | Propuesta, tres pasos, horario, condiciones y acceso. |
| UI-02 | `/seguimiento` | Pública | Referencia opaca y estado general; sin búsqueda por teléfono. |
| UI-03 | `/acceso` | Pública | Sesión y recuperación de cuenta. |
| UI-04 | `/registro` | Pública | Cuenta general y comprobación de contacto. |
| UI-05 | `/mis-custodias` | Usuario | Deposité / recibiré, filtros y detalle. |
| UI-06 | `/custodias/nueva` | Usuario | Destinatario registrado, punto, descripción y tamaño. |
| UI-07 | `/custodias/:id` | Participante | Historial permitido, plazo, comprobantes y credencial propia. |
| UI-08 | `/operacion` | Operador asignado | Recepción, consulta interna, verificación y confirmación. |
| UI-09 | `/incidencias` | Personal autorizado | Diferencias, recuperaciones y decisiones. |
| UI-10 | `/administracion` | Administrador | Puntos, horarios, personal, ubicaciones y tarifas. |
| UI-11 | `/auditoria` | Administrador / auditor | Eventos e indicadores con filtros. |
| UI-12 | `/avisos` | Cuenta activa | Bandeja y estado de lectura. |

El cliente protege la navegación para evitar confusión; el servidor vuelve a autorizar cada petición. Escribir una URL no debe revelar datos ni habilitar acciones.

## 3. Recorrido del emisor

La pantalla de nueva custodia explica “El registro previo no reserva espacio”. El usuario elige un destinatario comprobado sin disponer de un directorio público de personas: debe indicar el contacto exacto y el servidor devuelve una confirmación mínima, con límites de búsqueda. La descripción externa evita información sensible innecesaria.

Antes de enviar se muestra un resumen: punto, tamaño declarado, destinatario y condiciones. El resultado es “Registrada; pendiente de recepción”, con guía privada y posibilidad de cancelación. El precio final y la disponibilidad se confirman al recibir; la pantalla no afirma que ya existe un objeto almacenado.

## 4. Recorrido del destinatario

El destinatario entra a su cuenta y ve las custodias recibidas. En una custodia admitida y sin bloqueo puede generar un código temporal. El código se presenta una vez con tiempo restante, propósito y advertencia de compartirlo únicamente en la entrega. Reemitirlo requiere confirmación y revoca el anterior.

El detalle indica si existe prórroga pendiente y cómo resolverla; la consulta no solicita un pago al margen del servicio. La pantalla no muestra la ubicación interna del objeto al público. La imposibilidad de generar credencial presenta el motivo permitido sin revelar datos de terceros.

## 5. Terminal del operador

Dos áreas principales: recepción y retiro. Siempre muestra identidad del operador y punto activo. Cambiar de punto solo es posible si existe asignación válida.

Recepción: buscar la custodia, revisar descripción y condición externa, comprobar destinatario, elegir una ubicación libre, confirmar tarifa y registrar el cobro. El botón dice “Confirmar recepción”; solo cambia a éxito después de la respuesta del servidor. Ante conflicto de capacidad conserva los datos y obliga a comprobar otra ubicación.

Retiro: ingresar guía y código, registrar la comprobación visual y seleccionar “Verificar autorización”. El éxito muestra “Autorizado para entregar”, descripción del bulto y ubicación al operador. Luego aparece un segundo botón, “Confirmar que ya entregué el objeto”, con el identificador de la autorización. No se genera un cronómetro aleatorio ni se anuncia notificación enviada antes de recibir confirmación.

Si el operador detecta una diferencia, dispone de “No entregado: anular preparación” y “Abrir incidencia”. Después de una entrega real con confirmación fallida, el mensaje dice “Confirmación pendiente: no repetir entrega”. No se ofrece reintentar el acto físico.

## 6. Estados de interfaz

| Situación | Mensaje / acción |
|---|---|
| Cargando | Indicador y acción temporalmente deshabilitada, sin borrar el formulario. |
| Sin datos | Explicación y acción pertinente; sin inventar custodias de ejemplo. |
| No encontrado | Respuesta genérica; la consulta pública no confirma un número de teléfono. |
| Sesión vencida | Solicitar acceso y conservar solo datos no sensibles necesarios. |
| Sin conexión | Mostrar interrupción y suspender operaciones de inventario. |
| Conflicto de versión | Actualizar información y pedir revisar el estado real. |
| Código incorrecto o vencido | Mensaje genérico y contador permitido; no distinguir coincidencias parciales. |
| Límite de intentos | Informar espera o recuperación, sin permitir validar desde otra pantalla. |
| Incidencia bloqueante | Mostrar motivo permitido y acceso al procedimiento de revisión. |

Las demostraciones usan un entorno separado con rótulo visible. Una falla de la API no activa datos ficticios ni fabrica operaciones válidas.

## 7. Diseño adaptable y accesibilidad

En móvil se apilan acciones; las tablas se convierten en tarjetas con etiqueta. El campo de código permite pegar y utilizar teclado numérico sin obligar a seis casillas separadas. No se exige cámara, lectura de QR o periféricos. Los estados se expresan con texto e icono, nunca solo con color.

Se revisan contraste de texto, foco, orden de tabulación, nombre accesible, errores asociados al campo y anuncios de cambios de estado. Se usa WCAG 2.2 como referencia de criterios seleccionados; el ensayo no constituye certificación de conformidad completa.

## 8. Benchmarking y evaluación

La comparación visual estudia tareas y evidencia: visibilidad del horario, información de precio, claridad de la constancia y pasos de recuperación. No reproduce las cifras de espera ni juicios sobre competidores de la documentación anterior.

Las pruebas propuestas piden a cinco participantes: registrar, localizar el horario, identificar si un objeto fue recibido, obtener credencial propia y comprender una incidencia. Registrar éxito, ayuda, errores críticos y comentarios. Un hallazgo de entrega a persona incorrecta obliga a corregir el diseño antes del piloto.

Los [wireframes](../wireframes/README.md) son diseños estáticos. Sus códigos, personas y horarios son ejemplos ficticios rotulados; no prueban disponibilidad ni operaciones reales.
