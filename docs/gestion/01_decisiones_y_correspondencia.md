# Decisiones y correspondencia documental

Estado: diseño documental. Autoridad de alcance: instrucción del usuario del 26 de octubre de 2026, que excluye lockers inteligentes y hardware externo.

## 1. Decisiones de alcance

| ID | Decisión | Motivo y consecuencia |
|---|---|---|
| D-01 | Custodia asistida por operador. | El control digital autoriza una entrega humana; el sistema no bloquea ni abre un espacio físico. |
| D-02 | Equipos y espacio existentes. | No hay requerimiento de compra o integración de dispositivos. Se ingresa el código desde un teclado o pantalla disponibles. |
| D-03 | Conservar el intercambio asíncrono. | Emisor y destinatario no necesitan coincidir, pero ambos respetan los horarios del punto. |
| D-04 | Usuario general con participación por operación. | No es obligatorio tener una tienda, ser vendedor ni registrar un precio de producto. |
| D-05 | Una custodia activa por ubicación interna. | Simplifica inventario y evita mezcla de objetos en la primera versión; la capacidad real se levanta en el punto. |
| D-06 | Registro previo sin reserva de capacidad. | La ubicación se asigna al recibir físicamente el objeto. La pantalla lo explica; no promete espacio por prerregistrar. |
| D-07 | Servicio en un solo punto por operación. | No se incluye transporte entre puntos ni traslado interdepartamental. |
| D-08 | Cobro del servicio de custodia al depositar. | La tarifa cubre un plazo contratado; la prórroga se gestiona antes del retiro. No hay intermediación de ventas, COD ni liquidaciones a comerciantes. |
| D-09 | Acciones de inventario con conexión. | Sin servidor no se autorizan recepciones, retiros, devoluciones ni cobros operativos; un incidente posterior a una entrega real se reconcilia. |
| D-10 | Avisos en plataforma; correo como canal de software. | No se requiere WhatsApp, SMS, un teléfono conectado o equipos de terceros. El correo depende de configurar un servicio SMTP y se prueba antes del piloto. |
| D-11 | Un código de retiro no demuestra identidad civil. | Autoriza una operación concreta. La comprobación visual del destinatario y la actuación del personal forman parte del procedimiento. |
| D-12 | Auditoría con estado relacional actual. | Una tabla de eventos no convierte al sistema en Event Sourcing; tampoco es inalterable frente a un administrador de base de datos. |

La prohibición de hardware no se interpreta como prohibición de software de correo o alojamiento. El piloto puede ejecutarse en los equipos existentes; el modelo de despliegue se decide según disponibilidad. No se impone un proveedor contratado.

## 2. Cambio explícito del perfil

| Intención original | Adaptación vigente |
|---|---|
| Resolver incompatibilidad de horarios. | Depósito y retiro separados, dentro del horario del punto. |
| Resguardo formal y constancia. | Operador responsable, ubicación restringida al personal, recepción y comprobante digitales. |
| Arquitectura física y tecnológica de lockers. | Diseño del proceso y distribución funcional del espacio existente, más arquitectura web. |
| Control de acceso a compartimentos. | Autenticación, permisos sobre custodias y autorización de entrega al operador. |
| Registro y seguimiento. | Historial de recepción, verificación, entrega, devolución, cobros e incidencias. |
| Notificaciones. | Bandeja interna y correo con registro de intentos. |
| Validación del prototipo. | Pruebas de software y ensayo supervisado del servicio asistido. |

El título y los objetivos se reformulan porque la nueva solución no puede afirmar que implementa lockers inteligentes. La autorización del usuario ya establece este cambio; no se deja condicionado a otra aprobación.

## 3. Correspondencia completa

| Archivo del proyecto actual | Equivalente vigente | Tratamiento |
|---|---|---|
| `README.md` | [README](../../README.md) | Índice, alcance y estado documental. |
| `backend/README.md`, `backend/alembic/README` y configuración SQL/Compose | [Guía técnica](../ingenieria/08_guia_tecnica_y_despliegue.md) | Entornos, configuración, migraciones y recuperación propuestos; no un despliegue ya ejecutado. |
| `docs/negocio/BuzonExpress_Formulacion_Negocio.md` | [Formulación](../negocio/BuzonExpress_Formulacion_Negocio.md) | JTBD, lienzos, ERAC, cadena de valor y adopción aplicados a custodia. |
| `docs/ingenieria/BuzonExpress_Especificacion_Software.md` | [Especificación](../ingenieria/BuzonExpress_Especificacion_Software.md) | Requisitos, FURPS+, límites, historias y criterios verificables. |
| `docs/ingenieria/01_modelado_analisis_pressman.md` | [Análisis](../ingenieria/01_modelado_analisis_pressman.md) | Escenarios, clases, CRC, estados, secuencia y flujos. |
| `docs/ingenieria/02_modelado_diseno_ui.md` | [UI](../ingenieria/02_modelado_diseno_ui.md) | Reglas de Mandel, navegación y evaluación de interfaces. |
| `docs/ingenieria/03_modelado_datos_arquitectura.md` | [Datos y arquitectura](../ingenieria/03_modelado_datos_arquitectura.md) | Entidades, diccionario, integridad, componentes y concurrencia. |
| `docs/ingenieria/04_propuestas_wireframes_identidad.md` | [Identidad](../ingenieria/04_propuestas_wireframes_identidad.md) | Tres alternativas comparadas y selección razonada. |
| `docs/ingenieria/05_wireframes_estructurales_bn.md` | [Wireframes estructurales](../ingenieria/05_wireframes_estructurales_bn.md) | Pantallas públicas, de usuario, operador y administrador. |
| `docs/ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md` | [Casos de uso](../ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md) | Catálogo y doce casos expandidos. |
| `docs/wireframes/landing_page_wireframe.jpg` | [Landing SVG](../wireframes/landing_page_wireframe.svg) y PNG | Flujo asistido, horarios y alcance. |
| `docs/wireframes/corporate_identity_mockup.jpg` | [Identidad SVG](../wireframes/corporate_identity_mockup.svg) y PNG | Confianza apoyada en procesos comprobables. |
| `docs/wireframes/manifesto_grid_mockup.jpg` | [Manifiesto SVG](../wireframes/manifesto_grid_mockup.svg) y PNG | Políticas de custodia y comunicación. |
| `docs/wireframes/bw_wireframes_suite.jpg` | [Suite SVG](../wireframes/bw_wireframes_suite.svg) y PNG | Prerregistro, consultas, recepción y administración. |
| `docs/wireframes/bw_auth_terminal_wireframes.jpg` | [Acceso y terminal SVG](../wireframes/bw_auth_terminal_wireframes.svg) y PNG | Sesión, código y confirmación de entrega humana. |

Se añaden perfil, revisión de metodologías, bibliografía, demanda y costos, manual operativo, API, decisiones, plan, trazabilidad y pruebas. Los antecedentes originales se guardan fuera del árbol normativo `docs/`.

## 4. Qué se reutiliza del código existente

React, TypeScript, FastAPI, PostgreSQL y la separación por capas son una base viable. Se reutilizan componentes visuales e ideas de puntos, usuarios y registro de eventos tras revisar sus contratos. Se reemplazan autenticación de demostración, respuestas públicas con PIN, métricas simuladas y acciones locales presentadas como operaciones reales.

El modelo comercial de `seller_id`, COD y consolidación no se traslada automáticamente. La migración debe identificar emisores y destinatarios, inventariar objetos físicamente y conservar antecedentes. No se importan contraseñas locales ni PIN expuestos. Ningún documento de esta carpeta acredita que esos cambios ya estén implementados.
