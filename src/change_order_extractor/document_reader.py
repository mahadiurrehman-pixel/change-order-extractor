
from pathlib import Path

import pymupdf


class DocumentReadError(Exception):
    """Raised when a document cannot be read safely."""


def read_text(text: str) -> str:
    cleaned = text.strip()

    if not cleaned:
        raise DocumentReadError("Input text is empty.")

    return cleaned


def read_pdf(path: str | Path) -> str:
    pdf_path = Path(path)

    if not pdf_path.is_file():
        raise DocumentReadError(f"PDF file not found: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise DocumentReadError("Input file must have a .pdf extension.")

    try:
        with pymupdf.open(pdf_path) as document:
            if document.needs_pass:
                raise DocumentReadError("PDF requires a password.")

            pages = [page.get_text() for page in document]
            extracted_text = "\n".join(pages).strip()

    except DocumentReadError:
        raise
    except Exception as exc:
        raise DocumentReadError("Could not read the PDF.") from exc

    if not extracted_text:
        raise DocumentReadError(
            "No selectable text found. This PDF may require OCR."
        )

    return extracted_text
