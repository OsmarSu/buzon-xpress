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

## 2. Arquitectura de información y entradas actuales

La portada se divide en Inicio, Cómo funciona, Puntos y tarifas, Seguimiento, Nosotros y Contacto. Cada capítulo tiene su título coincidente con el menú, un tratamiento visual propio y una altura adaptable. La barra acompaña el desplazamiento, señala el capítulo visible y conserva espacio para los títulos al navegar mediante anclas. El scroll permanece bajo control del visitante.

Cómo funciona utiliza fotografías ilustrativas buscadas en Pexels y títulos breves para registrar, depositar y retirar. Acceso y registro tienen páginas independientes con formulario y una guía de uso del sistema: credenciales propias de BUZON Xpress, áreas de trabajo, creación de cuenta personal, verificación de correo y seguridad. Recuperación explica el cambio de contraseña y la continuidad del segundo factor. En el espacio autenticado, los módulos se muestran como paneles de `/cuenta` según el rol; las rutas previstas inicialmente para cada módulo no se publican como pantallas independientes.

| ID | Ruta | Audiencia | Contenido |
|---|---|---|---|
| UI-01 | `/` | Pública | Propuesta, tres pasos, horario, condiciones y acceso. |
| UI-02 | `/#seguimiento` | Pública | Referencia opaca y estado general; sin búsqueda por teléfono. |
| UI-03 | `/acceso` | Pública | Sesión, segundo factor y recuperación de cuenta. |
| UI-04 | `/registro` | Pública | Cuenta general y comprobación de contacto. |
| UI-05 | `/cuenta · custodias` | Usuario | Deposité / recibiré, filtros y detalle. |
| UI-06 | `/cuenta · nueva custodia` | Usuario | Destinatario registrado, punto, descripción y tamaño. |
| UI-07 | `/cuenta · detalle` | Participante | Historial permitido, plazo, comprobantes y credencial propia. |
| UI-08 | `/cuenta · operación` | Operador asignado | Recepción, consulta interna, verificación y confirmación. |
| UI-09 | `/cuenta · incidencias` | Personal autorizado | Diferencias, recuperaciones y decisiones. |
| UI-10 | `/cuenta · administración` | Administrador | Puntos, horarios, personal, ubicaciones y tarifas. |
| UI-11 | `/cuenta · auditoría` | Administrador / auditor | Eventos e indicadores con filtros. |
| UI-12 | `/cuenta · avisos` | Cuenta activa | Bandeja y estado de lectura. |

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

Los horarios se editan con campos de intervalos generales y una opción de horarios por día, sin pedir formatos de intercambio de datos. Si se completa un horario por día, ese grupo sustituye los intervalos generales y omite los días vacíos. La consulta presenta texto legible y ofrece orientación si un horario no se puede representar.

Los datos de demostración se identifican como ilustrativos. Las pantallas muestran información del servicio y omiten detalles de infraestructura. Una falla de la API no activa datos ficticios ni fabrica operaciones válidas.

## 7. Diseño adaptable y accesibilidad

Los formularios administrativos se distribuyen en recuadros amplios, con dos columnas independientes cuando hay espacio y una en pantallas estrechas. Cada columna conserva el orden de sus grupos y permite expandir un formulario sin desplazar los grupos de la otra columna. Los controles y los grupos con borde pueden reducir su ancho sin desbordar su contenedor. Cada campo conserva una etiqueta explícita; las indicaciones y ejemplos se asocian mediante `aria-describedby`. En los formularios internos, un icono de ayuda junto a la etiqueta muestra una burbuja al pasar el cursor, recibir foco de teclado o tocarlo. Las páginas de acceso, registro y recuperación conservan sus etiquetas y ejemplos dentro de los campos, sin iconos de ayuda. La burbuja no desplaza los campos; se cierra con Escape, al perder el foco o al tocar fuera. Su ancho se limita al del campo y su posición cambia hacia arriba cuando falta espacio inferior.

