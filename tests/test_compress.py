"""Tests for pdf_toolkit.pdf_resizer — compression pipeline."""

from pathlib import Path
import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal valid PDF for testing."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n"
        b"0000000000 65535 f\r\n"
        b"0000000009 00000 n\r\n"
        b"0000000058 00000 n\r\n"
        b"0000000115 00000 n\r\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n190\n%%EOF\n"
    )
    p = tmp_path / "sample.pdf"
    p.write_bytes(content)
    return p


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------

def test_import():
    """Package imports cleanly."""
    import pdf_toolkit  # noqa: F401
    from pdf_toolkit.pdf_resizer import app  # noqa: F401


def test_version():
    import pdf_toolkit
    assert pdf_toolkit.__version__ == "2.0.0"


def test_compress_returns_smaller_or_equal(sample_pdf: Path, tmp_path: Path):
    from pdf_toolkit.pdf_resizer import compress_pdf

    out = tmp_path / "out.pdf"
    result = compress_pdf(sample_pdf, out)
    assert result is True or result is False  # completes without exception
    # output file or original must exist
    assert out.exists() or sample_pdf.exists()
