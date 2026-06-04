# Excel File Structure

## Visible tabs

### Monthly tabs — `YYYY-MM`

One tab per statement month, e.g. `2026-03`.

#### Summary section (top of sheet)

| Row | Content |
|-----|---------|
| 1 | Title: `March 2026` — merged A1:D1, bold, size 14 |
| 2 | Blank |
| 3 | Column headers: `Category \| Income \| Expenses \| Net` — bold |
| 4… | One row per category that has transactions this month |
| last | Totals row: `Total \| {sum} \| {sum} \| {net}` — bold |

#### Daily view section

Starts two rows below the summary totals row.

Column headers: `Date | Description | Amount | Category` — bold

Transaction rows, sorted by date ascending:
- `Date`: shown only on the first transaction of each day (bold); blank for
  subsequent same-day rows
- `Amount`: positive for income (green text `#00AA00`), negative for expenses
- `Category`: assigned by LLM from the Settings list

### Settings tab

| A: Category | B: Color (hex) | C: Keywords |
|-------------|---------------|-------------|
| Groceries | #4CAF50 | supermarket, grocery, lidl, aldi, rewe |
| Dining | #FF9800 | restaurant, cafe, coffee, food delivery |
| Transport | #2196F3 | uber, taxi, train, bvg, db, fuel |
| Utilities | #9C27B0 | electricity, gas, water, internet, phone |
| Health | #F44336 | pharmacy, doctor, gym, fitness |
| Shopping | #795548 | amazon, clothing, electronics |
| Entertainment | #E91E63 | cinema, netflix, spotify, games |
| Transfer | #607D8B | bank transfer, own account |
| Other | #9E9E9E | |

The `Keywords` column is optional guidance for the LLM — not a rule engine.
Users may add, rename, or recolor categories freely.

---

## Hidden tabs

### `_parsers`

Stores one parser per bank format. Each parser occupies a contiguous block of rows
separated from the next by a `---` sentinel row.

| Column A | Column B |
|----------|----------|
| `bank` | `Neobank` |
| `format` | `Joint Account EUR Statement` |
| `version` | `1` |
| `updated` | `2026-03-15` |
| `code` | *(Python source — entire file as a single string in B, or split one logical line per row)* |
| `---` | *(block separator)* |

**Reading a parser:**
Scan for a row where A = `bank`. Collect rows until the next `---` separator.
Join the values from column B of all `code` rows into one string. `exec()` it into a
fresh namespace and extract `parse_pdf`.

**Writing a new parser:**
Append a new block after the last `---`. If a parser for the same bank already exists,
increment `version` and keep the old block — don't delete it. Old blocks are the
version history; they let you roll back if a newer parser regresses.

**Matching a parser to a PDF:**
Try `parse_pdf(path)` for each block in order, newest version first. The first one
that doesn't raise `ValueError` is the right parser. A `ValueError` means format
mismatch — try the next parser.

### `_tx_hashes`

Single column of 16-character hex strings, one per row. Each hash represents one
processed transaction. Append new hashes after each run. Check this sheet before
writing any transaction to the monthly tab — skip duplicates.

Hash derivation:
```python
import hashlib
key = f"{tx.date}|{tx.description}|{tx.amount}"
tx_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
```
