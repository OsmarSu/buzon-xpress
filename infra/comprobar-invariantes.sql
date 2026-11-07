-- Comprobaciones sobre el contenedor desechable de verificar-esquema.sh.
BEGIN;

DO $$
DECLARE
    actor uuid := gen_random_uuid();
    other_actor uuid := gen_random_uuid();
    first_point uuid := gen_random_uuid();
    second_point uuid := gen_random_uuid();
    first_location uuid := gen_random_uuid();
    second_location uuid := gen_random_uuid();
    other_location uuid := gen_random_uuid();
    first_custody uuid := gen_random_uuid();
    second_custody uuid := gen_random_uuid();
    first_assignment uuid := gen_random_uuid();
    credential uuid := gen_random_uuid();
    other_credential uuid := gen_random_uuid();
    test_authorization uuid := gen_random_uuid();
    event uuid := gen_random_uuid();
BEGIN
    INSERT INTO users (id, email, full_name, password_hash, role)
    VALUES (actor, 'operador@example.invalid', 'Operador sintético', 'fixture', 'OPERADOR'),
           (other_actor, 'persona@example.invalid', 'Persona sintética', 'fixture', 'USUARIO');
    INSERT INTO service_points (id, code, name, address, opening_hours)
    VALUES (first_point, 'P1', 'Punto 1', 'Prueba', '{}'),
           (second_point, 'P2', 'Punto 2', 'Prueba', '{}');
    INSERT INTO storage_locations (id, point_id, code, size_category, state)
    VALUES (first_location, first_point, 'A1', 'PEQUENO', 'DISPONIBLE'),
           (second_location, first_point, 'A2', 'PEQUENO', 'DISPONIBLE'),
           (other_location, second_point, 'A1', 'PEQUENO', 'DISPONIBLE');
    INSERT INTO custody_orders
        (id, tracking_number, public_reference_hash, sender_id, recipient_id, point_id, description, size_category, state)
    VALUES (first_custody, 'T1', repeat('1', 64), actor, other_actor, first_point, 'Objeto 1', 'PEQUENO', 'REGISTRADA'),
           (second_custody, 'T2', repeat('2', 64), actor, other_actor, first_point, 'Objeto 2', 'PEQUENO', 'REGISTRADA');

    INSERT INTO storage_assignments (id, custody_id, point_id, location_id, assigned_at)
    VALUES (first_assignment, first_custody, first_point, first_location, now());
    BEGIN
        INSERT INTO storage_assignments (id, custody_id, point_id, location_id, assigned_at)
        VALUES (gen_random_uuid(), second_custody, first_point, first_location, now());
        RAISE EXCEPTION 'Se admitió una ubicación activa duplicada';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO storage_assignments (id, custody_id, point_id, location_id, assigned_at)
        VALUES (gen_random_uuid(), first_custody, first_point, second_location, now());
        RAISE EXCEPTION 'Se admitió una custodia con dos asignaciones activas';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    BEGIN
        INSERT INTO storage_assignments (id, custody_id, point_id, location_id, assigned_at)
        VALUES (gen_random_uuid(), second_custody, first_point, other_location, now());
        RAISE EXCEPTION 'Se admitió una ubicación de otro punto';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    UPDATE storage_assignments SET released_at = now() WHERE id = first_assignment;
    INSERT INTO storage_assignments (id, custody_id, point_id, location_id, assigned_at)
    VALUES (gen_random_uuid(), second_custody, first_point, first_location, now());

    INSERT INTO pickup_credentials (id, custody_id, verifier, state, expires_at)
    VALUES (credential, first_custody, repeat('a', 64), 'RETENIDA', now() + interval '15 minutes'),
           (other_credential, second_custody, repeat('b', 64), 'RETENIDA', now() + interval '15 minutes');
    BEGIN
        INSERT INTO pickup_authorizations
            (id, custody_id, operator_id, credential_id, purpose, person_check, state, expires_at)
        VALUES (gen_random_uuid(), first_custody, actor, other_credential, 'RETIRO', 'PRESENCIAL', 'VALIDADA', now() + interval '2 minutes');
        RAISE EXCEPTION 'Se admitió una credencial de otra custodia';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    INSERT INTO pickup_authorizations
        (id, custody_id, operator_id, credential_id, purpose, person_check, state, expires_at)
    VALUES (test_authorization, first_custody, actor, credential, 'RETIRO', 'PRESENCIAL', 'CONSUMIDA', now() + interval '2 minutes');
    INSERT INTO handovers (id, custody_id, authorization_id, kind, operator_id, recipient_check, confirmed_at)
    VALUES (gen_random_uuid(), first_custody, test_authorization, 'RETIRO', actor, 'PRESENCIAL', now());
    BEGIN
        INSERT INTO handovers (id, custody_id, authorization_id, kind, operator_id, recipient_check, confirmed_at)
        VALUES (gen_random_uuid(), first_custody, test_authorization, 'RETIRO', actor, 'PRESENCIAL', now());
        RAISE EXCEPTION 'Se admitió un comprobante final duplicado';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;

    BEGIN
        INSERT INTO recovery_requests (id, custody_id, purpose, requested_by, decided_by, state, evidence)
        VALUES (gen_random_uuid(), first_custody, 'RECONCILIAR_ENTREGA', actor, actor, 'APROBADA', 'Prueba');
        RAISE EXCEPTION 'Se admitió una recuperación autoaprobada';
    EXCEPTION WHEN check_violation THEN NULL;
    END;

    INSERT INTO custody_events (id, custody_id, point_id, actor_id, event_type, correlation_id)
    VALUES (event, first_custody, first_point, actor, 'PRUEBA', gen_random_uuid());
    BEGIN
        UPDATE custody_events SET event_type = 'CAMBIO' WHERE id = event;
        RAISE EXCEPTION 'Se modificó un evento histórico';
    EXCEPTION WHEN SQLSTATE '55000' THEN NULL;
    END;
    BEGIN
        DELETE FROM custody_events WHERE id = event;
        RAISE EXCEPTION 'Se borró un evento histórico';
    EXCEPTION WHEN SQLSTATE '55000' THEN NULL;
    END;
END;
$$;

ROLLBACK;
\echo Invariantes comprobadas: ocupación única, coherencia de punto y credencial, salida única, doble control y eventos de solo inserción.
