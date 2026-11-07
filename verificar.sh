#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' 'Instala el entorno documental con uv venv --python 3.13 y uv pip sync herramientas/requirements.lock.txt.' >&2
    exit 1
fi
bash infra/verificar-esquema.sh
.venv/bin/python herramientas/validar_documentacion.py
