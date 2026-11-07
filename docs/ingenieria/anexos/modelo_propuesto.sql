-- BUZON Xpress reformulado. Esquema de referencia para una base nueva.
-- Reconstrucción a partir del diccionario y las reglas de la línea base 1.0.
-- Las transiciones y autorizaciones requieren implementación en la aplicación.

BEGIN;

CREATE TABLE users (
    id UUID PRIMARY KEY, -- Identificador de cuenta.
    email VARCHAR(254) NOT NULL UNIQUE, -- Correo normalizado; no directorio público.
    full_name VARCHAR(160) NOT NULL, -- Nombre declarado del participante.
    phone VARCHAR(24), -- Contacto normalizado opcional.
    password_hash TEXT NOT NULL, -- Verificador adaptativo; nunca contraseña plana.
    role VARCHAR(16) NOT NULL CHECK (role IN ('USUARIO','OPERADOR','ADMIN','AUDITOR')), -- Permiso global.
    contact_verified_at TIMESTAMPTZ, -- Comprobación por correo o presencial.
    contact_verification_hash CHAR(64), -- Hash de enlace de verificación pendiente.
    verification_expires_at TIMESTAMPTZ, -- Vigencia del enlace de comprobación.
    password_reset_hash CHAR(64), -- Hash de enlace de recuperación de cuenta.
    password_reset_expires_at TIMESTAMPTZ, -- Vigencia de recuperación de cuenta.
    is_active BOOLEAN NOT NULL DEFAULT TRUE, -- Habilitación de cuenta.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP -- Alta.
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY, -- Sesión interna.
    user_id UUID NOT NULL REFERENCES users(id), -- Cuenta propietaria.
    token_hash CHAR(64) NOT NULL UNIQUE, -- Hash del token de sesión.
    expires_at TIMESTAMPTZ NOT NULL, -- Límite absoluto de sesión.
    revoked_at TIMESTAMPTZ, -- Revocación explícita.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP -- Inicio.
);

CREATE TABLE service_points (
    id UUID PRIMARY KEY, -- Punto atendido.
    code VARCHAR(20) NOT NULL UNIQUE, -- Identificación pública del punto.
    name VARCHAR(120) NOT NULL, -- Nombre publicado.
    address TEXT NOT NULL, -- Dirección del servicio.
    opening_hours JSONB NOT NULL, -- Horario publicado y excepciones.
    timezone VARCHAR(64) NOT NULL DEFAULT 'America/La_Paz', -- Zona para presentación.
    is_active BOOLEAN NOT NULL DEFAULT TRUE -- Atención habilitada.
);

CREATE TABLE staff_assignments (
    id UUID PRIMARY KEY, -- Asignación de personal.
    user_id UUID NOT NULL REFERENCES users(id), -- Operador, administrador o auditor.
    point_id UUID NOT NULL REFERENCES service_points(id), -- Alcance permitido.
    is_active BOOLEAN NOT NULL DEFAULT TRUE, -- Vigencia operativa.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Alta.
    UNIQUE (user_id, point_id)
);

CREATE TABLE storage_locations (
    id UUID PRIMARY KEY, -- Referencia del espacio existente.
    point_id UUID NOT NULL REFERENCES service_points(id), -- Punto de pertenencia.
    code VARCHAR(24) NOT NULL, -- Código interno ingresado manualmente.
    size_category VARCHAR(12) NOT NULL CHECK (size_category IN ('PEQUENO','MEDIANO','GRANDE')), -- Capacidad declarada.
    state VARCHAR(20) NOT NULL CHECK (state IN ('DISPONIBLE','OCUPADA','BLOQUEADA','FUERA_SERVICIO')), -- Estado de uso.
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0), -- Control de actualización.
    UNIQUE (point_id, code),
    UNIQUE (id, point_id)
);

CREATE TABLE tariff_versions (
    id UUID PRIMARY KEY, -- Versión inmutable una vez utilizada.
    point_id UUID NOT NULL REFERENCES service_points(id), -- Punto aplicable.
    version INTEGER NOT NULL CHECK (version > 0), -- Número de versión.
    rules JSONB NOT NULL, -- Moneda BOB, tamaños, horas y precios por bloque.
    valid_from TIMESTAMPTZ NOT NULL, -- Inicio de aplicación.
    created_by UUID NOT NULL REFERENCES users(id), -- Responsable de tarifa.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Fecha de creación.
    UNIQUE (point_id, version),
    UNIQUE (id, point_id)
);

