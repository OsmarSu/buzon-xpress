#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "$0")/../backend"
uv sync --locked --python 3.13
db_name="buzon_test_$(python -c 'from secrets import token_hex; print(token_hex(5))')"
db_password=$(python -c 'from secrets import token_hex; print(token_hex(24))')
container=$(
    POSTGRES_PASSWORD="$db_password" docker run --detach --rm \
        --tmpfs /var/lib/postgresql/data:rw \
        --publish 127.0.0.1::5432 \
        --env POSTGRES_PASSWORD \
        --env "POSTGRES_DB=$db_name" \
        postgres:16-alpine
)
[[ "$container" =~ ^[0-9a-f]{64}$ ]]
trap 'docker rm -f "$container" >/dev/null 2>&1 || true' EXIT

ready=false
for _ in {1..40}; do
    if docker exec "$container" pg_isready -h 127.0.0.1 -U postgres -d "$db_name" >/dev/null 2>&1; then
        ready=true
        break
    fi
    sleep 0.5
done
if [[ "$ready" != true ]]; then
    printf '%s\n' 'PostgreSQL de ensayo no quedó listo.' >&2
    exit 1
fi

published=$(docker port "$container" 5432/tcp)
[[ "$published" =~ ^127\.0\.0\.1:[0-9]+$ ]]
export BUZON_DATABASE_URL="postgresql+psycopg://postgres:$db_password@$published/$db_name"
export BUZON_TEST_DATABASE_URL="$BUZON_DATABASE_URL"
export PYTHONDONTWRITEBYTECODE=1
uv run --locked alembic upgrade head
uv run --locked alembic downgrade base
uv run --locked alembic upgrade head
uv run --locked pytest -q
