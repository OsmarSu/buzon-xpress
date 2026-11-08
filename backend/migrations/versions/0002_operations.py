"""Create the custody and supervision schema from the versioned design."""

from alembic import op

revision = "0002_operations"
down_revision = "0001_identity"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE storage_locations (
            id UUID PRIMARY KEY,
            point_id UUID NOT NULL REFERENCES service_points(id),
            code VARCHAR(24) NOT NULL,
            size_category VARCHAR(12) NOT NULL CHECK (size_category IN ('PEQUENO','MEDIANO','GRANDE')),
            state VARCHAR(20) NOT NULL CHECK (state IN ('DISPONIBLE','OCUPADA','BLOQUEADA','FUERA_SERVICIO')),
            version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
            UNIQUE (point_id, code),
            UNIQUE (id, point_id)
        );
    """)
    op.execute("""
        CREATE TABLE tariff_versions (
            id UUID PRIMARY KEY,
            point_id UUID NOT NULL REFERENCES service_points(id),
            version INTEGER NOT NULL CHECK (version > 0),
            rules JSONB NOT NULL,
            valid_from TIMESTAMPTZ NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (point_id, version),
            UNIQUE (id, point_id)
        );
    """)
    op.execute("""
        CREATE TABLE custody_orders (
            id UUID PRIMARY KEY,
            tracking_number VARCHAR(32) NOT NULL UNIQUE,
            public_reference_hash CHAR(64) NOT NULL UNIQUE,
            sender_id UUID NOT NULL REFERENCES users(id),
            recipient_id UUID NOT NULL REFERENCES users(id),
            point_id UUID NOT NULL REFERENCES service_points(id),
            description VARCHAR(255) NOT NULL,
            size_category VARCHAR(12) NOT NULL CHECK (size_category IN ('PEQUENO','MEDIANO','GRANDE')),
            state VARCHAR(24) NOT NULL CHECK (state IN ('REGISTRADA','EN_CUSTODIA','RETIRO_EN_CURSO','RETIRADA','DEVOLUCION_EN_CURSO','DEVUELTA','CANCELADA')),
            tariff_id UUID,
            tariff_snapshot JSONB,
            service_total NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (service_total >= 0),
            received_at TIMESTAMPTZ,
            due_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (id, point_id),
            FOREIGN KEY (tariff_id, point_id) REFERENCES tariff_versions(id, point_id)
        );
    """)
    op.execute("""
        CREATE TABLE storage_assignments (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL,
            point_id UUID NOT NULL,
            location_id UUID NOT NULL,
            assigned_at TIMESTAMPTZ NOT NULL,
            released_at TIMESTAMPTZ,
            FOREIGN KEY (custody_id, point_id) REFERENCES custody_orders(id, point_id),
            FOREIGN KEY (location_id, point_id) REFERENCES storage_locations(id, point_id),
            CHECK (released_at IS NULL OR released_at >= assigned_at)
        );
    """)
    op.execute("""
        CREATE TABLE pickup_credentials (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL REFERENCES custody_orders(id),
            verifier CHAR(64) NOT NULL,
            state VARCHAR(12) NOT NULL CHECK (state IN ('ACTIVA','RETENIDA','CONSUMIDA','REVOCADA')),
            failed_attempts INTEGER NOT NULL DEFAULT 0 CHECK (failed_attempts >= 0),
            blocked_until TIMESTAMPTZ,
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (id, custody_id)
        );
    """)
    op.execute("""
        CREATE TABLE recovery_requests (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL REFERENCES custody_orders(id),
            purpose VARCHAR(32) NOT NULL CHECK (purpose IN ('REEMITIR_CREDENCIAL','CAMBIAR_DESTINATARIO','AUTORIZAR_DEVOLUCION','RECONCILIAR_ENTREGA')),
            requested_by UUID NOT NULL REFERENCES users(id),
            decided_by UUID REFERENCES users(id),
            state VARCHAR(12) NOT NULL CHECK (state IN ('PENDIENTE','APROBADA','RECHAZADA','EJECUTADA')),
            evidence TEXT NOT NULL,
            requested_changes JSONB NOT NULL DEFAULT '{}'::jsonb,
            decision_note TEXT,
            decided_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (id, custody_id),
            CHECK (decided_by IS NULL OR decided_by <> requested_by)
        );
    """)
    op.execute("""
        CREATE TABLE pickup_authorizations (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL REFERENCES custody_orders(id),
            operator_id UUID NOT NULL REFERENCES users(id),
            credential_id UUID,
            recovery_request_id UUID,
            purpose VARCHAR(12) NOT NULL CHECK (purpose IN ('RETIRO','DEVOLUCION')),
            person_check VARCHAR(40) NOT NULL,
            state VARCHAR(12) NOT NULL CHECK (state IN ('VALIDADA','CONSUMIDA','ANULADA')),
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (id, custody_id, purpose),
            FOREIGN KEY (credential_id, custody_id) REFERENCES pickup_credentials(id, custody_id),
            FOREIGN KEY (recovery_request_id, custody_id) REFERENCES recovery_requests(id, custody_id),
            CHECK ((purpose = 'RETIRO' AND credential_id IS NOT NULL AND recovery_request_id IS NULL) OR (purpose = 'DEVOLUCION' AND credential_id IS NULL AND recovery_request_id IS NOT NULL))
        );
    """)
    op.execute("""
        CREATE TABLE handovers (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL UNIQUE REFERENCES custody_orders(id),
            authorization_id UUID NOT NULL UNIQUE,
            kind VARCHAR(12) NOT NULL CHECK (kind IN ('RETIRO','DEVOLUCION')),
            operator_id UUID NOT NULL REFERENCES users(id),
            recipient_check VARCHAR(40) NOT NULL,
            reconciliation_request_id UUID,
            confirmed_at TIMESTAMPTZ NOT NULL,
            FOREIGN KEY (authorization_id, custody_id, kind) REFERENCES pickup_authorizations(id, custody_id, purpose),
            FOREIGN KEY (reconciliation_request_id, custody_id) REFERENCES recovery_requests(id, custody_id)
        );
    """)
    op.execute("""
        CREATE TABLE custody_events (
            id UUID PRIMARY KEY,
            custody_id UUID REFERENCES custody_orders(id),
            point_id UUID REFERENCES service_points(id),
            actor_id UUID REFERENCES users(id),
            event_type VARCHAR(64) NOT NULL,
            previous_state VARCHAR(24),
            new_state VARCHAR(24),
            correlation_id UUID NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    op.execute("""
        CREATE TABLE notifications (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(id),
            custody_id UUID REFERENCES custody_orders(id),
            event_key UUID NOT NULL,
            channel VARCHAR(12) NOT NULL CHECK (channel IN ('BANDEJA','CORREO')),
            state VARCHAR(12) NOT NULL CHECK (state IN ('PENDIENTE','ENVIADA','FALLIDA','LEIDA')),
            subject VARCHAR(160) NOT NULL,
            body TEXT NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0 CHECK (attempts >= 0),
            next_attempt_at TIMESTAMPTZ,
            sent_at TIMESTAMPTZ,
            read_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (user_id, event_key, channel)
        );
    """)
    op.execute("""
        CREATE TABLE incidents (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL REFERENCES custody_orders(id),
            opened_by UUID NOT NULL REFERENCES users(id),
            resolved_by UUID REFERENCES users(id),
            kind VARCHAR(40) NOT NULL,
            is_blocking BOOLEAN NOT NULL DEFAULT TRUE,
            state VARCHAR(16) NOT NULL CHECK (state IN ('ABIERTA','EN_REVISION','RESUELTA')),
            description TEXT NOT NULL,
            resolution_note TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMPTZ
        );
    """)
    op.execute("""
        CREATE TABLE service_payments (
            id UUID PRIMARY KEY,
            custody_id UUID NOT NULL REFERENCES custody_orders(id),
            received_by UUID NOT NULL REFERENCES users(id),
            kind VARCHAR(12) NOT NULL CHECK (kind IN ('INICIAL','PRORROGA','REEMBOLSO')),
            amount NUMERIC(12,2) NOT NULL CHECK (amount > 0),
            method VARCHAR(24) NOT NULL CHECK (method IN ('EFECTIVO','REFERENCIA_MANUAL')),
            reference VARCHAR(120),
            state VARCHAR(12) NOT NULL CHECK (state IN ('REGISTRADO','ANULADO')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)
    op.execute("""
        CREATE TABLE idempotency_keys (
            id UUID PRIMARY KEY,
            actor_id UUID NOT NULL REFERENCES users(id),
            operation VARCHAR(120) NOT NULL,
            request_key VARCHAR(120) NOT NULL,
            request_hash CHAR(64) NOT NULL,
            result_resource_id UUID,
            state VARCHAR(12) NOT NULL CHECK (state IN ('EN_CURSO','COMPLETADA')),
            expires_at TIMESTAMPTZ NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (actor_id, operation, request_key)
        );
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_storage_assignment_active_custody
            ON storage_assignments (custody_id) WHERE released_at IS NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_storage_assignment_active_location
            ON storage_assignments (location_id) WHERE released_at IS NULL;
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_pickup_credential_current
            ON pickup_credentials (custody_id) WHERE state IN ('ACTIVA', 'RETENIDA');
    """)
    op.execute("""
        CREATE UNIQUE INDEX uq_pickup_authorization_validated
            ON pickup_authorizations (custody_id) WHERE state = 'VALIDADA';
    """)
    op.execute("""
        CREATE FUNCTION reject_custody_event_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'Los eventos de custodia solo admiten inserciones' USING ERRCODE = '55000';
        END;
        $$;
    """)
    op.execute("""
        CREATE TRIGGER custody_events_append_only
            BEFORE UPDATE OR DELETE ON custody_events
            FOR EACH ROW EXECUTE FUNCTION reject_custody_event_mutation();
    """)


def downgrade() -> None:
    op.drop_table("idempotency_keys")
    op.drop_table("service_payments")
    op.drop_table("incidents")
    op.drop_table("notifications")
    op.drop_table("custody_events")
    op.drop_table("handovers")
    op.drop_table("pickup_authorizations")
    op.drop_table("recovery_requests")
    op.drop_table("pickup_credentials")
    op.drop_table("storage_assignments")
    op.drop_table("custody_orders")
    op.drop_table("tariff_versions")
    op.drop_table("storage_locations")
    op.execute("DROP FUNCTION reject_custody_event_mutation()")
