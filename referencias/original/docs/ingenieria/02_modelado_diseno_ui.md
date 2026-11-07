# Modelo de Diseño de Interfaz de Usuario (UI) y Wireframes: Buzzon Express
**Fase de Modelado según Roger S. Pressman y las Reglas de Oro de Theo Mandel**

---

## 1. Fundamentos de Diseño de Interfaz según Pressman

Roger S. Pressman destaca que la interfaz de usuario es la manifestación visible del software para el cliente. Siguiendo las **Tres Reglas de Oro de Theo Mandel** (*The Elements of User Interface Design*), el diseño de Buzzon Express se rige por:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      LAS TRES REGLAS DE ORO DE THEO MANDEL (EN PRESSMAN)                         │
├─────────────────────────┬───────────────────────────────────┬────────────────────────────────────┤
│ 1. Dar el control       │ 2. Reducir la carga de memoria    │ 3. Hacer la interfaz               │
│    al usuario           │    del usuario                    │    consistente                     │
├─────────────────────────┼───────────────────────────────────┼────────────────────────────────────┤
│ • El vendedor decide    │ • El comprador no requiere crear  │ • El código de color asignado      │
│   cuándo pre-registrar  │   cuenta con contraseñas complejas│   (Verde, Rojo, Azul, Amarillo) es │
│   y qué datos ingresar. │   (accede directo con su celular).│   idéntico en la celda física,     │
│ • El operador puede     │ • El operador no lee etiquetas    │   en la tablet del operador y en el│
│   conmutar entre modos  │   minúsculas: la interfaz proyecta│   portal del comprador.            │
│   (Recepción/Despacho)  │   bloques de color cromáticos de  │ • Misma terminología en todos los  │
│   con un solo toque.    │   alto contraste reconocibles <1s.│   puntos de contacto.              │
└─────────────────────────┴───────────────────────────────────┴────────────────────────────────────┘
```

---

## 2. Benchmarking Exhaustivo frente a la Competencia

Tomando como referencia el análisis del mercado local e internacional del proyecto:

```
┌─────────────────────────┬──────────────────────────┬──────────────────────────┬──────────────────────────┐
│ Criterio de Evaluación  │ Buzzon Express           │ Couriers Tradicionales   │ Lockers Internacionales  │
│                         │ (Nuestra Solución)       │ (Colmenas, Aguayo, Flota)│ (Amazon Hub, DHL, FedEx) │
├─────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Tiempo de retiro en     │ < 5 segundos             │ 3 a 10 minutos           │ 15 a 30 segundos         │
│ ventanilla              │ (Color + QR directo)     │ (Búsqueda manual)        │ (Pantalla táctil lenta)  │
├─────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Experiencia de fila     │ CERO FILAS               │ Filas de 30 a 60 min     │ Sin filas humanas        │
│                         │ (Pre-registro y colores) │ en ventanilla caótica    │ pero escasa cobertura    │
├─────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Consolidación           │ SÍ (Agrupa paquetes de   │ NO (Cobro y entrega      │ SÍ (Dentro de su propio  │
│ Multitienda             │ múltiples vendedoras)    │ individual e inconexa)   │ ecosistema cerrado)      │
├─────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Coste de Hardware       │ MUY BAJO (Estantería     │ BAJO (Cuadernos,         │ ALTÍSIMO ($10,000+ USD   │
│ (CAPEX de Punto)        │ modular + tablet/móvil)  │ libretas y estantes)     │ por casillero metálico)  │
├─────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Registro de Comprador   │ Cero fricción            │ Obliga a dictar cédula,  │ Requiere app o cuenta    │
│                         │ (Solo celular / QR)      │ llenar formularios papel │ corporativa registrada   │
├─────────────────────────┼──────────────────────────┼──────────────────────────┼──────────────────────────┤
│ Resiliencia a cortes    │ ALTA (IndexedDB local    │ Dependiente de papel o   │ Requiere conexión        │
│ de internet en feria    │ sincronizable en PWA)    │ sistemas web que caen    │ continua o satelital     │
└─────────────────────────┴──────────────────────────┴──────────────────────────┴──────────────────────────┘
```

---

## 3. Wireframe Visual de la Landing Page

Se ha diseñado y generado el wireframe de alta fidelidad para la pantalla principal (Landing Page), el cual se encuentra preservado en `docs/wireframes/landing_page_wireframe.jpg`:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                             ESTRUCTURA VISUAL DEL WIREFRAME GENERADO                             │
├──────────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                                  │
│  [Logo Buzzon]   [ Input Búsqueda Rápida Guía/Celular... ]       [Iniciar Sesión] [Registrarme]  │
│                                                                                                  │
│  ┌──────────────────────────────────────────────┐     ┌────────────────────────────────────────┐ │
│  │ Logística Inteligente para                   │     │  ┌──────────────────────────────────┐  │ │
│  │ Social Commerce en Bolivia                   │     │  │  CASILLERO VERDE ESMERALDA       │  │ │
│  │                                              │     │  │  V-A01                           │  │ │
│  │ Centraliza tus envíos de TikTok Live y redes.│     │  │  [ QR Retiro Inmediato ]         │  │ │
│  │ Almacenamiento temporal y despacho en 5s.    │     │  └──────────────────────────────────┘  │ │
│  │                                              │     │  Entrega guiada por colores en <5s     │ │
│  │  [ Empezar a Enviar Gratis ] [ Rastrear ]    │     └────────────────────────────────────────┘ │
│  └──────────────────────────────────────────────┘                                                │
│                                                                                                  │
│ ──────────────────────────────────────────────────────────────────────────────────────────────── │
│                                TABLA COMPARATIVA DE MERCADO                                      │
│  • Buzzon Express vs Couriers Locales (Colmenas, Aguayo, Flotas) vs Lockers (Amazon, DHL)        │
│ ──────────────────────────────────────────────────────────────────────────────────────────────── │
│                                                                                                  │
│                                 FLUJO EN 3 PASOS (CERO GRAVEDAD)                                 │
│       ( 1 )                           ( 2 )                           ( 3 )                      │
│   Pre-registro Web               Ventanilla Express              Retiro con QR en 5s             │
│   Introduce celular              Llegas y dejas paquetes         Pantalla se tiñe de color       │
│   del cliente en casa.           sin filas ni papeleos.          y entrega en 1 instante.        │
│                                                                                                  │
│ ──────────────────────────────────────────────────────────────────────────────────────────────── │
│                              BLOQUES CROMÁTICOS DE INNOVACIÓN                                    │
│  ┌───────────────┐     ┌───────────────┐     ┌───────────────┐     ┌───────────────┐             │
│  │    VERDE      │     │     ROJO      │     │     AZUL      │     │   AMARILLO    │             │
│  │  Cero Filas   │     │ Tarifa Plana  │     │ Consolidación │     │ Sincronización│             │
│  │               │     │               │     │  Multitienda  │     │  Trilateral   │             │
│  └───────────────┘     └───────────────┘     └───────────────┘     └───────────────┘             │
│                                                                                                  │
│  [ CTA Final: "Tu negocio no debería tener límites físicos" - Botón Registro ]                   │
│  [ Footer: Red de Puntos en La Paz/SCZ, Enlaces Legales, Contacto ]                              │
└──────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Especificación Detallada de Componentes de la Interfaz

### 4.1. Sección 1: Header y Barra de Utilidad Superior
* **Logotipo:** Isotipo institucional con isotipo de caja dinámica + texto tipográfico *Buzzon Express*.
* **Buscador Universal de Tracking:** Input flotante directo donde el comprador puede pegar su código o celular para ver el estado de su envío inmediatamente, sin iniciar sesión (aplicando la regla de *reducir carga cognitiva* de Theo Mandel).
* **Acciones:** Botón secundario *"Iniciar Sesión"* (para vendedores y operadores registrados) y botón primario *"Registrarme"*.

### 4.2. Sección 2: Hero Section (Patrón F de Usabilidad)
* **Titular de Alto Impacto:** *"Logística Inteligente para Social Commerce en Bolivia"*.
* **Subtítulo:** Enfocado en los beneficios medibles: *"Despacha y recoge paquetes de TikTok Live, Facebook Marketplace e Instagram sin filas y en menos de 5 segundos"*.
* **Prueba de Concepto Visual Interactiva:** A la derecha del texto, una maqueta interactiva del casillero verde `V-A01` con su código QR. Esto comunica al usuario la sencillez visual del producto antes de registrarse.

### 4.3. Sección 3: Matriz Comparativa (Análisis Competitivo Visible)
* Los usuarios del comercio informal y social commerce en Bolivia sufren a diario el maltrato de las paqueterías tradicionales. Esta sección desglosa transparentemente las ventajas:
  1. *Fila en mostrador:* 45 minutos (Agencias) vs. 0 minutos (Buzzon).
  2. *Búsqueda:* Cuaderno manual (Agencias) vs. Bloque de color en pantalla (Buzzon).
  3. *Consolidación:* Cobro triple (Agencias) vs. Descuento y paquete único (Buzzon).

### 4.4. Sección 4: El Flujo en Tres Pasos (Ley de Miller)
Agrupamiento de la información en 3 unidades discretas (*chunks*):
1. **Paso 1 - Pre-registro desde el celular:** El vendedor ingresa número del cliente y producto; obtiene el código de asignación.
2. **Paso 2 - Entrega en Ventanilla:** Deposita sin filas. El operador escanea y confirma recepción.
3. **Paso 3 - Retiro Instantáneo con QR:** El cliente se acerca al punto, muestra su QR o dicta su teléfono, y la pantalla cromática guía el despacho en menos de 5 segundos.

### 4.5. Sección 5: Los Bloques Cromáticos (Identidad de Dominio)
Cuatro tarjetas con los colores oficiales del sistema que educan al cliente sobre cómo funciona la categorización visual:
* **Verde Esmeralda (`#10B981`):** Simboliza *Cero Filas* y flujo rápido.
* **Rojo Carmesí (`#EF4444`):** Simboliza *Tarifa Plana Transparente* (sin recargos ocultos por peso o volumen imprevisto).
* **Azul Cobalto (`#3B82F6`):** Simboliza *Consolidación Inteligente* de múltiples compras en un solo casillero.
* **Amarillo Ámbar (`#F59E0B`):** Simboliza *Sincronización Trilateral* y cobro seguro contra entrega (COD).

---

## 5. Diseño de Navegación y Mapa de Rutas (Frontend React)

```
                              [ LANDING PAGE (/) ]
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
[/tracking?code=...]            [/login]                      [/register]
Portal de Seguimiento           Acceso por Roles              Onboarding Vendedor
Comprador (Sin Login)                  │                             │
                                ┌──────┴──────┐                      │
                                ▼             ▼                      ▼
                       [/seller/dashboard]  [/operator/terminal]  [/seller/onboarding]
                       Gestión de Envíos    Ventanilla Táctil     Configuración inicial
                       y Pre-registro       (Recepción / Despacho)
```
