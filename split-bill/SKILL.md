---
name: split-bill
description: "Split bills with friends/roommates/groups — unequal splits, partial payments, multi-currency with auto rates, image receipt scanning, JSON backend."
version: 1.1.0
author: ekajaya740
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Expenses, Bills, Splitting, Groups, Finance, Multi-Currency, OCR]
---

# Split Bill

Track group expenses, split bills with custom shares, handle partial payments ("someone paid some"), scan receipts from photos, auto-fetch exchange rates, and settle debts — all stored as simple JSON files. No external service needed.

## Storage

Each group is a `.json` file under `~/.hermes/data/split-bill/`:

```
~/.hermes/data/split-bill/
├── Trip to Chiang Mai.json
├── House Bills.json
└── Dinner Group.json
```

---

## Core Concepts

| Term | Meaning |
|---|---|
| **Group** | A named expense pool with members (e.g., "House Bills") |
| **Expense** | A single bill with description, total, payer(s) & amounts paid, split recipients & shares |
| **Payer** | Someone who fronted money — multiple payers allowed per expense with their respective amounts |
| **Share** | What each person owes toward the expense (equal or custom amounts) |
| **Balance** | Net amount a person is owed (+) or owes (−) after all expenses and settlements |
| **Settlement** | A payment from Person A to Person B that reduces net debt |

## Data Format

Each group file looks like this:

```json
{
  "name": "Trip to Chiang Mai",
  "currency": "THB",
  "members": ["Alice", "Alex", "Bob", "Carol"],
  "expenses": [
    {
      "id": 1,
      "description": "Hotel night 1",
      "total": 4500,
      "currency": "THB",
      "exchange_rate": 1.0,
      "created_at": "2026-05-12T10:00:00",
      "receipt_image": null,
      "payers": [
        {"name": "Alice", "amount": 4500}
      ],
      "shares": [
        {"name": "Alice", "amount": 1500},
        {"name": "Alex", "amount": 2000},
        {"name": "Bob", "amount": 1000}
      ]
    },
    {
      "id": 2,
      "description": "BBQ night",
      "total": 2000,
      "currency": "THB",
      "exchange_rate": 1.0,
      "created_at": "2026-05-12T19:00:00",
      "receipt_image": null,
      "payers": [
        {"name": "Alex", "amount": 1200},
        {"name": "Alice", "amount": 800}
      ],
      "shares": [
        {"name": "Alex", "amount": 500},
        {"name": "Alice", "amount": 500},
        {"name": "Bob", "amount": 500},
        {"name": "Carol", "amount": 500}
      ]
    }
  ],
  "settlements": []
}
```

---

## Receipt Image Scanning

When the user sends photos of bills/receipts, extract what is **reliable** and be transparent about what is **uncertain**.

**Reliable data (confirm once, then proceed):**
- Receipt total (合計 / Total / Grand Total / Amount Due)
- Currency (¥, THB, $, etc.)
- Date of transaction
- Amount paid / change (when visible)

**Unreliable data — do NOT guess:**
- Exact quantities per line item on blurry or vertically-printed receipts
- Individual item prices when the receipt is long, folded, or on thermal paper (vision models hallucinate qty easily)
- Store names obscured by folds or creases

---

### Workflow

#### Step A — Scan all receipts
Call `vision_analyze` per receipt. For each, extract reliably:
> "Receipt 1 — Date, Total, Currency, Amount Paid / Change"

Present a summary list to the user **before** trying to read every item.

#### Step B — Ask for missing info, don't speculate
Explicitly ask:
- **"Who paid each receipt?"** (Yuda? Eka? Split?) — never assume or fill in.
- **"Equal split per receipt, or custom shares?"**
- If the currency differs from the group base, ask: **"Convert using today's rate, or keep at face value?"**

#### Step C — Offer two paths
**Path 1 (fast, recommended for bulk receipts):**
Add expenses by receipt total. Each receipt becomes one line item with the total.

**Path 2 (item-level):**
If the user wants per-item splitting, say honestly when vision can't read it reliably:
> "I can't reliably read exact quantities on these receipts. If you want item-level splitting, please type the list from your original receipt and I'll record each item properly."

#### Step D — Confirm before saving
Present the final list:
> Receipt 1: ¥9,273, Apr 25 — paid by **Yuda**
> Receipt 2: ¥11,311, Apr 29 — paid by **Eka**
> ...
> Add all? [y/N]

Only after confirmation, add to the group JSON.

---

### Technical Pitfalls

