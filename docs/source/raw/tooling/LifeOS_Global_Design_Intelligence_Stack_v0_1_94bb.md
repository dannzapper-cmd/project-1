# Life OS · Global Design Intelligence Stack v0.1

**Fecha:** 2026-07-16  
**Estado:** documento estratégico vivo  
**Plataforma:** Android nativo, Kotlin + Jetpack Compose  
**Dirección:** Danny  
**Investigación y auditoría:** ChatGPT + Claude  
**Ejecución principal:** Cursor Composer 2.5  
**Memoria canónica:** GitHub

## Propósito

Definir el ecosistema gratuito o abierto de herramientas, MCPs, Skills, Rules, Hooks, subagentes, referencias y recursos que convertirá Cursor en un estudio de diseño e ingeniería visual de clase mundial para la fase artística de Life OS.

No se instalará todo indiscriminadamente. Se investigará un universo amplio, se clasificará y se activará únicamente lo que corresponda a cada tarea.

## Veredicto

La arquitectura correcta tiene cinco capas:

1. Documentos maestros y referencias visuales.
2. Herramientas de extracción y contexto.
3. Contexto normalizado y versionado en GitHub.
4. Skills, Rules, Hooks y subagentes propios.
5. Implementación y auditoría Android nativa.

Stack central recomendado:

- Figma MCP oficial.
- GitHub MCP oficial.
- Context7.
- MarkItDown.
- MCP Inspector.
- Cursor Rules y `AGENTS.md`.
- Cursor Agent Skills.
- Cursor Subagents.
- Cursor Hooks.
- Jetpack Compose, Android Studio y pruebas visuales.

Figma y otras fuentes serán canteras. GitHub conservará el ADN.


## 1. Dirección artística obligatoria

- Blanco como arquitectura predominante.
- Negro para texto, cifras, estructura, símbolos y precisión.
- Arcoíris como vocabulario semántico, no como cromatismo continuo.
- Cognitive Glass.
- Digitalismo Humanista.
- Registro de Vacío y Registro de Objeto Vivo.
- Luz reactiva a movimiento, presión, orientación o estado.
- Diversión inteligente sin infantilización.
- Motion funcional, cinematográfico e interrumpible.
- Haptics semánticos.
- Accesibilidad y performance como parte del lujo.
- Una identidad propia por nodo dentro de una sola gramática global.

El rediseño no puede romper navegación, owners, reducers, mutations, receipts, Undo, persistencia, contratos, consentimiento, permisos, deep links ni preparación futura para backend e IA.


## 2. Roadmap

### A. Consolidación
Subir documentos, referencias, arquitectura y restricciones a GitHub.

### B. Investigación
Evaluar MCPs, Skills, Rules, Hooks, subagentes, fuentes, iconos, avatares, motion, dashboards, QA y licencias.

### C. Infraestructura de Cursor
Crear `AGENTS.md`, reglas, Skills internas, subagentes, Hooks, comandos y un plugin interno.

### D. Sprint Figma MCP
Preparar seis selecciones y consumir las seis llamadas en pocos días. Guardar respuestas crudas, normalizarlas y convertirlas en tokens y contratos.

### E. Design System
Color, tipografía, spacing, formas, elevación, materiales, iconografía, motion, haptics, gráficos y componentes.

### F. Rediseño por superficies
Brief, diseño, implementación, autoauditoría, auditoría externa, corrección y aprobación.

### G. Gate artístico
Consistencia global, accesibilidad, performance, regresión visual, hardware real y documentación.


## 3. Arquitectura de Cursor

```text
AGENTS.md

.cursor/
├── rules/
│   ├── 00-lifeos-global.mdc
│   ├── 10-art-direction.mdc
│   ├── 20-compose-ui.mdc
│   ├── 30-motion-haptics.mdc
│   ├── 40-accessibility.mdc
│   ├── 50-performance.mdc
│   ├── 60-figma-mcp.mdc
│   └── 70-security.mdc
├── skills/
│   ├── lifeos-art-direction/
│   ├── lifeos-figma-harvest/
│   ├── lifeos-compose-translation/
│   ├── lifeos-motion/
│   ├── lifeos-haptics/
│   ├── lifeos-node-identity/
│   ├── lifeos-accessibility/
│   ├── lifeos-visual-audit/
│   ├── lifeos-performance/
│   └── lifeos-design-red-team/
├── agents/
│   ├── art-director.md
│   ├── compose-architect.md
│   ├── motion-director.md
│   ├── accessibility-auditor.md
│   ├── performance-auditor.md
│   └── visual-red-team.md
├── hooks/
└── commands/
```

Crear además:

`docs/design/LIFEOS_ART_CONTEXT_MANIFEST.md`

