# Life OS · Agent Contract

Contrato transversal para agentes Cursor (Composer 2.5, subagentes, Cloud Agents).

## Misión

Life OS es un sistema operativo personal inteligente — no una app de productividad genérica. La fase artística de Fase 2 rediseña toda la experiencia visual sin destruir el sistema nervioso funcional.

**Plataforma:** Android nativo · Kotlin · Jetpack Compose · arquitectura modular.

## Precedencia documental

1. Danny (director creativo) — autoridad estética final
2. `docs/source/raw/design/LifeOS_Sistema_Direccion_Artistica_Fase2_Android_v0_1_1__80c4.md`
3. `docs/source/raw/design/DISENO_d99d.pdf` (consulta visual)
4. Documentos maestros en `docs/source/` (ver `SOURCE_INDEX.md`)
5. `docs/design/LIFEOS_ART_CONTEXT_MANIFEST.md`
6. Este archivo y `.cursor/rules/`

## Invariantes (nunca romper en rediseño)

Navegación · owners · estado · reducers · events · mutations · receipts · Undo · Saver · persistencia · migraciones · process recreation · contratos · demo providers · consentimiento · permisos · privacidad · deep links · preparación backend/sync/IA.

**Un cambio visual NO autoriza cambios silenciosos en dominio, datos o arquitectura.**

## Flujo de trabajo

1. Leer checkpoint: `docs/execution/BLOCK_ART_000_CONTEXT_TOOLING_WORKING_CHECKPOINT.md`
2. Leer `CURRENT_BUILD.md`, `DECISIONS.md`, `CONTRADICTIONS.md`
3. Consultar manifest: `docs/design/LIFEOS_ART_CONTEXT_MANIFEST.md`
4. Por superficie: brief → diseño → implementación → autoauditoría → auditoría externa → aprobación Danny → cierre
5. Actualizar checkpoint al cerrar cada hito

## Reglas de seguridad

- No secretos en archivos versionados
- Verificar licencias antes de adoptar assets/MCPs (ver `docs/tooling/AI_TOOL_SECURITY_REGISTRY.md`)
- No evadir paywalls ni límites Figma
- No instalar MCPs sin revisar publisher y permisos
- Figma MCP: preparar antes de invocar; registrar cada llamada

## Prohibiciones absolutas (fase artística)

- No React, Tailwind, HTML, Framer Motion para la app Android
- No rediseñar sin brief aprobado
- No consumir Figma MCP sin plan en `docs/design/figma-harvest/`
- No copiar diseños protegidos literalmente

## Definition of Done (superficie)

Diseño aprobado · implementación fiel · estados completos · arquitectura intacta · tests verdes · accesibilidad · performance · motion interrumpible · Reduce Motion · haptics correctos · evidencia en gates · checkpoint actualizado · licencias registradas.

## Comandos esenciales

```bash
# Validar infraestructura artística
./scripts/lifeos/validate-art-context.sh

# Android (cuando exista repo Life OS)
./gradlew :app:assembleDebug
./gradlew testDebugUnitTest

# Git
git status && git diff
```

## Comandos Cursor

| Comando | Uso |
|---|---|
| `/lifeos-prepare-brief` | Preparar brief artístico |
| `/lifeos-import-reference` | Incorporar referencia visual |
| `/lifeos-figma-harvest-prep` | Preparar cosecha Figma |
| `/lifeos-implement-surface` | Implementar superficie |
| `/lifeos-visual-audit` | Auditar visualmente |
| `/lifeos-close-block` | Cerrar bloque con checkpoint |
| `/lifeos-recover-session` | Recuperar tras compactación |

## Protocolo post-compactación

1. Leer este `AGENTS.md`
2. Leer `.cursor/rules/00-lifeos-global.mdc`
3. Leer `docs/execution/BLOCK_ART_000_CONTEXT_TOOLING_WORKING_CHECKPOINT.md`
4. Leer `CURRENT_BUILD.md`, `DECISIONS.md`, `CONTRADICTIONS.md`
5. `git status` + `git diff`
6. Continuar desde primera tarea incompleta del checkpoint

## Referencias profundas

| Tema | Documento |
|---|---|
| Dirección artística | `docs/design/ART_DIRECTION_MASTER.md` |
| Tooling | `docs/tooling/GLOBAL_DESIGN_TOOL_REGISTRY.md` |
| Figma sprint | `docs/design/figma-harvest/FIGMA_SIX_CALL_PLAN.md` |
| Baseline repo | `docs/audits/ART_CONTEXT_REPOSITORY_BASELINE.md` |
| Fuentes | `docs/source/SOURCE_INDEX.md` |
