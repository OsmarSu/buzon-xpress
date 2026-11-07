# Wireframes estructurales y especificación de pantallas

Estado: prototipos estáticos. Principios: jerarquía de tareas, etiquetas consistentes y confirmación explícita de actos humanos. Las [cinco láminas](../wireframes/README.md) incluyen todos los recorridos centrales en SVG y PNG.

## 1. Galería y cobertura

| Lámina | Cobertura |
|---|---|
| `landing_page_wireframe` | UI-01 y acceso a consulta pública. |
| `corporate_identity_mockup` | Identidad, condiciones, horario y proceso. |
| `manifesto_grid_mockup` | Ejemplos, políticas y explicación del servicio. |
| `bw_wireframes_suite` | UI-02, UI-05, UI-06, UI-07, UI-09 y UI-10/11. |
| `bw_auth_terminal_wireframes` | UI-03, UI-04, UI-08 y acceso a UI-12. |

Son equivalentes reformulados de las cinco imágenes originales. No incluyen control de puertas, lectores o retiros desatendidos.

## 2. UI-01: portada

Orden: marca y navegación; propuesta y horario; registrar o consultar; tres pasos; condiciones y tamaños; contacto del punto. El texto “Atención por personal del punto” debe ser visible antes del primer llamado a la acción.

```text
BUZON Xpress           Cómo funciona | Puntos | Acceder
Deja un objeto hoy; permite que lo recojan después.
Custodia atendida. Consulta el horario antes de acudir.
[Registrar objeto] [Consultar estado]
1 Registra   2 Déjalo con el operador   3 Retiro autorizado
Condiciones | Tamaños y plazos | Responsable de atención
```

## 3. UI-02: seguimiento público

Entrada: referencia pública opaca, distinta de guía y credencial. Salida: recibido / pendiente / finalizado, nombre y horario del punto y fecha general si corresponde. No muestra nombre, teléfono, descripción, ubicación interna, código o cronología privada.

Estados: referencia vacía, no encontrada, consulta limitada y servicio no disponible. “Acceder a mi cuenta” permite ver detalles si existe autorización.

## 4. UI-03 y UI-04: acceso y cuenta

Campos: correo, contraseña y nombre/contacto en registro. No permite elegir administrador u operador desde un registro público. La verificación de contacto explica si se realizará por correo o presencialmente con personal.

El error de acceso es genérico. Se indica sesión vencida y se ofrece recuperar cuenta mediante el procedimiento previsto; no se incluyen contraseñas universales de demostración.

## 5. UI-05 y UI-06: mis custodias y registro

Lista con pestañas “Deposité” y “Recibiré”; filtros por estado y fecha. Cada tarjeta muestra referencia privada, punto, estado y plazo. Los totales se calculan con datos reales y tienen periodo.

Formulario: punto, contacto exacto del destinatario, descripción externa y tamaño. Resumen antes de crear. La advertencia de capacidad queda junto al botón: “El espacio se confirma al recibir el objeto”. No aparece un selector de casillero para usuarios.

## 6. UI-07: detalle privado y credencial

Orden: estado, siguiente acción, horario/punto, plazo, descripción, participantes permitidos e historial. La credencial solo se ofrece al destinatario de esa custodia y se muestra una vez, con vigencia. Al salir se elimina de memoria de la pantalla; no se guarda en almacenamiento persistente del navegador.

Los comprobantes de recepción y entrega muestran identificador, actor responsable y fecha. “Solicitud de cambio o incidencia” abre un expediente; no altera inmediatamente al destinatario.

## 7. UI-08: terminal

```text
Operador autenticado | Punto asignado | Conexión comprobada
[Recepción] [Retiro] [Inventario] [Incidencias]

RECEPCIÓN: guía -> revisar bulto -> ubicación -> tarifa y cobro
[Confirmar recepción]

RETIRO: guía + código + comprobación visual
[Verificar autorización]
Autorizado para entregar: bulto y ubicación internos
[Confirmar que ya entregué el objeto] [No entregado]
```

La primera acción de retiro no dice “entregado”. Un fallo después de entregar físicamente muestra “Confirmación pendiente; no repetir entrega”. Se conserva una referencia de operación para seguimiento, sin almacenar el código en logs o colas locales.

## 8. UI-09: incidencias y recuperaciones

Lista por prioridad y punto; detalle con hechos, actor, custodia y acciones. Un aprobador ve solicitante y evidencia antes de decidir. Si ambos son la misma persona, el botón queda inhabilitado y el servidor rechaza la decisión.

La confirmación de conciliación distingue “objeto permanece en el punto” de “entrega realizada fuera de confirmación”. Se solicita justificación; un cambio de estado nunca borra el hecho previo.

## 9. UI-10, UI-11 y UI-12: administración, auditoría y avisos

Administración: puntos, horarios, ubicaciones y personal. Una ubicación ocupada requiere tratamiento previo para retirarla de servicio. Tarifas: nueva versión con fecha de vigencia y simulación del cálculo, sin editar contratos históricos.

Auditoría: periodo, punto, tipo y correlación; exportación sin secretos. Indicadores: numerador, denominador, rango de fechas y nota de calidad de datos. Avisos: eventos pertinentes al usuario, estado de lectura y enlace privado; el correo no incluye el código de retiro.

## 10. Revisión estructural

Cada pantalla debe permitir identificar el estado real, el siguiente paso, el responsable de actuar y el resultado de un error. El protocolo de usabilidad comprueba esas preguntas con tareas concretas. Los wireframes no se interpretan como validación ya ejecutada.
