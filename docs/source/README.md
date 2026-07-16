# Life OS · Source Document Archive

Memoria canónica de documentos fuente para la fase artística de Fase 2.

## Estructura

```text
docs/source/
├── README.md                 ← este archivo
├── SOURCE_INDEX.md           ← localización rápida
├── SOURCE_PRECEDENCE.md      ← autoridad y precedencia
├── SOURCE_IMPORT_MANIFEST.md ← estado de incorporación
├── raw/                      ← originales preservados
│   ├── product/
│   ├── design/
│   ├── research/
│   ├── strategy/
│   └── tooling/
└── normalized/               ← versiones Markdown cuando aportan valor
    ├── product/
    ├── design/
    ├── research/
    ├── strategy/
    └── tooling/
```

## Reglas

1. **Nunca eliminar** versiones antiguas; registrar duplicados y precedencia.
2. Los PDFs visuales se conservan en `raw/`; la normalización es índice, no sustituto.
3. Los checksums viven en `raw/CHECKSUMS.sha256`.
4. Documentos bloqueados se registran en `SOURCE_IMPORT_MANIFEST.md`.

## Incorporación

Ver `SOURCE_IMPORT_MANIFEST.md` para estado actual y pasos de recuperación.
