# Formulación estratégica de negocio: BUZON Xpress

Estado: hipótesis de negocio y diseño del servicio. Referentes: B01–B06 de la [bibliografía](../metodologia/02_bibliografia_verificada.md). Las aplicaciones y decisiones de este documento son elaboración del proyecto.

## 1. Resumen y propuesta de valor

BUZON Xpress ofrece custodia temporal asistida para intercambios de objetos entre personas. Un emisor deja un bulto en un punto atendido y su destinatario lo recoge después de una verificación. El ingreso previsto proviene del servicio de custodia, según tamaño y plazo contratado.

Propuesta de valor: **“Deja un objeto con constancia y permite que su destinatario lo recoja después, dentro del horario del punto”.**

La capacidad del espacio y la disponibilidad del personal son límites del servicio. El software ayuda a cumplir el procedimiento, conservar evidencia y reducir errores. La conveniencia, confianza y disposición a pagar deben comprobarse con usuarios del entorno.

## 2. Jobs to Be Done

| Circunstancia | Progreso buscado | Alternativa a investigar | Criterio de contratación |
|---|---|---|---|
| Dos personas tienen horarios distintos. | Completar el intercambio sin esperar juntas. | Reprogramar encuentro o pedir ayuda a un conocido. | Cercanía y horario conveniente. |
| Se entrega un objeto prestado o documentos. | Saber quién recibió y quién retiró. | Portería o comercio receptor. | Constancia y verificación comprensibles. |
| Se vende ocasionalmente un producto. | Dejarlo disponible sin esperar al comprador. | Entrega personal o mensajería. | Costo total y facilidad para ambas partes. |
| Un comercio presta espacio al servicio. | Organizar la recepción sin perder control. | Cuaderno o planilla propia. | Carga operativa y remuneración compatibles. |

La entrevista indaga la última ocasión real: qué ocurrió, cómo se resolvió, cuánto tiempo y dinero demandó y qué salió mal. Una respuesta favorable a una idea hipotética no se cuenta como contratación ni intención de uso confirmada.

## 3. ERAC y curva de valor a investigar

| Eliminar | Reducir | Aumentar | Crear |
|---|---|---|---|
| Necesidad de que emisor y receptor coincidan. | Consultas repetidas sobre llegada y retiro. | Constancia de custodia y claridad del responsable. | Servicio por plazo en un punto atendido. |
| Registro comercial obligatorio para intercambios personales. | Dependencia de mensajes informales dispersos. | Información de horario, tarifa y condiciones. | Autorización digital ligada a una operación. |

No se declara una ventaja patentada ni una ausencia de competidores. La comparación se levantará con una ficha común: disponibilidad geográfica, horario, plazo, costo total para un mismo objeto, comprobante, proceso de retiro y atención de incidencias. Las columnas de competidores permanecerán sin puntuación hasta obtener evidencia fechada.

## 4. Business Model Canvas

| Bloque | Hipótesis de diseño |
|---|---|
| Segmentos | Personas del entorno del punto que realizan intercambios ocasionales; comerciantes pequeños como segmento adicional. |
| Propuesta de valor | Custodia con registro y entrega posterior autorizada, accesible desde un navegador. |
| Canales | Punto anfitrión, sitio web y recomendaciones del piloto; correo para comunicaciones. |
| Relaciones | Atención presencial, consulta digital y gestión de incidencias con responsable identificable. |
| Ingresos | Tarifa por tamaño y bloque temporal; prórroga acordada. El emisor paga el plazo inicial al depositar. |
| Recursos | Personal, espacio y equipos existentes, plataforma y procedimientos documentados. |
| Actividades | Recepción, organización, verificación, entrega, conciliación de inventario y soporte. |
| Socios | Responsable del punto y posibles proveedores de alojamiento o correo, si se requieren. |
| Costos | Tiempo del personal, costo de oportunidad del espacio, desarrollo, soporte, conectividad y servicios digitales. |

“Recursos existentes” no significa costo económico cero. La evaluación registra uso, capacidad y costo de oportunidad aunque no exista una compra inicial.

## 5. Lean Canvas

