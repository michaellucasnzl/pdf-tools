"""
PDF Toolkit — Shrink PDF file sizes by compressing images and optimizing structure.

Run with no arguments to open a file picker dialog.
Run with file paths or glob patterns for batch processing.
"""

from __future__ import annotations

import concurrent.futures
import glob
import json
import os
import shutil
import sys
import tempfile
import traceback
from enum import Enum
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

app = typer.Typer(
    name="pdf-toolkit",
    help="Shrink PDF file sizes by compressing images and optimizing structure.\n\n"
    "Run with no arguments to open a file picker dialog.",
    add_completion=False,
)
console = Console()

__version__ = "2.0.0"

CONFIG_PATH = Path.home() / ".pdf-toolkit.toml"

QUALITY_PRESETS = {
    "low": 30,
    "medium": 60,
    "high": 80,
    "lossless": None,
}


class Quality(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    lossless = "lossless"


# ---------------------------------------------------------------------------
# Config file
# ---------------------------------------------------------------------------

def load_config() -> dict:
    """Load ~/.pdf-toolkit.toml if it exists. Returns a flat dict of defaults."""
    if not CONFIG_PATH.exists():
        return {}
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # fallback: pip install tomli
        except ImportError:
            return {}
    try:
        with open(CONFIG_PATH, "rb") as f:
            return tomllib.load(f).get("defaults", {})
    except Exception:
        return {}


def save_config(settings: dict) -> None:
    """Write settings dict to ~/.pdf-toolkit.toml."""
    lines = ["[defaults]\n"]
    for k, v in settings.items():
        if isinstance(v, str):
            lines.append(f'{k} = "{v}"\n')
        elif isinstance(v, bool):
            lines.append(f"{k} = {'true' if v else 'false'}\n")
        elif v is None:
            pass
        else:
            lines.append(f"{k} = {v}\n")
    CONFIG_PATH.write_text("".join(lines))


def format_size(size_bytes: int) -> str:
    """Format bytes into a human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def pick_files() -> list[str]:
    """Open a tkinter file dialog to select PDF files."""
    try:
        import tkinter as tk
        from tkinter import filedialog
    except ImportError:
        console.print(
            "[red]tkinter is not available. Please provide file paths as arguments.[/red]"
        )
        raise typer.Exit(1)

    root = tk.Tk()
    root.withdraw()
    # Bring dialog to front on Windows
    root.attributes("-topmost", True)

    files = filedialog.askopenfilenames(
        title="Select PDF files to compress",
        filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
    )
    root.destroy()
    return list(files)


def _downscale_image(pil_img, page, max_dpi: int):
    """Return a downscaled copy of pil_img if its estimated DPI exceeds max_dpi."""
    from PIL import Image as PILImage

    try:
        page_w_in = max(float(page.mediabox.width), 1) / 72.0
        page_h_in = max(float(page.mediabox.height), 1) / 72.0
        img_w, img_h = pil_img.size
        effective_dpi = max(img_w / page_w_in, img_h / page_h_in)
        if effective_dpi > max_dpi:
            scale = max_dpi / effective_dpi
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))
            return pil_img.resize((new_w, new_h), PILImage.LANCZOS)
    except Exception:
        pass
    return pil_img


def _recompress_image(img, page, image_quality: int, max_dpi: int | None,
                      grayscale: bool, verbose: bool) -> None:
    """Recompress a single page image object in-place."""
    from PIL import Image as PILImage
    try:
        pil_img = img.image

        if max_dpi is not None:
            pil_img = _downscale_image(pil_img, page, max_dpi)

        if grayscale and pil_img.mode not in ("L", "LA"):
            pil_img = pil_img.convert("L")

        # Flatten alpha channel onto white before JPEG compression
        if pil_img.mode in ("RGBA", "LA", "PA"):
            background = PILImage.new("RGB", pil_img.size, (255, 255, 255))
            rgba = pil_img.convert("RGBA")
            background.paste(rgba, mask=rgba.split()[-1])
            pil_img = background
        elif pil_img.mode == "P":
            pil_img = pil_img.convert("RGB")

        img.replace(pil_img, quality=image_quality)
    except Exception as exc:
        if verbose:
            console.print(f"  [yellow]Warning: skipped an image ({exc})[/yellow]")


def parse_page_ranges(spec: str, total_pages: int) -> list[int]:
    """
    Parse a page range spec like '1-5,10,15-20' into a sorted list of
    0-based page indices. Page numbers in the spec are 1-based.
    Raises ValueError for invalid input.
    """
    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_s, end_s = part.split("-", 1)
            start, end = int(start_s), int(end_s)
            if start < 1 or end > total_pages or start > end:
                raise ValueError(
                    f"Range '{part}' is out of bounds (PDF has {total_pages} pages)"
                )
            indices.update(range(start - 1, end))
        else:
            n = int(part)
            if n < 1 or n > total_pages:
                raise ValueError(
                    f"Page {n} is out of bounds (PDF has {total_pages} pages)"
                )
            indices.add(n - 1)
    return sorted(indices)


def analyse_pdf(input_path: Path) -> dict:
    """Return metadata about a PDF useful for predicting compression savings."""
    from pypdf import PdfReader
    reader = PdfReader(str(input_path))
    num_pages = len(reader.pages)
    image_count = 0
    total_image_bytes = 0

    for page in reader.pages:
        try:
            for img in page.images:
                image_count += 1
                try:
                    total_image_bytes += len(img.data)
                except Exception:
                    pass
        except Exception:
            pass

    file_size = input_path.stat().st_size
    return {
        "file": str(input_path),
        "size_bytes": file_size,
        "size_human": format_size(file_size),
        "pages": num_pages,
        "images": image_count,
        "image_bytes": total_image_bytes,
        "image_ratio": round(total_image_bytes / file_size, 3) if file_size else 0,
    }


def split_pdf_pages(
    input_path: Path,
    output_dir: Path,
    page_indices: list[int] | None,
    image_quality: int | None,
    max_dpi: int | None,
    grayscale: bool,
    strip_metadata: bool,
    verbose: bool,
    quiet: bool,
    debug: bool = False,
) -> list[tuple[str, int, int, bool]]:
    """
    Split a PDF into one compressed file per (selected) page.
    Returns a results list compatible with print_summary.
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(str(input_path))
    num_pages = len(reader.pages)
    indices = page_indices if page_indices is not None else list(range(num_pages))
    pad = len(str(num_pages))
    stem = input_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, int, int, bool]] = []

    with Progress(
        SpinnerColumn(),
        TextColumn("  [progress.description]{task.description}"),
        BarColumn(bar_width=30),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        disable=quiet,
        transient=False,
    ) as progress:
        task = progress.add_task(f"Splitting {len(indices)} pages...", total=len(indices))

        for idx in indices:
            page_num = idx + 1
            out_name = f"{stem}_p{str(page_num).zfill(pad)}.pdf"
            out_path = output_dir / out_name

            progress.update(
                task,
                description=f"Page {page_num}/{num_pages}: {out_name}",
            )

            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(temp_fd)
            try:
                writer = PdfWriter()
                writer.add_page(reader.pages[idx])
                with open(temp_path, "wb") as f:
                    writer.write(f)

                original_size = Path(temp_path).stat().st_size

                success = compress_pdf(
                    Path(temp_path), out_path,
                    image_quality, max_dpi, grayscale, strip_metadata,
                    verbose=False, quiet=True, debug=debug,
                )
                new_size = out_path.stat().st_size if success else original_size
                results.append((out_name, original_size, new_size, success))
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

            progress.advance(task)

    return results


