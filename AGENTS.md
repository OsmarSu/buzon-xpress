# Instrucciones para desarrollar BUZON Xpress

- Trabaja desde la especificación, el catálogo de requisitos y OpenAPI de esta carpeta. Cada cambio debe indicar sus identificadores RF, RN o T y el criterio de aceptación que cubre.
- El servicio organiza custodia temporal con recepción y entrega humana. Usa las ubicaciones como referencias físicas manuales. Las integraciones de hardware, COD y liquidaciones de vendedores pertenecen al antecedente.
- Mantén la autorización en servidor y usa datos sintéticos. Los códigos de retiro, cookies, credenciales, hashes y datos de personas se excluyen de prompts, logs y repositorio.
- Preserva límites de capas. Una operación sensible confirma una transacción y deja evidencia de auditoría. Revisa idempotencia, concurrencia y recuperación cuando cambien recepción, autorización o entrega.
- Usa una rama y un worktree por tarea de escritura. El responsable de integración revisa el diff, verifica contratos y ejecuta las pruebas antes de unir cambios.
- Ejecuta `./verificar.sh` si cambian el modelo, el contrato o la documentación. Para el código de producto usa también los comandos de pruebas y compilación que incorpore cada fase.
- El ensayo de esquema usa el contenedor desechable de `infra/verificar-esquema.sh`. Cualquier futura migración debe apuntar a una base nueva de ensayo, separada del BUZON antecedente.
- Reporta archivos cambiados, pruebas ejecutadas y limitaciones. El estado de las treinta pruebas de producto cambia únicamente con evidencia reproducible.
