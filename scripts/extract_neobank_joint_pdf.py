"""Parser for Neobank Joint Account EUR Statement PDF.

Bound strictly to the format produced by Neobank Europe UAB.
Raises ValueError immediately on any structural mismatch so callers
know this script is not applicable to a different PDF layout.

Usage:
    python scripts/extract_neobank_joint_pdf.py <statement.pdf>
    python scripts/extract_neobank_joint_pdf.py --self-test
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pdfplumber

# ---------------------------------------------------------------------------
# Format fingerprints – any deviation triggers a ValueError
# ---------------------------------------------------------------------------

_HEADER_LINE_1 = "Neobank"
_HEADER_LINE_2 = "Joint Account EUR Statement"
_ISSUER_SUBSTR = "Neobank Europe UAB Zweigniederlassung Deutschland"

# ---------------------------------------------------------------------------
# Regexes
# ---------------------------------------------------------------------------

_DATE_PREFIX_RE = re.compile(
    r"^((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4})\s+"
)
_AMOUNT_RE = re.compile(r"€([\d.,]+)")
_ACCOUNT_NAME_RE = re.compile(r"Account name\s+(.+)")
_OPENING_BALANCE_RE = re.compile(r"Account \(Current Account\)\s+€([\d.,]+)")

# Lines that carry metadata, not transaction data
_DETAIL_PREFIXES = ("To:", "Card:", "Reference:", "From:", "Neobank Rate")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Transaction:
    date: str
    description: str
    amount: Decimal  # negative = money out, positive = money in


@dataclass
class Statement:
    bank: str
    account_holders: list[str]  # e.g. ["THOMAS MÜLLER", "JANE MÜLLER"]
    transactions: list[Transaction]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_amount(s: str) -> Decimal:
    """Convert European-format '1.022,47' → Decimal('1022.47')."""
    return Decimal(s.replace(".", "").replace(",", "."))


def _assert_format(condition: bool, detail: str) -> None:
    if not condition:
        raise ValueError(
            f"Unsupported PDF format — this script only handles "
            f"'Neobank Joint Account EUR Statement'. Detail: {detail}"
        )


def _extract_lines(path: str | Path) -> list[str]:
    lines: list[str] = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines.extend(text.splitlines())
    return [ln.strip() for ln in lines if ln.strip()]


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------


def parse_pdf(path: str | Path) -> Statement:
    """Parse a Neobank Joint Account EUR Statement PDF.

    Fails immediately with ValueError if the file does not match the
    expected format, so callers can detect inapplicable inputs early.
    """
    lines = _extract_lines(path)

    # --- Format validation (fail fast) ---
    _assert_format(
        len(lines) >= 4,
        "file is too short to be a valid statement",
    )
    _assert_format(
        lines[0] == _HEADER_LINE_1,
        f"line 1 expected '{_HEADER_LINE_1}', got '{lines[0]}'",
    )
    _assert_format(
        lines[1] == _HEADER_LINE_2,
        f"line 2 expected '{_HEADER_LINE_2}', got '{lines[1]}'",
    )
    _assert_format(
        any(_ISSUER_SUBSTR in ln for ln in lines),
        f"issuer string '{_ISSUER_SUBSTR}' not found anywhere in document",
    )
    _assert_format(
        any("Account transactions" in ln for ln in lines),
        "'Account transactions' section header not found",
    )
    _assert_format(
        any("Date Description" in ln for ln in lines),
        "transaction table header ('Date Description …') not found",
    )

    # --- Extract account holders ---
    account_holders: list[str] = []
    for ln in lines:
        m = _ACCOUNT_NAME_RE.search(ln)
        if m:
            raw = m.group(1).strip()
            account_holders = [part.strip() for part in raw.split("&") if part.strip()]
            break
    _assert_format(bool(account_holders), "'Account name' line not found")

    # --- Extract opening balance to correctly sign the first transaction ---
    prev_balance: Decimal | None = None
    for ln in lines:
        m = _OPENING_BALANCE_RE.search(ln)
        if m:
            prev_balance = _parse_amount(m.group(1))
            break
    _assert_format(
        prev_balance is not None, "opening balance not found in balance summary"
    )

    # --- Parse transactions ---
    transactions: list[Transaction] = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        m = _DATE_PREFIX_RE.match(ln)
        if not m:
            i += 1
            continue

        amounts = _AMOUNT_RE.findall(ln)
        if len(amounts) < 2:
            # Fewer than 2 euro amounts → header/summary row, not a transaction
            i += 1
            continue

        date_str = m.group(1)

        # Description sits between the date and the first € sign
        after_date = ln[m.end():]
        first_euro = after_date.index("€")
        primary_desc = after_date[:first_euro].strip()

        # Running balance is always the last amount; transaction value is second-to-last
        balance = _parse_amount(amounts[-1])
        tx_amount = _parse_amount(amounts[-2])

        # Advance past this line and collect all detail lines
        j = i + 1
        to_detail = ""
        card_detail = ""
        reference_detail = ""
        from_detail = ""
        while j < len(lines):
            sub = lines[j]
            if sub.startswith("To:"):
                to_detail = sub[len("To:"):].strip()
                j += 1
            elif sub.startswith("Card:"):
                card_detail = sub[len("Card:"):].strip()
                j += 1
            elif sub.startswith("Reference:"):
                reference_detail = sub[len("Reference:"):].strip()
                j += 1
            elif sub.startswith("From:"):
                from_detail = sub[len("From:"):].strip()
                j += 1
            elif any(sub.startswith(p) for p in _DETAIL_PREFIXES):
                j += 1
            else:
                break

        parts = [primary_desc]
        if to_detail:
            parts.append(to_detail)
        if card_detail:
            parts.append(card_detail)
        if reference_detail:
            parts.append(f"Reference: {reference_detail}")
        if from_detail:
            parts.append(f"From: {from_detail}")
        description = " ".join(parts)

        # Determine sign from balance movement
        assert prev_balance is not None  # guaranteed above
        signed = tx_amount if balance > prev_balance else -tx_amount

        transactions.append(
            Transaction(date=date_str, description=description, amount=signed)
        )
        prev_balance = balance
        i = j

    _assert_format(bool(transactions), "no transactions could be parsed")

    return Statement(
        bank="Neobank",
        account_holders=account_holders,
        transactions=transactions,
    )


# ---------------------------------------------------------------------------
# Self-test (bound to test/test_data/test_statement_joint_nb_0326.pdf)
# ---------------------------------------------------------------------------

_TEST_PDF = (
    Path(__file__).parent.parent
    / "test"
    / "test_data"
    / "test_statement_joint_nb_0326.pdf"
)


def _self_test() -> None:
    """Assert known facts about the bundled test statement."""
    if not _TEST_PDF.is_file():
        raise FileNotFoundError(f"Test PDF not found: {_TEST_PDF}")

    stmt = parse_pdf(_TEST_PDF)

    assert stmt.bank == "Neobank", f"bank: {stmt.bank!r}"
    assert stmt.account_holders == [
        "THOMAS MÜLLER",
        "JANE MÜLLER",
    ], f"holders: {stmt.account_holders}"

    n = len(stmt.transactions)
    assert n == 45, f"expected 45 transactions, got {n}"

    # First transaction
    t0 = stmt.transactions[0]
    assert t0.date == "Mar 1, 2026", f"first date: {t0.date!r}"
    assert t0.description.startswith("CafeNord"), f"first desc: {t0.description!r}"
    assert t0.amount == Decimal("-4.19"), f"first amount: {t0.amount}"

    # Last transaction
    t_last = stmt.transactions[-1]
    assert t_last.date == "Mar 28, 2026", f"last date: {t_last.date!r}"
    assert t_last.description.startswith(
        "Transfer from THOMAS MÜLLER"
    ), f"last desc: {t_last.description!r}"
    assert t_last.amount == Decimal("250.00"), f"last amount: {t_last.amount}"

    # Transfers (money in)
    transfers = [
        t for t in stmt.transactions if t.description.startswith("Transfer from")
    ]
    assert len(transfers) == 3, f"expected 3 transfers, got {len(transfers)}"
    assert all(t.amount > 0 for t in transfers), "transfers must be positive"
    assert sorted(t.amount for t in transfers) == [
        Decimal("250.00"),
        Decimal("750.00"),
        Decimal("900.00"),
    ]

    # All non-transfers must be negative (money out)
    expenses = [
        t for t in stmt.transactions if not t.description.startswith("Transfer from")
    ]
    assert all(t.amount < 0 for t in expenses), "all expenses must be negative"

    # Aggregate totals over the 45 visible transactions.
    # The PDF's balance summary (€1,022.47 out) covers all of March including
    # Mar 29-31 entries not on any page; we verify only the visible sum.
    total_in = sum(t.amount for t in stmt.transactions if t.amount > 0)
    total_out = sum(-t.amount for t in stmt.transactions if t.amount < 0)
    assert total_in == Decimal("1900.00"), f"total in: {total_in}"
    assert total_out == Decimal("1011.44"), f"total out: {total_out}"

    print("Self-test PASSED — 45 transactions, totals verified.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--self-test":
        _self_test()
        return

    if len(sys.argv) != 2:
        print(
            f"Usage:\n"
            f"  {sys.argv[0]} <statement.pdf>\n"
            f"  {sys.argv[0]} --self-test",
            file=sys.stderr,
        )
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.is_file():
        print(f"File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    stmt = parse_pdf(pdf_path)

    print(f"Bank:             {stmt.bank}")
    print(f"Account holders:  {' & '.join(stmt.account_holders)}")
    print()
    print(f"{'Date':<16} {'Amount':>10}  Description")
    print("-" * 80)
    for tx in stmt.transactions:
        amount_str = f"{tx.amount:+.2f}"
        print(f"{tx.date:<16} {amount_str:>10}  {tx.description}")


if __name__ == "__main__":
    main()