def _split_summary(
    source_name: str,
    source_size: int,
    results: list[tuple[str, int, int, bool]],
) -> None:
    """Print a compact summary table for a split operation."""
    table = Table(title=f"\nSplit: {source_name}", show_lines=False)
    table.add_column("Output file", style="bold")
    table.add_column("Size", justify="right")

    total_new = 0
    for name, _, new, ok in results:
        if ok:
            table.add_row(name, format_size(new))
            total_new += new
        else:
            table.add_row(name, "[red]FAILED[/red]")

    table.add_section()
    success_count = sum(1 for *_, ok in results if ok)
    reduction = (1 - total_new / source_size) * 100 if source_size > 0 else 0
    color = "green" if reduction > 0 else "yellow"
    table.add_row(
        f"{success_count} pages — original {format_size(source_size)}",
        f"[{color}]{format_size(total_new)} ({reduction:.1f}%)[/{color}]",
    )
    console.print(table)


def _resolve_split_dir(
    input_path: Path,
    output_dir: Path | None,
    suffix: str,
) -> Path:
    """Return the directory where split pages should be written."""
    folder_name = f"{input_path.stem}{suffix}"
    if output_dir:
        return output_dir / folder_name
    return input_path.parent / folder_name


def compress_pdf(
    input_path: Path,
    output_path: Path,
    image_quality: int | None,
    max_dpi: int | None,
    grayscale: bool,
    strip_metadata: bool,
    verbose: bool,
    quiet: bool,
    debug: bool = False,
) -> bool:
    """
    Compress a single PDF file.

    Phase 1: pypdf — image recompression + content stream compression
    Phase 2: pikepdf — object cleanup + linearization

    Returns True on success, False on failure.
    """
    from pypdf import PdfWriter

    try:
        writer = PdfWriter(clone_from=str(input_path))
        num_pages = len(writer.pages)

        do_image_pass = image_quality is not None or max_dpi is not None or grayscale
        effective_quality = image_quality if image_quality is not None else 92
        img_steps = num_pages if do_image_pass else 0
        total_steps = img_steps + num_pages + 2

        with Progress(
            SpinnerColumn(),
            TextColumn("  [progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            disable=quiet,
            transient=False,
        ) as progress:
            task = progress.add_task("Starting...", total=total_steps)

            # Phase 1a: image recompression / downscaling / greyscale
            if do_image_pass:
                for i, page in enumerate(writer.pages):
                    progress.update(
                        task,
                        description=f"Recompressing images  (page {i + 1}/{num_pages})",
                        advance=1,
                    )
                    try:
                        for img in page.images:
                            _recompress_image(
                                img, page, effective_quality,
                                max_dpi, grayscale, verbose,
                            )
                    except Exception as exc:
                        if verbose:
                            progress.console.print(
                                f"  [yellow]Warning: skipped page {i+1} images ({exc})[/yellow]"
                            )

            # Phase 1b: lossless content stream compression
            for i, page in enumerate(writer.pages):
                progress.update(
                    task,
                    description=f"Compressing streams   (page {i + 1}/{num_pages})",
                    advance=1,
                )
                page.compress_content_streams()

            progress.update(task, description="Writing to disk...          ", advance=1)
            temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
            os.close(temp_fd)

            try:
                with open(temp_path, "wb") as f:
                    writer.write(f)

                progress.update(task, description="Optimising structure...     ", advance=1)

                import pikepdf

                pdf = pikepdf.open(temp_path)
                pdf.remove_unreferenced_resources()

                if strip_metadata:
                    with pdf.open_metadata() as meta:
                        for key in list(meta.keys()):
                            del meta[key]
                    if hasattr(pdf, "docinfo") and pdf.docinfo is not None:
                        for key in list(pdf.docinfo.keys()):
                            del pdf.docinfo[key]

                output_path.parent.mkdir(parents=True, exist_ok=True)
                pdf.save(str(output_path), linearize=True)
                pdf.close()

                if output_path.stat().st_size >= input_path.stat().st_size:
                    shutil.copy2(str(input_path), str(output_path))

                progress.update(task, description="Done                        ")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        return True

    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
        if debug:
            console.print(traceback.format_exc())
        return False


def resolve_output_path(
    input_path: Path,
    output_dir: Path | None,
    suffix: str,
    overwrite: bool,
) -> Path:
    if overwrite:
        out_name = input_path.name
    else:
        out_name = f"{input_path.stem}{suffix}{input_path.suffix}"
    return (output_dir / out_name) if output_dir else (input_path.parent / out_name)


def expand_files(file_args: list[str], directory: Path | None, recursive: bool) -> list[Path]:
    """Expand file arguments, globs, and directory scanning into a list of PDF paths."""
    files: list[Path] = []

    if directory:
        pattern = "**/*.pdf" if recursive else "*.pdf"
        for p in directory.glob(pattern):
            if p.is_file():
                files.append(p)
        return sorted(set(files))

    for arg in file_args:
        expanded = glob.glob(arg, recursive=True)
        if expanded:
            for e in expanded:
                p = Path(e)
                if p.is_file() and p.suffix.lower() == ".pdf":
                    files.append(p)
                elif p.is_file():
                    console.print(f"[yellow]Skipping non-PDF file: {p.name}[/yellow]")
        else:
            p = Path(arg)
            if p.exists() and p.is_file():
                if p.suffix.lower() == ".pdf":
                    files.append(p)
                else:
                    console.print(f"[yellow]Skipping non-PDF file: {p.name}[/yellow]")
            else:
                console.print(f"[yellow]File not found: {arg}[/yellow]")

    return sorted(set(files))


def decrypt_pdf(
    input_path: Path,
    output_path: Path,
    password: str,
    strip_metadata: bool,
    quiet: bool,
    debug: bool = False,
) -> bool:
    """
    Open a password-protected PDF and save it without any encryption or password.

    Returns True on success, False on failure.
    """
    try:
        import pikepdf

        pdf = pikepdf.open(str(input_path), password=password)
        pdf.remove_unreferenced_resources()

        if strip_metadata:
            with pdf.open_metadata() as meta:
                for key in list(meta.keys()):
                    del meta[key]
            if hasattr(pdf, "docinfo") and pdf.docinfo is not None:
                for key in list(pdf.docinfo.keys()):
                    del pdf.docinfo[key]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pdf.save(str(output_path), linearize=True)
        pdf.close()
        return True

    except pikepdf.PasswordError:
        console.print(f"  [red]Error: incorrect password for {input_path.name}[/red]")
        if debug:
            console.print(traceback.format_exc())
        return False
    except Exception as e:
        console.print(f"  [red]Error: {e}[/red]")
        if debug:
            console.print(traceback.format_exc())
        return False


def merge_pdfs(
    input_paths: list[Path],
    output_path: Path,
    image_quality: int | None,
    max_dpi: int | None,
    grayscale: bool,
    strip_metadata: bool,
    verbose: bool,
    quiet: bool,
    debug: bool = False,
) -> bool:
    """Merge multiple PDFs into one, then compress."""
    from pypdf import PdfWriter

    try:
        if not quiet:
            console.print(f"  Merging {len(input_paths)} files...")
        writer = PdfWriter()
        for p in input_paths:
            writer.append(str(p))

        temp_fd, temp_merged = tempfile.mkstemp(suffix=".pdf")
        os.close(temp_fd)
        try:
            with open(temp_merged, "wb") as f:
                writer.write(f)
            writer.close()
            return compress_pdf(
                Path(temp_merged), output_path,
                image_quality, max_dpi, grayscale, strip_metadata,
                verbose, quiet, debug,
            )
        finally:
            if os.path.exists(temp_merged):
                os.remove(temp_merged)

    except Exception as e:
        console.print(f"  [red]Merge error: {e}[/red]")
        if debug:
            console.print(traceback.format_exc())
        return False


def version_callback(value: bool):
    if value:
        console.print(f"pdf-toolkit v{__version__}")
        raise typer.Exit()


# ---------------------------------------------------------------------------
# Main command
# ---------------------------------------------------------------------------

@app.command(context_settings={"max_content_width": 120})
def main(
    files: Optional[List[str]] = typer.Argument(
        None,
        help="PDF files to process. Supports glob patterns. "
        "If omitted, opens a file picker dialog.",
    ),
    quality: Optional[Quality] = typer.Option(
        None, "--quality", "-q", help="Compression quality preset.",
    ),
    output_dir: Optional[Path] = typer.Option(
        None, "--output-dir", "-o", help="Output directory. Default: same as input.",
    ),
    suffix: Optional[str] = typer.Option(
        None, "--suffix", "-s",
        help="Suffix added to output filenames. [default: _compressed]",
    ),
    overwrite: bool = typer.Option(False, "--overwrite",
                                   help="Overwrite original files."),
    directory: Optional[Path] = typer.Option(
        None, "--dir", "-d", help="Process all PDFs in a directory.",
    ),
    recursive: bool = typer.Option(False, "--recursive", "-r",
                                   help="With --dir, include subdirectories."),
    strip_metadata: bool = typer.Option(False, "--strip-metadata",
                                        help="Remove document metadata."),
    backup: bool = typer.Option(False, "--backup", "-b",
                                help="Create .bak backup before overwriting."),
    verbose: bool = typer.Option(False, "--verbose", "-v",
                                 help="Show detailed progress."),
    quiet: bool = typer.Option(False, "--quiet",
                               help="Suppress all output except errors."),
    split_pages: bool = typer.Option(
        False, "--split-pages", "-p",
        help="Split each PDF into one file per page.",
    ),
    pages: Optional[str] = typer.Option(
        None, "--pages",
        help="With --split-pages, only extract these pages. e.g. '1-5,10,15-20'.",
    ),
    merge: bool = typer.Option(
        False, "--merge", "-m",
        help="Merge all input files into a single PDF before compressing.",
    ),
    merge_output: Optional[Path] = typer.Option(
        None, "--merge-output",
        help="Output path for merged file (overrides --output-dir for merge).",
    ),
    grayscale: bool = typer.Option(
        False, "--grayscale", "-g",
        help="Convert colour images to greyscale. Great for scanned documents.",
    ),
    max_dpi: Optional[int] = typer.Option(
        None, "--max-dpi",
        help="Downsample images exceeding this DPI. 150=screen/email, 300=print.",
        min=36, max=1200,
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run",
        help="Analyse files and predict compression without writing output.",
    ),
    decrypt: bool = typer.Option(
        False, "--decrypt",
        help="Remove password protection from encrypted PDFs. Requires --password.",
    ),
    password: Optional[str] = typer.Option(
        None, "--password",
        help="Password used to open an encrypted PDF (for --decrypt).",
    ),
    workers: Optional[int] = typer.Option(
        None, "--workers", "-w",
        help="Parallel worker threads for batch jobs. Default: CPU core count.",
        min=1, max=32,
    ),
    output_json: bool = typer.Option(
        False, "--json", help="Print a JSON summary to stdout.",
    ),
    debug: bool = typer.Option(False, "--debug",
                               help="Print full tracebacks on errors."),
    save_defaults: bool = typer.Option(
        False, "--save-defaults",
        help="Save the current options as personal defaults in ~/.pdf-toolkit.toml.",
    ),
    show_config: bool = typer.Option(
        False, "--show-config",
        help="Print the current personal config file and exit.",
    ),
    reset_config: bool = typer.Option(
        False, "--reset-config",
        help="Delete the personal config file and exit.",
    ),
    version: Optional[bool] = typer.Option(
        None, "--version", callback=version_callback, is_eager=True,
        help="Show version and exit.",
    ),
):
    """
    Shrink PDF file sizes by compressing images and optimizing structure.

    \b
    Examples:
      pdf-toolkit                                  File picker dialog
      pdf-toolkit *.pdf                            Compress all PDFs in current dir
      pdf-toolkit scan.pdf -q low                  Aggressive compression
      pdf-toolkit scan.pdf -g                      Convert to greyscale
      pdf-toolkit scan.pdf -q low --max-dpi 150 -g Maximum compression
      pdf-toolkit scan.pdf --split-pages           One file per page
      pdf-toolkit scan.pdf --split-pages --pages 1-5,10   Specific pages only
      pdf-toolkit a.pdf b.pdf c.pdf --merge        Merge then compress
      pdf-toolkit scan.pdf --dry-run               Predict size without writing
      pdf-toolkit *.pdf -w 4                       Batch with 4 parallel workers
      pdf-toolkit -q low --save-defaults           Save low quality as your default
      pdf-toolkit secret.pdf --decrypt --password mypass   Remove PDF password
    """
    if output_json:
        quiet = True

    # ── Config management flags ───────────────────────────────────────────────
    if show_config:
        if CONFIG_PATH.exists():
            console.print(f"[bold]Config:[/bold] {CONFIG_PATH}\n")
            console.print(CONFIG_PATH.read_text())
        else:
            console.print(f"[dim]No config file yet. Use --save-defaults to create one.[/dim]")
        raise typer.Exit()

    if reset_config:
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()
            console.print(f"[green]Config reset — {CONFIG_PATH} deleted.[/green]")
        else:
            console.print("[dim]No config file found; nothing to reset.[/dim]")
        raise typer.Exit()

    # ── Apply saved config defaults ───────────────────────────────────────────
    cfg = load_config()
    if quality is None:
        quality = Quality(cfg.get("quality", "medium"))
    if suffix is None:
        suffix = cfg.get("suffix", "_compressed")
    if max_dpi is None and "max_dpi" in cfg:
        max_dpi = int(cfg["max_dpi"])
    if not grayscale and cfg.get("grayscale", False):
        grayscale = True

    if save_defaults:
        new_cfg: dict = {"quality": quality.value, "suffix": suffix}
        if max_dpi:
            new_cfg["max_dpi"] = max_dpi
        if grayscale:
            new_cfg["grayscale"] = True
        save_config(new_cfg)
        if not quiet:
            console.print(f"[green]Defaults saved to {CONFIG_PATH}[/green]")

    # ── Resolve file list ─────────────────────────────────────────────────────
    file_args = files or []
    if not file_args and not directory:
        if not quiet:
            console.print("[cyan]No files specified — opening file picker...[/cyan]")
        picked = pick_files()
        if not picked:
            console.print("[yellow]No files selected. Exiting.[/yellow]")
            raise typer.Exit()
        file_args = picked

    pdf_files = expand_files(file_args, directory, recursive)

    if not pdf_files:
        console.print("[yellow]No PDF files found to process.[/yellow]")
        raise typer.Exit(1)

    image_quality = QUALITY_PRESETS[quality.value]

    # ── --dry-run ─────────────────────────────────────────────────────────────
    if dry_run:
        _run_dry_run(pdf_files, output_json)
        return

    # ── --decrypt ─────────────────────────────────────────────────────────────
    if decrypt:
        if not password:
            console.print(
                "[red]--decrypt requires --password. "
                "Usage: pdf-toolkit file.pdf --decrypt --password <password>[/red]"
            )
            raise typer.Exit(1)
        _run_decrypt(
            pdf_files, output_dir, suffix if suffix != "_compressed" else "_decrypted",
            overwrite, backup, strip_metadata, quiet, debug, output_json,
            password,
        )
        return

    # ── --merge ───────────────────────────────────────────────────────────────
    if merge:
        _run_merge(
            pdf_files, merge_output, output_dir, suffix,
            image_quality, max_dpi, grayscale, strip_metadata,
            verbose, quiet, debug, output_json,
        )
        return

    # ── Header ────────────────────────────────────────────────────────────────
    if not quiet:
        flags = []
        if max_dpi:
            flags.append(f"max-dpi:[cyan]{max_dpi}[/cyan]")
        if grayscale:
            flags.append("[cyan]greyscale[/cyan]")
        if split_pages:
            flags.append("[cyan]split-pages[/cyan]")
        flags_str = "  " + "  ".join(flags) if flags else ""
        console.print(
            f"\n[bold]PDF Resizer[/bold] — quality:[cyan]{quality.value}[/cyan]"
            f"{flags_str}  files:[cyan]{len(pdf_files)}[/cyan]\n"
        )

    # ── Split mode ────────────────────────────────────────────────────────────
    if split_pages:
        _run_split(
            pdf_files, pages, output_dir, suffix,
            image_quality, max_dpi, grayscale, strip_metadata,
            verbose, quiet, debug, output_json,
        )
        return

    # ── Normal compression ────────────────────────────────────────────────────
    if len(pdf_files) > 1:
        n_workers = workers or min(len(pdf_files), (os.cpu_count() or 2))
        results, any_failed = _run_parallel(
            pdf_files, output_dir, suffix, overwrite, backup,
            image_quality, max_dpi, grayscale, strip_metadata,
            verbose, quiet, debug, n_workers,
        )
    else:
        results, any_failed = _run_sequential(
            pdf_files, output_dir, suffix, overwrite, backup,
            image_quality, max_dpi, grayscale, strip_metadata,
            verbose, quiet, debug,
        )

    _finish(results, any_failed, quiet, output_json)


# ---------------------------------------------------------------------------
# Runner helpers
# ---------------------------------------------------------------------------

def _run_decrypt(
    pdf_files: list[Path],
    output_dir: Path | None,
    suffix: str,
    overwrite: bool,
    backup: bool,
    strip_metadata: bool,
    quiet: bool,
    debug: bool,
    output_json: bool,
    password: str,
) -> None:
    if not quiet:
        console.print(
            f"\n[bold]PDF Toolkit — decrypt[/bold]  "
            f"files:[cyan]{len(pdf_files)}[/cyan]\n"
        )

    results: list[tuple[str, int, int, bool]] = []
    any_failed = False

    for pdf_file in pdf_files:
        original_size = pdf_file.stat().st_size
        if not quiet:
            console.print(f"[bold]{pdf_file.name}[/bold] ({format_size(original_size)})")

        out_path = resolve_output_path(pdf_file, output_dir, suffix, overwrite)

        if overwrite and backup:
            backup_path = pdf_file.with_suffix(pdf_file.suffix + ".bak")
            shutil.copy2(pdf_file, backup_path)
            if not quiet:
                console.print(f"  [dim]Backup: {backup_path}[/dim]")

        if overwrite:
            temp_fd, temp_out = tempfile.mkstemp(suffix=".pdf", dir=str(pdf_file.parent))
            os.close(temp_fd)
            actual_out = Path(temp_out)
        else:
            actual_out = out_path

        success = decrypt_pdf(
            pdf_file, actual_out, password, strip_metadata, quiet, debug
        )

        if success:
            if overwrite:
                shutil.move(str(actual_out), str(pdf_file))
            new_size = (pdf_file if overwrite else out_path).stat().st_size
            results.append((pdf_file.name, original_size, new_size, True))
            if not quiet:
                saved = original_size - new_size
                console.print(
                    f"  [green]→ {out_path.name if not overwrite else pdf_file.name}  "
                    f"{format_size(new_size)}"
                    + (f"  (saved {format_size(saved)})" if saved > 0 else "")
                    + "  [encryption removed][/green]"
                )
        else:
            if overwrite and actual_out.exists():
                actual_out.unlink()
            results.append((pdf_file.name, original_size, original_size, False))
            any_failed = True

    _finish(results, any_failed, quiet, output_json)


def _run_dry_run(pdf_files: list[Path], output_json: bool) -> None:
    analyses = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"),
                  console=console, transient=True) as progress:
        task = progress.add_task("Analysing...", total=len(pdf_files))
        for f in pdf_files:
            analyses.append(analyse_pdf(f))
            progress.advance(task)

    if output_json:
        print(json.dumps(analyses, indent=2))
        return

    table = Table(title="\nDry Run — Analysis", show_lines=False)
    table.add_column("File", style="bold")
    table.add_column("Size", justify="right")
    table.add_column("Pages", justify="right")
    table.add_column("Images", justify="right")
    table.add_column("Image ratio", justify="right")
    table.add_column("Est. saving*", justify="right")

    for a in analyses:
        est_save = int(a["image_bytes"] * 0.55)
        est_size = max(a["size_bytes"] - est_save, a["size_bytes"] // 10)
        est_pct = (1 - est_size / a["size_bytes"]) * 100 if a["size_bytes"] else 0
        table.add_row(
            Path(a["file"]).name, a["size_human"],
            str(a["pages"]), str(a["images"]),
            f"{a['image_ratio']:.0%}",
            f"[green]~{est_pct:.0f}%[/green]" if est_pct > 5 else "[dim]minimal[/dim]",
        )

    console.print(table)
    console.print("[dim]* Estimate based on medium quality. Actual results will vary.[/dim]\n")


def _run_merge(
    pdf_files, merge_output, output_dir, suffix,
    image_quality, max_dpi, grayscale, strip_metadata,
    verbose, quiet, debug, output_json,
) -> None:
    total_in = sum(f.stat().st_size for f in pdf_files)
    if not quiet:
        console.print(
            f"\n[bold]PDF Resizer — merge[/bold]  "
            f"[cyan]{len(pdf_files)}[/cyan] files → 1\n"
        )
        for f in pdf_files:
            console.print(f"  [dim]{f.name}[/dim]")
        console.print()

    if merge_output:
        out_path = merge_output
    elif output_dir:
        out_path = output_dir / f"merged{suffix}.pdf"
    else:
        out_path = pdf_files[0].parent / f"merged{suffix}.pdf"

    if not quiet:
        console.print(f"[bold]→ {out_path.name}[/bold]")

    success = merge_pdfs(
        pdf_files, out_path,
        image_quality, max_dpi, grayscale, strip_metadata,
        verbose, quiet, debug,
    )
    new_size = out_path.stat().st_size if success else 0
    _finish([("merged.pdf", total_in, new_size, success)], not success, quiet, output_json)


def _run_split(
    pdf_files, pages_spec, output_dir, suffix,
    image_quality, max_dpi, grayscale, strip_metadata,
    verbose, quiet, debug, output_json,
) -> None:
    any_failed = False
    json_out = []

    for pdf_file in pdf_files:
        original_size = pdf_file.stat().st_size
        if not quiet:
            console.print(f"[bold]{pdf_file.name}[/bold] ({format_size(original_size)})")

        page_indices = None
        if pages_spec:
            from pypdf import PdfReader
            total = len(PdfReader(str(pdf_file)).pages)
            try:
                page_indices = parse_page_ranges(pages_spec, total)
            except ValueError as e:
                console.print(f"  [red]{e}[/red]")
                any_failed = True
                continue

        split_dir = _resolve_split_dir(pdf_file, output_dir, suffix)
        page_results = split_pdf_pages(
            pdf_file, split_dir, page_indices,
            image_quality, max_dpi, grayscale, strip_metadata,
            verbose, quiet, debug,
        )
        if not quiet:
            _split_summary(pdf_file.name, original_size, page_results)
        if any(not ok for *_, ok in page_results):
            any_failed = True

        if output_json:
            json_out.append({
                "file": str(pdf_file),
                "original_size": original_size,
                "pages": [
                    {"name": n, "size": new, "success": ok}
                    for n, _, new, ok in page_results
                ],
            })

    if output_json:
        print(json.dumps(json_out, indent=2))
    elif not quiet and not any_failed:
        console.print("\n[green]Done![/green]")

    if any_failed:
        raise typer.Exit(1)


def _run_sequential(
    pdf_files, output_dir, suffix, overwrite, backup,
    image_quality, max_dpi, grayscale, strip_metadata,
    verbose, quiet, debug,
) -> tuple[list, bool]:
    results = []
    any_failed = False
    for pdf_file in pdf_files:
        r, failed = _process_one(
            pdf_file, output_dir, suffix, overwrite, backup,
            image_quality, max_dpi, grayscale, strip_metadata,
            verbose, quiet, debug,
        )
        results.append(r)
        if failed:
            any_failed = True
    return results, any_failed


def _run_parallel(
    pdf_files, output_dir, suffix, overwrite, backup,
    image_quality, max_dpi, grayscale, strip_metadata,
    verbose, quiet, debug, n_workers,
) -> tuple[list, bool]:
    if not quiet:
        console.print(
            f"[dim]Running {n_workers} parallel workers for {len(pdf_files)} files...[/dim]\n"
        )

    results_map: dict[Path, tuple] = {}
    any_failed = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=n_workers) as executor:
        future_to_file = {
            executor.submit(
                _process_one, f, output_dir, suffix, overwrite, backup,
                image_quality, max_dpi, grayscale, strip_metadata,
                verbose, True, debug,
            ): f
            for f in pdf_files
        }
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=30),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
            disable=quiet,
        ) as progress:
            task = progress.add_task(
                f"Compressing {len(pdf_files)} files...", total=len(pdf_files)
            )
            for future in concurrent.futures.as_completed(future_to_file):
                f = future_to_file[future]
                try:
                    r, failed = future.result()
                    results_map[f] = (r, failed)
                    if failed:
                        any_failed = True
                except Exception:
                    s = f.stat().st_size
                    results_map[f] = ((f.name, s, s, False), True)
                    any_failed = True
                    if debug:
                        console.print(traceback.format_exc())
                progress.advance(task)

    results = []
    for f in pdf_files:
        r, failed = results_map[f]
        name, original, new, ok = r
        results.append(r)
        if not quiet:
            reduction = (1 - new / original) * 100 if original > 0 and ok else 0.0
            color = "green" if ok and reduction > 0 else ("yellow" if ok else "red")
            status = f"{format_size(new)} ({reduction:+.1f}%)" if ok else "FAILED"
            console.print(f"  [{color}]{name}: {format_size(original)} → {status}[/{color}]")

    return results, any_failed


