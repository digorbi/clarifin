"""Parser for Neobank Joint Account EUR statement (text format)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

_DATE_RE = re.compile(
    r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b"
)
_AMOUNTS_RE = re.compile(r"€([\d.,]+)")

_SKIP_PREFIXES = (
    "To:", "Card:", "Reference:", "From:", "Neobank Rate",
    "Neobank Europe", "Report lost", "QR ", "Get help",
    "© ", "Page ", "Date Description", "Generated on",
    "Joint Account", "Neobank\n", "Neobank",
    "Balance summary", "Product ", "Account (", "Total ",
    "The balance", "Please review", "Account transactions",
    "THOMAS MÜLLER", "Birkenweg", "22305", "Hamburg", "Germany",
)


@dataclass
class Transaction:
    date: str
    description: str
    amount: Decimal


def _parse_amount(s: str) -> Decimal:
    """Convert European-format amount string to Decimal (e.g. '1.022,47' → 1022.47)."""
    return Decimal(s.replace(".", "").replace(",", "."))


def parse(text: str) -> list[Transaction]:
    transactions: list[Transaction] = []
    prev_balance: Decimal | None = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if any(line.startswith(p) for p in _SKIP_PREFIXES):
            continue
        if not _DATE_RE.match(line):
            continue

        amounts = _AMOUNTS_RE.findall(line)
        if len(amounts) < 2:
            continue

        balance = _parse_amount(amounts[-1])
        tx_amount = _parse_amount(amounts[-2])

        # description sits between date and first €
        date_end = re.match(
            r"^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})\s+",
            line,
        )
        if not date_end:
            continue
        date_str = date_end.group(1)
        after_date = line[date_end.end():]
        first_euro = after_date.index("€")
        description = after_date[:first_euro].strip()

        if prev_balance is not None:
            signed = tx_amount if balance > prev_balance else -tx_amount
        else:
            signed = -tx_amount  # assume first tx is an expense if no prior context

        transactions.append(
            Transaction(date=date_str, description=description, amount=signed)
        )
        prev_balance = balance

    return transactions


def parse_file(path: str | Path) -> list[Transaction]:
    return parse(Path(path).read_text(encoding="utf-8"))


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <statement.txt>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).is_file():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(1)

    print(f"{'Date':<16} {'Amount':>10}  Description")
    print("-" * 60)
    for tx in parse_file(path):
        amount_str = f"{tx.amount:+.2f}"
        print(f"{tx.date:<16} {amount_str:>10}  {tx.description}")
