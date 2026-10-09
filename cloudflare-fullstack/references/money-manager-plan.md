# Money Manager — Reference Plan & Build Notes

Complete implementation plan for a full-featured money management app using the Cloudflare full-stack pattern (Astro + Hono + R2 + Neon + Drizzle + shadcn/ui). Also serves as build notes from the actual implementation session.

## Key Design Decisions

1. **Transfers are wallet-to-wallet only.** No external transfers.
2. **Image uploads go to R2 via Files SDK.** Use `files-sdk` (https://files-sdk.dev) with `files-sdk/r2` adapter instead of raw R2 binding API. Transactions have an `image_url` field storing the R2 object key.
3. **No auto currency conversion.** Exchange rates are view-only reference data. Users manually enter `toAmount` for cross-currency transfers.
4. **Balances are computed, not stored.** Derived from transactions + adjustments via SQL.
5. **Audit trail for balance adjustments.** `balance_adjustments` table records old_balance → new_balance with reason.

## Files SDK R2 Pattern

```typescript
import { Files } from "files-sdk";
import { r2 } from "files-sdk/r2";

const files = new Files({
  adapter: r2({
    binding: env.IMAGES,           // R2Bucket binding — zero egress
    bucket: "app-images",
    accountId: env.R2_ACCOUNT_ID,  // for presigned URLs
    accessKeyId: env.R2_ACCESS_KEY_ID,
    secretAccessKey: env.R2_SECRET_ACCESS_KEY,
  }),
});

// Upload: files.upload(key, arrayBuffer, { contentType })  ← ArrayBuffer, not File!
// Download: await files.download(key) → ReadableStream/body
// Head: files.head(key) → { type, size, ... }
// Delete: files.delete(key)
// Presigned URL: files.url(key, { expiresIn: 300 })
// Presigned upload: files.signedUploadUrl(key, { expiresIn: 60, contentType })
```

**Important:** `files.upload()` requires `ArrayBuffer`, not a `File` object. Convert with `await file.arrayBuffer()` before passing.

Install: `bun add files-sdk @aws-sdk/client-s3 @aws-sdk/s3-presigned-post @aws-sdk/s3-request-presigner`

## Schema

```
wallets
  id, name, currency (ISO 4217), color, icon, is_default, sort_order, created_at, updated_at

categories
  id, name, type (income|expense|transfer), icon, color, sort_order, created_at

transactions
  id, wallet_id FK, category_id FK, type (income|expense|transfer),
  amount numeric(18,2), description, to_wallet_id FK (transfers),
  to_amount numeric(18,2) (manual cross-currency), image_url (R2 key),
  date, created_at, updated_at

balance_adjustments
  id, wallet_id FK, old_balance, new_balance, reason, created_at

goals
  id, wallet_id FK, name, target_amount, current_amount, deadline, created_at, updated_at

exchange_rates (view-only)
  from_currency, to_currency, rate numeric(18,6), fetched_at
  PK (from_currency, to_currency)
```

## Drizzle Relations

The `transactions` table has two FK references to `wallets` (walletId + toWalletId), so relations must use `relationName`:

```typescript
export const walletsRelations = relations(wallets, ({ many }) => ({
  transactions: many(transactions),
  toTransactions: many(transactions, { relationName: 'toWallet' }),
  adjustments: many(balanceAdjustments),
  goals: many(goals),
}));

export const transactionsRelations = relations(transactions, ({ one }) => ({
  wallet: one(wallets, { fields: [transactions.walletId], references: [wallets.id], relationName: 'wallet' }),
  toWallet: one(wallets, { fields: [transactions.toWalletId], references: [wallets.id], relationName: 'toWallet' }),
  category: one(categories, { fields: [transactions.categoryId], references: [categories.id] }),
}));
```

Without `relationName`, Drizzle throws: "There are multiple relations to the same table — add relationName."

## API Routes

```
POST/GET/PATCH/DELETE  /api/wallets[:id]
POST/GET/PATCH/DELETE  /api/transactions[:id]  (filters: walletId, type, categoryId, startDate, endDate, page, limit)
POST/GET               /api/adjustments
GET/POST               /api/categories
GET                    /api/stats/overview, /api/stats/monthly, /api/stats/by-category
POST/GET/DELETE        /api/upload[:key]       (R2 via files-sdk)
POST/GET/PATCH/DELETE  /api/goals[:id]
GET/POST               /api/exchange-rates[/refresh]
```

## Frontend Pages

```
/                        Dashboard: balance cards, monthly chart, recent txns, goal progress
/wallets                 Wallet list with balances
/wallets/:id             Wallet detail + adjustment history
/transactions            Filtered/paginated history + add form with image upload
/goals                   Goals with progress bars + create
/settings                Category CRUD, currency info
```

## Build Approach: Parallel Subagents

When the API and app workspaces are independent (app calls API via fetch), dispatch 2 parallel subagents via `delegate_task(tasks=[...])`:

1. **API subagent**: Build all routes, schema, middleware, config (api/ workspace)
2. **App subagent**: Build all pages, components, layout, shadcn setup (app/ workspace)

Provide each subagent with complete context (schema, env types, API endpoint specs, component breakdown) so it doesn't need to read plan files. This builds in ~10 min what serial per-task would take 30+ min.

## DB Connection Pattern

Single fallback in every route:
```typescript
const db = createDb(c.env.HYPERDRIVE?.connectionString ?? c.env.DATABASE_URL);
```

## Computed Balance SQL

```sql
COALESCE(
  (SELECT COALESCE(SUM(t.amount), 0) FROM transactions t WHERE t.wallet_id = $1 AND t.type = 'income')
  - (SELECT COALESCE(SUM(t.amount), 0) FROM transactions t WHERE t.wallet_id = $1 AND t.type = 'expense')
  + (SELECT COALESCE(SUM(t.to_amount), 0) FROM transactions t WHERE t.to_wallet_id = $1 AND t.type = 'transfer')
  - (SELECT COALESCE(SUM(t.amount), 0) FROM transactions t WHERE t.wallet_id = $1 AND t.type = 'transfer')
  + (SELECT COALESCE(SUM(ba.new_balance - ba.old_balance), 0) FROM balance_adjustments ba WHERE ba.wallet_id = $1)
, 0) AS balance
```

For all-wallets-at-once, join against wallets table and group by currency.

## Seed Data

Default categories (13):
- Income: Salary 💼, Freelance 💻, Investment 📈, Gift 🎁
- Expense: Food 🍔, Transport 🚗, Entertainment 🎮, Shopping 🛍️, Bills 📄, Health 🏥, Education 📚
- Transfer: Transfer 🔄

## Actual File Tree (Built)

```
money-manager/
├── .gitignore
├── package.json              # workspaces: [app, api]
├── tsconfig.json
├── drizzle.config.ts
├── drizzle/0001_seed_categories.sql
├── api/
│   ├── package.json, tsconfig.json, wrangler.toml, .dev.vars
│   └── src/
│       ├── index.ts          # Hono app, CORS, logger, routes mount
│       ├── types.ts          # Env interface
│       ├── db/schema.ts      # 7 tables + relations
│       ├── db/index.ts       # createDb factory
│       ├── lib/files.ts      # Files SDK R2 factory
│       ├── middleware/error.ts
│       └── routes/
│           ├── wallets.ts       # CRUD + computed balance
│           ├── transactions.ts  # CRUD + filters + pagination
│           ├── adjustments.ts  # POST (auto oldBalance) + GET
│           ├── categories.ts   # List + create
│           ├── goals.ts        # CRUD + wallet join
│           ├── stats.ts        # overview, monthly, by-category
│           ├── upload.ts       # R2 upload/serve/delete
│           └── exchange-rates.ts
├── app/
│   ├── package.json, tsconfig.json, astro.config.mjs, components.json
│   └── src/
│       ├── layouts/Layout.astro
│       ├── pages/ (6 routes)
│       ├── components/ (7 app components + 15 shadcn ui/)
│       ├── lib/ (api.ts, format.ts, utils.ts)
│       └── styles/globals.css
```

## Deploy Steps

```bash
# 1. Create Neon DB, get connection string
# 2. Create R2 bucket
npx wrangler r2 bucket create money-manager-images
# 3. Create Hyperdrive config
npx wrangler hyperdrive create DB --connection-string="postgres://..."
# 4. Update api/wrangler.toml with Hyperdrive ID
# 5. Set secrets
npx wrangler secret put DATABASE_URL
npx wrangler secret put R2_ACCOUNT_ID
npx wrangler secret put R2_ACCESS_KEY_ID
npx wrangler secret put R2_SECRET_ACCESS_KEY
# 6. Deploy API
cd api && npx wrangler deploy
# 7. Deploy app
cd app && npx wrangler pages deploy dist/
# 8. Run seed SQL
psql $DATABASE_URL -f drizzle/0001_seed_categories.sql
```