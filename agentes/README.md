# Propuesta de desarrollo con agentes en WSL

**Propuesta verificada contra la documentación pública el 7 de noviembre de 2026.** Las versiones, los puertos y los pasos de conexión se prepararon para una prueba posterior. El entorno de agentes queda como propuesta de instalación.

## Configuración recomendada

```text
Persona responsable → DeepSeek Harness (:3080) → OmniRoute (:20128/v1)
                                                   └→ Ollama (:11434) → modelo local
                      Git worktrees y pruebas en WSL ← cambios revisables
```

| Componente | Papel y opción inicial |
| --- | --- |
| DeepSeek Harness | Entorno de sesiones, herramientas y subagentes. Paquete oficial `@deepseek-ai/dsh@0.2.2-rc.1`. Requiere Node ≥24.9.0 y la máquina tiene 24.22.2. Agent Teams está en vista previa y se probaría después de validar sesiones y herramientas. |
| OmniRoute | Gateway compatible con OpenAI para cambiar modelos sin cambiar el flujo de trabajo. Paquete `omniroute@3.8.53`, estado local separado. Crear una ruta `buzon-local` con un solo destino Ollama y una clave de acceso del gateway. |
| Ollama | Infiere en WSL. Probar primero `qwen3:8b` para código y llamadas a herramientas. Como segunda opción local, probar `deepseek-r1:8b` para planificación y revisión. Ambos archivos cuantizados publicados ocupan unos 5,2 GB cada uno. Probar `qwen3:4b` si falta margen para el contexto. |
| OpenCode | Cliente alternativo si una versión de Harness falla con streaming o herramientas. Usaría el mismo endpoint de OmniRoute con proveedor personalizado, el mismo repositorio y los mismos criterios de prueba. |