CREATE TABLE custody_orders (
    id UUID PRIMARY KEY, -- Operación de custodia.
    tracking_number VARCHAR(32) NOT NULL UNIQUE, -- Guía privada, insuficiente para retirar.
    public_reference_hash CHAR(64) NOT NULL UNIQUE, -- Hash de referencia pública aleatoria.
    sender_id UUID NOT NULL REFERENCES users(id), -- Emisor de la operación.
    recipient_id UUID NOT NULL REFERENCES users(id), -- Destinatario autorizado.
    point_id UUID NOT NULL REFERENCES service_points(id), -- Mismo punto para recepción y entrega.
    description VARCHAR(255) NOT NULL, -- Descripción externa del bulto.
    size_category VARCHAR(12) NOT NULL CHECK (size_category IN ('PEQUENO','MEDIANO','GRANDE')), -- Tamaño confirmado al recibir.
    state VARCHAR(24) NOT NULL CHECK (state IN ('REGISTRADA','EN_CUSTODIA','RETIRO_EN_CURSO','RETIRADA','DEVOLUCION_EN_CURSO','DEVUELTA','CANCELADA')), -- Estado normativo.
    tariff_id UUID, -- Versión aplicada al recibir.
    tariff_snapshot JSONB, -- Condiciones aceptadas que no cambian retroactivamente.
    service_total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (service_total >= 0), -- Total del servicio contratado y prorrogado.
    received_at TIMESTAMPTZ, -- Inicio real de custodia.
    due_at TIMESTAMPTZ, -- Fin del plazo contratado.
    completed_at TIMESTAMPTZ, -- Retiro, devolución o cancelación finalizada.
    version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0), -- Versión comprobada en mutaciones.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Prerregistro.
    UNIQUE (id, point_id),
    FOREIGN KEY (tariff_id, point_id) REFERENCES tariff_versions(id, point_id)
);

CREATE TABLE storage_assignments (
    id UUID PRIMARY KEY, -- Historial de ubicación de una custodia.
    custody_id UUID NOT NULL, -- Operación ocupante.
    point_id UUID NOT NULL, -- Garantiza coherencia entre punto y ubicación.
    location_id UUID NOT NULL, -- Espacio ocupado.
    assigned_at TIMESTAMPTZ NOT NULL, -- Inicio de ocupación.
    released_at TIMESTAMPTZ, -- Fin de ocupación; NULL identifica asignación activa.
    FOREIGN KEY (custody_id, point_id) REFERENCES custody_orders(id, point_id),
    FOREIGN KEY (location_id, point_id) REFERENCES storage_locations(id, point_id),
    CHECK (released_at IS NULL OR released_at >= assigned_at)
);

CREATE TABLE pickup_credentials (
    id UUID PRIMARY KEY, -- Credencial de retiro; el código no se almacena.
    custody_id UUID NOT NULL REFERENCES custody_orders(id), -- Operación única autorizable.
    verifier CHAR(64) NOT NULL, -- HMAC ligado a custodia y propósito.
    state VARCHAR(12) NOT NULL CHECK (state IN ('ACTIVA','RETENIDA','CONSUMIDA','REVOCADA')), -- Ciclo de uso.
    failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0), -- Intentos persistidos.
    blocked_until TIMESTAMPTZ, -- Límite de bloqueo temporal.
    expires_at TIMESTAMPTZ NOT NULL, -- Vigencia según servidor.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Emisión.
    UNIQUE (id, custody_id)
);

CREATE TABLE recovery_requests (
    id UUID PRIMARY KEY, -- Expediente de excepción.
    custody_id UUID NOT NULL REFERENCES custody_orders(id), -- Operación afectada.
    purpose VARCHAR(32) NOT NULL CHECK (purpose IN ('REEMITIR_CREDENCIAL','CAMBIAR_DESTINATARIO','AUTORIZAR_DEVOLUCION','RECONCILIAR_ENTREGA')), -- Acción solicitada.
    requested_by UUID NOT NULL REFERENCES users(id), -- Solicitante autenticado.
    decided_by UUID REFERENCES users(id), -- Responsable distinto del solicitante.
    state VARCHAR(12) NOT NULL CHECK (state IN ('PENDIENTE','APROBADA','RECHAZADA','EJECUTADA')), -- Estado del expediente.
    evidence TEXT NOT NULL, -- Hechos y comprobaciones mínimas, sin secretos.
    requested_changes JSONB NOT NULL DEFAULT '{}'::jsonb, -- Cambio concreto propuesto y validado, como nuevo destinatario.
    decision_note TEXT, -- Fundamento de decisión.
    decided_at TIMESTAMPTZ, -- Fecha de revisión.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Solicitud.
    UNIQUE (id, custody_id),
    CHECK (decided_by IS NULL OR decided_by <> requested_by)
);