Este manifest indicará qué documentos, Skills, MCPs, subagentes, pruebas e invariantes corresponden a cada tarea.


## 4. MCPs investigados

| MCP | Uso | Estado |
|---|---|---|
| Figma oficial | Diseños, variables, componentes, contexto | Core |
| GitHub oficial | Repositorio, issues, PRs y trazabilidad | Core |
| Context7 | Documentación actual de librerías | Core tras prueba |
| MarkItDown | Convertir PDF/Office/imágenes a Markdown | Core |
| Penpot oficial | Diseño abierto y editable por agentes | Especialista |
| Filesystem reference | Archivos con allowlist | Core local |
| Git reference | Operaciones Git estructuradas | Evaluar |
| Memory reference | Memoria estructurada | No usar como verdad canónica |
| Playwright | QA web y landing | Solo web |
| MCP Inspector | Inspección y depuración | Core de seguridad |

Combinación recomendada:

- Siempre activos: GitHub, Context7 y Filesystem restringido.
- Por bloque: Figma, MarkItDown, Penpot o Playwright.
- Mantenimiento: MCP Inspector y Registry oficial.

Antes de instalar: revisar publisher, repositorio, LICENSE, SECURITY, releases, scopes, telemetría y permisos.


## 5. Agent Skills

La evidencia de 2026 indica que Skills genéricas frecuentemente no mejoran resultados y pueden empeorarlos cuando contienen instrucciones antiguas o incompatibles. Life OS debe preferir Skills propias, verificadas contra documentos y APIs oficiales.

### Candidatos externos

1. Anthropic `skill-creator`.
2. Anthropic public Skills.
3. `aldefy/compose-skill`.
4. `awesome-android-agent-skills`.
5. `jetpack-compose-skills`.
6. `android-agent-skills`.
7. `compose_skill` para auditoría.
8. `accessibility-skills`.
9. Community Accessibility Agents.
10. Directorios amplios solo para descubrimiento, nunca instalación automática.

### Skills internas obligatorias

1. `lifeos-art-direction`
2. `lifeos-figma-harvest`
3. `lifeos-compose-design-translation`
4. `lifeos-motion-choreography`
5. `lifeos-haptics-semantics`
6. `lifeos-node-art-identity`
7. `lifeos-accessibility-audit`
8. `lifeos-visual-regression`
9. `lifeos-performance-art`
10. `lifeos-design-red-team`

No instalar múltiples Skills que enseñen lo mismo. Elegir una base, auditarla y fusionar lo útil en nuestra Skill canónica.


## 6. Rules, Hooks y subagentes

### Rules

- Global: Android nativo, documentos fuente, arquitectura e invariantes.
- Art Direction: blanco, negro, arcoíris semántico, luz reactiva y no-collage.
- Compose: componentes semánticos, state hoisting, tokens, previews y semantics.
- Motion: causalidad, interrupción, Reduce Motion y presupuesto.
- Performance: recomposición, GPU, batería, shaders y hardware medio.
- Security: no secretos, allowlists, licencias y dependencias fijadas.

### Hooks

1. `pre-design-block`
2. `pre-implementation`
3. `post-token-change`
4. `post-component-change`
5. `pre-commit`
6. `post-test`
7. `pre-session-end`
8. `post-compaction-recovery`
9. `visual-evidence-gate`
10. `license-check`

### Subagentes

- Art Director.
- Compose Architect.
- Motion Director.
- Accessibility Auditor.
- Performance Auditor.
- Visual Red Team.

Los Hooks deben ser rápidos y deterministas. Las suites largas solo se ejecutan en gates.


## 7. Plugin interno

Crear:

```text
.cursor/plugins/lifeos-art-studio/
```

Debe empaquetar:

- MCP config.
- Skills.
- subagentes.
- Rules.
- Hooks.
- comandos.
- plantillas.
- schemas.
- checklists.
- protocolos de Figma y auditoría.

El plugin interno será más importante que acumular plugins externos porque conocerá la arquitectura, documentos, diseño y restricciones de Life OS.


## 8. Figma y Penpot

### Figma

Ventajas: comunidad, variables, componentes, Auto Layout, prototipos, MCP oficial y handoff.

Límites: seis lecturas MCP en Starter, funciones beta, outputs limitados y ausencia de conversión productiva automática.

Plan intensivo de seis llamadas:

1. Foundations.
2. Primitivos.
3. Widgets y dashboards.
4. LIAH y Quick Dial.
5. Identidad de nodos.
6. Flujo final o auditoría.

Cada llamada se guarda en:

```text
docs/design/figma-harvest/
├── raw/
└── normalized/
```

