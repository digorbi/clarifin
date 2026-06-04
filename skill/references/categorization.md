# Transaction Categorization

## Approach

Categorization is an LLM task — not a keyword matcher. The goal is to assign each
transaction exactly one category from the `Settings` tab, using the description and
amount as signal. The keyword hints in Settings are guidance, not rules.

## Process

1. Read the `Settings` tab: collect category names and their keyword hints.
2. Ensure an `Other` category exists — add it if the user hasn't defined one.
3. Build one prompt containing all uncategorized transactions and send it in a single
   LLM call. Don't categorize one transaction at a time.
4. Parse the JSON response into `{index: category_name}` and apply.

## Prompt template

```
Categorize these household transactions. Assign each to exactly one category.

Categories and keyword hints:
{for each category: "- {name}: {keywords}"}

Transactions:
{for each tx: "{index}. {date} | {description} | {amount}"}

Reply with only JSON: {"0": "Groceries", "1": "Transport", ...}
Use only the category names listed above. If nothing fits, use "Other".
```

## Rules

- Always assign a category — never leave blank.
- Amounts don't change the category (a restaurant refund is still Dining).
- Transfers between the account holder's own accounts → `Transfer`.
- Income transfers from external parties (salary, freelance) → `Income` if that
  category exists; otherwise `Other`.
- When the LLM returns an unrecognized category name, substitute `Other`.
