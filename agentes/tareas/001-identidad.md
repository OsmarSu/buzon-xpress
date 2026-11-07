# BZ-001 · Identidad y alcance

Estado: pendiente. Fase 2 del [plan de implementación](../../docs/gestion/02_plan_implementacion.md). Cubre RF-01, RF-02, RN-01 y RN-13.

## Entrega inicial

Construir la primera sección vertical con identidad, sesión y permisos en servidor. Definir migración de identidad con Alembic desde una base vacía, crear cuentas sintéticas y conectar la pantalla de acceso a la API. Usar [especificación](../../docs/ingenieria/BuzonExpress_Especificacion_Software.md), [contrato](../../docs/ingenieria/anexos/openapi.yaml) y [reglas de seguridad](../../docs/ingenieria/07_contratos_api_y_seguridad.md).

1. **Coordinación**. Revisar los endpoints `/auth/register`, `/auth/login`, `/auth/logout` y `/auth/me`, sus códigos de error, sesión, verificación y alcance. Precisar qué parte de contacto y recuperación entra en esta entrega.
2. **Backend**. Trabajar en `backend/app`, `backend/migrations` y `backend/tests`. Crear migración, verificador de contraseña adaptativo, sesión revocable y decisiones de acceso por rol y punto.
3. **Frontend**. Trabajar en `frontend/src` y `frontend/tests` después de acordar DTO y errores. Conectar inicio, cierre de sesión y lectura de usuario actual.
4. **QA**. Comprobar sesión válida, cierre y revocación, solicitud sin autenticación, permiso insuficiente y acceso fuera del punto asignado. Verificar respuestas y logs sin credenciales.

La persona responsable integra cada rama después de revisar los cambios, aplicar la migración en una base de ensayo separada y repetir las pruebas. La siguiente entrega introduce registro y recepción de una custodia sintética.