CREATE TABLE pickup_authorizations (
    id UUID PRIMARY KEY, -- Autorización de entrega, no comprobante final.
    custody_id UUID NOT NULL REFERENCES custody_orders(id), -- Custodia retenida para entrega.
    operator_id UUID NOT NULL REFERENCES users(id), -- Operador autorizado que prepara y confirma.
    credential_id UUID, -- Credencial retenida para retiro normal.
    recovery_request_id UUID, -- Aprobación de devolución.
    purpose VARCHAR(12) NOT NULL CHECK (purpose IN ('RETIRO','DEVOLUCION')), -- Destino de la entrega.
    person_check VARCHAR(40) NOT NULL, -- Constancia de comprobación presencial declarada por el operador.
    state VARCHAR(12) NOT NULL CHECK (state IN ('VALIDADA','CONSUMIDA','ANULADA')), -- Consumo único.
    expires_at TIMESTAMPTZ NOT NULL, -- Plazo breve para entrega.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Verificación.
    UNIQUE (id, custody_id, purpose),
    FOREIGN KEY (credential_id, custody_id) REFERENCES pickup_credentials(id, custody_id),
    FOREIGN KEY (recovery_request_id, custody_id) REFERENCES recovery_requests(id, custody_id),
    CHECK ((purpose = 'RETIRO' AND credential_id IS NOT NULL AND recovery_request_id IS NULL) OR (purpose = 'DEVOLUCION' AND credential_id IS NULL AND recovery_request_id IS NOT NULL))
);

CREATE TABLE handovers (
    id UUID PRIMARY KEY, -- Comprobante final de entrega humana.
    custody_id UUID NOT NULL UNIQUE REFERENCES custody_orders(id), -- Una salida final por custodia.
    authorization_id UUID NOT NULL UNIQUE, -- Autorización consumida.
    kind VARCHAR(12) NOT NULL CHECK (kind IN ('RETIRO','DEVOLUCION')), -- Retiro al destinatario o devolución al emisor.
    operator_id UUID NOT NULL REFERENCES users(id), -- Responsable de la entrega.
    recipient_check VARCHAR(40) NOT NULL, -- Constancia de comprobación visual sin imagen documental.
    reconciliation_request_id UUID, -- Expediente si la confirmación fue recuperada.
    confirmed_at TIMESTAMPTZ NOT NULL, -- Fecha de confirmación persistida.
    FOREIGN KEY (authorization_id, custody_id, kind) REFERENCES pickup_authorizations(id, custody_id, purpose),
    FOREIGN KEY (reconciliation_request_id, custody_id) REFERENCES recovery_requests(id, custody_id)
);

CREATE TABLE custody_events (
    id UUID PRIMARY KEY, -- Evento histórico agregado explícitamente.
    custody_id UUID REFERENCES custody_orders(id), -- Custodia afectada, si corresponde.
    point_id UUID REFERENCES service_points(id), -- Alcance de consulta del evento.
    actor_id UUID REFERENCES users(id), -- Actor humano o NULL para tarea técnica identificada en payload.
    event_type VARCHAR(64) NOT NULL, -- Tipo de hecho.
    previous_state VARCHAR(24), -- Estado previo si hubo transición.
    new_state VARCHAR(24), -- Estado posterior si hubo transición.
    correlation_id UUID NOT NULL, -- Relación con petición o expediente.
    payload JSONB NOT NULL DEFAULT '{}'::jsonb, -- Datos mínimos sin códigos ni contraseñas.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP -- Fecha de servidor.
);

CREATE TABLE notifications (
    id UUID PRIMARY KEY, -- Aviso y registro de salida pendiente.
    user_id UUID NOT NULL REFERENCES users(id), -- Destinatario del aviso.
    custody_id UUID REFERENCES custody_orders(id), -- Operación relacionada.
    event_key UUID NOT NULL, -- Clave para no duplicar el mismo aviso.
    channel VARCHAR(12) NOT NULL CHECK (channel IN ('BANDEJA','CORREO')), -- Canal de software.
    state VARCHAR(12) NOT NULL CHECK (state IN ('PENDIENTE','ENVIADA','FALLIDA','LEIDA')), -- ENVIADA significa aceptación por el canal, no lectura del correo.
    subject VARCHAR(160) NOT NULL, -- Asunto sin secretos.
    body TEXT NOT NULL, -- Mensaje y enlace al detalle privado.
    attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0), -- Intentos de envío.
    next_attempt_at TIMESTAMPTZ, -- Reintento programado.
    sent_at TIMESTAMPTZ, -- Aceptación por el canal.
    read_at TIMESTAMPTZ, -- Lectura confirmada en bandeja.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Creación transaccional.
    UNIQUE (user_id, event_key, channel)
);

