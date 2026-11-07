# Análisis de metodologías, libros e ideas aplicadas

## 1. Método de elaboración y límites

Se inventariaron los ocho documentos existentes y sus cinco láminas; se contrastaron con el perfil y la restricción de hardware. Se verificaron autorías y conceptos con fuentes primarias: autores, editoriales, instituciones responsables de normas y artículos originales. La [bibliografía](02_bibliografia_verificada.md) identifica qué material se consultó: ficha, índice, extracto o recurso público. No se declara lectura íntegra de libros comerciales ni cumplimiento certificado de normas.

Los marcos se emplean para tomar decisiones y producir evidencia. Los siguientes ejemplos son aplicaciones originales al proyecto, no afirmaciones textuales de sus autores.

## 2. Negocio y descubrimiento

| Marco y obra | Idea utilizada | Aplicación a BUZON Xpress | Evidencia que exige |
|---|---|---|---|
| Osterwalder y Pigneur, *Business Model Generation* [B01]. | Explicitar cómo se crea, entrega y captura valor mediante un modelo de negocio. | Separar usuario beneficiario, pagador, punto anfitrión y operador; relacionar tarifa con recursos y actividades. | Lienzo con hipótesis y prueba de costos/ingresos. |
| Maurya, *Running Lean*, 3.ª ed. [B02]. | Formular y probar supuestos de un negocio mediante ciclos de aprendizaje. | Priorizar frecuencia del problema y disposición a pagar antes de ampliar funcionalidades. | Entrevistas, prueba de uso y decisiones de continuar o ajustar. |
| Christensen, Hall, Dillon y Duncan, *Competing Against Luck* [B03]. | Entender el progreso que busca la persona en sus circunstancias. | “Necesito dejar un objeto hoy para que otra persona lo recoja cuando pueda”. Investigar alternativas que ya usa y razones de cambio. | Relatos de episodios reales, sin confundir preferencias declaradas con demanda. |
| Kim y Mauborgne, *Blue Ocean Strategy* y ERAC [B04]. | Reconsiderar factores de valor mediante eliminar, reducir, aumentar y crear. | Eliminar coordinación simultánea, reducir incertidumbre, aumentar constancia y crear custodia accesible por tiempo. | Comparación observada; no afirmar mercado sin competencia. |
| Porter, *Competitive Advantage* [B05]. | Analizar las actividades que producen valor y costo. | Descomponer recepción, registro, almacenamiento, verificación y entrega; estimar trabajo humano por operación. | Tiempos observados, costos y puntos de error. |
| Moore, *Crossing the Chasm* [B06]. | Focalizar adopción en un segmento y una solución completa para su caso de uso. | Empezar en un punto y segmento accesible para un piloto. La elección de usuarios locales se valida; no presume expansión nacional. | Usuarios repetidos, servicio completo y referencias del piloto. |

Los dos lienzos cumplen propósitos distintos: Business Model Canvas describe socios, actividades y recursos; Lean Canvas explicita problema, solución, métricas y supuestos. Se presentan por separado en la formulación para evitar atribuir ambos instrumentos al mismo autor.

## 3. Ingeniería y análisis

Pressman y Maxim, *Software Engineering: A Practitioner's Approach*, 9.ª edición [I01], organizan contenidos de proceso, requisitos, diseño, calidad y gestión. Aquí se aplica una secuencia iterativa: comprender el servicio, modelar escenarios, diseñar componentes, verificar y revisar. Cada entrega atraviesa esas actividades; no se toma el índice del libro como un proceso obligatorio.

Cockburn, *Writing Effective Use Cases* [I02], aporta la descripción de metas, actores, alcance y escenarios. El catálogo emplea un nivel de resumen para ordenar capacidades y un nivel de objetivo de usuario para describir la interacción. Los casos incluyen garantías y extensiones; no se limitan a diagramas.

Larman, *Applying UML and Patterns*, 3.ª edición [I03], sustenta el uso de modelos de dominio, responsabilidades y desarrollo iterativo. Se aplica GRASP: Custodia conoce sus transiciones; Autorización conoce su vigencia; el servicio de aplicación coordina la recepción; la interfaz no decide permisos. Mermaid se utiliza como notación de documentación. Un grafo de actores se etiqueta como vista de interacción y no como diagrama UML formal de casos de uso.

Sommerville, *Software Engineering*, 10.ª edición [I04], aporta una perspectiva complementaria sobre ingeniería de requisitos, confiabilidad y sistemas. Se usa para distinguir una validación de software de una validación del servicio humano: una respuesta HTTP correcta no prueba que el operador entregó el objeto correcto.

FURPS+ [Q01] sirve para clasificar requisitos funcionales, usabilidad, confiabilidad, desempeño, soporte y restricciones. Es una taxonomía, no un proceso completo ni una norma equivalente a ISO/IEC/IEEE 29148. La ficha pública de esta última [Q02] se usa como referencia del campo de ingeniería de requisitos; no se afirma que se haya aplicado íntegramente una norma de acceso restringido.

