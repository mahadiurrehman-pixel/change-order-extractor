
import argparse
import json
import sys

from change_order_extractor.document_reader import (
    DocumentReadError,
    read_pdf,
)
from change_order_extractor.groq_client import extract_change_order


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured change-order data from a PDF."
    )
    parser.add_argument("pdf_path", help="Path to a text-based PDF")
    args = parser.parse_args()

    try:
        document_text = read_pdf(args.pdf_path)
        result = extract_change_order(document_text)
    except (DocumentReadError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Extraction interrupted by user.", file=sys.stderr)
        return 130

    print(json.dumps(result.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
