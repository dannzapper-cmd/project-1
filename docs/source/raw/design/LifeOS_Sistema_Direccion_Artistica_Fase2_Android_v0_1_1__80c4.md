# Life OS · Sistema Operativo de Dirección Artística y Rediseño Android

**Versión:** v0.1  
**Estado:** Documento rector vivo para la fase artística de Fase 2  
**Plataforma objetivo actual:** Android nativo  
**Stack de implementación:** Kotlin + Jetpack Compose  
**Orquestación:** Danny dirige; ChatGPT y Claude diseñan/auditan; Cursor Composer 2.5 ejecuta  
**Fecha:** 2026-07-16

---

## 0. Propósito

Este documento define cómo convertir la anatomía funcional ya construida de Life OS en una experiencia artística, sensorial y técnicamente excelente, sin romper el “backend del frontend”: navegación, estado, owners, reducers, eventos, mutations, receipts, Undo, persistencia, contratos demo, permisos, privacidad, accesibilidad ni preparación futura para backend e IA reales.

No es un moodboard ni una lista de tendencias. Es el sistema de trabajo para que:

1. las referencias visuales de Danny;
2. los documentos de Cognitive Glass, Digitalismo Humanista, motion, haptics e intimidad;
3. Figma y sus recursos;
4. MCPs y plugins confiables;
5. Cursor Composer 2.5;
6. Kotlin y Jetpack Compose;
7. auditorías de ChatGPT, Claude y Cursor;

funcionen como una sola cadena de diseño y fabricación.

---

# 1. Objetivo

Rediseñar toda la aplicación durante la fase artística de Fase 2, superficie por superficie y componente por componente, hasta que Life OS deje de sentirse como una aplicación gubernamental formal, genérica o simplemente funcional y adquiera:

- identidad artística propia;
- lujo humano y funcional;
- diseño blanco vivo;
- precisión negra;
- color arcoíris semántico;
- tipografía de primer nivel;
- materiales digitales;
- motion con intención;
- haptics semánticos;
- ergonomía emocional;
- accesibilidad;
- rendimiento nativo;
- continuidad visual;
- personalidad diferenciada por nodo;
- una sola alma reconocible en todo el producto.

---

# 2. Dirección de Danny: especificaciones obligatorias

## 2.1 Blanco como arquitectura principal

El blanco es el campo predominante de Life OS.

No es crema, beige ni marfil por defecto. Tampoco debe sentirse clínico, bancario, frío o estéril.

La humanidad del blanco se construye mediante:

- luz;
- sombra;
- profundidad;
- gradientes casi imperceptibles;
- tactilidad;
- movimiento;
- haptics;
- tipografía;
- microcopy;
- proporción;
- color contextual;
- comportamiento respetuoso.

## 2.2 Negro como precisión y contraste

El negro se usa principalmente para:

- texto;
- iconografía;
- estructura;
- cifras;
- contornos;
- contraste;
- controles que necesitan autoridad visual.

No debe convertir toda la interfaz en un sistema blanco y negro rígido ni competir con el color semántico.

## 2.3 Arcoíris como vida, no “cromatismo”

Life OS no debe ser “cromático” en el sentido de gradientes iridiscentes permanentes, interfaces tornasoladas o decoración multicolor constante.

“Arcoíris” significa disponer de todo el espectro cromático como vocabulario semántico. El color aparece según:

- nodo;
- acción;
- estado;
- prioridad;
- riesgo;
- progreso;
- confirmación;
- movimiento de LIAH;
- identidad de un objeto;
- evento contextual;
- interacción ganada.

El color debe ser preciso, escaso y significativo. La pantalla continúa siendo esencialmente blanca.

## 2.4 Luz reactiva

Una referencia clave del PDF no se seleccionó por su color cromático, sino porque la percepción de la luz sobre el botón cambiaba mientras el botón se movía.

Esto se convierte en una regla:

> La luz digital debe reaccionar al movimiento, orientación, presión, profundidad o estado cuando dicha reacción ayude a que el objeto se sienta vivo.

Aplicaciones posibles:

- desplazamiento del highlight durante press/drag;
- reflexión que cambia con la inclinación o el gesto;
- borde luminoso que recorre una superficie al confirmar;
- sombreado dinámico durante transformaciones;
- iluminación de LIAH vinculada a voz, escucha o procesamiento;
- “sheen” breve y no infinito cuando una acción se completa.