## 4. Arquitectura y datos

Evans, *Domain-Driven Design* [A01], y su referencia pública [A02] orientan el vocabulario de custodia, recepción, ubicación y entrega. Se reconocen límites entre custodia, identidad, cobros del servicio y comunicaciones. En el primer producto son módulos de una aplicación; no se deduce que cada contexto necesite un servidor independiente.

Martin, *Clean Architecture* y su artículo [A03], justifican que las reglas de negocio no dependan del framework o del ORM. Se documentan puertos de repositorio, reloj, verificador y mensajería. El nombre de una carpeta no demuestra por sí mismo que esta separación exista en una implementación.

Fowler, *Patterns of Enterprise Application Architecture* [A04], aporta Unit of Work y control de concurrencia. Se propone una transacción por operación digital, comparando versiones y bloqueando la ubicación al asignar. “Optimistic Offline Lock” describe conflictos de transacciones de negocio; su nombre no garantiza funcionamiento sin conexión a internet.

Codd [D01] y Date [D02] sustentan el uso de relaciones, claves, dependencias e integridad. Se aplican al separar custodias de asignaciones, tarifas de cobros y credenciales de consultas públicas. Se documentan dependencias funcionales principales; no se declara BCNF del modelo completo sin demostración. Las copias históricas de precio en una custodia son una decisión deliberada de trazabilidad.

Brown y el modelo C4 [A05] permiten comunicar contexto, aplicaciones y componentes. Se incluyen vistas de contexto, contenedores y componentes porque responden preguntas diferentes; un contenedor C4 no es necesariamente un contenedor Docker.

## 5. Interfaz, entregas y calidad

Mandel, *The Elements of User Interface Design* [U01], agrupa sus reglas en control del usuario, reducción de memoria y consistencia. Se traducen en cancelación antes de recibir, instrucciones visibles y nombres de estado estables. La seguridad no se sacrifica para reducir pasos. El número de tres etapas de una landing es una decisión de comunicación; no se presenta como una consecuencia de la llamada ley de Miller.

Patton, *User Story Mapping* [P01], se aplica para recorrer la experiencia completa y cortar entregas horizontales: primero un depósito y retiro coherentes, luego recuperación y evaluación. Un panel muy elaborado sin persistencia no constituye una entrega del servicio.

Humble y Farley, *Continuous Delivery* [P02], inspiran compilación, pruebas, migraciones reproducibles y recuperación. Forsgren, Humble y Kim, *Accelerate* [P03], aportan el interés por medir desempeño de entrega y estabilidad. Las métricas de desarrollo se mantienen separadas de tiempo de atención y demanda. No se trasladan umbrales de empresas estudiadas como garantías del piloto.

OWASP [S01–S03] y WCAG 2.2 [U02] complementan las obras históricas con guías públicas sobre autenticación, autorización y accesibilidad. Se seleccionan controles concretos y se prueban; esta documentación no declara certificación de seguridad ni conformidad integral de accesibilidad.

## 6. Proceso de trabajo adoptado

1. Descubrir necesidades con entrevistas y observación autorizada del punto.
2. Refinar requisitos y riesgos; registrar decisiones y supuestos.
3. Modelar un escenario completo y sus errores antes de construirlo.
4. Diseñar el contrato, persistencia y pantalla de ese escenario.
5. Implementar y probar en un entorno con datos sintéticos.
6. Ensayar el servicio con personal y objetos de prueba.
7. Medir y revisar tanto el producto como el negocio.

Se trabaja con un tablero de pendientes, trabajo en curso y terminado. No se declara Scrum: no se han establecido sus roles, eventos ni compromisos. Una iteración finaliza con una demostración y evidencia de aceptación, no por haber transcurrido una semana.

## 7. Correcciones respecto a los antecedentes

- Se corrige *Competing Against Time*: sus autores son George Stalk y Thomas Hout [B07]; para JTBD se utiliza *Competing Against Luck* [B03].
- Se separan análisis competitivo y afirmaciones promocionales: no hay cifras de espera de competidores sin medición.
- Se distingue una bitácora de auditoría de Event Sourcing.
- Se elimina la equivalencia entre “casillero en base de datos” y dispositivo inteligente.
- Se sustituyen garantías de menos de cinco segundos, cero filas y cobertura nacional por metas y alcance verificables.
- Se distingue autorización digital, identidad civil, presencia del objeto y entrega humana. Cada una requiere evidencia propia.

El resultado metodológico se verifica siguiendo [requisito → caso de uso → datos/API/UI → prueba](../gestion/03_matriz_trazabilidad.md), no contando cuántos autores se mencionan.