| Hazard | Mitigation |
|---|---|
| `vision_analyze` timeouts on dense, long receipts | Scan once for totals; if it times out, retry with a focused prompt or present what you have. Do NOT loop retry blindly. |
| Tesseract OCR on vertical Japanese thermal receipts | Almost useless — do not rely on it for item-level detail. Treat as fallback only. |
| Hallucinated item names / quantities | When the model returns plausible-sounding but garbled product names, flag as unreliable. Do not silently store them. |
| Bulk receipt fatigue | When a user sends 3+ receipts, process as a batch and present a summary table. Don't force them through N individual confirmations. |

**Image reference in data:** If the user sends a receipt image, save a copy to `~/.hermes/data/split-bill/receipts/<group>/<expense_id>.jpg` and store the path in `receipt_image`.

---

## Multi-Currency & Auto Exchange Rates

When an expense uses a **different currency** than the group's base currency:

### Step 1 — Auto-fetch rate

Use `web_search` with a query like `"THB to USD exchange rate today"` or `"1 USD to THB 2026-05-12"` to get the current rate.

```python
def fetch_exchange_rate(from_currency, to_currency):
    """Search web for current rate and extract it."""
    query = f"{from_currency} to {to_currency} exchange rate today"
    # Use web_search via the agent, return best-guess rate
```

### Step 2 — Fallback

If the web search fails or the rate can't be parsed, **use the source currency as-is** — record the expense at face value in its own currency without converting. The agent will note: *"Could not fetch THB→USD rate. Recording 120 USD at face value."*

### Step 3 — Confirm with user

Present the fetched rate and ask for confirmation before saving:

```
> add-expense group="Trip to Chiang Mai" description="Bangkok hotel" total=120 currency=USD paid_by=Bob split=Alice,Bob,Carol
  Fetched rate: 1 USD = 34.5 THB (from Google Finance)
  120 USD = 4,140 THB — confirm? [y/N]
```

If the user corrects the rate, use their provided rate instead.

---

## Workflow

### 1. Create a Group

```
new-group name="House Bills" members=Alex,Alice,Bob currency=THB
```

Creates `~/.hermes/data/split-bill/House Bills.json`.

### 2. Add an Expense — All Variations

**Equal split, one payer (simplest):**
```
add-expense group="House Bills" description="Electricity bill" total=2400 paid_by=Alex split=Alex,Alice,Bob
```
→ Alex paid 2,400. 3-way equal split: 800 each. Alex net: +1,600.

**Unequal split, one payer:**
```
add-expense group="House Bills" description="Water bill" total=1500 paid_by=Alice shares=Alice:0, Alex:500, Bob:1000
```
→ Alice paid 1,500. Alex owes 500, Bob owes 1,000, Alice owes 0 (covered by payment).

**Partial payment ("someone paid some") — multiple payers:**
```
add-expense group="House Bills" description="BBQ" total=2000 paid_by=Alex:1200, Alice:800 split=Alex,Alice,Bob,Carol
```
→ Alex credited 1,200, Alice credited 800. Each of 4 owes 500. Net: Alex +700, Alice +300, Bob −500, Carol −500.

**Partial payment + unequal split:**
```
add-expense group="House Bills" description="Groceries" total=3000 paid_by=Alex:2000, Bob:1000 shares=Alice:1200, Bob:300, Carol:1500
```
→ Alex credited 2,000, Bob credited 1,000. Alice owes 1,200, Bob owes 300 (net +700), Carol owes 1,500.

**Multi-currency expense (auto rate, then fallback):**
```
add-expense group="Trip to Chiang Mai" description="Japan layover" total=8000 currency=JPY paid_by=Alex split=Alex,Alice,Bob
```
→ Agent web-searches JPY→THB rate. If found (e.g., 0.24): 8,000 JPY = 1,920 THB. If not found: records 8,000 JPY at face value.

**From receipt image:**
```
User sends a photo of a bill → agent reads it → "I see 1,850 THB total." → user confirms → agent asks for payer/split
```

### 3. Show Balances

```
balances group="House Bills"
```

Returns a table:
```
╔════════╤═══════════╗
║ Person │ Balance   ║
╠════════╪═══════════╣
║ Alice  │ +2,300    ║
║ Alex   │ +1,200    ║
║ Bob    │ −1,500    ║
║ Carol  │ −2,000    ║
╚════════╧═══════════╝
```

Positive = owed money (paid more than their share). Negative = owes money (consumed more than they paid).

### 4. Simplify Debts (Minimum Transactions)

```
simplify group="House Bills"
```

Uses the greedy algorithm: sort creditors (descending) and debtors (descending), match largest creditor to largest debtor.

```
Current debts:
  (+2,300) Alice ← Bob 1,500, Carol 800
  (+1,200) Alex  ← Carol 1,200

→ Optimized (2 transactions):
  Bob   → Alice: 1,500
  Carol → Alex:    200
  Carol → Alice:   1,800
```

### 5. Settle Up

```
settle group="House Bills" from=Bob to=Alice amount=1500
```
→ Appends a settlement record. Re-run `balances` to see updated net.