No usar iridiscencia o brillo continuo sin función.

## 2.5 Diversión inteligente

Life OS debe ser divertida sin volverse infantil, ruidosa ni manipulativa.

La diversión nace de:

- tactilidad;
- sorpresa controlada;
- transformaciones elegantes;
- objetos que responden;
- color ganado;
- avatares con carácter;
- símbolos claros;
- microanimaciones;
- cierre satisfactorio de acciones;
- composición viva;
- pequeños momentos de belleza.

No nace de:

- confeti constante;
- gacha;
- estímulos de casino;
- exceso de rebote;
- colores aleatorios;
- personajes invasivos;
- recompensas variables;
- movimiento permanente de todo.

---

# 3. Lectura artística del PDF “DISEÑO”

El PDF funciona como corpus de referencias, no como catálogo para copiar literalmente.

## 3.1 Dashboards técnicos blancos

Se extrae:

- modularidad;
- aire;
- densidad organizada;
- simetría;
- controles circulares;
- datos jerarquizados;
- superficies con volumen;
- profundidad tenue;
- precisión industrial.

No se copia:

- densidad de escritorio en móvil;
- apariencia SaaS genérica;
- tablas demasiado pequeñas;
- controles decorativos;
- composición imposible para una mano.

## 3.2 Botones de cristal y agentes

Se extrae:

- objeto focal;
- material translúcido controlado;
- luz interna;
- presencia;
- estado;
- affordance;
- respuesta visual antes y después del toque.

Aplicación principal:

- LIAH;
- comandos;
- confirmaciones;
- Quick Dial;
- acciones destacadas.

## 3.3 Neumorphism

Se adopta:

- sensación de presión;
- superficies empotradas o elevadas;
- sombras duales cuidadosamente calibradas;
- controles que parecen tener masa.

Se rechaza:

- bajo contraste;
- botones que no se distinguen;
- uso en textos densos;
- toda la app hecha con neomorfismo;
- sombras costosas o inconsistentes.

## 3.4 Glassmorphism

Se adopta:

- relación entre planos;
- continuidad espacial;
- refracción o blur selectivo;
- profundidad;
- superficie contextual.

Se rechaza:

- cristal por todas partes;
- texto sobre fondos impredecibles;
- transparencia que rompa WCAG;
- blur pesado en listas;
- estética “futurista” genérica.

## 3.5 Claymorphism

Se adopta:

- alegría táctil;
- volumen amable;
- color controlado;
- objetos memorables;
- formas con personalidad.

Se rechaza:

- infantilización;
- plastilina permanente;
- iconos 3D incongruentes;
- exceso de volumen en información seria.

Uso potencial:

- onboarding;
- estados vacíos;
- logros ganados;
- Salud, Hogar o Personal en momentos específicos;
- pequeñas ilustraciones y avatares.

## 3.6 Brutalism

Se adopta:

- contraste;
- carácter;
- decisiones tipográficas valientes;
- jerarquía inequívoca;
- composición gráfica con tensión.

Se rechaza:

- caos;
- bordes agresivos por moda;
- legibilidad baja;
- aspecto “anti-diseño”;
- incompatibilidad con la calma de Life OS.

Uso potencial:

- campañas, posters internos, momentos editoriales;
- Mundo/Social;
- contenido cultural;
- pantallas excepcionales, no la gramática base.

## 3.7 Spatial UI

Se adopta:

- capas;
- profundidad;
- continuidad;
- elementos que mantienen identidad al transformarse;
- sensación de espacio navegable.

Se rechaza:

- copiar interfaces de gafas en teléfono;
- exceso de transparencias;
- paralaje decorativo;
- profundidad que confunda jerarquía.

---

# 4. Veredicto de herramientas

## 4.1 Figma

**Rol:** herramienta principal de exploración visual y especificación.

Debe servir para:

- frames aprobados;
- auto layout;
- componentes;
- variantes;
- variables;
- prototipos;
- iconografía;
- composición;
- anotaciones;
- estados;
- referencias;
- handoff visual;
- vínculo selectivo con Cursor mediante MCP.

No será la única fuente de verdad. La memoria canónica también vivirá en GitHub.