### Penpot

Ventajas: open source, gratuito, self-host, estándares abiertos y MCP.

Decisión: plan B estratégico y laboratorio. No dividir la fuente de verdad entre Figma y Penpot desde el inicio.


## 9. Tipografía

Criterios: licencia abierta, legibilidad móvil, variable axes, números tabulares, soporte lingüístico, personalidad y rendimiento Android.

Diez candidatos:

1. Inter
2. Geist
3. Manrope
4. Plus Jakarta Sans
5. IBM Plex Sans
6. Instrument Sans
7. Satoshi, sujeto a licencia
8. General Sans, sujeto a licencia
9. Public Sans
10. Google Sans Flex, sujeto a verificación final

Shortlist inicial para pruebas reales:

- Inter.
- Manrope.
- Plus Jakarta Sans.
- IBM Plex Sans.
- Instrument Sans.

Probar en Salud, Finanzas, Journaling, cifras, textos largos y escalado de fuente al 200%.


## 10. Iconografía, símbolos y signos

Candidatos:

1. Material Symbols
2. Lucide
3. Phosphor
4. Tabler
5. Iconoir
6. Remix Icon
7. Heroicons
8. Solar Icons
9. Hugeicons Free
10. Iconify como catálogo

Recomendación:

- Base: Material Symbols o Phosphor.
- Complementaria: Lucide o Iconoir.
- Propios: LIAH, Quick Dial, nodos y símbolos institucionales.
- Iconify se usa para búsqueda y normalización, no para mezclar estilos.

Todos los SVG deben normalizar stroke, grid, optical size y semántica antes de entrar al producto.


## 11. Avatares e ilustraciones

Candidatos:

1. DiceBear
2. Open Peeps
3. Humaaans
4. Boring Avatars
5. Multiavatar
6. Avataaars
7. Notionists
8. Personas
9. Micah
10. Sistema propio de Life OS

Uso recomendado:

- externos para prototipos, demos, fallback y referencias;
- un sistema propio para identidad final;
- no adoptar una librería popular como rostro definitivo de la marca.


## 12. Dashboards y design systems

Diez sistemas para estudiar:

1. Material Design 3
2. IBM Carbon
3. Microsoft Fluent
4. GitHub Primer
5. Shopify Polaris
6. Atlassian Design System
7. Salesforce Lightning
8. Adobe Spectrum
9. SAP Fiori
10. Ant Design

Extraer accesibilidad, tokens, documentación, estados, jerarquía y patrones de datos. No copiar apariencia corporativa, componentes web ni densidad de escritorio.

Referencias artísticas adicionales:

- Oura.
- Whoop.
- Revolut.
- Linear.
- Nothing.
- Samsung One UI.
- Mercedes MBUX.
- Volvo.
- Teenage Engineering.
- Nintendo.


## 13. Motion, luz y haptics

### Herramientas

1. Compose Animation.
2. Transition APIs.
3. Animatable.
4. AnimatedContent.
5. Shared transitions.
6. GraphicsLayer.
7. Canvas.
8. RuntimeShader/AGSL.
9. Lottie Android.
10. Rive Android.

### Decisión

- Motion estructural: Compose.
- Luz reactiva: GraphicsLayer, Brush, Canvas y shaders selectivos.
- Animaciones cerradas: Lottie.
- State machines gráficas: Rive cuando sea sostenible.

### Reglas

- interrumpible;
- causal;
- no bloquear contenido;
- Reduce Motion;
- pausar fuera de pantalla;
- fallback;
- medir jank;
- no loops decorativos masivos.

### Haptics

Familias: Contact, Selection, Snap, Drag, Confirmation, Completion, Warning, Error, Protection y Emergency.

No vibrar cada toque. Usar feedback del sistema cuando sea posible y detectar capacidades del hardware.


## 14. QA visual y performance

Diez herramientas o técnicas:

1. Compose Preview.
2. Interactive Preview.
3. Screenshot testing Android.
4. Paparazzi.
5. Roborazzi.
6. Shot.
7. Compose UI tests.
8. Macrobenchmark.
9. JankStats.
10. Baseline Profiles.

Evaluar Paparazzi y Roborazzi; no adoptar ambos automáticamente.

Matriz mínima:

- compact/expanded;
- loading/empty/error;
- disabled;
- 100%, 130% y 200% font;
- TalkBack;
- Reduce Motion;
- dispositivos medios;
- distintas densidades;
- contraste;
- touch targets;
- regresión visual.


## 15. Seguridad y licencias

Amenazas:

- prompt injection;
- Skills maliciosas;
- repositorios abandonados;
- scripts ocultos;
- permisos amplios;
- exfiltración;
- telemetría;
- supply-chain;
- licencias incompatibles.

