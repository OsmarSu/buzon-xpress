#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
container=$(docker run --rm -d --network none \
    --tmpfs /var/lib/postgresql/data:rw,nosuid,nodev,size=256m \
    -e POSTGRES_HOST_AUTH_METHOD=trust \
    -e POSTGRES_DB=buzon_validacion \
    postgres:16-alpine)
trap 'docker stop --time 2 "$container" >/dev/null 2>&1 || true' EXIT

for attempt in {1..60}; do
    if docker exec "$container" pg_isready -h 127.0.0.1 -U postgres -d buzon_validacion >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done
docker exec "$container" pg_isready -h 127.0.0.1 -U postgres -d buzon_validacion >/dev/null

docker exec -i "$container" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d buzon_validacion \
    < docs/ingenieria/anexos/modelo_propuesto.sql
docker exec -i "$container" psql -X -q -v ON_ERROR_STOP=1 -U postgres -d buzon_validacion \
    < infra/comprobar-invariantes.sql
docker exec "$container" psql -X -At -v ON_ERROR_STOP=1 -U postgres -d buzon_validacion \
    -c "SELECT 'PostgreSQL ' || current_setting('server_version') || ': ' || count(*) || ' tablas verificadas' FROM pg_tables WHERE schemaname = 'public'"
