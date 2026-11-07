# Regeneración y revisión documental

Este entorno usa Python 3.13, PyYAML, python-docx, markdown-it-py, Pillow, PySide6 y openapi-spec-validator. En Arch están instalados Graphviz, librsvg, LibreOffice y Poppler. Docker ejecuta el ensayo de PostgreSQL.

## Verificar la línea base

Desde la raíz:

```bash
./verificar.sh
```

Si se necesita reinstalar las dependencias:

```bash
uv venv --python 3.13
uv pip sync --python .venv/bin/python herramientas/requirements.lock.txt
```

La revisión comprueba enlaces locales, hashes de referencias históricas, correspondencia, requisitos, rutas, diagramas y exportables. Valida OpenAPI 3.1 con un validador de esquema. El ensayo de SQL crea una base desechable en memoria sin puertos expuestos y verifica restricciones de ocupación, coherencia, entrega y auditoría. Las pruebas funcionales del producto están registradas en el plan y se ejecutarán con la implementación.

## Regenerar documentos

Editar primero las fuentes Markdown o el SQL de referencia, según el cambio. Conservar la relación entre requisitos, contrato, diccionario y trazabilidad. Estos comandos actualizan los exportables y diagramas de la carpeta actual:

```bash
source .venv/bin/activate
python herramientas/generar_catalogos.py
python herramientas/generar_diagramas.py
python herramientas/generar_visuales.py
python herramientas/exportar_documentos.py
python herramientas/validar_documentacion.py
```

El exportador utiliza un perfil temporal independiente de LibreOffice. La alternativa Qt produce PDF y HTML sin interfaz visible. Word y PDF comparten fuentes Markdown y pueden tener paginación distinta. Para conservar la edición de presentación, regenerar en una copia y revisar el resultado antes de sustituir los entregables.
