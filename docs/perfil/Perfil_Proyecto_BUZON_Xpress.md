# Perfil de proyecto: BUZON Xpress

## Plataforma web para la custodia temporal asistida y el intercambio asíncrono de objetos

Preparación y Evaluación de Proyectos · La Paz, Bolivia · 2026.

Versión documental 1.0. El emplazamiento concreto, la capacidad y los importes se determinan mediante el levantamiento del punto piloto. Este documento describe una propuesta; no presenta resultados de una empresa operativa.

## 1. Introducción

La entrega de un objeto entre dos personas requiere coordinar lugar y horario. Cuando esa coordinación falla, el emisor puede posponerla, contratar un traslado o pedir a un tercero que lo guarde. BUZON Xpress propone un servicio en el que personal de un punto recibe un objeto, registra su custodia y lo entrega posteriormente a un destinatario autorizado.

La plataforma organiza el proceso y conserva evidencia digital. La recepción y la entrega son actividades humanas; el espacio de almacenamiento permanece bajo responsabilidad del personal. Se utilizan equipos y espacio disponibles, sin incorporar hardware externo ni lockers inteligentes.

## 2. Antecedentes y diagnóstico por realizar

El perfil antecedente identifica dificultades de coordinación, resguardo informal y falta de trazabilidad. La documentación del proyecto existente aporta una base web orientada al comercio social. En su código se observaron modelos de paquetes y puntos, una API y pantallas de demostración, además de limitaciones de autenticación e integración.

Estos antecedentes justifican investigar el problema, pero no prueban su magnitud local ni la disposición a pagar. El diagnóstico propuesto combina entrevistas sobre intercambios recientes, observación autorizada de un punto y un ensayo controlado. Se contrastan consignas, comercios receptores, encuentros personales y mensajería, sin afirmar que tales servicios estén ausentes o sean inferiores.

## 3. Identificación y planteamiento del problema

Problema central: dificultad para concretar intercambios de objetos sin coincidencia horaria, con una constancia suficiente de recepción, custodia y entrega.

| Causas a investigar | Manifestación | Efecto posible |
|---|---|---|
| Agendas incompatibles. | Encuentros reprogramados o esperas. | Tiempo y coordinación adicionales. |
| Resguardo sin registro. | Terceros reciben objetos sin constancia uniforme. | Incertidumbre sobre responsable y destinatario. |
| Verificación insuficiente. | Se entrega por nombre o teléfono sin autorización comprobable. | Error de entrega y dificultad de reconstrucción. |
| Falta de información de disponibilidad. | No se conoce si el objeto llegó o sigue guardado. | Viajes innecesarios y consultas repetidas. |

Pregunta del proyecto: ¿cómo diseñar y evaluar una plataforma y un procedimiento de custodia asistida que permitan recibir y entregar objetos en momentos distintos, con autorización y trazabilidad, usando recursos existentes?

## 4. Justificación

La propuesta separa temporalmente al emisor del destinatario y establece responsabilidades durante la custodia. Su valor esperado es reducir incertidumbre, errores y esfuerzo de coordinación. La validación debe comprobar si ese valor resulta suficiente frente al costo, la distancia al punto y su horario.

El enfoque asistido hace viable investigar la solución con infraestructura disponible. La seguridad depende de controles digitales, organización del espacio y actuación del personal; no se promete protección física automática ni eliminación de pérdidas.

## 5. Objetivos

**Objetivo general:** desarrollar y evaluar un prototipo de plataforma web para gestionar la custodia temporal asistida y el intercambio asíncrono de objetos, mediante identificación de usuarios, autorización de entrega, registro de operaciones y notificaciones, utilizando equipos y espacio existentes.

| ID | Objetivo específico | Entregable y comprobación |
|---|---|---|
| OE-01 | Analizar necesidades y requisitos funcionales, operativos y de seguridad. | Diagnóstico, requisitos y validación de escenarios con usuarios y operador. |
| OE-02 | Diseñar el proceso de atención, la organización del punto y la arquitectura del software. | Flujo operativo, distribución funcional y modelos de arquitectura y datos. |
| OE-03 | Desarrollar identificación y autorización digital de las entregas. | Autenticación, permisos y credenciales con pruebas de rechazo y uso único. |
| OE-04 | Implementar registro, recepción, ubicación, retiro y devolución. | Ciclo persistido y ensayo de inventario con objetos de prueba. |
| OE-05 | Integrar notificaciones e historial para usuarios y personal. | Avisos en plataforma, correo configurable y eventos asociados al actor. |
| OE-06 | Evaluar funcionamiento, usabilidad, seguridad y viabilidad inicial. | Protocolo, resultados del piloto y evaluación de demanda, costos y capacidad. |

