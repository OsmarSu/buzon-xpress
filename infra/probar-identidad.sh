#!/usr/bin/env bash
set -euo pipefail
exec "$(dirname -- "$0")/probar-sistema.sh" tests/integration/test_identity.py tests/unit/test_point_access.py "$@"