def _process_one(
    pdf_file, output_dir, suffix, overwrite, backup,
    image_quality, max_dpi, grayscale, strip_metadata,
    verbose, quiet, debug,
) -> tuple[tuple, bool]:
    original_size = pdf_file.stat().st_size

    if not quiet:
        console.print(f"[bold]{pdf_file.name}[/bold] ({format_size(original_size)})")

    out_path = resolve_output_path(pdf_file, output_dir, suffix, overwrite)

    if overwrite and backup:
        backup_path = pdf_file.with_suffix(pdf_file.suffix + ".bak")
        shutil.copy2(pdf_file, backup_path)
        if verbose:
            console.print(f"  [dim]Backup: {backup_path}[/dim]")

    if overwrite:
        temp_fd, temp_out = tempfile.mkstemp(suffix=".pdf", dir=str(pdf_file.parent))
        os.close(temp_fd)
        actual_out = Path(temp_out)
    else:
        actual_out = out_path

    success = compress_pdf(
        pdf_file, actual_out,
        image_quality, max_dpi, grayscale, strip_metadata,
        verbose, quiet, debug,
    )

    if success:
        if overwrite:
            shutil.move(str(actual_out), str(pdf_file))
        new_size = (pdf_file if overwrite else out_path).stat().st_size
        result = (pdf_file.name, original_size, new_size, True)
        if not quiet:
            reduction = (1 - new_size / original_size) * 100 if original_size > 0 else 0
            color = "green" if reduction > 0 else "yellow"
            console.print(
                f"  [{color}]→ {format_size(new_size)} ({reduction:+.1f}%)[/{color}]"
            )
        return result, False
    else:
        if overwrite and actual_out.exists():
            actual_out.unlink()
        return (pdf_file.name, original_size, original_size, False), True


