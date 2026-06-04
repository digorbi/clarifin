"""Validate parsed transactions from a generated parser against known ground truth.

Usage:
    python check_transactions.py <parser_file> --pdf <pdf_path> --expected <json_path>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from decimal import Decimal
from pathlib import Path
from types import ModuleType


def load_parser(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location("_parser", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("parser", help="path to the generated parser script")
    ap.add_argument("--pdf", required=True, help="PDF to parse")
    ap.add_argument("--expected", required=True, help="expected transactions JSON")
    args = ap.parse_args()

    expected = json.loads(Path(args.expected).read_text())
    mod = load_parser(Path(args.parser))
    stmt = mod.parse_pdf(args.pdf)

    failures: list[str] = []

    if stmt.bank != expected["bank"]:
        failures.append(f"bank: {stmt.bank!r} != {expected['bank']!r}")

    if len(stmt.transactions) != expected["transaction_count"]:
        failures.append(
            f"tx count: {len(stmt.transactions)} != {expected['transaction_count']}"
        )

    if stmt.transactions:
        t0, exp0 = stmt.transactions[0], expected["first_transaction"]
        if t0.date != exp0["date"]:
            failures.append(f"first date: {t0.date!r} != {exp0['date']!r}")
        if not t0.description.startswith(exp0["description_prefix"]):
            failures.append(
                f"first desc: {t0.description!r} missing prefix {exp0['description_prefix']!r}"
            )
        if t0.amount != Decimal(exp0["amount"]):
            failures.append(f"first amount: {t0.amount} != {exp0['amount']}")

        tl, expl = stmt.transactions[-1], expected["last_transaction"]
        if tl.date != expl["date"]:
            failures.append(f"last date: {tl.date!r} != {expl['date']!r}")
        if not tl.description.startswith(expl["description_prefix"]):
            failures.append(
                f"last desc: {tl.description!r} missing prefix {expl['description_prefix']!r}"
            )
        if tl.amount != Decimal(expl["amount"]):
            failures.append(f"last amount: {tl.amount} != {expl['amount']}")

    totals = expected.get("totals", {})
    if totals.get("income"):
        total_in = sum(t.amount for t in stmt.transactions if t.amount > 0)
        if total_in != Decimal(totals["income"]):
            failures.append(f"income total: {total_in} != {totals['income']}")
    if totals.get("expenses"):
        total_out = sum(-t.amount for t in stmt.transactions if t.amount < 0)
        if total_out != Decimal(totals["expenses"]):
            failures.append(f"expense total: {total_out} != {totals['expenses']}")

    if failures:
        print("FAIL:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)

    print(f"PASS: {len(stmt.transactions)} transactions verified against expected JSON")


if __name__ == "__main__":
    main()