## 4.2 Cursor Composer 2.5

**Rol:** taller principal de implementación y automatización.

Cursor debe hacer todo lo razonablemente automatizable:

- instalar/configurar MCPs y plugins aprobados;
- consultar Figma;
- guardar contexto;
- normalizar tokens;
- crear documentación;
- generar componentes Compose;
- implementar motion;
- integrar haptics;
- crear previews;
- ejecutar pruebas;
- comparar resultados;
- autoauditar;
- corregir;
- actualizar checkpoints y evidencia.

Cursor no debe decidir por sí solo la dirección artística final. Puede proponer, pero Danny aprueba y ChatGPT/Claude auditan.

## 4.3 Framer

**Rol:** no usar como fuente canónica de la app Android.

Puede usarse después para:

- landing page;
- IOUMAN web;
- prototipos web;
- experimentos promocionales;
- escenas de presentación.

Framer Motion no es la librería de motion de Android. La app usa Compose Animation, gestos, Canvas, GraphicsLayer, shaders y APIs Android.

## 4.4 Jetpack Compose

**Rol:** material productivo real.

Debe resolver:

- estructura visual;
- estados;
- transformaciones;
- navegación;
- microinteracciones;
- gestos;
- drag;
- presses;
- iluminación dinámica viable;
- gráficos;
- Quick Dial;
- superficies contextuales;
- accesibilidad;
- motion interrumpible;
- haptics.

## 4.5 Lottie

**Rol:** animaciones vectoriales cerradas.

Ideal para:

- ilustraciones;
- iconos animados;
- onboarding;
- estados vacíos;
- confirmaciones;
- pequeños loops cuidadosamente presupuestados.

No usar para:

- navegación;
- layouts completos;
- widgets dinámicos;
- lógica crítica;
- controles semánticos centrales;
- motion que dependa de datos complejos.

## 4.6 Rive

**Rol:** laboratorio futuro para LIAH y objetos interactivos complejos.

Puede ser valioso por:

- state machines;
- data binding;
- interacción;
- animación reactiva;
- identidad visual persistente.

No depender de él mientras el flujo gratuito no permita exportar e integrar de forma sostenible. Mantener arquitectura reemplazable.

## 4.7 Penpot

**Rol:** respaldo abierto y plan de soberanía.

Útil para:

- diseño open source;
- autoalojamiento futuro;
- evitar dependencia total de Figma;
- archivos basados en estándares abiertos;
- experimentación diseño-código.

No sustituye inicialmente a Figma porque el ecosistema y el MCP oficial de Figma son más estratégicos para esta fase.

---

# 5. Realidad del Figma MCP gratuito

## 5.1 Límite confirmado

Figma Starter dispone actualmente de **seis llamadas de herramientas MCP al mes**.

Esto impide usar el MCP como conexión permanente para cientos de pantallas.

## 5.1.1 Decisión operativa de Life OS

Life OS no esperará un mes entre extracciones.

Las seis llamadas disponibles se consumirán en un sprint corto e intensivo, después de preparar cuidadosamente:

- los recursos seleccionados;
- los frames consolidados;
- las preguntas;
- el formato de salida;
- las rutas donde Cursor guardará cada resultado;
- la traducción requerida a Android nativo, Kotlin y Jetpack Compose.

El límite mensual es una restricción del proveedor, no una cadencia de trabajo del proyecto.


## 5.2 Qué significa “una llamada”

Cada invocación de una herramienta del servidor MCP cuenta. No debemos asumir que:

- una conversación completa equivale a una llamada;
- el agente puede extraer toda una biblioteca ilimitada;
- seis llamadas permiten copiar toda Figma Community;
- una llamada capturará cada detalle de un sistema gigantesco.

## 5.3 Estrategia correcta: extracción intensiva en pocos días

Las seis llamadas se usarán **todas en pocos días**, como sesiones intensivas de extracción de alto valor sobre selecciones previamente preparadas y consolidadas. No se reservarán para ciclos mensuales ni se ralentizará la construcción esperando nuevas cuotas.

Antes de usar una llamada:

