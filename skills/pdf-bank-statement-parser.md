# Skill: PDF Bank Statement Parser Generator

You are generating a PDF bank statement parser script for the clarifin project.

**Input:** a path to a bank statement PDF.

## Your process

**Step 1 — Study the PDF**

Extract the full text from the PDF using pdfplumber, printing each page with page
numbers, so you can study the exact layout.

**Step 2 — Identify the format**

Note down:
- The bank name (usually a header on every page)
- The account holder name(s)
- The exact string that uniquely identifies this statement format (issuer line,
  statement type header, etc.)
- The transaction table structure: which columns exist, how dates are formatted,
  how amounts are formatted (European comma-decimal or dot-decimal, currency symbol)
- Every sub-line that follows each transaction row (e.g. `To:`, `Card:`,
  `Reference:`, `From:`, exchange rate lines) — capture all of them

**Step 3 — Write the script**

Create python script with:

- `pdfplumber` for PDF reading
- A `Transaction` dataclass: `date: str`, `description: str`, `amount: Decimal`
  (negative = money out, positive = money in)
- A `Statement` dataclass: `bank: str`, `account_holders: list[str]`,
  `transactions: list[Transaction]`
- A `parse_pdf(path) -> Statement` function that:
  - Fails fast with a descriptive `ValueError` on any format mismatch — check
    header lines, issuer string, and section headers before parsing anything
  - Infers transaction sign from the running balance column (balance up = money in,
    balance down = money out)
  - Builds the description by concatenating the primary transaction name with all
    sub-lines (preserving their labels like `Reference:`, `From:`), space-separated
- A `_self_test()` function that parses the input PDF and asserts:
  - Correct bank name and account holders
  - Exact transaction count
  - First and last transaction (date, description prefix, amount)
  - All income transactions are positive, all expense transactions are negative
  - Money-in and money-out totals
- A `main()` with a `--self-test` flag and a CLI that prints bank, account holders,
  and a formatted transaction table

**Step 4 — Verify**

```bash
python scripts/extract_<...>.py --self-test
ruff check scripts/extract_<...>.py
mypy scripts/extract_<...>.py
```

Fix all failures before reporting done.

## Conventions

- `from __future__ import annotations` at the top
- European amount format: strip `.` then replace `,` with `.` before `Decimal()`
- Line length 88 characters max
- No comments explaining what the code does — only add one when the why is non-obvious
