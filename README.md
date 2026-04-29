# Playto Payout Engine

Production-style payout simulation with a Django/DRF backend, PostgreSQL row locks, Celery/Redis workers, and a React dashboard. All money amounts are stored as signed integer paise.

## Setup (Local)

```bash
git clone <repo-url>
cd playto-payout
cp .env.example .env
docker compose up -d db redis
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_data
docker compose up web worker beat
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API runs at `http://localhost:8000/api/v1`.

## Architecture Overview

Balances are never stored on `Merchant`; they are derived from `LedgerEntry` rows with `Sum("amount")`. Credits are positive, holds/debits are negative, and hold releases are positive. Concurrent payout requests lock the merchant row with PostgreSQL `SELECT ... FOR UPDATE` before calculating balance, so two workers cannot spend the same funds. Idempotency is guarded by a database unique constraint on `(merchant, key)` and cached response bodies for 24 hours.

## Running Tests

```bash
docker compose run --rm web python manage.py test
```

The concurrency test uses `TransactionTestCase` and real Python threads so PostgreSQL row-level locking is exercised.

## API Reference

All endpoints require:

```http
X-Merchant-ID: 1
Content-Type: application/json
```

### GET `/api/v1/merchants/me/`

Returns merchant profile, balances in paise, and bank accounts.

```bash
curl -H "X-Merchant-ID: 1" http://localhost:8000/api/v1/merchants/me/
```

### GET `/api/v1/merchants/me/ledger/`

Returns paginated ledger entries.

```bash
curl -H "X-Merchant-ID: 1" "http://localhost:8000/api/v1/merchants/me/ledger/?page_size=20"
```

### GET `/api/v1/merchants/me/bank-accounts/`

```bash
curl -H "X-Merchant-ID: 1" http://localhost:8000/api/v1/merchants/me/bank-accounts/
```

### POST `/api/v1/payouts/`

Requires a UUID `Idempotency-Key`.

```bash
curl -X POST http://localhost:8000/api/v1/payouts/ \
  -H "Content-Type: application/json" \
  -H "X-Merchant-ID: 1" \
  -H "Idempotency-Key: 11111111-1111-4111-8111-111111111111" \
  -d '{"amount_paise":5000,"bank_account_id":1}'
```

### GET `/api/v1/payouts/`

```bash
curl -H "X-Merchant-ID: 1" http://localhost:8000/api/v1/payouts/
```

### GET `/api/v1/payouts/{id}/`

```bash
curl -H "X-Merchant-ID: 1" http://localhost:8000/api/v1/payouts/1/
```

## Demo Merchants

Seed data creates:

- `1` PixelCraft Studio
- `2` WordFlow Agency
- `3` DevSprint Labs

## Verification Commands

```bash
docker compose run --rm web python manage.py check_invariants
docker compose run --rm web python manage.py test
cd frontend && npm run build
```

No live deployment URL has been configured in this workspace.
