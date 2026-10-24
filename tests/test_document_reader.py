
import pymupdf
import pytest

from change_order_extractor.document_reader import (
    DocumentReadError,
    read_pdf,
    read_text,
)


def test_read_text():
    assert read_text("  Change Order #104  ") == "Change Order #104"


def test_empty_text_is_rejected():
    with pytest.raises(DocumentReadError):
        read_text("   ")


def test_read_pdf(tmp_path):
    pdf_path = tmp_path / "sample.pdf"

    with pymupdf.open() as document:
        page = document.new_page()
        page.insert_text(
            (72, 72),
            "Change Order #104. Additional electrical work costs $4500.",
        )
        document.save(pdf_path)

    result = read_pdf(pdf_path)

    assert "Change Order #104" in result
    assert "$4500" in result


def test_missing_pdf_is_rejected(tmp_path):
    with pytest.raises(DocumentReadError):
        read_pdf(tmp_path / "missing.pdf")