El formulario de acceso precede a la ayuda en el orden de lectura y de teclado; en escritorio se presenta junto a ella y en móvil aparece primero. Los títulos de los módulos coinciden con sus opciones de navegación. El cambio de pantalla conserva el foco en el título y muestra el inicio de la página o tarjeta con margen bajo la barra fija.

En móvil se apilan acciones; las tablas se convierten en tarjetas con etiqueta. El campo de código permite pegar y utilizar teclado numérico sin obligar a seis casillas separadas. No se exige cámara, lectura de QR o periféricos. Los estados se expresan con texto e icono, nunca solo con color.

Las entradas de sección y transiciones son breves y respetan `prefers-reduced-motion`. Los indicadores de carga reflejan solicitudes reales, conservan el formulario y anuncian el estado a tecnologías de apoyo. MFA permite pegar el código de la aplicación o usar un código de recuperación; el enrolamiento muestra la clave solo durante la configuración y los códigos de respaldo una sola vez.

Se revisan contraste de texto, foco, orden de tabulación, nombre accesible, errores asociados al campo y anuncios de cambios de estado. Se usa WCAG 2.2 como referencia de criterios seleccionados; el ensayo no constituye certificación de conformidad completa.

## 8. Benchmarking y evaluación

La comparación visual estudia tareas y evidencia: visibilidad del horario, información de precio, claridad de la constancia y pasos de recuperación. No reproduce las cifras de espera ni juicios sobre competidores de la documentación anterior.

Las pruebas propuestas piden a cinco participantes: registrar, localizar el horario, identificar si un objeto fue recibido, obtener credencial propia y comprender una incidencia. Registrar éxito, ayuda, errores críticos y comentarios. Un hallazgo de entrega a persona incorrecta obliga a corregir el diseño antes del piloto.

Los [wireframes](../wireframes/README.md) son diseños estáticos. Sus códigos, personas y horarios son ejemplos ficticios rotulados; no prueban disponibilidad ni operaciones reales.

## 9. Revisión de claridad del contenido — 14 de noviembre de 2026

Se revisaron los textos de portada, acceso, registro, recuperación y módulos por rol. Se sustituyó “envíos” por “custodias”, se explicó el contacto exacto del destinatario y se conservaron las diferencias entre registrar, recibir, autorizar y confirmar una entrega física. La ayuda de autenticación describe el sistema y las funciones realmente disponibles, sin atribuir permisos de personal al registro público.

La revisión visual del sitio publicado cubrió anchos de 320, 390, 820 y 1280 píxeles en las páginas revisadas: sin desbordamiento horizontal, formulario antes de la ayuda en móvil, etiquetas identificables y títulos visibles bajo la barra fija. Se comprobó la coincidencia de los seis títulos públicos con el menú, los paneles de administración y la terminal del operador. Pasaron las cinco pruebas del frontend y la compilación TypeScript/Vite. Esta revisión técnica no sustituye la prueba de comprensión con cinco participantes (T-19), que continúa pendiente.

La comprobación posterior de formularios mantuvo 42 controles administrativos dentro de sus recuadros a 320, 390, 820 y 1280 píxeles de ancho, sin desplazamiento horizontal. También se revisaron los campos visibles de custodias, incidencias, indicadores, acceso, registro y terminal del operador, junto con la consulta de ayudas contextuales y la conservación del texto escrito. La prueba se realizó mediante consultas y cambios de vista, sin crear operaciones de negocio.

La revisión de contenido del 14 de noviembre retiró la etiqueta técnica de tres descripciones ilustrativas de custodias, con respaldo y eventos de corrección. Las nueve pruebas actuales del frontend cubren también los intervalos generales, la prioridad de horarios por día, los formularios vacíos y la presentación legible del horario.

## Primera fase de la interfaz Android