1. Danny y los agentes seleccionan recursos.
2. Se descartan recursos mediocres o redundantes.
3. Se agrupan referencias en un solo archivo o página de Figma.
4. Se organiza por secciones y frames.
5. Se nombran capas, componentes y variables.
6. Se decide exactamente qué información se quiere extraer.
7. Se prepara el prompt para Kotlin + Jetpack Compose.
8. Se crea un destino en el repositorio para guardar la respuesta.

## 5.4 Plan intensivo para consumir las seis llamadas

### Llamada 1 · Fundación visual

Extraer:

- paleta;
- tipografía;
- escala;
- spacing;
- radios;
- sombras;
- bordes;
- materiales;
- iconografía;
- densidad;
- grid.

### Llamada 2 · Primitivos de interacción

Extraer:

- botones;
- inputs;
- chips;
- toggles;
- sliders;
- dropdowns;
- tabs;
- navegación;
- estados press/focus/disabled/error.

### Llamada 3 · Widgets y dashboards

Extraer:

- anatomía de cards/widgets;
- gráficos;
- jerarquías;
- compact/expanded;
- responsive behavior;
- data density.

### Llamada 4 · LIAH, Quick Dial y objetos vivos

Extraer:

- estados;
- geometría;
- luz;
- capas;
- transforms;
- motion intent;
- gestos;
- confirmaciones.

### Llamada 5 · Identidad de nodos

Extraer:

- Salud;
- Finanzas;
- Personal;
- Hogar;
- Movilidad;
- Mundo/Social;
- Profesión;
- Mis Datos;
- Emergencia.

### Llamada 6 · Flujo aprobado, auditoría o extracción final

Usar para:

- un flujo clave completo;
- comparación;
- corrección;
- extracción de un frame final;
- actualización de un sistema modificado.

La distribución puede cambiar por prioridad. Las seis llamadas deben prepararse y ejecutarse en una ventana corta de trabajo, idealmente dentro de uno a pocos días. No gastar llamadas para explorar sin preparar.

## 5.5 Qué debe guardar Cursor de cada llamada

Guardar dos capas:

### Capa A · Captura cruda

```text
docs/design/figma-harvest/raw/SPRINT_FIGMA_001/
├── call_01_prompt.md
├── call_01_raw_response.md
├── call_01_selection.md
├── call_01_screenshot.png
└── call_01_metadata.md
```

### Capa B · Contexto normalizado

```text
docs/design/figma-harvest/normalized/
├── FIGMA_FOUNDATION.md
├── FIGMA_COMPONENTS.md
├── FIGMA_WIDGETS.md
├── FIGMA_LIAH_QUICK_DIAL.md
├── FIGMA_NODE_IDENTITIES.md
└── FIGMA_FLOW_CONTRACTS.md
```

Además, Cursor debe convertir lo estable en:

```text
design-system/
├── tokens/
├── components/
├── motion/
├── haptics/
├── icons/
├── charts/
└── themes/
```

## 5.6 Manual export como vía gratuita complementaria

Aunque el MCP esté limitado, Danny puede exportar manualmente desde Figma:

- PNG;
- SVG;
- PDF;
- assets;
- capturas;
- prototipos grabados;
- variables o especificaciones documentadas.

Cursor puede leer esos archivos locales y el repositorio sin consumir llamadas MCP.

La estrategia no es “hacer trampa” vulnerando planes o límites. Es usar eficientemente las capacidades gratuitas permitidas y preservar legalmente el contexto obtenido.

---

# 6. Selección de recursos de Figma Community

No duplicar cientos de archivos.

Cada candidato se evalúa con una matriz:

| Criterio | Peso |
|---|---:|
| Calidad artística | 20 |
| Coherencia con Life OS | 20 |
| Estructura interna | 15 |
| Auto layout | 10 |
| Variables y tokens | 10 |
| Componentes/variantes | 10 |
| Adaptabilidad móvil | 5 |
| Accesibilidad | 5 |
| Licencia y uso | 5 |

Puntaje mínimo recomendado: 75/100.

## 6.1 Categorías que sí investigar

- design systems móviles;
- dashboards blancos de alta densidad;
- interfaces financieras;
- salud y bienestar;
- spatial UI;
- glass controlado;
- neumorfismo accesible;
- sistemas de motion;
- sistemas de gráficos;
- iconografía lineal;
- iconografía de objetos;
- avatares;
- IA/orbes/agentes;
- quick controls;
- radial navigation;
- journaling;
- privacidad y datos;
- estados vacíos;
- onboarding.

