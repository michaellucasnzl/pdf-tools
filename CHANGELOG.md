# Changelog

All notable changes to this project will be documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned (see ImplementationNotes_V2.md for details)
- Phase 1: Project restructure & PyMuPDF integration
- Phase 2: PDF ↔ image conversion
- Phase 3: PDF → DOCX
- Phase 4: DOCX / XLSX / HTML → PDF
- Phase 5: Text extraction & PDF → Markdown
- Phase 6: Password protection & encryption
- Phase 7: Page manipulation (rotate, reorder, delete, crop)
- Phase 8: Watermarking & stamping
- Phase 9: OCR — scanned PDFs → searchable
- Phase 10: Page numbers, headers & footers
- Phase 11: Redaction
- Phase 12: Fill & flatten PDF forms
- Phase 13: PDF/A archival compliance
- Phase 14: NiceGUI desktop/web interface
- Phase 15: Polish, packaging & distribution

---

## [2.0.0] — 2026-03-18

### Changed
- Renamed project from **pdf-resizer** to **pdf-toolkit**
- Migrated to `src/` layout — package lives at `src/pdf_toolkit/`
- Entry point changed from `pdf-resizer` to `pdf-toolkit`
- Config file renamed from `~/.pdf-resizer.toml` to `~/.pdf-toolkit.toml`

### Added
- `tests/` directory with initial smoke tests
- `CHANGELOG.md`
- `[tool.ruff]` and `[tool.pytest.ini_options]` sections in `pyproject.toml`

---

## [1.x] — prior releases

Initial release as pdf-resizer. Features: compress, split, merge, analyse PDFs.
