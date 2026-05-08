# clarifin

A Claude skill for household finance tracking. Processes bank statements, accepts manual cash entries, categorises transactions, and keeps everything in a single `.xlsx` file — one place to look, nothing to sync.

---

## What it does

- **Ingests bank statements** in PDF format (sourced from Google Drive or email — input handling is outside this skill's scope)
- **Accepts manual cash entries** for transactions that never hit a bank account
- **Categorises transactions** automatically, with corrections that improve over time
- **Tracks multiple family members** in a shared ledger — one file, everyone visible
- **Outputs a single `.xlsx`** that is both the data store and the human-readable report: monthly tabs, spending vs. savings summaries, and category breakdowns

No database. No dashboard to log into. No subscription. The spreadsheet is the product.

---

## Usage

TBD

---

## Design decisions

**Why `.xlsx` as the data store?**  
Every household already knows how to open, share, and back up a spreadsheet. Spreadsheets open everywhere — including Google Sheets — no extra tooling, no dashboard to log into. The file is both the data store and the human-readable report. The tradeoff is scale — this is designed for a family, not a firm.

**Why a skill bundle rather than a standalone script?**  
Running inside a Claude-compatible shell (Claude, ChatGPT, etc.) means no installation, no server, and no hosting — works from mobile, desktop, or web. The LLM runtime also brings built-in integrations: it can pull statements from email or Google Drive and push the updated ledger back, without any glue code. On top of that, the LLM handles parsing edge cases — ambiguous transaction descriptions, unclear amounts — by asking for clarification rather than silently failing.

---

## Requirements

- Claude with skill support
- Google Drive or email access configured at the orchestration layer (not handled here)
- An `.xlsx` file as the designated ledger (created on first run if absent)

---

## Status

Personal project. Shared as-is. Issues and pull requests are welcome, but response time is best-effort.

---

## License

MIT