La aplicación 0.2.2 abre en Consultar seguimiento. Sin sesión muestra esa consulta y el acceso en la cabecera; después de autenticar usa navegación inferior por Seguimiento, Custodias, Puntos, Avisos y Cuenta. El acceso y registro ocupan pantallas independientes sin ayudas emergentes. Las acciones privadas requieren sesión; tras acceder se retoma el área solicitada. El prerregistro explica la confirmación presencial de capacidad y precio. El código de retiro solo se presenta al destinatario autorizado, con vencimiento, y se oculta al cerrar el detalle o cambiar de aplicación. Cancelación, renovación del código de paquete y reemisión requieren confirmación. La prueba en teléfono físico y con TalkBack sigue pendiente.

La previsualización de la primera fase móvil comprobó acceso con cuenta publicada, retorno al área solicitada, listado y detalle de custodias, cotización y validación de campos vacíos sin registrar nuevas operaciones de negocio. Esta evidencia corresponde al renderizado web de React Native y no reemplaza una ejecución física en Android.

La revisión móvil del 15 de noviembre de 2026 comprobó las rutas de Expo Router, la entrada directa a una pantalla privada sin sesión, el retorno después del acceso, la reapertura del mismo detalle desde Avisos y el cierre de sesión. En anchos de 320 y 390 píxeles, los cinco destinos inferiores conservan icono y título visibles, con blancos táctiles de al menos 50 píxeles de alto. Al recuperar el foco se consultan los datos de cada sección. Las respuestas tardías de una sesión anterior no invalidan la sesión nueva y un código de retiro solicitado no vuelve a mostrarse después de cerrar el detalle o pasar a segundo plano.

Ante el reporte de iconos invisibles en el móvil, la revisión 0.2.1 cambió la navegación a SVG nativo y enlazó la familia Ionicons restante dentro del APK. El inicio omite la portada comercial y las opciones privadas antes del acceso. La revisión a 320 y 390 píxeles comprobó cabecera, consulta, protección de Puntos y menú autenticado, incluido el título Seguimiento completo. La evidencia visual procede de React Native Web y de la configuración nativa generada; la comprobación final del hallazgo requiere instalar el APK revisado en el teléfono.

### Ajustes móviles 0.2.2

La cabecera pública y privada muestra solo el nombre escrito. El pie web omite el apartado Fotografías del recorrido. El término visible es **Código de Paquete**, separado de la guía privada y del código de retiro. Los campos móviles comparten un contenedor que desplaza el control enfocado por encima del teclado, tanto en acceso y registro como en los formularios de cuenta y las ventanas de custodia. La revisión en previsualización no sustituye la confirmación del teclado físico Android.

Puntos permite buscar por nombre o zona, abrir dirección y horario, cotizar por tamaño y horas y continuar al prerregistro con esos datos. El destinatario y la descripción se completan después. El prerregistro exige contacto verificado y no reserva espacio. Las ubicaciones son ficticias; no se muestran distancias ni disponibilidad en tiempo real.

Las categorías declaran máximos **con embalaje, en largo × ancho × alto**: pequeño **30 × 20 × 15 cm**, mediano **50 × 40 × 30 cm** y grande **70 × 50 × 50 cm**. Se elige el menor tamaño que admita el objeto; el personal comprueba la categoría y capacidad al recibirlo. Son límites de la política de recepción, no medidas capturadas o verificadas automáticamente por el servidor.

La revisión 0.2.2 aprobó doce pruebas del cliente móvil y comprobó en la previsualización la cotización de 48 horas para tamaño mediano y el traslado de la selección de Miraflores al prerregistro, incluida su reapertura. La web publicada se revisó a 320, 390 y 1280 píxeles; los selectores muestran medidas completas. El APK final contiene el componente nativo del teclado y conserva el certificado de la entrega anterior. Estas verificaciones no sustituyen el recorrido en un teléfono Android.

La web y Android 0.2.4 marcan con un asterisco los campos obligatorios. Operación y Auditoría consultan los puntos asignados a la sesión. Revisión abre directamente su área de incidencias y excepciones.
