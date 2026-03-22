# PDF Toolkit v2.0 — Implementation Plan

> **Vision:** Build **pdf-toolkit** as a full-featured, native, open-source
> PDF toolkit — with a modern GUI for casual users and a powerful CLI for advanced
> users on Windows and Linux. **No cloud. No accounts. No commercial dependencies.**

---

## Table of Contents

1. [Licensing Strategy — FOSS First](#1-licensing-strategy--foss-first)
2. [Library Stack](#2-library-stack)
3. [Architecture](#3-architecture)
4. [Phase Plan](#4-phase-plan)
   - Phase 1: [Project Restructure & PyMuPDF Integration](#phase-1-project-restructure--pymupdf-integration)
   - Phase 2: [PDF → Images & Images → PDF](#phase-2-pdf--images--images--pdf)
   - Phase 3: [PDF → Word (DOCX) Conversion](#phase-3-pdf--word-docx-conversion)
   - Phase 4: [Word / Excel / HTML → PDF Conversion](#phase-4-word--excel--html--pdf-conversion)
   - Phase 5: [Text Extraction & PDF → Markdown](#phase-5-text-extraction--pdf--markdown)
   - Phase 6: [Password Protection & Encryption](#phase-6-password-protection--encryption)
   - Phase 7: [Page Manipulation (Rotate, Reorder, Delete, Crop)](#phase-7-page-manipulation-rotate-reorder-delete-crop)
   - Phase 8: [Watermarking & Stamping](#phase-8-watermarking--stamping)
   - Phase 9: [OCR — Scanned PDFs → Searchable PDFs](#phase-9-ocr--scanned-pdfs--searchable-pdfs)
   - Phase 10: [Page Numbers, Headers & Footers](#phase-10-page-numbers-headers--footers)
   - Phase 11: [Redaction](#phase-11-redaction)
   - Phase 12: [Fill & Flatten PDF Forms](#phase-12-fill--flatten-pdf-forms)
   - Phase 13: [PDF/A Archival Compliance](#phase-13-pdfa-archival-compliance)
   - Phase 14: [NiceGUI — Modern Desktop/Web GUI](#phase-14-nicegui--modern-desktopweb-gui)
   - Phase 15: [Polish, Packaging & Distribution](#phase-15-polish-packaging--distribution)
5. [Dependency Summary](#5-dependency-summary)
6. [Risks & Mitigations](#6-risks--mitigations)

---

## 1. Licensing Strategy — FOSS First

Every dependency must be genuinely free and open-source. No freeware, no "free tier",
no commercial-only features that we'd later need to pay for.

### PyMuPDF — AGPL-3.0

PyMuPDF (the engine that powers most of our new features) is licensed under
**AGPL-3.0**. This is a legitimate FOSS license — it is
[OSI-approved](https://opensource.org/license/agpl-v3) and
[FSF-approved](https://www.gnu.org/licenses/agpl-3.0.en.html). However, AGPL is
**copyleft**: any program that links to an AGPL library and is distributed (including
over a network) must also make its complete source code available under AGPL-compatible
terms.

**What this means for us:**

| Scenario | OK? | Notes |
|----------|-----|-------|
| Open-source repo on GitHub, users install from source | **Yes** | AGPL is satisfied — source is available |
| Distribute a .zip / installer with full source included | **Yes** | Source accompanies the binary |
| Publish as a pip package (source on PyPI + GitHub) | **Yes** | Source is public |
| Sell as a closed-source commercial product | **No** | Would need Artifex commercial license |
| Run as a SaaS (web service others connect to) | **No** | AGPL requires source for network users too |

**Decision:** Change the project license from MIT to **AGPL-3.0**. This is the simplest
and most honest approach — it matches PyMuPDF, keeps everything FOSS, and costs nothing.
Users can still use, modify, and redistribute the tool freely; they just must keep it
open-source if they distribute it.

### All other dependencies

| Library | License | Copyleft? | Status |
|---------|---------|-----------|--------|
| `pikepdf` | MPL-2.0 | File-level only | **OK** — compatible with AGPL |
| `Pillow` | MIT-like (HPND) | No | **OK** |
| `pypdf` | BSD-3-Clause | No | **OK** |
| `typer` | MIT | No | **OK** |
| `rich` | MIT | No | **OK** |
| `python-docx` | MIT | No | **OK** |
| `openpyxl` | MIT | No | **OK** |
| `NiceGUI` | MIT | No | **OK** |
| Tesseract OCR | Apache-2.0 | No | **OK** — external tool, not linked |
| LibreOffice | MPL-2.0 | File-level only | **OK** — external tool, not linked |

**Every single dependency is genuinely FOSS. No commercial licenses. No freeware traps.**

---

## 2. Library Stack

### Core engine (all phases)

| Package | Purpose | Why |
|---------|---------|-----|
| **`pymupdf`** >=1.25 | PDF conversion, rendering, OCR, encryption, watermarks, redaction, page manipulation, text extraction | Single library covers 90% of new features. Built on MuPDF C engine — extremely fast. AGPL-3.0. |
| **`pikepdf`** >=8.0 | PDF compression, linearisation, PDF/A metadata | Already in use. Best for structure-level optimisation. MPL-2.0. |
| **`Pillow`** >=10.0 | Image processing | Already in use. Needed for some image edge cases. MIT-like. |
| **`pypdf`** >=4.0 | Existing compression pipeline | Already in use. Will be gradually replaced by PyMuPDF but kept for backward compat. BSD-3. |

### CLI & display

| Package | Purpose |
|---------|---------|
| **`typer[all]`** >=0.9 | CLI framework with subcommands (MIT) |
| **`rich`** | Terminal output — bundled with typer[all] (MIT) |

### GUI (Phase 14)

| Package | Purpose |
|---------|---------|
| **`nicegui`** >=2.0 | Web-based GUI with native desktop mode (MIT) |

### Optional (enhanced conversion, Phase 4)

| Package | Purpose |
|---------|---------|
| **`python-docx`** >=1.0 | Read DOCX for pure-Python fallback conversion (MIT) |
| **`openpyxl`** >=3.1 | Read XLSX for pure-Python fallback conversion (MIT) |

### External tools (optional, auto-detected at runtime)

| Tool | Features it enables | FOSS license | Install |
|------|-------------------|--------------|---------|
| **LibreOffice** | High-fidelity DOCX/XLSX/HTML → PDF | MPL-2.0 | [libreoffice.org](https://www.libreoffice.org/download/) |
| **Tesseract OCR** | Scanned PDF → searchable text | Apache-2.0 | [UB-Mannheim builds](https://github.com/UB-Mannheim/tesseract/wiki) (Win) / `apt install tesseract-ocr` (Linux) |

Both are optional. The app detects them at runtime and offers graceful fallbacks or
a clear "install X for this feature" message when they're missing.

---

## 3. Architecture

### Target project structure

```
pdf-toolkit/
├── pdf_toolkit/                    # main package
│   ├── __init__.py                 # version, public API
│   ├── __main__.py                 # python -m pdf_toolkit
│   │
│   ├── core/                       # business logic — NO UI imports
│   │   ├── __init__.py
│   │   ├── compress.py             # existing compression pipeline (pypdf + pikepdf)
│   │   ├── convert.py              # PDF↔DOCX, XLSX→PDF, images↔PDF
│   │   ├── encrypt.py              # encryption / decryption
│   │   ├── extract.py              # text extraction, PDF→Markdown
│   │   ├── manipulate.py           # rotate, reorder, delete, crop, page numbers
│   │   ├── ocr.py                  # Tesseract OCR integration
│   │   ├── redact.py               # text/pattern redaction
│   │   ├── watermark.py            # text & image watermarks
│   │   ├── forms.py                # form field fill & flatten
│   │   ├── archive.py              # PDF/A compliance
│   │   └── detect.py               # runtime detection of LibreOffice, Tesseract, etc.
│   │
│   ├── cli/                        # Typer CLI — imports from core/
│   │   ├── __init__.py
│   │   ├── app.py                  # root Typer app, subcommand wiring
│   │   ├── compress.py             # `pdf-toolkit compress ...`
│   │   ├── convert.py              # `pdf-toolkit convert ...`
│   │   ├── encrypt.py              # `pdf-toolkit encrypt / decrypt ...`
│   │   ├── extract.py              # `pdf-toolkit extract-text / to-markdown ...`
│   │   ├── manipulate.py           # `pdf-toolkit rotate / delete-pages / crop ...`
│   │   ├── ocr.py                  # `pdf-toolkit ocr ...`
│   │   ├── watermark.py            # `pdf-toolkit watermark ...`
│   │   ├── redact.py               # `pdf-toolkit redact ...`
│   │   ├── forms.py                # `pdf-toolkit fill-form / flatten-form ...`
│   │   └── helpers.py              # shared CLI utilities (progress, formatting, file expansion)
│   │
│   ├── gui/                        # NiceGUI app — imports from core/
│   │   ├── __init__.py
│   │   ├── app.py                  # main NiceGUI entrypoint
│   │   ├── tabs/
│   │   │   ├── compress.py
│   │   │   ├── convert.py
│   │   │   ├── tools.py            # watermark, encrypt, OCR, redact, etc.
│   │   │   └── settings.py
│   │   └── components.py           # reusable UI components
│   │
│   └── config.py                   # TOML config loading/saving
│
├── tests/
│   ├── test_compress.py
│   ├── test_convert.py
│   ├── test_encrypt.py
│   ├── test_extract.py
│   ├── test_manipulate.py
│   └── ...
│
├── pyproject.toml
├── requirements.txt
├── requirements-gui.txt
├── requirements-full.txt
├── LICENSE                         # AGPL-3.0
├── README.md
├── ImplementationNotes_V2.md       # this file
├── setup.bat / setup.sh
├── Run PDF Toolkit.bat / run.sh
├── install_context_menu.bat
└── uninstall_context_menu.bat
```

### Design principles

1. **Core is UI-agnostic.** `pdf_toolkit.core.*` has zero UI imports. Both CLI and GUI
   consume the same core functions.

2. **Progress via callbacks.** Core functions accept an optional
   `on_progress(current: int, total: int, message: str)` callback. CLI wires this to
   `rich.progress`, GUI wires it to NiceGUI progress bars.

3. **Graceful degradation.** Features that need external tools (LibreOffice, Tesseract)
   detect them at runtime. If missing, the user gets a clear error with install
   instructions — never a cryptic traceback.

4. **Backward compatibility.** Running `pdf-toolkit` with no subcommand and PDF files
   as arguments defaults to `compress` — same behaviour as v1.

---

## 4. Phase Plan

Each phase is a self-contained unit of work. After each phase:
- All existing tests still pass
- The new feature works end-to-end (CLI at minimum)
- A git commit is made with a descriptive message

---

### Phase 1: Project Restructure & PyMuPDF Integration

**Goal:** Reorganise the codebase from a single `pdf_resizer.py` into the
`pdf_toolkit/` package structure. Add PyMuPDF as a dependency. Keep all existing
functionality working.

**Tasks:**
1. Create `pdf_toolkit/` package directory structure (core/, cli/, gui/ stubs)
2. Move existing compression logic into `pdf_toolkit/core/compress.py`
3. Move CLI (Typer app, options, helpers) into `pdf_toolkit/cli/`
4. Move config logic into `pdf_toolkit/config.py`
5. Extract shared helpers (format_size, expand_files, pick_files) into `cli/helpers.py`
6. Add `pymupdf>=1.25` to dependencies
7. Create `pdf_toolkit/core/detect.py` — runtime detection of PyMuPDF, LibreOffice,
   Tesseract, etc.
8. Update `pyproject.toml`: new package name, entry point, AGPL-3.0 license
9. Update `setup.bat`, `setup.sh`, `Run PDF Toolkit.bat`, `run.sh` for new structure
10. Update `install_context_menu.bat` / `uninstall_context_menu.bat`
11. Change LICENSE file to AGPL-3.0
12. Restructure CLI to use subcommands: `pdf-toolkit compress` (default), with the
    old no-subcommand behaviour preserved as a fallback
13. Verify: `pdf-toolkit compress file.pdf -q medium` works identically to the old
    `pdf-toolkit file.pdf -q medium`

**New dependencies:** `pymupdf>=1.25`

**CLI after this phase:**
```
pdf-toolkit compress file.pdf -q medium
pdf-toolkit compress *.pdf --split-pages
pdf-toolkit compress a.pdf b.pdf --merge
pdf-toolkit file.pdf                        # backward compat → compress
```

**Commit message:** `feat: restructure into pdf_toolkit package, add PyMuPDF, subcommands`

---

### Phase 2: PDF → Images & Images → PDF

**Goal:** Add bidirectional conversion between PDFs and image files.

**Tasks:**
1. `core/convert.py` — `pdf_to_images()` function:
   - Input: PDF path, page range (optional), output format (png/jpeg), DPI (72–600),
     output directory
   - Uses `pymupdf.Matrix` for DPI scaling, `page.get_pixmap()` for rendering
   - Returns list of output file paths
2. `core/convert.py` — `images_to_pdf()` function:
   - Input: list of image paths, output PDF path, page size (auto/a4/letter),
     quality setting
   - Uses `pymupdf.open(img) → convert_to_pdf()` pipeline
   - Returns output path
3. `cli/convert.py` — `pdf-toolkit to-images` subcommand:
   - Options: `--format png|jpeg`, `--dpi`, `--pages`, `-o`
   - Progress bar per page
4. `cli/convert.py` — `pdf-toolkit images-to-pdf` subcommand:
   - Options: `--page-size auto|a4|letter`, `-q`, `-o`
   - Accepts glob patterns for input images
5. Tests for both directions

**Implementation reference:**
```python
import pymupdf

# PDF → Images
doc = pymupdf.open("input.pdf")
for i, page in enumerate(doc):
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)  # scale factor from DPI
    pix = page.get_pixmap(matrix=mat)
    pix.save(f"page_{i + 1}.png")

# Images → PDF
doc = pymupdf.open()
for img_path in image_files:
    img = pymupdf.open(img_path)
    rect = img[0].rect
    pdf_bytes = img.convert_to_pdf()
    img.close()
    img_pdf = pymupdf.open("pdf", pdf_bytes)
    page = doc.new_page(width=rect.width, height=rect.height)
    page.show_pdf_page(rect, img_pdf, 0)
doc.save("output.pdf")
```

**CLI after this phase:**
```
pdf-toolkit to-images report.pdf --format png --dpi 300
pdf-toolkit to-images report.pdf --pages 1-5 --dpi 150
pdf-toolkit images-to-pdf *.jpg -o album.pdf
pdf-toolkit images-to-pdf photo1.png photo2.png --page-size a4
```

**Commit message:** `feat: PDF↔image conversion (png, jpeg) via PyMuPDF`

---

### Phase 3: PDF → Word (DOCX) Conversion

**Goal:** Convert PDF files to editable Word documents.

**Tasks:**
1. `core/convert.py` — `pdf_to_docx()` function:
   - Input: PDF path, output path (optional), page range (optional)
   - Uses PyMuPDF's `Converter` class (wraps pdf2docx internally)
   - Returns output path
2. `cli/convert.py` — `pdf-toolkit to-docx` subcommand:
   - Options: `--pages`, `-o`, batch support with `--workers`
   - Progress bar
3. Handle edge cases: encrypted PDFs (prompt for password first), invalid PDFs
4. Tests

**Implementation reference:**
```python
from pymupdf import Converter

def pdf_to_docx(input_path, output_path=None, pages=None):
    if output_path is None:
        output_path = input_path.with_suffix(".docx")
    cv = Converter(str(input_path))
    cv.convert(str(output_path), pages=pages)
    cv.close()
    return output_path
```

**What it preserves:** text with formatting, images, tables, page layout (approximate),
headers/footers.

**Known limitations:** Complex multi-column layouts, embedded fonts, and mathematical
formulas may not convert perfectly. This is inherent to the PDF format (visual, not
semantic) and applies to every FOSS tool. Our conversion quality matches or exceeds
other open-source options.

**CLI after this phase:**
```
pdf-toolkit to-docx report.pdf
pdf-toolkit to-docx report.pdf --pages 1-5 -o ./output/
pdf-toolkit to-docx *.pdf -w 4
```

**Commit message:** `feat: PDF → DOCX conversion via PyMuPDF Converter`

---

### Phase 4: Word / Excel / HTML → PDF Conversion

**Goal:** Convert DOCX, XLSX, and HTML files to PDF. Uses a tiered strategy:
try LibreOffice first (best quality), fall back to pure-Python rendering.

**Tasks:**
1. `core/detect.py` — `find_libreoffice()` function:
   - Windows: check common paths (`C:\Program Files\LibreOffice\...`, PATH)
   - Linux: `which libreoffice` / `which soffice`
   - Returns path or None
2. `core/convert.py` — `office_to_pdf()` function (LibreOffice backend):
   - Calls `soffice --headless --convert-to pdf --outdir <dir> <input>`
   - Timeout handling, error capture
   - Works for DOCX, XLSX, PPTX, ODT, ODS, HTML, RTF, CSV
3. `core/convert.py` — `docx_to_pdf_fallback()` function (pure Python):
   - Uses `python-docx` to read paragraphs, tables, images
   - Renders into PDF via PyMuPDF `insert_htmlbox()` (builds intermediate HTML)
   - Limited but works for simple documents with no external tools
4. `core/convert.py` — `xlsx_to_pdf_fallback()` function (pure Python):
   - Uses `openpyxl` to read cell data
   - Renders as HTML table → PDF via PyMuPDF `insert_htmlbox()`
   - Data/text only — no charts, styling, merged cells
5. `core/convert.py` — `to_pdf()` dispatcher:
   - Detects input format by extension
   - `.docx/.doc/.odt/.rtf` → tries LibreOffice, falls back to docx_to_pdf_fallback
   - `.xlsx/.xls/.ods/.csv` → tries LibreOffice, falls back to xlsx_to_pdf_fallback
   - `.html/.htm` → tries LibreOffice, or PyMuPDF HTML rendering
   - Reports which backend was used
6. `cli/convert.py` — `pdf-toolkit to-pdf` subcommand:
   - Auto-detects input format
   - Options: `-o`, batch support
   - Warns if LibreOffice is not found and fallback is used
7. Add `python-docx>=1.0` and `openpyxl>=3.1` as optional dependencies
8. Tests

**Implementation reference:**
```python
import subprocess

def office_to_pdf(input_path, output_dir, soffice_path):
    subprocess.run([
        soffice_path, "--headless", "--convert-to", "pdf",
        "--outdir", str(output_dir), str(input_path)
    ], check=True, timeout=120)
```

**CLI after this phase:**
```
pdf-toolkit to-pdf document.docx
pdf-toolkit to-pdf report.xlsx
pdf-toolkit to-pdf *.docx -o ./output/
pdf-toolkit to-pdf page.html
```

**User experience when LibreOffice is missing:**
```
⚠ LibreOffice not found — using basic converter (some formatting may be lost).
  For best results, install LibreOffice: https://www.libreoffice.org/download/
→ output.pdf (basic conversion)
```

**Commit message:** `feat: DOCX/XLSX/HTML → PDF conversion (LibreOffice + Python fallback)`

---

### Phase 5: Text Extraction & PDF → Markdown

**Goal:** Extract text content from PDFs in multiple formats.

**Tasks:**
1. `core/extract.py` — `extract_text()` function:
   - Input: PDF path, format (plain/html/json), page range
   - Uses `pymupdf page.get_text()` with format variants
   - Returns extracted text string
2. `core/extract.py` — `pdf_to_markdown()` function:
   - Input: PDF path, output path
   - Uses `pymupdf doc.to_markdown()` (built on pymupdf4llm)
   - Returns markdown string
3. `cli/extract.py` — `pdf-toolkit extract-text` subcommand:
   - Options: `--format plain|html|json`, `--pages`, `-o`
   - Default: prints to stdout; `-o` writes to file
4. `cli/extract.py` — `pdf-toolkit to-markdown` subcommand:
   - Options: `--pages`, `-o`
5. Tests

**Implementation reference:**
```python
import pymupdf

doc = pymupdf.open("input.pdf")

# Plain text
text = "\n".join(page.get_text() for page in doc)

# Markdown
markdown = doc.to_markdown()

# HTML (per page)
html = "\n".join(page.get_text("html") for page in doc)

# Structured JSON (per page)
import json
blocks = [page.get_text("dict") for page in doc]
```

**CLI after this phase:**
```
pdf-toolkit extract-text report.pdf
pdf-toolkit extract-text report.pdf --format html -o report.html
pdf-toolkit extract-text report.pdf --pages 1-3 --format json
pdf-toolkit to-markdown report.pdf
pdf-toolkit to-markdown report.pdf -o report.md
```

**Commit message:** `feat: text extraction (plain/HTML/JSON) and PDF → Markdown`

---

### Phase 6: Password Protection & Encryption

**Goal:** Encrypt PDFs with passwords and granular permissions, and decrypt
password-protected PDFs.

**Tasks:**
1. `core/encrypt.py` — `encrypt_pdf()` function:
   - Input: PDF path, output path, user_password, owner_password (optional),
     permissions dict (print, copy, annotate, modify)
   - Uses PyMuPDF AES-256 encryption
   - Returns output path
2. `core/encrypt.py` — `decrypt_pdf()` function:
   - Input: PDF path, password, output path
   - Uses `doc.authenticate()` then saves without encryption
   - Returns output path
3. `core/encrypt.py` — `pdf_info()` function:
   - Reports: encrypted status, permissions, page count, metadata
4. `cli/encrypt.py` — `pdf-toolkit encrypt` subcommand:
   - Options: `--password`, `--owner-password`, `--no-print`, `--no-copy`,
     `--no-modify`, `-o`
   - Secure password input (not echoed to terminal)
5. `cli/encrypt.py` — `pdf-toolkit decrypt` subcommand:
   - Options: `--password`, `-o`
6. `cli/encrypt.py` — `pdf-toolkit info` subcommand:
   - Shows: page count, encrypted, permissions, metadata, file size, image count
7. Tests

**Implementation reference:**
```python
import pymupdf

# Encrypt
doc = pymupdf.open("input.pdf")
perm = int(
    pymupdf.PDF_PERM_ACCESSIBILITY
    | pymupdf.PDF_PERM_PRINT
    | pymupdf.PDF_PERM_COPY
)
doc.save("protected.pdf",
    encryption=pymupdf.PDF_ENCRYPT_AES_256,
    owner_pw="owner_secret",
    user_pw="open_password",
    permissions=perm)

# Decrypt
doc = pymupdf.open("protected.pdf")
doc.authenticate("owner_secret")
doc.save("decrypted.pdf", encryption=pymupdf.PDF_ENCRYPT_NONE)
```

**CLI after this phase:**
```
pdf-toolkit encrypt doc.pdf --password "secret123"
pdf-toolkit encrypt doc.pdf --password "open" --owner-password "admin" --no-print --no-copy
pdf-toolkit decrypt protected.pdf --password "secret123"
pdf-toolkit info report.pdf
```

**Commit message:** `feat: PDF encryption (AES-256), decryption, and info command`

---

### Phase 7: Page Manipulation (Rotate, Reorder, Delete, Crop)

**Goal:** Modify PDF pages without re-encoding content.

**Tasks:**
1. `core/manipulate.py` — functions:
   - `rotate_pages(pdf, angle, pages)` — rotate 90/180/270
   - `delete_pages(pdf, pages)` — remove specific pages
   - `reorder_pages(pdf, new_order)` — rearrange page sequence
   - `reverse_pages(pdf)` — reverse the entire document
   - `crop_pages(pdf, rect, pages)` — set crop box
   - All accept page range specs and return output path
2. `cli/manipulate.py` — subcommands:
   - `pdf-toolkit rotate`
   - `pdf-toolkit delete-pages`
   - `pdf-toolkit reorder`
   - `pdf-toolkit crop`
3. Tests

**Implementation reference:**
```python
import pymupdf

doc = pymupdf.open("input.pdf")
doc[0].set_rotation(90)           # rotate
doc.delete_pages([2, 5, 8])       # delete
doc.move_page(5, 0)               # reorder
page = doc[0]
page.set_cropbox(pymupdf.Rect(50, 50, 500, 700))  # crop
doc.save("modified.pdf")
```

**CLI after this phase:**
```
pdf-toolkit rotate doc.pdf --angle 90
pdf-toolkit rotate doc.pdf --angle 90 --pages 1-3,7
pdf-toolkit delete-pages doc.pdf --pages 5,8,12
pdf-toolkit reorder doc.pdf --order 3,1,2,5,4
pdf-toolkit reorder doc.pdf --reverse
pdf-toolkit crop doc.pdf --rect 50,50,500,700 --pages 1-5
```

**Commit message:** `feat: page manipulation — rotate, delete, reorder, crop`

---

### Phase 8: Watermarking & Stamping

**Goal:** Add text or image watermarks/stamps to PDF pages.

**Tasks:**
1. `core/watermark.py` — `add_text_watermark()` function:
   - Input: PDF path, text, fontsize, color (hex), opacity, rotation, position,
     overlay/underlay, page range
   - Uses PyMuPDF `page.insert_text()` with rotation and opacity
   - Centered diagonal text by default
2. `core/watermark.py` — `add_image_watermark()` function:
   - Input: PDF path, image path, position (center/corners), opacity, scale,
     overlay/underlay, page range
   - Uses PyMuPDF `page.insert_image()` with overlay parameter
3. `cli/watermark.py` — `pdf-toolkit watermark` subcommand:
   - Options: `--text`, `--image`, `--opacity`, `--rotation`, `--position`,
     `--overlay/--underlay`, `--pages`, `-o`
4. Tests

**Implementation reference:**
```python
import pymupdf

doc = pymupdf.open("input.pdf")
for page in doc:
    # Image watermark (behind content)
    page.insert_image(page.bound(), filename="watermark.png", overlay=False)
    # Text watermark
    page.insert_text(
        (page.rect.width / 2, page.rect.height / 2),
        "DRAFT", fontsize=72, color=(0.8, 0.8, 0.8), rotate=45, overlay=True)
doc.save("watermarked.pdf")
```

**CLI after this phase:**
```
pdf-toolkit watermark doc.pdf --text "DRAFT"
pdf-toolkit watermark doc.pdf --text "CONFIDENTIAL" --opacity 0.3 --rotation 45
pdf-toolkit watermark doc.pdf --text "DRAFT" --color "#FF0000" --fontsize 80
pdf-toolkit watermark doc.pdf --image logo.png --position bottom-right --opacity 0.5
pdf-toolkit watermark doc.pdf --image stamp.png --underlay
```

**Commit message:** `feat: text and image watermarks with opacity, rotation, positioning`

---

### Phase 9: OCR — Scanned PDFs → Searchable PDFs

**Goal:** Add a searchable text layer to scanned/image-based PDFs using Tesseract OCR.

**Requires:** Tesseract OCR (Apache-2.0, FOSS) installed on the system.

**Tasks:**
1. `core/detect.py` — `find_tesseract()` function:
   - Windows: check PATH and common install locations
   - Linux: `which tesseract`
   - Returns path and available languages, or None
2. `core/ocr.py` — `ocr_pdf()` function:
   - Input: PDF path, output path, language, auto-detect (only OCR pages that need it)
   - Auto-detection: `needs_ocr(page)` — checks if page has selectable text vs images
   - Uses PyMuPDF `page.get_textpage_ocr()` for existing PDFs
   - Uses `Pixmap.pdfocr_save()` for image inputs
   - Returns output path and per-page stats
3. `core/ocr.py` — `ocr_image()` function:
   - Input: image path(s), output PDF path, language
   - Converts images to searchable PDF
4. `cli/ocr.py` — `pdf-toolkit ocr` subcommand:
   - Options: `--language`, `--auto` (only OCR pages that need it), `--pages`, `-o`
   - Clear error if Tesseract is not installed
5. Tests

**Implementation reference:**
```python
import pymupdf

# OCR a scanned PDF
doc = pymupdf.open("scanned.pdf")
for page in doc:
    tp = page.get_textpage_ocr(language="eng", full=True)
    text = page.get_text(textpage=tp)

# OCR an image directly to searchable PDF
pix = pymupdf.Pixmap("scanned_page.png")
pix.pdfocr_save("searchable.pdf", language="eng")

# Auto-detect pages that need OCR
def needs_ocr(page):
    text = page.get_text().strip()
    images = page.get_images()
    return len(text) < 10 and len(images) > 0
```

**CLI after this phase:**
```
pdf-toolkit ocr scan.pdf
pdf-toolkit ocr scan.pdf --language eng+deu
pdf-toolkit ocr scan.pdf --auto                   # only OCR pages that need it
pdf-toolkit ocr photo.jpg -o searchable.pdf
```

**User experience when Tesseract is missing:**
```
✗ Tesseract OCR is not installed.

  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
  Linux:   sudo apt install tesseract-ocr
  macOS:   brew install tesseract
```

**Commit message:** `feat: OCR support via Tesseract — scanned PDFs → searchable text`

---

### Phase 10: Page Numbers, Headers & Footers

**Goal:** Add page numbers, headers, and/or footers to every page (or selected pages).

**Tasks:**
1. `core/manipulate.py` — `add_page_numbers()` function:
   - Input: PDF path, position (bottom-center, bottom-right, etc.), format string
     (`"Page {n} of {total}"`, `"{n}"`, etc.), fontsize, color, start number, page range
   - Uses PyMuPDF `page.insert_text()` at calculated positions
2. `core/manipulate.py` — `add_header_footer()` function:
   - Input: PDF path, header text, footer text, fontsize, color, page range
   - Supports `{n}`, `{total}`, `{date}` placeholders
3. `cli/manipulate.py` — `pdf-toolkit add-page-numbers` subcommand
4. `cli/manipulate.py` — `pdf-toolkit add-header` / `pdf-toolkit add-footer` subcommands
5. Tests

**Implementation reference:**
```python
import pymupdf

doc = pymupdf.open("input.pdf")
for i, page in enumerate(doc):
    # Footer with page numbers
    page.insert_text(
        (page.rect.width / 2 - 40, page.rect.height - 30),
        f"Page {i + 1} of {doc.page_count}",
        fontsize=10, color=(0.4, 0.4, 0.4))
    # Header
    page.insert_text(
        (50, 30), "Company Report — Confidential",
        fontsize=8, color=(0.5, 0.5, 0.5))
doc.save("with_numbers.pdf")
```

**CLI after this phase:**
```
pdf-toolkit add-page-numbers doc.pdf
pdf-toolkit add-page-numbers doc.pdf --position bottom-right --format "{n}/{total}"
pdf-toolkit add-page-numbers doc.pdf --start 5 --pages 3-20
pdf-toolkit add-header doc.pdf --text "Company Report — {date}"
pdf-toolkit add-footer doc.pdf --text "Page {n} of {total}" --fontsize 8
```

**Commit message:** `feat: add page numbers, headers, and footers`

---

### Phase 11: Redaction

**Goal:** Permanently remove sensitive text from PDFs (not just an overlay — actual
content removal for legal/security compliance).

**Tasks:**
1. `core/redact.py` — `redact_text()` function:
   - Input: PDF path, search terms (list of strings), page range, fill color
   - Uses `page.search_for()` to find text locations
   - Uses `page.add_redact_annot()` + `page.apply_redactions()` to permanently remove
   - Returns count of redactions applied
2. `core/redact.py` — `redact_pattern()` function:
   - Same as above but with regex patterns (e.g. SSN, email addresses, phone numbers)
3. `core/redact.py` — built-in patterns:
   - `ssn` → `\b\d{3}-\d{2}-\d{4}\b`
   - `email` → common email regex
   - `phone` → common phone number patterns
   - `credit-card` → `\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b`
4. `cli/redact.py` — `pdf-toolkit redact` subcommand:
   - Options: `--text "string"` (repeatable), `--pattern "regex"` (repeatable),
     `--preset ssn|email|phone|credit-card`, `--pages`, `-o`
   - Preview mode: `--dry-run` shows what would be redacted without modifying
5. Tests

**Implementation reference:**
```python
import pymupdf

doc = pymupdf.open("input.pdf")
page = doc[0]

# Search and redact
areas = page.search_for("confidential information")
for area in areas:
    page.add_redact_annot(area, fill=(0, 0, 0))  # black box
page.apply_redactions()  # permanently removes content
doc.save("redacted.pdf")
```

**Important:** PyMuPDF redaction actually removes the underlying content — it's not
just an overlay. This is critical for legal/security compliance.

**CLI after this phase:**
```
pdf-toolkit redact doc.pdf --text "John Doe" --text "123 Main St"
pdf-toolkit redact doc.pdf --pattern "\d{3}-\d{2}-\d{4}"
pdf-toolkit redact doc.pdf --preset ssn --preset email
pdf-toolkit redact doc.pdf --text "CONFIDENTIAL" --dry-run
```

**Commit message:** `feat: permanent text redaction with search, regex, and presets`

---

### Phase 12: Fill & Flatten PDF Forms

**Goal:** Programmatically fill PDF form fields and optionally flatten them to
static content.

**Tasks:**
1. `core/forms.py` — `list_fields()` function:
   - Input: PDF path
   - Returns list of field dicts: name, type, current value, options (for dropdowns)
2. `core/forms.py` — `fill_form()` function:
   - Input: PDF path, field_data (dict or JSON file path), output path
   - Uses PyMuPDF `page.widgets()` to find and fill fields
3. `core/forms.py` — `flatten_form()` function:
   - Input: PDF path, output path
   - Converts all form fields to static content (no longer editable)
4. `cli/forms.py` — subcommands:
   - `pdf-toolkit list-fields form.pdf`
   - `pdf-toolkit fill-form form.pdf --data data.json`
   - `pdf-toolkit flatten-form form.pdf`
5. Tests

**Implementation reference:**
```python
import pymupdf

doc = pymupdf.open("form.pdf")
page = doc[0]

# List fields
for widget in page.widgets():
    print(f"{widget.field_name}: {widget.field_type_string}")

# Fill fields
for widget in page.widgets():
    if widget.field_name == "name":
        widget.field_value = "John Doe"
        widget.update()
doc.save("filled_form.pdf")
```

**CLI after this phase:**
```
pdf-toolkit list-fields form.pdf
pdf-toolkit list-fields form.pdf --json
pdf-toolkit fill-form form.pdf --data values.json
pdf-toolkit fill-form form.pdf --set "name=John Doe" --set "date=2026-03-18"
pdf-toolkit flatten-form form.pdf
```

**Commit message:** `feat: PDF form field listing, filling, and flattening`

---

### Phase 13: PDF/A Archival Compliance

**Goal:** Best-effort conversion to PDF/A for long-term archival.

**Tasks:**
1. `core/archive.py` — `convert_to_pdfa()` function:
   - Input: PDF path, output path, level (1b, 2b, 3b)
   - Steps: embed fonts, remove JavaScript, strip dynamic content,
     add XMP metadata with PDF/A conformance, embed ICC colour profile
   - Uses pikepdf for metadata + PyMuPDF for content processing
   - Returns output path and compliance report
2. `cli/convert.py` — add `--pdfa` flag to `pdf-toolkit compress`
3. `cli/convert.py` — `pdf-toolkit to-pdfa` subcommand for explicit conversion
4. Tests

**Note:** Full PDF/A compliance is extremely complex. Our approach is "best-effort" —
we handle the most common requirements (metadata, font embedding, removing transparency).
For critical archival needs, users should validate with tools like veraPDF (FOSS).

**CLI after this phase:**
```
pdf-toolkit to-pdfa doc.pdf
pdf-toolkit to-pdfa doc.pdf --level 2b
pdf-toolkit compress doc.pdf --pdfa    # compress and make PDF/A
```

**Commit message:** `feat: best-effort PDF/A archival conversion`

---

### Phase 14: NiceGUI — Modern Desktop/Web GUI

**Goal:** Build a modern, drag-and-drop GUI that non-technical users can use
without touching a terminal.

**Library:** NiceGUI (`nicegui>=2.0`) — MIT licensed, runs as a local web server with
optional native desktop mode (frameless browser window that looks like a desktop app).

**Tasks:**
1. `gui/app.py` — main application shell:
   - Dark mode by default
   - Header with app title and version
   - Tab bar: Compress | Convert | Tools | Settings
   - `pdf-toolkit gui` CLI command to launch
   - `ui.run(native=True)` for desktop mode, `ui.run()` for web mode
2. `gui/tabs/compress.py` — Compress tab:
   - Drag-and-drop file upload (`ui.upload` with `.pdf` filter)
   - Quality preset selector (segmented button)
   - Max DPI slider
   - Greyscale toggle
   - Compress button with progress bar
   - Results table: filename, original size, new size, reduction %
   - Download link for compressed files
3. `gui/tabs/convert.py` — Convert tab:
   - Conversion type selector: PDF→DOCX, DOCX→PDF, PDF→Images, Images→PDF,
     XLSX→PDF, PDF→Markdown
   - Dynamic options per conversion type (DPI, format, pages, etc.)
   - File upload + convert button + results/download
4. `gui/tabs/tools.py` — Tools tab:
   - Accordion or sub-tabs for: Encrypt, Decrypt, Watermark, OCR, Page Numbers,
     Rotate, Delete Pages, Redact, Fill Form, Info
   - Each with appropriate inputs and controls
5. `gui/tabs/settings.py` — Settings tab:
   - Default quality preset
   - Default output directory
   - Dark/light mode toggle
   - Save/reset settings
6. Make the GUI the default when `pdf-toolkit` is run with no arguments on desktop
   (instead of the old tkinter file picker)
7. Update `Run PDF Toolkit.bat` and `run.sh` to launch GUI
8. Tests (at minimum, verify the app starts without errors)

**GUI layout sketch:**
```
┌──────────────────────────────────────────────────┐
│  📄 PDF Toolkit                              v2.0│
├────────┬──────────┬─────────┬────────────────────┤
│Compress│ Convert  │  Tools  │  Settings          │
├────────┴──────────┴─────────┴────────────────────┤
│                                                  │
│  ┌──────────────────────────────────────┐        │
│  │     📁 Drop PDF files here           │        │
│  │        or click to browse            │        │
│  └──────────────────────────────────────┘        │
│                                                  │
│  Quality:  [ Low ] [ Medium ] [ High ] [Lossless]│
│  Max DPI:  ═══════════●═══════  300              │
│  □ Greyscale                                     │
│                                                  │
│  [ 🔨 Compress ]                                 │
│                                                  │
│  ┌─────────────────────────────────────────────┐ │
│  │ File          Original    New     Reduction │ │
│  │ report.pdf    4.2 MB    1.1 MB    73.8%    │ │
│  │ scan.pdf     12.8 MB    3.2 MB    75.0%    │ │
│  │ ─────────────────────────────────────────── │ │
│  │ Total         17.0 MB    4.3 MB    74.7%   │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  [ ⬇ Download All ]                              │
└──────────────────────────────────────────────────┘
```

**Commit message:** `feat: NiceGUI desktop/web interface with drag-and-drop`

---

### Phase 15: Polish, Packaging & Distribution

**Goal:** Final polish, comprehensive error handling, documentation, and packaging.

**Tasks:**
1. **Context menu update:** Expand Windows right-click menu to include all major
   operations (Compress, Convert to DOCX, Encrypt, etc.)
2. **README rewrite:** Full documentation of all features, CLI reference, GUI screenshots
3. **Error messages:** Audit every error path — friendly messages with actionable
   suggestions, never raw tracebacks (unless `--debug` is passed)
4. **Help text:** Comprehensive `--help` for every subcommand with examples
5. **Startup speed:** Lazy-import heavy libraries (pymupdf, pikepdf) so `--help` and
   `--version` are instant
6. **PyInstaller / Nuitka investigation:** Can we produce a single .exe for Windows
   users who don't have Python? (Both are FOSS — feasibility study, may be a separate
   future effort)
7. **CI/CD:** GitHub Actions workflow for linting and basic tests
8. **Changelog:** CHANGELOG.md with all v2 features
9. **Final dependency audit:** Verify every dependency is FOSS, pinned, and minimal

**Commit message:** `chore: v2.0 polish — docs, error handling, context menu, CI`

---

## 5. Dependency Summary

### `requirements.txt` (after all phases)

```
# Core PDF engine
pymupdf>=1.25
pikepdf>=8.0
pypdf>=4.0
Pillow>=10.0

# CLI
typer[all]>=0.9

# Python 3.10 compat (not needed for 3.11+)
tomli>=2.0; python_version < "3.11"
```

### `requirements-gui.txt`

```
-r requirements.txt
nicegui>=2.0
```

### `requirements-full.txt`

```
-r requirements-gui.txt
python-docx>=1.0
openpyxl>=3.1
```

### Every dependency is FOSS

| Package | License | Type |
|---------|---------|------|
| pymupdf | AGPL-3.0 | Copyleft (OSI-approved) |
| pikepdf | MPL-2.0 | Weak copyleft (OSI-approved) |
| pypdf | BSD-3-Clause | Permissive |
| Pillow | HPND (MIT-like) | Permissive |
| typer | MIT | Permissive |
| rich | MIT | Permissive |
| nicegui | MIT | Permissive |
| python-docx | MIT | Permissive |
| openpyxl | MIT | Permissive |
| LibreOffice | MPL-2.0 | Weak copyleft — external tool |
| Tesseract OCR | Apache-2.0 | Permissive — external tool |

---

## 6. Risks & Mitigations

### AGPL-3.0 license change
- **Risk:** Some contributors or users may dislike copyleft.
- **Mitigation:** AGPL is the standard FOSS license for PyMuPDF-based projects. It
  only restricts people who want to distribute closed-source derivatives. Our project
  is open-source — nothing changes in practice for users or contributors.

### PyMuPDF is a large dependency (~30 MB)
- **Risk:** Increases install size.
- **Mitigation:** It replaces the need for multiple smaller libraries. Net complexity
  is lower. The entire venv will be ~100 MB — comparable to any modern Python project.

### PDF → DOCX conversion quality
- **Risk:** Complex layouts won't convert perfectly.
- **Mitigation:** This is a fundamental limitation of the PDF format. Our conversion
  matches or exceeds other FOSS tools. Document the limitations clearly.

### DOCX/XLSX → PDF without LibreOffice
- **Risk:** Pure-Python fallback produces basic output.
- **Mitigation:** Clearly warn users and suggest LibreOffice installation. The fallback
  is still useful for simple documents.

### OCR requires Tesseract
- **Risk:** Users may not have Tesseract installed.
- **Mitigation:** Clear error message with platform-specific install instructions.
  Feature degrades gracefully — rest of the app works fine.

### NiceGUI adds web server overhead
- **Risk:** Some users may be uncomfortable with a local web server.
- **Mitigation:** NiceGUI in native mode looks like a normal desktop app. The server
  is local-only (127.0.0.1), accepts no external connections, shuts down when the
  window closes. Document this clearly.

### PDF/A compliance is imperfect
- **Risk:** Best-effort PDF/A may not pass strict validators.
- **Mitigation:** Document as "best-effort". Recommend veraPDF (FOSS) for strict
  compliance validation.

---

*Document version: 2.0 — March 2026*
*Phases: 15 — each a self-contained git commit*
*License: AGPL-3.0 — every dependency is FOSS*