## 6. Alcance y delimitación

Se propone un punto piloto en el área urbana de La Paz, sujeto a disponibilidad de un espacio autorizado por su responsable. La cantidad de ubicaciones se levanta físicamente; no se asume capacidad nacional.

Se gestionan objetos admitidos por tamaño y condiciones acordadas del punto. Una operación representa un bulto identificable, un emisor, un destinatario y una ubicación exclusiva mientras se encuentra bajo custodia. El registro previo no reserva espacio; la aceptación se confirma al recibir el objeto.

Se incluyen cuentas generales, gestión de puntos, recepción, autorización, entrega, devolución asistida, cobro del servicio, avisos, incidencias, auditoría y reportes. Quedan fuera transporte, compra o venta de productos, cobro contra entrega a favor de terceros, liquidaciones bancarias, consolidación multitienda y dispositivos automatizados.

La atención ocurre dentro del horario publicado. Una cuenta o código no acredita por sí solo identidad civil; el procedimiento establece comprobación visual y registro mínimo, sin almacenar imágenes documentales en el prototipo.

## 7. Solución y operación

El emisor y el destinatario tienen cuentas activas y contacto comprobado por correo o verificación presencial documentada. El emisor registra el objeto y selecciona al destinatario. El operador verifica admisibilidad, disponibilidad y tarifa, cobra el servicio y registra la recepción y ubicación en una transacción.

El destinatario consulta su bandeja y genera una credencial temporal. En el punto presenta el código; el operador verifica la operación y al destinatario. El sistema autoriza la entrega y conserva una operación en curso. Después de entregar físicamente el bulto, el operador confirma el retiro, consume la autorización y libera la ubicación. Las diferencias o cortes posteriores a una entrega se gestionan como incidencias.

El plazo vencido no libera una ubicación ocupada ni autoriza disposición del objeto. Se informa al usuario y se tramita prórroga o devolución. La política exacta de permanencia se establece antes del piloto.

## 8. Metodología

La investigación es exploratoria y aplicada. Se proponen diez entrevistas basadas en episodios recientes y observación de sesiones de atención; es una muestra por conveniencia, sin representatividad estadística. La evaluación operativa propuesta comprende treinta ciclos con objetos de prueba y cinco sesiones de usabilidad. Estas cantidades son un diseño inicial que puede ampliarse según resultados.

La ingeniería se organiza en iteraciones con requisitos, modelos, implementación y pruebas de un flujo completo. Pressman y Maxim, Cockburn, Larman, Evans, Martin, Fowler y Patton aportan herramientas concretas. La [justificación metodológica](../metodologia/01_marcos_y_aplicacion.md) explica su selección y límites.

## 9. Factibilidad y evaluación

La evaluación distingue disponibilidad técnica de recursos, factibilidad operativa del personal y factibilidad económica del servicio. Se levantan tiempos por recepción y retiro, permanencia media, ocupación, costos fijos y variables y precio aceptable.

No se fijan ingresos o rentabilidad sin datos. El [modelo económico](../negocio/02_demanda_costos_y_evaluacion.md) ofrece fórmulas, sensibilidad y una plantilla de captura. Las condiciones del emplazamiento y del servicio requieren investigación específica antes de atención al público; este perfil no emite conclusiones jurídicas.

## 10. Cronograma propuesto

Se plantean seis iteraciones de una semana como referencia de planificación: descubrimiento y alcance; identidad y contratos; registro y recepción; autorización y retiro; recuperación y comunicaciones; ensayo y evaluación. La duración es una estimación, no un compromiso sin conocer capacidad del equipo. El [plan](../gestion/02_plan_implementacion.md) define dependencias y entregables.

## 11. Resultados esperados y límites

Se espera obtener un prototipo que registre quién recibió, dónde se almacenó, quién autorizó y quién entregó cada objeto. La aceptación requiere que usuarios ajenos sean rechazados, que una ubicación no se asigne dos veces y que el historial permita reconstruir una operación y sus incidencias.

El estudio permitirá decidir si el servicio merece continuar, ajustar horario o segmento, modificar tarifas o detenerse. La conclusión actual es de diseño: existe una formulación coherente con la restricción. La eficacia, demanda y rentabilidad permanecen pendientes de medición.

## 12. Referencias y anexos

La [bibliografía verificada](../metodologia/02_bibliografia_verificada.md) y el [archivo del perfil original](../../referencias/original/PERFIL_ORIGINAL_BUZON_XPRESS.docx) completan los antecedentes. Se adjuntan requisitos, modelos, wireframes, manual, plan de pruebas e instrumentos de investigación mediante el índice del [proyecto](../../README.md).
