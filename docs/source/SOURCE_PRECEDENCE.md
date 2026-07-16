# Life OS · Source Precedence

**Actualizado:** 2026-07-16

## Leyenda de roles

| Rol | Significado |
|---|---|
| **fuente de verdad** | Autoridad máxima para su dominio |
| **complemento** | Amplía sin contradecir la fuente primaria |
| **interpretación** | Síntesis operativa; no sustituye fuentes |
| **investigación** | Candidatos y exploración; requiere validación |
| **decisión** | Compromiso registrado del equipo |
| **referencia visual** | Consulta visual obligatoria |
| **histórico** | Versión anterior preservada |
| **contradictorio** | Conflicto documentado; no resolver silenciosamente |
| **pendiente de validación** | Falta incorporación o aprobación |

## Matriz de precedencia

| Documento | Rol | Precede a | Notas |
|---|---|---|---|
| Danny (director creativo) | fuente de verdad | Todo lo estético final | Autoridad humana |
| SRC-001 Dirección Artística v0.1.1 | fuente de verdad | SRC-005, interpretaciones | Documento rector Fase 2 |
| SRC-003 DISENO.pdf | referencia visual | Moodboards externos | No copiar literalmente |
| SRC-002 Global Design Intelligence Stack | complemento | Tooling genérico | Clasificación herramientas |
| SRC-005 Dirección Artística v0.1 | histórico | — | Supersedido por SRC-001 |
| DISENO.pdf p.17–21 (texto web) | investigación / contradictorio | Stack Android | Recomienda React/Tailwind — **rechazado para Life OS** |
| SUPERPROMPT 001 | decisión / protocolo | Flujo de este bloque | |
| Documentos maestros pendientes | pendiente de validación | — | Ver SOURCE_INDEX |
| `docs/design/*` generados | interpretación | Implementación diaria | Enlazan a fuentes |
| Figma Community assets | investigación | — | Licencia individual obligatoria |
| Material Design / SaaS kits | referencia / investigación | Apariencia Life OS | Extraer principios, no copiar |

## Reglas de resolución

1. **Producto y arquitectura:** documentos de producto (cuando existan) > código canónico > interpretación agente.
2. **Dirección visual:** Danny > SRC-001 > SRC-003 visual > SRC-002.
3. **Tooling:** verificación oficial 2026 > SRC-002 > investigación PDF web.
4. **Duplicados:** versión más reciente con mismo contenido ampliado gana (SRC-001 > SRC-005).
5. **Contradicciones:** registrar en `CONTRADICTIONS.md`; no resolver sin Danny.

## Contradicciones conocidas

Ver `CONTRADICTIONS.md` en raíz del repositorio.
