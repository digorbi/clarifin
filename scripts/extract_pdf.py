"""PDF → raw text lines extractor using pdfplumber."""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber


def extract_pdf(path: str) -> list[str]:
    """Return non-empty text lines extracted from a PDF."""
    lines: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())
    return [line for line in lines if line.strip()]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/statement.pdf>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).is_file():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    extracted = extract_pdf(pdf_path)
    for line in extracted:
        print(line)
