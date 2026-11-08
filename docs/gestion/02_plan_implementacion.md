# Plan de implementación y transición

Plan de implementación de la línea base. El [registro de pruebas](../validacion/resultados_pruebas.csv) recoge el estado técnico de las entregas. Duración de referencia: seis iteraciones de una semana; ajustar según equipo y disponibilidad del punto.

## 1. Orden y dependencias

| Iteración | Entregable | Dependencia | Aceptación |
|---|---|---|---|
| 1 | Diagnóstico, alcance, vocabulario y diseño de servicio. | Acceso a participantes y punto. | Hipótesis identificadas, capacidad levantada y reglas revisadas con personal. |
| 2 | Identidad, permisos, contratos y migración inicial aislada. | Diseño de participantes y roles. | Registro, contacto, sesión y pruebas de acceso ajeno y alcance. |
| 3 | Registro, tarifa, recepción e inventario integrados. | Identidad y modelo de datos. | Una recepción persistida; prueba concurrente y falla transaccional sin duplicados. |
| 4 | Credencial, verificación, entrega y comprobante. | Custodia e inventario. | Retiro completo, código reutilizado rechazado y recuperación ante respuesta perdida. |
| 5 | Avisos, vencimientos, incidencias y devolución. | Flujo de salida estable. | Fallo de correo visible, devolución aprobada y conciliación ensayadas. |
| 6 | Ensayo, usabilidad y evaluación económica inicial. | Flujos críticos y operación preparados. | Informe con evidencia, limitaciones y decisión de continuidad. |

No se dedica una iteración completa a una landing sin un flujo comprobable. La primera demostración integral utiliza datos sintéticos y registra, recibe, autoriza y confirma un objeto de prueba.

## 2. Trabajo sobre la base técnica existente

1. Preparar un repositorio o copia de desarrollo independiente; conservar el original como antecedente.
2. Sustituir las cuentas locales y los permisos de interfaz por identidad y autorización en servidor.
3. Adaptar paquetes a custodias y separar credencial, autorización, asignación y comprobante.
4. Implementar una unidad de trabajo por operación; retirar `commit` dispersos.
5. Conectar pantallas a API y eliminar respuestas ficticias fuera del modo de demostración explícito.
6. Incorporar avisos persistidos y tarea de correo configurable.
7. Introducir migraciones, entorno de pruebas y copias reproducibles.
8. Ejecutar escenarios funcionales, negativos y operativos antes de usar objetos reales.

Las entregas se contrastan con el contrato y la evidencia de pruebas por módulo.

## 3. Migración de datos

El esquema propuesto parte de una base vacía. Para migrar operaciones existentes, usar una copia de ensayo y un informe de correspondencia: vendedor a emisor, comprador a destinatario comprobado, paquete a custodia, punto a ubicación y estado de posesión a inventario físico.

No inferir que todos los compradores tienen cuenta, ni convertir automáticamente datos de ventas en autorizaciones de entrega. Los objetos presentes se cotejan con personal y responsable. Diferencias se registran como incidencias.

No migrar contraseñas planas o PIN de demostración. Revocar credenciales antiguas y establecer nuevas cuentas o recuperación verificable. Conservar los antecedentes comerciales en un archivo separado si corresponde, sin reutilizar COD y liquidaciones como cobros de custodia.

Criterios de cierre: conteos explicados, ninguna custodia activa sin ubicación física comprobada, ninguna ubicación duplicada, historial conservado y ensayo de reversión sobre la copia. No se ejecuta migración sobre datos actuales por producir esta documentación.

## 4. Calidad de cada entrega

Terminado significa: requisitos relevantes revisados, caso de uso cubierto, código integrado con persistencia, errores visibles, pruebas pertinentes ejecutadas y documento actualizado. Una pantalla con datos locales no satisface esa definición.

El flujo de cambios incluye revisión de requisitos, migración, pruebas, compilación, entorno de ensayo y procedimiento de recuperación. Los despliegues se identifican por versión. Las métricas de desarrollo son tiempo de entrega del cambio, fallas y recuperación; las métricas de servicio se calculan aparte.

## 5. Riesgos y respuesta

| Riesgo | Señal | Respuesta |
|---|---|---|
| No hay segundo responsable para excepciones. | Solicitudes sin decisión. | Mantener custodia y acordar horarios de revisión; no habilitar autoaprobación. |
| Capacidad o personal insuficientes. | Rechazos y espera creciente. | Ajustar admisión, horario y alcance; revisar economía del punto. |
| Entrega humana sin confirmación. | Autorización en curso y objeto ausente. | Bloqueo, evidencia y conciliación supervisada. |
| Datos de mercado débiles. | Opiniones sin episodios o usos. | Ampliar entrevistas o replantear segmento, sin proyectar demanda ficticia. |
| Exposición de secretos en código heredado. | PIN o contraseñas en respuestas y logs. | Reemplazar contrato y revocar credenciales; pruebas negativas antes del piloto. |
| Falta de conectividad. | Operaciones interrumpidas. | Suspender mutaciones, informar y recuperar de manera controlada. |

## 6. Decisiones pendientes de datos

Ubicación exacta, tamaño físico admisible, horario, tarifa, duración contractual, política final de permanencia, responsable de revisión y conservación de datos. Están documentadas como parámetros a levantar. No impiden completar el diseño ni se sustituyen por cifras inventadas.
