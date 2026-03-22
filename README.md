# PDF Toolkit

Make PDF files smaller — just pick them from a file dialog and it does the rest.

No cloud upload. No account. Works entirely on your computer.

---

## Quick start — Windows

1. **[Download the zip](https://github.com/michaellucasnzl/pdf-tools/archive/refs/heads/main.zip)** and unzip it anywhere.
2. Double-click **`setup.bat`** — this installs everything automatically (needs [Python](https://www.python.org/downloads/) 3.11+; tick *"Add to PATH"* during install).
3. Double-click **`Run PDF Toolkit.bat`** — a file picker opens. Select your PDFs and click Open.

That's it. Compressed files are saved next to the originals with `_compressed` added to the name.

> **Drag and drop:** you can also drag PDF files directly onto `Run PDF Toolkit.bat`.

---

## Quick start — Linux / macOS

You need Python 3.11+ and, for the file dialog, `python3-tk`.

```bash
# Ubuntu / Debian
sudo apt install python3 python3-venv python3-tk

# Fedora
sudo dnf install python3 python3-tkinter

# macOS (Homebrew)
brew install python-tk
```

Then:

```bash
git clone https://github.com/michaellucasnzl/pdf-tools.git
cd pdf-toolkit
bash setup.sh        # installs dependencies once
./run.sh             # opens file picker
```

No file dialog? Run from the command line instead (see below).

---

## Common uses

| Goal | Command |
|------|---------|
| Pick files visually | `./run.sh` (or double-click on Windows) |
| Compress a specific file | `./run.sh report.pdf` |
| Compress all PDFs in a folder | `./run.sh *.pdf` |
| Maximum compression (scanned docs) | `./run.sh scan.pdf -q low --max-dpi 150 -g` |
| Convert colour scans to greyscale | `./run.sh scan.pdf --grayscale` |
| Split into one file per page | `./run.sh catalogue.pdf --split-pages` |
| Merge several PDFs into one | `./run.sh a.pdf b.pdf c.pdf --merge` |
| Preview savings without changing files | `./run.sh scan.pdf --dry-run` |
| Replace the original (keeps a backup) | `./run.sh scan.pdf --overwrite --backup` |

On Windows replace `./run.sh` with `"Run PDF Toolkit.bat"` — or just drag files onto it.

---

## Quality settings

Pass `-q` to choose how much compression to apply:

| `-q low` | Most aggressive — good for archiving or email |
| `-q medium` | *(default)* Good balance of quality and size |
| `-q high` | Gentle compression, near-original quality |
| `-q lossless` | No image changes — only structural optimisation |

---

## All options

```
Usage: pdf-toolkit [OPTIONS] [FILES]...

-q, --quality       low / medium / high / lossless   (default: medium)
-g, --grayscale     Convert colour images to greyscale
--max-dpi           Reduce image resolution (150 = screen, 300 = print)
-p, --split-pages   One file per page
--pages             With --split-pages: which pages, e.g. "1-5,10"
-m, --merge         Merge inputs into one file before compressing
--merge-output      Path for the merged output file
--dry-run           Show predicted savings without writing anything
-w, --workers       How many files to process in parallel (default: all CPUs)
-o, --output-dir    Where to save results (default: same folder as input)
-s, --suffix        Suffix added to filenames (default: _compressed)
--overwrite         Replace the original file
-b, --backup        Save a .bak copy before overwriting
--strip-metadata    Remove author, title, and other metadata
--json              Print results as JSON (useful for scripting)
--debug             Show full error details
--save-defaults     Save current options as your personal defaults
--show-config       Print your saved defaults
--reset-config      Clear your saved defaults
--version           Show version
```

---

## Windows right-click menu (optional)

Right-click any PDF → **Compress PDF** or **Split PDF pages** — without opening a terminal:

1. Run `setup.bat` first (if not done already).
2. Right-click `install_context_menu.bat` → **Run as administrator**.

To remove: right-click `uninstall_context_menu.bat` → **Run as administrator**.

---

## Saving your preferred settings

Run once with `--save-defaults` to avoid typing options every time:

```bash
./run.sh -q low --max-dpi 150 -g --save-defaults
```

Settings are saved to `~/.pdf-toolkit.toml` and applied automatically on every run.

---

## How it works

1. Optionally converts images to greyscale and downsamples them to the target DPI.
2. Re-encodes images at the chosen JPEG quality.
3. Compresses all content streams with lossless deflate.
4. Removes unused objects and linearises the PDF for fast loading.

If the result would be *larger* than the original, the original is kept unchanged.

---

## License

MIT — see [LICENSE](LICENSE).


## Features

- **File picker dialog** — run with no arguments and choose files visually
- **Batch processing** — glob patterns, multiple files, or whole folders
- **Four quality presets** — from aggressive to lossless
- **`--grayscale`** — convert colour images to greyscale for dramatic size reductions on scanned docs
- **`--max-dpi`** — downsample images to a target DPI
- **`--split-pages`** — one compressed PDF per page, with optional page range selection
- **`--merge`** — combine multiple PDFs into one before compressing
- **`--dry-run`** — analyse files and predict savings without writing anything
- **Parallel batch** — compress multiple files simultaneously with `--workers`
- **`--json`** — machine-readable JSON summary for scripting
- **`--debug`** — full tracebacks on errors for troubleshooting
- **Personal config** — save your preferred defaults to `~/.pdf-toolkit.toml`
- **Windows context menu** — right-click any PDF to compress or split it
- **Smart safeguard** — never grows a file; if compression makes it larger the original is preserved
- **No external tools required** — pure Python, no Ghostscript needed

## Requirements

- Python 3.11+
- `tkinter` (ships with Python on Windows and macOS; on Linux: `sudo apt install python3-tk`)

## Installation

### From source (recommended for development)

```bash
git clone https://github.com/michaellucasnzl/pdf-tools.git
cd pdf-toolkit
python -m venv .venv

# Windows
.\.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e .
```

After `pip install -e .` (or `pip install .`) the `pdf-toolkit` command is available globally in your virtual environment.

### From requirements.txt only

```bash
pip install -r requirements.txt
python pdf_resizer.py [OPTIONS] [FILES]
```

### Windows context menu (right-click integration)

After installing, run **as Administrator**:

```
install_context_menu.bat
```

This adds two entries to the right-click menu for every `.pdf` file:

- **Compress PDF** — compresses with your saved defaults
- **Split PDF pages** — splits into one file per page

To remove them:

```
uninstall_context_menu.bat
```

---

## Usage

### File picker (easiest — no typing)

```bash
pdf-toolkit
```

Opens a file dialog. Select one or many PDFs, click Open, done.

### Single file

```bash
pdf-toolkit report.pdf
```

Produces `report_compressed.pdf` in the same folder.

### Multiple files / globs

```bash
pdf-toolkit file1.pdf file2.pdf
pdf-toolkit *.pdf
pdf-toolkit "invoices/*.pdf"
```

> **Windows note:** Wrap glob patterns in quotes so PowerShell doesn't expand them early.

### Entire folder

```bash
pdf-toolkit --dir ./my-documents
pdf-toolkit --dir ./my-documents --recursive
```

### Drag and drop (Windows)

Drag PDF files onto `pdf_resizer.py` in File Explorer. Windows passes the paths as arguments automatically.

---

## Options

```
Usage: pdf-toolkit [OPTIONS] [FILES]...

  Shrink PDF file sizes by compressing images and optimizing structure.

Arguments:
  [FILES]...     PDF files to process. Supports glob patterns.
                 Omit to open a file picker dialog.

Options:
  -q, --quality [low|medium|high|lossless]
                         Compression quality preset  [default: medium]
  -g, --grayscale        Convert colour images to greyscale
  --max-dpi INTEGER      Downsample images exceeding this DPI (36–1200)
  -p, --split-pages      Split into one file per page
  --pages TEXT           With --split-pages: page range, e.g. '1-5,10,15-20'
  -m, --merge            Merge all inputs into one PDF before compressing
  --merge-output PATH    Output path for merged file
  --dry-run              Analyse and predict savings without writing output
  -w, --workers INT      Parallel worker threads for batch jobs (default: CPU count)
  -o, --output-dir PATH  Output directory (default: same as input)
  -s, --suffix TEXT      Suffix for output filenames  [default: _compressed]
  --overwrite            Overwrite original files
  -d, --dir PATH         Process all PDFs in a directory
  -r, --recursive        With --dir, include subdirectories
  --strip-metadata       Remove document metadata
  -b, --backup           Create .bak backup before overwriting
  -v, --verbose          Show detailed per-image progress
  --quiet                Suppress all output except errors
  --json                 Print a JSON summary to stdout
  --debug                Print full tracebacks on errors
  --save-defaults        Save current options to ~/.pdf-toolkit.toml
  --show-config                                    Print the current config and exit.
  --reset-config                                   Delete the personal config file and exit.
  --version                                        Show version and exit.
  --help                 Show this message and exit
```

---

## Quality Presets

| Preset | Image Quality | Best For |
|--------|:---:|----------|
| `low` | 30% | Maximum size reduction — archival or email |
| `medium` *(default)* | 60% | Good balance of quality and size |
| `high` | 80% | Mild reduction, near-original appearance |
| `lossless` | — | No image recompression; structure/stream optimisation only |

### Typical results

| Preset | Reduction |
|--------|:---------:|
| `low` | ~65–70% |
| `medium` | ~55–60% |
| `high` | ~40–50% |
| `lossless` | 0–15% |

Results vary depending on how images were originally embedded. Scanned documents and presentation PDFs see the biggest gains.

---

## Image Downsampling (`--max-dpi`)

For **image-heavy PDFs** (scans, product sheets, catalogues), the biggest wins come from reducing resolution. Use `--max-dpi` to cap the DPI of all embedded images:

```bash
pdf-toolkit scan.pdf --max-dpi 150        # screen/email — biggest reduction
pdf-toolkit scan.pdf --max-dpi 300        # print-ready — moderate reduction
pdf-toolkit scan.pdf -q low --max-dpi 150 # combined — maximum compression
```

| `--max-dpi` | Good for | Typical extra saving vs quality-only |
|:-----------:|----------|:------------------------------------:|
| 96 | Phone/web thumbnails | very high |
| 150 | Screen reading, email | high |
| 200 | Mixed use | moderate |
| 300 | Print-ready output | low–moderate |

---

## Greyscale Conversion (`--grayscale` / `-g`)

Converts all colour images to greyscale before recompressing. Extremely effective for black-and-white scanned documents that were accidentally saved in colour mode.

```bash
pdf-toolkit scan.pdf -g
pdf-toolkit scan.pdf -g -q low --max-dpi 150   # maximum compression
```

Alpha channels are automatically flattened onto a white background before JPEG encoding, so transparent PNGs are handled safely.

---

## Splitting into Single-Page Files (`--split-pages` / `-p`)

Extracts every page into its own compressed PDF, placed in a sub-folder:

```bash
pdf-toolkit catalogue.pdf --split-pages
```

```
catalogue_compressed/
  catalogue_p01.pdf
  catalogue_p02.pdf
  catalogue_p03.pdf
  ...
```

### Select specific pages with `--pages`

Page numbers are 1-based. Use commas and ranges:

```bash
pdf-toolkit catalogue.pdf --split-pages --pages "1-5,10,15-20"
pdf-toolkit report.pdf    --split-pages --pages "3,7-9"
```

### Combine with other options

```bash
pdf-toolkit scan.pdf --split-pages -q high           # high quality per page
pdf-toolkit scan.pdf --split-pages -q low --max-dpi 150  # maximum reduction
pdf-toolkit scan.pdf --split-pages -o ./output       # custom output location
pdf-toolkit scan.pdf --split-pages --suffix _pages   # custom folder suffix
```

---

## Merging PDFs (`--merge` / `-m`)

Combine multiple PDFs into a single file, then compress it:

```bash
pdf-toolkit chapter1.pdf chapter2.pdf chapter3.pdf --merge
# → merged_compressed.pdf  (next to chapter1.pdf)

# Custom output path
pdf-toolkit *.pdf --merge --merge-output book.pdf

# Merge and send to output folder
pdf-toolkit *.pdf --merge --output-dir ./dist
```

---

## Dry Run

Analyse files and predict how much space will be saved — without writing anything:

```bash
pdf-toolkit scan.pdf --dry-run
pdf-toolkit *.pdf --dry-run
pdf-toolkit *.pdf --dry-run --json   # machine-readable output
```

The dry-run table shows file size, page count, image count, image-to-file ratio, and an estimated saving (based on the medium quality preset).

---

## Parallel Batch Processing (`--workers` / `-w`)

When processing multiple files, pdf-toolkit automatically uses parallel threads. The default is the CPU core count. Override with `--workers`:

```bash
pdf-toolkit *.pdf -w 2    # conservative — useful when memory is tight
pdf-toolkit *.pdf -w 8    # aggressive — fast on a big machine
```

---

## JSON Output (`--json`)

Prints a machine-readable JSON summary to stdout. Suppresses all normal output (implies `--quiet`):

```bash
pdf-toolkit *.pdf --json
```

```json
[
  {
    "file": "report.pdf",
    "original_bytes": 4194304,
    "new_bytes": 1258291,
    "reduction_pct": 70.0,
    "success": true
  }
]
```

Combine with `--dry-run` for scriptable pre-flight analysis.

---

## Personal Config (`~/.pdf-toolkit.toml`)

Save your preferred defaults so you never have to retype them:

```bash
# Save current options as defaults
pdf-toolkit -q low --max-dpi 150 -g --save-defaults
```

This writes to `~/.pdf-toolkit.toml`:

```toml
[defaults]
quality = "low"
suffix = "_compressed"
max_dpi = 150
grayscale = true
```

Edit the file manually at any time. Supported keys:

| Key | Type | Example |
|-----|------|---------|
| `quality` | string | `"medium"` |
| `suffix` | string | `"_small"` |
| `max_dpi` | integer | `150` |
| `grayscale` | bool | `true` |

View or reset:

```bash
pdf-toolkit --show-config   # print current config
pdf-toolkit --reset-config  # delete config file
```

---

## Examples

```bash
# Compress with aggressive settings
pdf-toolkit scan.pdf -q low

# Greyscale + downscale + quality for maximum reduction
pdf-toolkit scan.pdf -g -q low --max-dpi 150

# Split a catalogue into individual pages
pdf-toolkit catalogue.pdf --split-pages

# Split only pages 1–5 and page 10
pdf-toolkit catalogue.pdf --split-pages --pages "1-5,10"

# Merge three chapters, then compress
pdf-toolkit ch1.pdf ch2.pdf ch3.pdf --merge --merge-output book.pdf

# Preview what would happen without making changes
pdf-toolkit *.pdf --dry-run

# Batch compress an entire archive in parallel
pdf-toolkit --dir ./archive -r -w 6

# Overwrite originals with backup, strip metadata
pdf-toolkit *.pdf --overwrite --backup --strip-metadata

# Quiet mode — exit code only (0 = success, 1 = any failure)
pdf-toolkit *.pdf --quiet

# Machine-readable output for scripting
pdf-toolkit *.pdf --json > results.json
```

---

## How It Works

Compression runs in two phases:

1. **pypdf** — Optionally converts images to greyscale, downscales any images exceeding `--max-dpi` using Lanczos resampling, re-encodes them at the target JPEG quality (alpha channels are safely flattened), then applies lossless FlateDecode compression to all content streams.
2. **pikepdf** — Removes unreferenced objects and resources from the PDF object graph, optionally strips metadata, then re-saves with linearisation (enables fast web viewing).

If the resulting file is larger than the original, the original bytes are kept instead.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [`pypdf`](https://github.com/py-pdf/pypdf) | Image recompression, content stream FlateDecode |
| [`pikepdf`](https://github.com/pikepdf/pikepdf) | Object cleanup, linearisation (powered by QPDF) |
| [`Pillow`](https://github.com/python-pillow/Pillow) | Image transcoding, greyscale conversion, DPI downscaling |
| [`typer`](https://github.com/fastapi/typer) | CLI framework with rich output |
| [`tomli`](https://github.com/hukkin/tomli) | TOML config parsing (Python < 3.11 only) |

---

## License

MIT — see [LICENSE](LICENSE).


## Features

- **File picker dialog** — run with no arguments and choose files visually
- **Batch processing** — use glob patterns, multiple files, or point at a whole folder
- **Four quality presets** — from aggressive to lossless
- **Smart safeguard** — never grows a file; if compression makes it larger, the original is preserved
- **Detailed summary table** — see original size, new size, and % reduction for every file
- **No external tools required** — pure Python, no Ghostscript install needed
- **Safe by default** — writes to a new `_compressed` file; original is kept unless you pass `--overwrite`

## Requirements

- Python 3.11+
- `tkinter` (ships with Python on Windows and macOS; on Linux: `sudo apt install python3-tk`)

## Installation

```bash
git clone https://github.com/michaellucasnzl/pdf-tools.git
cd pdf-toolkit
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

## Usage

### File picker (easiest — no typing)

```bash
python pdf_resizer.py
```

Opens a file dialog. Select one or many PDFs, click Open, and they're compressed automatically.

### Single file

```bash
python pdf_resizer.py report.pdf
```

Produces `report_compressed.pdf` in the same folder.

### Multiple files

```bash
python pdf_resizer.py file1.pdf file2.pdf file3.pdf
```

### Glob pattern (batch)

```bash
python pdf_resizer.py *.pdf
python pdf_resizer.py "invoices/*.pdf"
```

> **Windows note:** Wrap glob patterns in quotes so PowerShell doesn't expand them before Python can.

### Entire folder

```bash
python pdf_resizer.py --dir ./my-documents
python pdf_resizer.py --dir ./my-documents --recursive
```

### Drag and drop (Windows)

Drag PDF files onto `pdf_resizer.py` in File Explorer. Windows passes the paths as arguments automatically.

---

## Options

```
Usage: pdf-toolkit [OPTIONS] [FILES]...

Arguments:
  [FILES]...    PDF files to process. Supports glob patterns.
                If omitted, opens a file picker dialog.

Options:
  -q, --quality [low|medium|high|lossless]
                        Compression quality preset  [default: medium]
  -p, --split-pages     Split into one file per page. Files are named
                        <stem>_p01.pdf, <stem>_p02.pdf, … and placed in a
                        sub-folder next to the original.
  --max-dpi INTEGER     Downsample images exceeding this DPI.
                        150 = screen/email quality, 300 = print quality.
                        Combines with --quality for maximum reduction.
  -o, --output-dir PATH Output directory (default: same as input)
  -s, --suffix TEXT     Suffix for output filenames  [default: _compressed]
  --overwrite           Overwrite original files instead of creating new ones
  -d, --dir PATH        Process all PDFs in a directory
  -r, --recursive       With --dir, include subdirectories
  --strip-metadata      Remove document metadata (author, title, etc.)
  -b, --backup          Create a .bak backup before overwriting
  -v, --verbose         Show detailed per-phase progress
  --quiet               Suppress all output except errors
  --version             Show version and exit
  --help                Show this message and exit
```

---

## Splitting into single-page files

Use `--split-pages` (`-p`) to extract every page into its own compressed PDF. This is useful when you want to:
- Share or upload individual pages
- Keep higher resolution but reduce per-page size
- Use pages as standalone assets (product sheets, catalogues, slides)

```bash
# Split a PDF into one file per page
python pdf_resizer.py catalogue.pdf --split-pages
```

Output files are written to a sub-folder next to the original:
```
catalogue_compressed/
  catalogue_p01.pdf
  catalogue_p02.pdf
  catalogue_p03.pdf
  ...
```

The folder name uses the same `--suffix` as the normal mode (`_compressed` by default). Override it:

```bash
# Custom folder name suffix
python pdf_resizer.py catalogue.pdf --split-pages --suffix _pages
# → catalogue_pages/catalogue_p01.pdf ...

# Send to a specific output directory
python pdf_resizer.py catalogue.pdf --split-pages -o ./output
# → output/catalogue_compressed/catalogue_p01.pdf ...
```

Compression options apply to each individual page:

```bash
# Split with high quality (keep resolution)
python pdf_resizer.py scan.pdf --split-pages -q high

# Split with downsampling for maximum reduction
python pdf_resizer.py scan.pdf --split-pages -q low --max-dpi 150
```

After processing, a summary table shows every output file and its size, plus the total reduction versus the original.

---

## Quality Presets

| Preset | Image Quality | Best For |
|--------|:---:|---------|
| `low` | 30% | Maximum size reduction — acceptable for archival or email |
| `medium` *(default)* | 60% | Good balance of quality and size |
| `high` | 80% | Mild reduction, near-original appearance |
| `lossless` | — | No image recompression; only structure/stream optimisation |
### Image downsampling with `--max-dpi`

For **image-heavy PDFs** (scans, product sheets, catalogues), the biggest wins come from reducing image resolution — not just JPEG quality. Use `--max-dpi` to cap the DPI of all embedded images:

```bash
# Good for screen viewing / email — biggest size reduction
python pdf_resizer.py scan.pdf --max-dpi 150

# Good for printing — moderate reduction
python pdf_resizer.py scan.pdf --max-dpi 300

# Combine with quality preset for maximum compression
python pdf_resizer.py scan.pdf -q low --max-dpi 150
```

| `--max-dpi` | Good for | Typical extra reduction vs quality-only |
|:-----------:|----------|:---------------------------------------:|
| 96 | Phone/web thumbnails | very high |
| 150 | Screen reading, email | high |
| 200 | Mixed use | moderate |
| 300 | Print-ready output | low–moderate |

The DPI is estimated from image pixel dimensions versus page dimensions. If an image is already below the target DPI it is left untouched.
### Typical results

| Preset | Reduction |
|--------|:---------:|
| `low` | ~65–70% |
| `medium` | ~55–60% |
| `high` | ~40–50% |
| `lossless` | 0–15% |

Results vary depending on how images were originally embedded. Scanned documents and presentation PDFs see the biggest gains.

---

## Examples

```bash
# Compress with aggressive settings, save to a specific folder
python pdf_resizer.py scan.pdf -q low -o ./compressed

# Image-heavy PDF — downsample to 150 DPI for maximum reduction
python pdf_resizer.py scan.pdf --max-dpi 150

# Both together — maximum compression
python pdf_resizer.py scan.pdf -q low --max-dpi 150

# Split a catalogue into individual pages
python pdf_resizer.py catalogue.pdf --split-pages

# Split and keep high quality per page
python pdf_resizer.py catalogue.pdf --split-pages -q high

# Overwrite originals with a safety backup
python pdf_resizer.py *.pdf --overwrite --backup

# Compress entire archive recursively, strip metadata
python pdf_resizer.py --dir ./archive -r --strip-metadata

# Quiet mode — no output, just exit code (0 = success, 1 = failure)
python pdf_resizer.py *.pdf --quiet
```

---

## How It Works

Compression runs in two phases:

1. **pypdf** — Optionally downscales images exceeding `--max-dpi`, then re-encodes them at the target JPEG quality, then applies lossless FlateDecode compression to all content streams.
2. **pikepdf** — Removes unreferenced objects and resources from the PDF object graph, then re-saves with linearisation (fast web view).

If the resulting file is larger than the original, the original bytes are kept instead.

---

## Dependencies

| Package | Purpose |
|---------|---------|
| [`pypdf`](https://github.com/py-pdf/pypdf) | Image recompression, content stream FlateDecode |
| [`pikepdf`](https://github.com/pikepdf/pikepdf) | Object cleanup, linearisation (powered by QPDF) |
| [`Pillow`](https://github.com/python-pillow/Pillow) | Image transcoding (used by pypdf) |
| [`typer`](https://github.com/fastapi/typer) | CLI framework with rich output |

---

## License

MIT — see [LICENSE](LICENSE).