## 6.2 Qué descartar

- archivos sin componentes;
- frames planos sin auto layout;
- imitaciones de Dribbble imposibles de implementar;
- kits web presentados como mobile;
- dashboards de escritorio;
- glass con contraste insuficiente;
- neumorfismo ilegible;
- UI kits sin licencia clara;
- assets generativos sin procedencia;
- “futurismo” genérico azul/morado;
- estilos incompatibles entre sí;
- recursos cuyo valor sea solo una captura bonita.

## 6.3 Resultado esperado de la investigación

Para cada recurso:

```text
Nombre:
URL:
Autor:
Licencia:
Categoría:
Qué aporta:
Qué no copiar:
Aplicación en Life OS:
Riesgo técnico:
Riesgo visual:
Puntuación:
Decisión: adoptar / extraer principios / descartar
```

---

# 7. MCPs, plugins, skills y reglas

## 7.1 Set inicial mínimo

### Figma oficial

Uso:

- `get_design_context`;
- screenshots selectivos;
- variables y componentes;
- prompts personalizados;
- skills de integración.

### Contexto de documentación oficial

Usar un MCP o skill confiable que consulte documentación actual de:

- Kotlin;
- Jetpack Compose;
- Android APIs;
- Lottie Android;
- Rive Android cuando corresponda;
- testing;
- accesibilidad;
- performance.

### GitHub

Uso:

- issues;
- PRs;
- decisiones;
- evidencia;
- checkpoints;
- auditorías;
- historial.

No instalar MCPs de moda sin revisión.

## 7.2 Regla de seguridad

Antes de instalar cualquier MCP/plugin:

1. identificar publisher;
2. preferir oficial o verificado;
3. revisar repositorio y licencia;
4. revisar permisos;
5. revisar datos enviados;
6. limitar secretos;
7. configurar allowlist;
8. fijar versión;
9. documentar instalación;
10. probar en una rama o entorno seguro.

## 7.3 Plugin interno de Life OS

La mejor inversión no será acumular plugins externos. Será crear un plugin o paquete interno para Cursor que incluya:

- rules;
- skills;
- subagents;
- commands;
- hooks;
- plantillas;
- checklist;
- rutas canónicas;
- acceso a documentos;
- protocolo Figma;
- protocolo Compose;
- protocolo de auditoría;
- protocolo de checkpoint;
- Definition of Done artístico.

Nombre provisional:

```text
.cursor/plugins/lifeos-art-direction/
```

---

# 8. Arquitectura de diseño en el repositorio

```text
docs/design/
├── ART_DIRECTION_MASTER.md
├── VISUAL_REFERENCE_ATLAS.md
├── REFERENCE_DECISIONS.md
├── FIGMA_WORKFLOW.md
├── DESIGN_AUDIT_PROTOCOL.md
├── NODE_ART_IDENTITIES.md
├── ACCESSIBILITY_VISUAL_RULES.md
├── PERFORMANCE_VISUAL_BUDGETS.md
├── figma-harvest/
│   ├── raw/
│   └── normalized/
├── motion/
├── haptics/
├── sound/
├── research/
└── evidence/

design-system/
├── tokens/
│   ├── color/
│   ├── typography/
│   ├── spacing/
│   ├── shape/
│   ├── elevation/
│   ├── motion/
│   └── haptics/
├── primitives/
├── components/
├── patterns/
├── charts/
├── illustrations/
├── avatars/
└── icons/
```

---

# 9. Protección del backend del frontend

## 9.1 Regla de separación

El rediseño no puede alterar silenciosamente:

- domain models;
- owners;
- reducers;
- events;
- mutations;
- receipts;
- Undo;
- Saver;
- migrations;
- persistence;
- navigation contracts;
- deep links;
- permissions;
- consent;
- demo providers;
- future provider interfaces;
- data governance.

## 9.2 Capas recomendadas

```text
Dominio / datos
      ↓
Estado canónico
      ↓
UI models
      ↓
Componentes semánticos Life OS
      ↓
Tokens y materiales
      ↓
Motion + haptics
      ↓
Render Compose
```

## 9.3 Componentes semánticos

No crear “ButtonBlue”, “CardGlass” o “BigWhiteBox”.

Crear componentes con intención:

