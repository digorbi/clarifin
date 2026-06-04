---
name: bank-statement-processor
description: Use this skill to process bank statement PDFs and produce or update a structured Excel household budget report. Trigger whenever the user mentions bank statements, processing PDFs with transactions, updating a budget Excel, categorizing spending, monthly summaries, or importing financial data from PDFs. Also trigger when the user shares PDF files and wants spending analysis or a budget overview, even without the words "bank statement" or "Excel". Always use this skill — even for a single PDF — whenever the goal is a structured financial report from bank data.
compatibility:
  python: ">=3.12"
  packages: [pdfplumber, openpyxl]
---

# Bank Statement Processor

Turn one or more bank statement PDFs into a structured Excel budget report. The Excel
file is the persistent memory of the system — it stores parsed transactions, category
settings, and the Python parsers that extracted the data, so future runs reuse them
without re-deriving anything.

## Inputs

- One or more bank statement PDFs
- An existing Excel file (optional — created fresh if absent)

## Output

An updated Excel file with:
- One tab per statement month (`2026-03`, `2026-04`, …)
- A `Settings` tab with user-configurable categories and colors
- A hidden `_parsers` sheet with the Python code used to parse each bank format
- A hidden `_tx_hashes` sheet for deduplication across runs

## Workflow

### Step 1 — Open or create the Excel

If the user provides an existing Excel file, open it with openpyxl. If none exists,
copy `skill/template.xlsx` to the user's working directory as the starting file —
it already has the correct Settings tab, hidden `_parsers` and `_tx_hashes` sheets.
Read `references/excel-structure.md` now for the full sheet schemas and hidden-sheet format.

From the open workbook, read:
- `Settings` tab → category list (name, hex color, keyword hints)
- `_parsers` hidden sheet → available parsers (bank name, version, Python source)
- `_tx_hashes` hidden sheet → hashes of already-processed transactions

### Step 2 — For each PDF: find or generate a parser

For each input PDF:

1. **Try existing parsers first.** For each parser block in `_parsers`, exec the code
   and call `parse_pdf(path)`. Catch `ValueError` — the first call that succeeds
   identifies the right parser for this format.

2. **If all parsers raise `ValueError`**, no existing parser matches. Read
   `references/parser-generation.md` and follow it to generate a new parser.
   After generation, verify it passes ruff, mypy, and `--self-test` before continuing.
   Store the new parser in `_parsers` (see `references/excel-structure.md`).

### Step 3 — Parse and deduplicate

Call `parse_pdf(path)` to get a `Statement` with `transactions: list[Transaction]`.

Hash each transaction for deduplication:

```python
import hashlib
key = f"{tx.date}|{tx.description}|{tx.amount}"
tx_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
```

Skip any transaction whose hash already appears in `_tx_hashes`. Append new hashes
to that sheet after processing.

### Step 4 — Categorize

Read `references/categorization.md`. Send all new transactions plus the Settings
category list to the LLM in one batch call and get back a category per transaction.

### Step 5 — Write to the monthly tab

Determine the statement month from the transaction dates (e.g. `2026-03`). Create
the tab if it doesn't exist; append to it otherwise.

See `references/excel-structure.md` for the exact layout: summary section at the top
(income/expenses per category), daily transaction view below.

### Step 6 — Save and report

Save the Excel file. Print: bank name, account holders, new transactions added, month.

---

## Reference files — read on demand

| File | Read at |
|------|---------|
| `references/excel-structure.md` | Step 1 (sheet schema), Step 2 (parser storage), Step 5 (tab layout) |
| `references/parser-generation.md` | Step 2 only, when no existing parser matches |
| `references/categorization.md` | Step 4 |