CREATE TABLE incidents (
    id UUID PRIMARY KEY, -- Diferencia o falla del servicio.
    custody_id UUID NOT NULL REFERENCES custody_orders(id), -- Objeto afectado.
    opened_by UUID NOT NULL REFERENCES users(id), -- Responsable de registrar el hecho.
    resolved_by UUID REFERENCES users(id), -- Responsable de resolver.
    kind VARCHAR(40) NOT NULL, -- Tipo de diferencia o interrupción.
    is_blocking BOOLEAN NOT NULL DEFAULT TRUE, -- Impide entrega ordinaria.
    state VARCHAR(16) NOT NULL CHECK (state IN ('ABIERTA','EN_REVISION','RESUELTA')), -- Seguimiento.
    description TEXT NOT NULL, -- Hechos observados sin códigos.
    resolution_note TEXT, -- Fundamento de cierre.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Apertura.
    resolved_at TIMESTAMPTZ -- Cierre.
);

CREATE TABLE service_payments (
    id UUID PRIMARY KEY, -- Registro del cobro del servicio, sin procesador bancario.
    custody_id UUID NOT NULL REFERENCES custody_orders(id), -- Custodia correspondiente.
    received_by UUID NOT NULL REFERENCES users(id), -- Personal que comprobó el importe.
    kind VARCHAR(12) NOT NULL CHECK (kind IN ('INICIAL','PRORROGA','REEMBOLSO')), -- Concepto; reembolso se resta al conciliar.
    amount NUMERIC(12,2) NOT NULL CHECK (amount > 0), -- Importe positivo en BOB.
    method VARCHAR(24) NOT NULL CHECK (method IN ('EFECTIVO','REFERENCIA_MANUAL')), -- Comprobación humana, sin integración de pagos.
    reference VARCHAR(120), -- Referencia mínima sin credenciales bancarias.
    state VARCHAR(12) NOT NULL CHECK (state IN ('REGISTRADO','ANULADO')), -- Corrección con auditoría.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP -- Fecha de registro.
);

CREATE TABLE idempotency_keys (
    id UUID PRIMARY KEY, -- Reintento de una petición operativa.
    actor_id UUID NOT NULL REFERENCES users(id), -- Alcance por actor.
    operation VARCHAR(120) NOT NULL, -- Ruta y acción canónicas.
    request_key VARCHAR(120) NOT NULL, -- Clave de petición del cliente.
    request_hash CHAR(64) NOT NULL, -- HMAC del contenido canónico con secreto de servidor; no hash simple de un código breve.
    result_resource_id UUID, -- Recurso que permite recuperar el resultado sin secretos.
    state VARCHAR(12) NOT NULL CHECK (state IN ('EN_CURSO','COMPLETADA')), -- Progreso transaccional.
    expires_at TIMESTAMPTZ NOT NULL, -- Conservación de la clave.
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, -- Recepción.
    UNIQUE (actor_id, operation, request_key)
);

CREATE UNIQUE INDEX uq_storage_assignment_active_custody
    ON storage_assignments (custody_id) WHERE released_at IS NULL;
CREATE UNIQUE INDEX uq_storage_assignment_active_location
    ON storage_assignments (location_id) WHERE released_at IS NULL;
CREATE UNIQUE INDEX uq_pickup_credential_current
    ON pickup_credentials (custody_id) WHERE state IN ('ACTIVA', 'RETENIDA');
CREATE UNIQUE INDEX uq_pickup_authorization_validated
    ON pickup_authorizations (custody_id) WHERE state = 'VALIDADA';

CREATE FUNCTION reject_custody_event_mutation() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Los eventos de custodia solo admiten inserciones' USING ERRCODE = '55000';
END;
$$;

CREATE TRIGGER custody_events_append_only
    BEFORE UPDATE OR DELETE ON custody_events
    FOR EACH ROW EXECUTE FUNCTION reject_custody_event_mutation();

COMMIT;