```text
LifeActionButton
LifeWidget
LifeNodeHeader
LifeInsight
LifeMetric
LifeTimeline
LifeConfirmation
LifePrivacyIndicator
LifeEmergencyControl
LiahOrb
QuickDial
```

Cada componente debe declarar:

- propósito;
- estado;
- interacción;
- riesgo;
- accesibilidad;
- motion role;
- haptic role;
- performance budget;
- test coverage;
- variantes aprobadas.

---

# 10. Motion

## 10.1 Orden de implementación

1. estética estática;
2. estados visuales;
3. interacción y gestos;
4. motion;
5. haptics;
6. sonido después.

## 10.2 Familias

- press/release;
- selección;
- navegación;
- expansión;
- transformación;
- drag/snap;
- loading real;
- confirmación;
- error;
- protección;
- presencia de LIAH;
- visualización de voz;
- continuidad entre pantallas.

## 10.3 Animaciones infinitas

Permitidas solo cuando comunican:

- escucha;
- procesamiento;
- sincronización;
- progreso real;
- estado activo;
- respiración mínima de una presencia viva.

Obligaciones:

- detener fuera de pantalla;
- respetar Reduce Motion;
- reducir en ahorro de batería;
- evitar recomposición innecesaria;
- medir jank;
- limitar superficies simultáneas;
- ofrecer estado estático equivalente.

## 10.4 Luz y material en movimiento

Investigar:

- `graphicsLayer`;
- `Brush`;
- gradientes;
- shaders;
- `RenderEffect`;
- Canvas;
- transforms;
- clipping;
- shadow APIs.

Usar efectos avanzados solo con fallback y presupuesto.

---

# 11. Haptics

Las hápticas son semánticas.

Familias mínimas:

- contacto;
- selección;
- snap;
- confirmación;
- transformación;
- advertencia;
- error;
- protección;
- emergencia.

Priorizar feedback definido por el sistema para adaptarse al hardware. Los efectos personalizados deben degradarse con dignidad.

---

# 12. Sonido

El sonido se pospone hasta después de consolidar:

- sistema visual;
- motion;
- haptics;
- estados;
- identidad de LIAH.

Preparar desde ahora un contrato:

```text
SoundRole
├── Contact
├── Selection
├── Confirmation
├── Completion
├── LiahListening
├── LiahProcessing
├── Warning
├── Error
└── Emergency
```

Nada debe depender exclusivamente del sonido.

---

# 13. Flujo operativo por superficie

## Paso 1 · Baseline

Cursor:

- lee documentos;
- inspecciona código;
- captura estado actual;
- identifica owners;
- identifica tests;
- crea checkpoint;
- registra riesgos.

## Paso 2 · Brief artístico

ChatGPT/Claude:

- definen objetivo;
- referencias;
- composición;
- jerarquía;
- color;
- material;
- tipografía;
- motion;
- haptics;
- restricciones;
- criterio de terminado.

Danny aprueba.

## Paso 3 · Figma o especificación visual

- se crea/selecciona frame;
- se documentan estados;
- se decide si merece una llamada MCP;
- se exporta material necesario.

## Paso 4 · Implementación Cursor

Composer 2.5:

- crea tokens/componentes reutilizables;
- implementa primera pasada completa;
- no rompe owners;
- ejecuta tests;
- actualiza checkpoint.

## Paso 5 · Autoauditoría independiente

Composer:

- compara contra diseño;
- revisa UX;
- revisa estados;
- revisa accesibilidad;
- revisa performance;
- corrige;
- repite pruebas;
- documenta evidencia.

## Paso 6 · Auditoría externa

ChatGPT y Claude revisan desde perspectivas distintas:

- arte y coherencia;
- producto y UX;
- arquitectura;
- accesibilidad;
- privacidad;
- performance;
- motion/haptics;
- deuda.

## Paso 7 · Aprobación de Danny

Danny prueba:

- sensación;
- claridad;
- belleza;
- diversión;
- carácter;
- fidelidad a su visión.

## Paso 8 · Cierre

- commit;
- evidencia selectiva;
- decisión registrada;
- checkpoint cerrado;
- siguiente superficie.

---

# 14. Evidencia sin burocracia

No crear evidencia excesiva por cada microcambio.

Guardar evidencia en gates:

