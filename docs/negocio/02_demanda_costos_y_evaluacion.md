# Investigación de demanda, costos y evaluación inicial

## 1. Datos y supuestos

Este documento ofrece instrumentos para levantar datos y fórmulas para evaluarlos. No contiene cotizaciones, precios de mercado ni resultados reales. Las celdas vacías de la [plantilla de parámetros](parametros_evaluacion.csv) se completan con evidencia, fecha y responsable.

La unidad comercial es una custodia de un bulto por un plazo y tamaño. La unidad de capacidad es una ubicación disponible durante una hora o un día. La permanencia del objeto consume capacidad aunque no haya atención humana durante ese intervalo.

## 2. Guion de entrevista

Antes de entrevistar, explicar propósito académico, uso de las respuestas y posibilidad de no responder. Registrar un identificador de participante; evitar documentos personales y datos del objeto que no sean necesarios.

1. Describa la última vez que entregó algo a otra persona y no pudieron coincidir.
2. ¿Qué objeto era, de forma general, y en qué zona se entregaba?
3. ¿Qué alternativas consideró y cuál utilizó?
4. ¿Cuántos intentos de coordinación o visitas realizó?
5. ¿Qué tiempo y gasto implicó esa solución?
6. ¿Quién quedó a cargo del objeto y qué constancia recibió?
7. ¿Qué le preocupó y qué salió bien o mal?
8. ¿Con qué frecuencia tuvo situaciones similares en los últimos tres meses?
9. ¿Qué horario y distancia harían práctico un punto de custodia?
10. Tras explicar el servicio, ¿qué condición impediría que lo use? ¿Qué pagaría y por qué?

Las respuestas sobre precio son exploratorias. No se registran como compra ni se multiplica su proporción por la población para proyectar demanda. Se conserva una tabla con episodio, alternativa, frecuencia, costo, fricción, objeción y observación del entrevistador.

## 3. Observación y comparación de alternativas

Para cada sesión autorizada registrar inicio, fin, llegadas, recepciones, retiros, personas en espera, personal y fallas. No filmar ni fotografiar personas como requisito del estudio.

Ficha de alternativa: nombre o tipo, zona, fecha, horario publicado, objeto comparable, plazo, importe total informado, comprobante, verificación y fuente. Una característica desconocida se marca “sin dato”, nunca “no existe”. No se publican acusaciones o cifras de competidores a partir de impresiones.

## 4. Presupuesto y costos

| Grupo | Partida a levantar | Tratamiento |
|---|---|---|
| Inversión inicial | Diseño, desarrollo, pruebas, puesta en marcha y capacitación. | Valorar horas del equipo aunque no se paguen durante la materia. |
| Espacio existente | Área utilizada y disponibilidad por horario. | Incluir costo de oportunidad o acuerdo con el anfitrión. |
| Equipos disponibles | Tiempo y disponibilidad del equipo de cómputo existente. | Sin compra obligatoria; registrar costo de uso si corresponde. |
| Operación fija | Personal base, conectividad, soporte y alojamiento si se utilizan. | Mensualizar con evidencia. |
| Operación variable | Trabajo por custodia, comunicaciones y consumibles realmente empleados. | Medir por operación; no duplicar salarios ya incluidos como fijos. |
| Contingencias | Incidencias, devolución y recuperación técnica. | Estimar con escenarios; no afirmar frecuencia observada sin datos. |

No se presupuestan cerraduras, lectores, cámaras, controladores ni dispositivos para esta solución. Los servicios de software elegidos se cotizan antes de contratarlos; no se incluyen precios inventados.

## 5. Modelo de tarifa

Propuesta parametrizable: por cada tamaño existe un precio base que cubre `h_base` horas y una tarifa por bloque adicional de `h_bloque` horas. El precio se registra como versión y se conserva una copia de las reglas aceptadas en la custodia.

```text
horas_extra = max(0, horas_contratadas - h_base)
bloques_extra = ceil(horas_extra / h_bloque)
precio_contratado = precio_base + bloques_extra * precio_bloque
```

Al recibir se registra el inicio y el vencimiento contratado. Una prórroga utiliza la política que consta en la versión aceptada y genera un cobro del servicio. Se informa el importe antes de confirmarlo. El código de retiro no se bloquea por un importe calculado en el navegador; el servidor comprueba la conciliación del servicio antes de autorizar la entrega.

El momento exacto de cobro, las fracciones, el redondeo monetario y el tratamiento de retrasos requieren validación comercial. Para el prototipo se diseña prepago al depositar y prórroga antes de retirar; se usan cantidades decimales y moneda BOB, sin modificar importes históricos al cambiar tarifas.

## 6. Capacidad y carga humana

```text
custodias_mes = Q
permanencia_media_dias = d
ubicaciones = C
dias_mes = D
ocupacion_media = (Q * d) / (C * D)
capacidad_teorica_mes = (C * D) / d
horas_atencion = Q * (min_recepcion + min_retiro + min_soporte) / 60
```

Estas expresiones suponen una ubicación por custodia y promedios estables. La capacidad teórica no garantiza atender picos: se inspeccionan tamaños, distribución de permanencias, horario y reservas de contingencia. Las ubicaciones bloqueadas se excluyen de la capacidad disponible durante su bloqueo.

## 7. Contribución, equilibrio y sensibilidad

```text
precio_medio = ingresos_servicio / custodias_completadas
costo_variable_unitario = costos_variables / custodias_completadas
contribucion_unitaria = precio_medio - costo_variable_unitario
resultado_operativo_mes = Q * contribucion_unitaria - costos_fijos_mes
punto_equilibrio_Q = costos_fijos_mes / contribucion_unitaria
```

Si la contribución es cero o negativa, no existe un punto de equilibrio finito con esa estructura. Hay que revisar precio o costos. Si el volumen de equilibrio supera la capacidad factible del espacio o del personal, el diseño no es viable aunque una proyección de ingresos parezca favorable.

El análisis se ejecuta para escenarios conservador, central y favorable variando frecuencia, permanencia, contribución y ocupación. Cada escenario identifica qué datos son observados y cuáles supuestos. Se reportan también devoluciones y tiempos de recuperación.

Para una evaluación de inversión posterior puede calcularse un flujo de caja y `VAN = -I0 + sum(FC_t/(1+r)^t)`. La tasa y los periodos deben ser coherentes y justificados; no se decide una tasa ni se ofrece una recomendación financiera con datos ausentes. La TIR no sustituye el análisis de capacidad o de supuestos.

## 8. Criterios de decisión

Continuar a un piloto público requiere evidencia de necesidad, personal disponible, procedimiento practicable, resultados de autorización e inventario satisfactorios y un escenario económico consistente. Si falla una condición se registra el motivo y se ajusta el diseño; no se concluye rentabilidad porque se completó el software.

Anexos del estudio: consentimientos o constancia de participación, fichas anónimas, registro de sesiones, cotizaciones fechadas, parámetros, cálculos y acta de decisión. Los resultados están pendientes de ejecución.