Protocolo:

1. verificar fuente;
2. licencia;
3. pin de commit;
4. permisos;
5. inspección estática;
6. repositorio de prueba;
7. allowlist;
8. no secretos;
9. registro de versión;
10. revisión periódica.

Crear:

`docs/tooling/AI_TOOL_SECURITY_REGISTRY.md`

No se evadirán licencias, paywalls ni límites contractuales. Se optimizará legítimamente el uso gratuito y se preservará el contexto permitido.


## 16. Adopción

### Instalar ahora

- Figma MCP.
- GitHub MCP.
- Context7.
- MarkItDown.
- MCP Inspector.
- `skill-creator`.
- una Skill Compose auditada.
- Rules internas.
- Hooks internos.
- subagentes internos.

### Evaluar pronto

- Penpot MCP.
- Paparazzi.
- Roborazzi.
- Rive.
- DiceBear.
- Phosphor.
- Instrument Sans.
- BrowserStack futuro.

### Posponer

- Framer como base móvil.
- tooling React/Tailwind.
- múltiples sistemas de avatares.
- múltiples frameworks de screenshot.
- MCPs sin publisher.
- assets con licencia dudosa.


## 17. Definition of Done

Un bloque artístico no termina hasta que:

- diseño aprobado;
- implementación fiel;
- estados completos;
- arquitectura intacta;
- tests verdes;
- accesibilidad;
- performance;
- motion interrumpible;
- Reduce Motion;
- haptics correctos;
- evidencia selectiva;
- checkpoint actualizado;
- licencias registradas;
- autoauditoría;
- auditoría externa;
- correcciones cerradas.


## 18. Fuentes verificadas

### Cursor
- https://cursor.com/docs/plugins
- https://cursor.com/docs/skills
- https://cursor.com/docs/rules
- https://cursor.com/docs/hooks
- https://cursor.com/docs/subagents
- https://cursor.com/marketplace

### Figma
- https://developers.figma.com/docs/figma-mcp-server/
- https://developers.figma.com/docs/figma-mcp-server/rate-limits-access/
- https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/
- https://developers.figma.com/docs/figma-mcp-server/remote-server-installation/
- https://developers.figma.com/docs/figma-mcp-server/add-custom-rules/
- https://developers.figma.com/docs/figma-mcp-server/trigger-specific-tools/
- https://developers.figma.com/docs/figma-mcp-server/mcp-vs-agent/
- https://developers.figma.com/docs/figma-mcp-server/server-returning-web-code/

### MCP
- https://github.com/modelcontextprotocol/registry
- https://github.com/modelcontextprotocol/servers
- https://github.com/mcp
- https://github.com/github/github-mcp-server

### Android
- https://developer.android.com/develop/ui/compose
- https://developer.android.com/develop/ui/compose/animation/quick-guide
- https://developer.android.com/develop/ui/compose/performance
- https://developer.android.com/develop/ui/compose/graphics/draw/brush
- https://developer.android.com/develop/ui/views/haptics
- https://developer.android.com/topic/performance/vitals/render

### Skills
- https://github.com/anthropics/skills
- https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md
- https://github.com/aldefy/compose-skill
- https://github.com/new-silvermoon/awesome-android-agent-skills
- https://github.com/anhvt52/jetpack-compose-skills
- https://github.com/krutikJain/android-agent-skills

### Diseño y motion
- https://penpot.app/
- https://penpot.app/open-design-infrastructure
- https://rive.app/docs/runtimes/android/android
- https://rive.app/docs/runtimes/state-machines
- https://lottiefiles.com/
- https://lottie.github.io/

### Tipografía, iconos y avatares
- https://fonts.google.com/
- https://developers.google.com/fonts
- https://www.fontshare.com/
- https://fontsource.org/
- https://icon-sets.iconify.design/
- https://www.dicebear.com/
- https://www.openpeeps.com/
- https://www.humaaans.com/


## 19. Veredicto final

Life OS no necesita cien herramientas activas. Necesita que cien candidatos hayan sido estudiados y que solo los mejores entren al taller.

La combinación recomendada es:

```text
Figma + GitHub + Context7 + MarkItDown
                ↓
AGENTS.md + Rules + Skills + Hooks + Subagents
                ↓
Design System propio
                ↓
Cursor Composer 2.5
                ↓
Kotlin + Jetpack Compose
                ↓
Auditoría visual + UX + accesibilidad + performance
```

Cursor no debe limitarse a producir pantallas bonitas. Debe operar como una fábrica artística y técnica disciplinada, alimentada por memoria canónica, herramientas especializadas, fuentes verificadas y dirección creativa humana.
