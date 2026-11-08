# BUZON Xpress final

**Línea base 1.1 · 7 de noviembre de 2026 · Arch WSL**

BUZON Xpress organiza la custodia temporal y el intercambio asíncrono de objetos. El emisor registra y deja el objeto, el operador lo guarda en una ubicación interna y el destinatario lo recoge tras la comprobación digital y presencial. El punto usa su espacio y sus equipos existentes. El personal realiza la recepción y la entrega.

## 1. Documentación

| Para consultar | Fuente |
| --- | --- |
| Alcance, objetivos y justificación | [Perfil](docs/perfil/Perfil_Proyecto_BUZON_Xpress.md) y [decisiones](docs/gestion/01_decisiones_y_correspondencia.md) |
| Negocio, demanda y costos | [Formulación](docs/negocio/BuzonExpress_Formulacion_Negocio.md) y [evaluación](docs/negocio/02_demanda_costos_y_evaluacion.md) |
| Requisitos y reglas | [Especificación](docs/ingenieria/BuzonExpress_Especificacion_Software.md) y [trazabilidad](docs/gestion/03_matriz_trazabilidad.md) |
| Flujos y pantallas | [Casos de uso](docs/ingenieria/06_casos_de_uso_alto_nivel_y_expandidos.md), [diseño UI](docs/ingenieria/02_modelado_diseno_ui.md) y [wireframes](docs/wireframes/README.md) |
| Contratos y persistencia | [OpenAPI](docs/ingenieria/anexos/openapi.yaml), [SQL](docs/ingenieria/anexos/modelo_propuesto.sql) y [diccionario](docs/ingenieria/03_modelado_datos_arquitectura.md) |
| Operación y aceptación | [Manual](docs/operacion/01_manual_operativo.md), [plan de validación](docs/validacion/01_plan_validacion.md) y [plan de implementación](docs/gestion/02_plan_implementacion.md) |
| Documentos para presentar | [Perfil y dossier de la edición 1.0 en Word, PDF y HTML](entregables/README.md) |

La base documental proviene de `../buzon-xpress-reformulado`. El código de `../buzon-xpress` es el antecedente ejecutable de paquetería, útil para evaluar componentes reutilizables. El perfil, la especificación y el contrato de esta carpeta gobiernan la futura implementación de custodia.

## 2. Estructura y verificación

[Mapa de archivos, límites de cada capa y orden de implementación](docs/gestion/04_estructura_de_archivos.md).

El árbol inicial reserva espacio para React/TypeScript, FastAPI, SQLAlchemy y Alembic. La base de referencia se reconstruyó a partir del diccionario de 156 columnas y las reglas documentadas. Su destino es una base nueva. La primera migración del producto se escribirá como parte de la fase de identidad.

Ejecutar en WSL:

```bash
cd /home/oswi/Proyectos/buzon-xpress-final
./verificar.sh
```

La comprobación valida enlaces, trazabilidad, OpenAPI y el SQL en PostgreSQL 16 desechable. [Resultado documental](docs/validacion/03_verificacion_linea_base.md) · [Herramientas](herramientas/README.md)
