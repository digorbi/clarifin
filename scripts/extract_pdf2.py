"""PDF → rows of text chunks extractor using pdfplumber.

Assumes bank-statement-style content is row-based. Groups word-level
bounding boxes by vertical position (y-tolerance in points) and sorts
each row left-to-right by x position.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pdfplumber

_Y_TOLERANCE = 3  # points; words within this vertical distance share a row


def extract_pdf2(path: str, y_tolerance: int = _Y_TOLERANCE) -> list[list[str]]:
    """Return text grouped into rows based on vertical position."""
    rows: dict[int, list[tuple[float, str]]] = {}

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            for word in page.extract_words():
                text = word["text"].strip()
                if not text:
                    continue
                y = word["top"]
                bucket = next(
                    (k for k in rows if abs(k - y) <= y_tolerance),
                    None,
                )
                if bucket is None:
                    bucket = y
                    rows[bucket] = []
                rows[bucket].append((word["x0"], text))

    return [
        [text for _, text in sorted(chunks)]
        for _, chunks in sorted(rows.items())
    ]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/statement.pdf>", file=sys.stderr)
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).is_file():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    for row in extract_pdf2(pdf_path):
        print(row)