### 6. View History

```
history group="House Bills"
```

Shows all expenses + settlements in chronological order.

---

## Balance Calculation Logic

For each person, compute:

```
net_balance = sum(amounts they paid) − sum(share amounts they owe) − sum(settlements they sent) + sum(settlements they received)
```

Implementation reference:

```python
import json

def load_group(name):
    path = f"{HOMEDIR}/.hermes/data/split-bill/{name}.json"
    with open(path) as f:
        return json.load(f)

def save_group(group):
    path = f"{HOMEDIR}/.hermes/data/split-bill/{group['name']}.json"
    with open(path, "w") as f:
        json.dump(group, f, indent=2)

def compute_balances(group):
    balances = {m: 0 for m in group["members"]}
    for ex in group["expenses"]:
        rate = ex.get("exchange_rate", 1.0)
        adjusted_total = ex["total"] * rate
        for payer in ex["payers"]:
            balances[payer["name"]] += payer["amount"] * rate
        for share in ex["shares"]:
            balances[share["name"]] -= share["amount"] * rate
    for s in group.get("settlements", []):
        balances[s["from"]] -= s["amount"]
        balances[s["to"]] += s["amount"]
    return balances

def simplify_debts(balances):
    creditors = sorted([(n, v) for n, v in balances.items() if v > 0],
                       key=lambda x: -x[1])
    debtors = sorted([(n, -v) for n, v in balances.items() if v < 0],
                     key=lambda x: -x[1])
    payments = []
    ci = di = 0
    while ci < len(creditors) and di < len(debtors):
        amt = min(creditors[ci][1], debtors[di][1])
        payments.append((debtors[di][0], creditors[ci][0], round(amt, 2)))
        creditors[ci] = (creditors[ci][0], round(creditors[ci][1] - amt, 2))
        debtors[di] = (debtors[di][0], round(debtors[di][1] - amt, 2))
        if creditors[ci][1] == 0: ci += 1
        if debtors[di][1] == 0: di += 1
    return payments
```

---

## Exchange Rate Auto-Fetch Pattern

When the user adds an expense with `currency=X` that differs from the group's base currency:

1. Search: `"{from_currency} to {to_currency} exchange rate"` via `web_search`
2. Extract the numeric rate from search results
3. Show rate to user for confirmation before saving
4. If search fails or rate unreadable → record expense at face value (no conversion), note it to user
5. User can override the rate at any time: `rate=34.5`

---

## Command Reference

All commands are natural-language prompts to the agent, not shell commands. The agent interprets and executes against the JSON files.

| You say | What happens |
|---|---|
| `new-group name="..." members=A,B,C` | Creates group JSON file |
| `add-expense group="..." desc="..." total=N paid_by=X split=A,B,C` | Equal split, one payer |
| `add-expense group="..." desc="..." total=N paid_by=X shares=X:a, Y:b` | Unequal split, one payer |
| `add-expense group="..." desc="..." total=N paid_by=X:n1, Y:n2 shares=...` | Multiple payers + any split |
| `add-expense ... currency=USD` | Auto-fetches rate, falls back to face value |
| `add-expense ... currency=USD rate=34.5` | Explicit rate override |
| `balances group="..."` | Show net balances table |
| `simplify group="..."` | Show optimized repayment plan |
| `settle group="..." from=X to=Y amount=N` | Record a payment |
| `history group="..."` | Chronological log of all entries |
| `list-groups` | Show all groups |

### Receipt scanning

| You send / say | What happens |
|---|---|
| *(send single receipt photo)* | Agent scans with `vision_analyze`, shows total + asks who paid + how to split |
| *(send 2+ receipt photos at once)* | Agent scans all, prints summary list with totals/dates, then asks who paid each + split mode |
| `add this bill` *(with photo)* | Same — scan, confirm, then agent asks who paid and how to split |
| *(photo + caption)* | Agent respects caption as description, scans photo for total |
| `show me what's on these receipts` | Read-only mode: extracts details without saving, user decides next step |

---

## Pitfalls

- **Group name case sensitivity** — group names are case-sensitive as file names. Use exact names or the agent normalizes them.
- **Member consistency** — the `members` list in the group is the source of truth. Adding an expense with a name not in members will prompt you to add them.
- **All balances computed in base currency** — multi-currency expenses are converted via `rate`. When auto-fetch fails, the expense is recorded at face value in its own currency with no conversion applied.
- **Receipt scanning quality** — depends on image clarity. Always confirm extracted amounts with the user before saving. Blurry, folded, or handwritten receipts may give inaccurate readings.
- **Decimal precision** — amounts are rounded to 2 decimal places.
- **Auto rate is a best-effort web search** — it may return stale or slightly inaccurate rates. Always present it to the user for confirmation before saving.