| Bloque | Hipótesis comprobable |
|---|---|
| Problema | La coordinación temporal dificulta ciertos intercambios y genera incertidumbre. |
| Segmento inicial | Usuarios accesibles de un solo punto; el segmento se selecciona con evidencia del diagnóstico. |
| Propuesta única | Entrega en otro momento con constancia y responsable. |
| Solución inicial | Prerregistro, recepción atendida, ubicación, aviso, código y comprobante de retiro. |
| Canales | Invitación presencial y comunicación digital a participantes que consientan. |
| Ingresos | Tarifa del servicio; no cobro del precio del objeto ni comisiones de venta. |
| Costos | Costos fijos del punto y software, más costo variable por operación y permanencia. |
| Métricas | Usos completados, repetición, ocupación, permanencia, errores, tiempo de atención y contribución. |
| Ventaja difícil de copiar | Todavía no demostrada. La confianza y acuerdos del punto podrían desarrollarse, pero no se presentan como activos consolidados. |

## 6. Cadena de valor y diseño operativo

| Actividad | Valor que entrega | Costo o falla relevante | Control |
|---|---|---|---|
| Admisión | Condiciones claras antes de aceptar. | Recepción de un objeto no admisible. | Lista y comprobación visual. |
| Recepción | Constancia y comienzo del plazo. | Datos incorrectos o ubicación duplicada. | Revisión y transacción única. |
| Custodia | Objeto localizable. | Ocupación prolongada o error de ubicación. | Ubicación exclusiva y conciliación diaria. |
| Verificación | Entrega autorizada. | Código compartido, vencido o de otro objeto. | Validación en servidor y comprobación del destinatario. |
| Entrega | Finalización documentada. | Fallo entre entrega humana y confirmación. | Paso explícito de confirmación y reconciliación. |
| Soporte | Resolución de diferencias. | Cambio de destinatario sin autorización. | Solicitud, evidencia y aprobación de otra persona. |

Actividades de apoyo: capacitación, control de acceso del personal, mantenimiento de software, copias de seguridad y revisión de costos. La tarifa debe cubrir tanto recepción como retiro y los casos de soporte esperables.

## 7. Política de servicio propuesta

- Prerregistrar no reserva una ubicación. La recepción confirma disponibilidad y aceptación.
- El servicio se presta en el punto seleccionado y en su horario publicado.
- Una ubicación alberga una custodia activa; el público no entra al almacenamiento.
- Se registra descripción externa suficiente para identificar el bulto y su condición aparente; no se afirma conocimiento del contenido.
- El precio y el plazo se informan y aceptan antes de recibir. El importe se calcula en servidor con una versión tarifaria.
- El vencimiento genera aviso y revisión; no elimina la custodia ni autoriza disponer del objeto.
- La devolución y los cambios de destinatario requieren procedimiento documentado y aprobación separada.
- Ante falta de conexión se suspenden operaciones nuevas que afecten inventario. Se informa la situación sin mostrar éxito ficticio.

Las condiciones finales de admisibilidad, responsabilidad y permanencia se establecen para el emplazamiento tras la investigación correspondiente. El prototipo no anuncia seguro contratado, ausencia de riesgo o garantía de operación permanente.

## 8. Adopción y experimentos

Se propone comenzar con participantes cercanos a un punto y un caso de uso claro. La solución completa incluye atención, instrucciones, acceso al horario y recuperación de incidencias. Un aumento de registros sin operaciones completadas no justifica expandirse.

| Hipótesis | Experimento | Evidencia | Decisión |
|---|---|---|---|
| H-01: el problema ocurre con frecuencia relevante. | Diez entrevistas de episodios recientes. | Frecuencia, alternativas y costos declarados. | Elegir segmento o replantear necesidad. |
| H-02: el punto resulta conveniente. | Recorrido y prueba de horario con participantes. | Distancia, visitas fallidas y abandonos. | Ajustar ubicación u horario. |
| H-03: el proceso es comprensible. | Cinco sesiones con tareas. | Finalización, errores y ayuda requerida. | Corregir interfaz y procedimiento. |
| H-04: existe margen operativo. | Treinta ciclos supervisados con tiempos y permanencia. | Contribución y carga de personal. | Ajustar precio, capacidad o continuidad. |
| H-05: existe uso repetido. | Seguimiento del piloto en un plazo definido. | Segunda operación real por usuario. | Evaluar continuidad; sin inferencia nacional. |

Estos tamaños son propuestas de ensayo, no muestras representativas. Todos los resultados están pendientes. Los instrumentos y cálculos se detallan en [demanda y evaluación](02_demanda_costos_y_evaluacion.md).