- baseline;
- diseño aprobado;
- estados principales;
- grabación de motion;
- accesibilidad;
- performance;
- resultado final;
- before/after;
- defectos importantes corregidos.

Toda evidencia debe evitar datos sensibles.

---

# 15. Qué puede hacer Cursor y qué requiere dirección humana

## Cursor puede hacer

- investigación técnica;
- extracción mediante MCP;
- documentación;
- tokens;
- componentes;
- implementación;
- pruebas;
- automatización;
- comparación;
- auditoría;
- corrección;
- mantenimiento;
- evidencia;
- refactors.

## Cursor no debe decidir solo

- gusto final;
- identidad de marca;
- qué emoción debe dominar;
- qué referencias representan a Life OS;
- qué combinación artística es correcta;
- si una superficie “se siente” íntima;
- cuándo la diversión cruza hacia infantilización;
- qué imperfección artística es deseable.

Danny es director creativo y autoridad final. ChatGPT y Claude funcionan como coarquitectos y críticos. Cursor fabrica y verifica.

---

# 16. Decisiones firmes

1. Android nativo es el objetivo actual.
2. Kotlin + Jetpack Compose es el material de producción.
3. Cursor Composer 2.5 ejecutará la mayor parte posible.
4. Figma gratuito será la mesa principal de diseño.
5. El MCP oficial de Figma se usará en cosechas preparadas.
6. Todo contexto extraído se persistirá y normalizará en GitHub.
7. Framer no será la base de la app Android.
8. Lottie se reservará para animaciones cerradas.
9. Rive se evaluará sin crear dependencia económica actual.
10. Penpot será respaldo abierto, no herramienta principal inicial.
11. El sistema interno de Cursor será más importante que acumular MCPs.
12. El rediseño no tocará silenciosamente el backend del frontend.
13. Cada superficie será auditada tras implementación.
14. Sonido vendrá después de visual, motion y haptics.
15. La app será blanca, divertida, precisa, viva y cromáticamente semántica.
16. El diseño final será una combinación coherente de referencias, nunca un collage.

---

# 17. Próximas acciones

1. Crear inventario de recursos visuales del PDF.
2. Investigar y puntuar recursos reales de Figma Community.
3. Elegir 5–10 recursos de máximo valor, no decenas.
4. Instalar el plugin oficial de Figma en Cursor.
5. Crear el plugin interno `lifeos-art-direction`.
6. Crear carpetas de harvest y documentos canónicos.
7. Definir la primera cosecha MCP.
8. Elegir la primera superficie insignia.
9. Producir brief artístico.
10. Implementar, auditar y corregir.

---

# 18. Fuentes actuales verificadas

- Figma MCP rate limits: https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/
- Figma MCP remote setup for Cursor: https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- Figma MCP local setup: https://developers.figma.com/docs/figma-mcp-server/local-server-installation/
- Figma MCP tools/prompts: https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/
- Figma custom rules: https://developers.figma.com/docs/figma-mcp-server/add-custom-rules/
- Figma create skills: https://developers.figma.com/docs/figma-mcp-server/create-skills/
- Figma write to canvas: https://developers.figma.com/docs/figma-mcp-server/write-to-canvas/
- Cursor plugins: https://cursor.com/docs/plugins
- Cursor marketplace: https://cursor.com/marketplace
- Cursor plugin architecture: https://cursor.com/blog/marketplace
- Compose animation: https://developer.android.com/develop/ui/compose/animation/quick-guide
- Compose gestures: https://developer.android.com/develop/ui/compose/touch-input/pointer-input/tap-and-press
- Android haptics: https://developer.android.com/develop/ui/views/haptics
- Haptics principles: https://developer.android.com/develop/ui/views/haptics/haptics-principles
- Custom haptics: https://developer.android.com/develop/ui/views/haptics/custom-haptic-effects
- Compose gradients/shaders: https://developer.android.com/develop/ui/compose/graphics/draw/brush
- Android rendering performance: https://developer.android.com/topic/performance/vitals/render
- Compose foundation: https://developer.android.com/jetpack/androidx/releases/compose-foundation
- Lottie specification: https://lottie.github.io/
- LottieFiles: https://lottiefiles.com/
- Penpot: https://penpot.app/
- Penpot self-hosting: https://penpot.app/self-host