def _finish(
    results: list[tuple[str, int, int, bool]],
    any_failed: bool,
    quiet: bool,
    output_json: bool,
) -> None:
    if output_json:
        out = []
        for name, original, new, ok in results:
            reduction = round((1 - new / original) * 100, 1) if original > 0 and ok else None
            out.append({
                "file": name,
                "original_bytes": original,
                "new_bytes": new,
                "reduction_pct": reduction,
                "success": ok,
            })
        print(json.dumps(out, indent=2))
    elif not quiet:
        if len(results) > 1:
            print_summary(results)
        elif len(results) == 1:
            console.print("\n[green]Done![/green]" if results[0][3] else "\n[red]Compression failed.[/red]")
        elif not any_failed:
            console.print("\n[green]Done![/green]")

    if any_failed or any(not ok for _, _, _, ok in results):
        raise typer.Exit(1)


def print_summary(results: list[tuple[str, int, int, bool]]):
    table = Table(title="\nSummary", show_lines=False)
    table.add_column("File", style="bold")
    table.add_column("Original", justify="right")
    table.add_column("New Size", justify="right")
    table.add_column("Reduction", justify="right")

    total_original = total_new = success_count = 0

    for name, original, new, ok in results:
        if ok:
            reduction = (1 - new / original) * 100 if original > 0 else 0
            color = "green" if reduction > 0 else "yellow"
            table.add_row(
                name, format_size(original), format_size(new),
                f"[{color}]{reduction:.1f}%[/{color}]",
            )
            total_original += original
            total_new += new
            success_count += 1
        else:
            table.add_row(name, format_size(original), "[red]FAILED[/red]", "")
            total_original += original

    if success_count > 0:
        table.add_section()
        total_reduction = (1 - total_new / total_original) * 100 if total_original > 0 else 0
        table.add_row(
            f"Total ({success_count} files)",
            format_size(total_original),
            format_size(total_new),
            f"[bold]{total_reduction:.1f}%[/bold]",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app()