Referencias de herramientas y modelos. [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) · [Agent Teams](https://deepseek-harness.github.io/deepseek-harness/en/reference/) · [OmniRoute](https://github.com/cheaper-inference/OmniRoute) · [Qwen3 8B](https://ollama.com/library/qwen3:8b) · [DeepSeek R1 8B](https://ollama.com/library/deepseek-r1:8b) · [OpenCode](https://opencode.ai/docs/models)

WSL mostró **RTX 3070 Laptop de 8 GiB**, aproximadamente **7,2 GiB libres** en la medición, **15 GiB de RAM** y **16 hilos**. Los pesos de un modelo son solo parte del consumo. Empezaría con un modelo cargado, una inferencia activa y un contexto de 4–8K, ampliándolo si la prueba conserva velocidad y memoria. Los roles pueden trabajar por turnos sobre el mismo modelo. El uso de GPU se comprobaría con `ollama ps` y `nvidia-smi`. [Compatibilidad NVIDIA](https://docs.ollama.com/gpu) · [Concurrencia y modo local](https://docs.ollama.com/faq)

## Qué significa gratis

- Harness, OmniRoute autohospedado y Ollama local se pueden usar sin comprar tokens. El costo local es el consumo del equipo. El paquete Harness y el modelo al que se conecta tienen condiciones independientes. [Licencia de Harness](https://github.com/deepseek-ai/deepseek-harness) · [OmniRoute autohospedado](https://omniroute.cheaperinference.com/) · [Ollama local](https://docs.ollama.com/faq)
- Para una segunda opinión sobre código autorizado y datos sintéticos, se puede crear una ruta separada `buzon-free` con modelos de OpenRouter etiquetados `:free` que declaren herramientas. OpenRouter publica un límite base de 50 solicitudes al día y 20 por minuto para esas variantes. Revisar el catálogo, cuota y política del proveedor antes de elegir cada modelo. Ante un límite, volver al modelo local o esperar. [Catálogo y cuotas de OpenRouter](https://openrouter.ai/collections/free-models)
- La API oficial de DeepSeek factura por tokens. La propuesta de costo cero usa el modelo destilado local o un proveedor con cuota gratuita verificada. Mantener la API de pago fuera de las rutas automáticas. [Modelos y precios de DeepSeek](https://api-docs.deepseek.com/quick_start/pricing)

## Instalación e integración propuestas

1. Desde la raíz de este proyecto, reservar `.agentes-local` con permisos privados. Ahí quedarían los modelos, el estado del router, la configuración de Harness y la caché npm. Instalar Ollama desde el paquete oficial Linux amd64, fijando versión y verificando el artefacto. Se puede extraer con sus bibliotecas bajo `.agentes-local/ollama`. Arrancar dentro de Arch y comprobar detección de GPU. [Instalación Linux](https://docs.ollama.com/linux)

   ```bash
   install -d -m 700 .agentes-local .agentes-local/modelos .agentes-local/router .agentes-local/dsh
   export PATH="$PWD/.agentes-local/ollama/bin:$PATH"
   OLLAMA_HOST=127.0.0.1:11434 OLLAMA_MODELS="$PWD/.agentes-local/modelos" \
     OLLAMA_NO_CLOUD=1 OLLAMA_NUM_PARALLEL=1 OLLAMA_MAX_LOADED_MODELS=1 \
     OLLAMA_CONTEXT_LENGTH=8192 ollama serve
   ```

   En otra terminal de WSL, desde la misma raíz y con el mismo `PATH`, ejecutar `ollama pull qwen3:8b`. Probar `ollama run qwen3:8b`, medir VRAM y comprobar una llamada a herramienta. Descargar un segundo modelo después de medir el primero.

2. Instalar OmniRoute como dependencia local de herramientas. El paquete publicado declara compatibilidad con Node 24. npm puede pedir una lista explícita de scripts de instalación para los binarios nativos. Revisar la lista del release y habilitar solo los paquetes requeridos. [Instalación y scripts de OmniRoute](https://github.com/cheaper-inference/OmniRoute) · [Variables y proveedores](https://github.com/cheaper-inference/OmniRoute/wiki/User-Guide) · [Enlace local en la versión fijada](https://github.com/cheaper-inference/OmniRoute/blob/release/v3.8.53/bin/cli/utils/serverHost.mjs)

   ```bash
   export npm_config_cache="$PWD/.agentes-local/npm-cache"
   npm install --prefix "$PWD/.agentes-local/router-cli" omniroute@3.8.53
   OMNIROUTE_SERVER_HOST=127.0.0.1 DATA_DIR="$PWD/.agentes-local/router" REQUIRE_API_KEY=true \
     .agentes-local/router-cli/node_modules/.bin/omniroute serve --port 20128 --no-open
   ```

   Abrir el panel en `http://127.0.0.1:20128`, terminar la configuración de autenticación, conectar el proveedor Ollama a `http://127.0.0.1:11434`, crear el alias `buzon-local` y generar una clave del gateway. Verificar con `ss -lntp` que los servicios escuchen en loopback. Los dos procesos en WSL comparten loopback.

3. Arrancar DeepSeek Harness desde la raíz del proyecto. En `Settings → Models → Add model provider → Custom model API`, elegir ID `buzon-router`, protocolo **OpenAI Chat Completions**, URL `http://127.0.0.1:20128/v1` y la clave de OmniRoute. Descubrir los modelos o añadir el ID exacto que devuelve `GET /v1/models`. Elegir `buzon-local` como modelo de la sesión. [Arranque oficial](https://github.com/deepseek-ai/deepseek-harness) · [Proveedor personalizado](https://deepseek-harness.github.io/deepseek-harness/en/guide/providers)

   ```bash
   DSH_HOME="$PWD/.agentes-local/dsh" npm_config_cache="$PWD/.agentes-local/npm-cache" \
     npx @deepseek-ai/dsh@0.2.2-rc.1 web --no-open
   ```

4. Probar una consulta sin herramientas, después streaming, una herramienta de lectura y una edición acotada con prueba. Verificar que la petición llegue a Ollama. Si Harness y el gateway discrepan sobre campos del protocolo, probar la conexión directa de diagnóstico a `http://127.0.0.1:11434/v1` y comparar con el perfil personalizado. Ajustar compatibilidad según el error observado. Activar Agent Teams solo después de que una sesión de escritura aislada complete el ciclo. [Compatibilidad de solicitudes](https://deepseek-harness.github.io/deepseek-harness/en/guide/providers) · [Configuración de agentes](https://deepseek-harness.github.io/deepseek-harness/en/reference/)

## Cómo trabajaríamos en este sistema

| Rol | Entrada | Entrega |
| --- | --- | --- |
| Coordinación y arquitectura | RF, RN, OpenAPI, modelo y criterio de aceptación | Tareas pequeñas, archivos asignados, dependencias y decisiones a revisar |
| Backend y datos | Contrato congelado y casos de uso | Casos, persistencia, migración aislada y pruebas de API |
| Frontend | DTO, wireframes y errores del contrato | Pantalla conectada, estados de carga y error, pruebas de interacción |
| QA y revisión | Requisitos, diff y comandos reproducibles | Pruebas negativas, concurrencia, revisión de permisos y evidencia |
| Integración humana | Diff de cada rama, resultados y decisiones pendientes | Selección de cambios, revisión cruzada y versión local comprobada |

Primero un líder descompone el trabajo y asigna rutas disjuntas. En esta GPU, comenzar con dos roles por turnos. Un agente implementa y otro revisa con el contexto acotado. Al ampliar el flujo, cada rol de escritura usa un worktree y una rama propia. Los contratos y migraciones tienen responsable único. Los worktrees separan cambios de Git. El control de acceso de los procesos se configura por separado, con permisos limitados a su área, sin credenciales del producto y sin acceso directo al socket Docker. La persona responsable ejecuta los ensayos Docker desde la raíz.

```bash
git worktree add -b tarea/BZ-001-backend .worktrees/BZ-001-backend main
```

Se entrega al agente una [tarea con criterios verificables](plantilla-tarea.md). El agente devuelve el diff, las pruebas ejecutadas y los hallazgos. El revisor usa una sesión independiente y ejecuta las comprobaciones pertinentes. Se integra cuando el resultado cumple el contrato, compila y pasa las pruebas. Las operaciones externas quedan a cargo de la persona responsable.

Primera prueba del equipo de agentes: [BZ-001 · Identidad y alcance](tareas/001-identidad.md). Empezar con un cambio pequeño de lectura y prueba de contrato antes de distribuir backend y frontend. Medir éxito de herramientas, tiempo por cambio, consumo de VRAM y retrabajo. Conservar la división por requisitos, contratos, ramas y revisión para otros sistemas. Cambiar el modelo solo cuando una prueba comparable muestre una mejora.
