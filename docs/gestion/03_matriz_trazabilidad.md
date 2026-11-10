# Matriz de trazabilidad

Estado: matriz de trazabilidad de la solución implementada. Relaciona requisitos, casos de uso, datos, pantallas, API y pruebas; no equivale a la aceptación del servicio ni a la autorización de un piloto.

La verificación local más reciente del código en `9405ed7` (2026-11-10) ejecutó la suite de backend con PostgreSQL 16 desechable, carga y restauración local. En un clon limpio, el frontend pasó sus cinco pruebas y compiló para producción. Los resultados por caso conservan su versión y fecha de evidencia en el [registro de pruebas](../validacion/resultados_pruebas.csv); los ensayos con personas y en el punto de servicio siguen pendientes o parciales.

## Objetivos del perfil

| Objetivo | Requisitos principales | Evidencia complementaria |
|---|---|---|
| OE-01 | RF-03, RF-04, RF-14 | Diagnóstico, entrevistas y reglas revisadas con el personal. |
| OE-02 | RF-05, RF-16, RNF-06, RNF-11 | Arquitectura, diccionario, organización del punto y wireframes. |
| OE-03 | RF-01, RF-02, RF-07, RF-08 | Pruebas de identidad, permisos, vigencia y uso único. |
| OE-04 | RF-03, RF-04, RF-05, RF-09, RF-10, RF-12 | Ciclo integrado y conciliación material. |
| OE-05 | RF-06, RF-11, RF-15 | Avisos, eventos y consulta limitada. |
| OE-06 | RF-17, RF-18 y RNF-01 a RNF-12 | Piloto, resultados, recuperación y evaluación económica. |

## Requisitos funcionales

| Requisito | Caso | Datos | Pantalla | API | Prueba |
|---|---|---|---|---|---|
| RF-01 | CU-01 | users, sessions | UI-03, UI-04 | /auth/register; /auth/login; /auth/logout | T-01 |
| RF-02 | CU-01 | users, staff_assignments, sessions | UI-03, UI-08 | /auth/me | T-02 |
| RF-03 | CU-02 | custody_orders, custody_events | UI-06 | /custodies | T-03 |
| RF-04 | CU-03 | custody_orders, storage_assignments, storage_locations, service_payments | UI-08 | /custodies/{custody_id}/receive | T-04 |
| RF-05 | CU-03 | storage_assignments, storage_locations | UI-08 | /inventory | T-05 |
| RF-06 | CU-04 | custody_orders, custody_events | UI-02, UI-05, UI-07 | /custodies/{custody_id}; /public-tracking/{reference} | T-06 |
| RF-07 | CU-05 | pickup_credentials | UI-07 | /custodies/{custody_id}/credentials | T-07 |
| RF-08 | CU-06 | pickup_credentials, pickup_authorizations, custody_orders | UI-08 | /custodies/{custody_id}/verify | T-08 |
| RF-09 | CU-07 | handovers, pickup_authorizations, storage_assignments, custody_orders | UI-08 | /custodies/{custody_id}/handover | T-09 |
| RF-10 | CU-10 | recovery_requests, pickup_authorizations, handovers | UI-09 | /custodies/{custody_id}/return-authorization; /custodies/{custody_id}/return-handover | T-10 |
| RF-11 | CU-08 | notifications | UI-12 | /notifications | T-11 |
| RF-12 | CU-09 | tariff_versions, service_payments, custody_orders | UI-08 | /points/{point_id}/quote; /custodies/{custody_id}/receive; /custodies/{custody_id}/extend | T-12 |
| RF-13 | CU-09 | custody_orders, notifications, service_payments | UI-07, UI-08 | /custodies/{custody_id}/extend | T-13 |
| RF-14 | CU-10 | incidents, recovery_requests | UI-09 | /custodies/{custody_id}/incidents; /recovery-requests; /recovery-requests/{request_id}/decision | T-14 |
| RF-15 | CU-12 | custody_events | UI-11 | /audit/events | T-15 |
| RF-16 | CU-11 | service_points, storage_locations, staff_assignments, tariff_versions | UI-10 | /admin/points; /admin/locations; /admin/staff-assignments; /admin/tariffs | T-16 |
| RF-17 | CU-12 | custody_orders, custody_events, handovers, incidents | UI-11 | /reports | T-17 |
| RF-18 | CU-07 | idempotency_keys, handovers | UI-08, UI-09 | /custodies/{custody_id}/handover; /custodies/{custody_id}/abort-handover | T-18 |

## Calidad

| Requisito | Categoría | Prueba | Estado |
|---|---|---|---|
| RNF-01 | Usabilidad | T-19 | Pendiente: falta el ensayo con cinco participantes del servicio. |
| RNF-02 | Desempeño | T-20 | Parcial: medición local de `/reports`; faltan otras consultas y el entorno piloto. |
| RNF-03 | Seguridad | T-21 | Aprobada en las comprobaciones técnicas locales registradas. |
| RNF-04 | Confiabilidad | T-22 | Parcial: se verificó una reversión transaccional; faltan otros flujos de salida. |
| RNF-05 | Recuperación | T-23 | Parcial: restauración local verificada; falta medirla en la infraestructura del punto. |
| RNF-06 | Mantenibilidad | T-24 | Parcial: comprobaciones técnicas; falta completar aislamiento y pruebas unitarias de transiciones. |
| RNF-07 | Accesibilidad | T-25 | Parcial: revisión inicial en Edge; falta cubrir teclado, contraste y lectores de pantalla. |
| RNF-08 | Observabilidad | T-26 | Parcial: correlación y proyección verificadas; falta revisar el despliegue y sus logs. |
| RNF-09 | Comunicaciones | T-27 | Parcial: bandeja y STARTTLS local comprobados; falta medir el transporte del punto. |
| RNF-10 | Concurrencia | T-28 | Aprobada en la prueba local de recepción simultánea. |
| RNF-11 | Restricción | T-29 | Aprobada para el recorrido sintético; falta repetirlo con personal y equipos del piloto. |
| RNF-12 | Privacidad | T-30 | Parcial: proyecciones revisadas; faltan política de conservación y respuesta de alta duplicada. |

## Control de cambios

Una modificación de una regla exige revisar requisito, caso, modelo, contrato, interfaz y prueba relacionados. Las reglas RN-01 a RN-14 se aplican transversalmente según la especificación y el manual. La prohibición de hardware corresponde a D-01, D-02 y RNF-11.

Documentos: [especificación](../ingenieria/BuzonExpress_Especificacion_Software.md), [casos](../ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md), [datos](../ingenieria/03_modelado_datos_arquitectura.md), [API](../ingenieria/07_contratos_api_y_seguridad.md), [UI](../ingenieria/02_modelado_diseno_ui.md) y [pruebas](../validacion/01_plan_validacion.md).
