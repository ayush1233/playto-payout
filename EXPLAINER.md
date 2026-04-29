# EXPLAINER

## Question 1 — The Ledger

`Merchant.get_available_balance()` uses:

```python
LedgerEntry.objects.filter(
    merchant=self,
    entry_type__in=[
        LedgerEntry.EntryType.CREDIT,
        LedgerEntry.EntryType.DEBIT,
        LedgerEntry.EntryType.HOLD,
        LedgerEntry.EntryType.HOLD_RELEASE,
    ],
).aggregate(total=Sum("amount"))
```

There is no stored balance field because stored balances can drift from ledger history. The ledger is the source of truth: credits are positive, holds and debits are negative, and hold releases are positive. In this project, “double-entry” means payout lifecycle events are represented by offsetting ledger movements: a hold reserves funds, a hold release reverses that reservation, and a debit records final money out. That makes the audit trail reconstructable.

## Question 2 — The Lock

The critical line is in `payouts/services.py`:

```python
locked_merchant = Merchant.objects.select_for_update().get(id=merchant.id)
```

It runs inside `transaction.atomic()` before the balance aggregate. PostgreSQL emits a `SELECT ... FOR UPDATE`, which takes a row-level lock on the merchant row. A Python `threading.Lock` would only protect one process; Django deployments commonly run multiple Gunicorn workers and Celery processes. The second concurrent request waits at the database lock until the first transaction commits, then recalculates balance against the updated ledger.

## Question 3 — The Idempotency

Duplicate requests are detected by `(merchant, key)` in `core.models.IdempotencyKey`. The `unique_together` constraint is the database-level guard, so even simultaneous requests cannot both create a fresh idempotency row. If the second request hits an `IntegrityError`, the decorator waits 50ms and rereads the existing row. If the first response has been stored, the exact body and status are returned; otherwise the second request receives HTTP 409. Keys expire after 24 hours, long enough for normal client retries while preventing unbounded key growth.

## Question 4 — The State Machine

```python
VALID_TRANSITIONS = {
    Status.PENDING: [Status.PROCESSING],
    Status.PROCESSING: [Status.COMPLETED, Status.FAILED],
    Status.COMPLETED: [],
    Status.FAILED: [],
}

def transition_to(self, new_status):
    if new_status not in self.VALID_TRANSITIONS[self.status]:
        raise InvalidStatusTransition(self.status, new_status)
    self.status = new_status
    self.save(update_fields=["status", "updated_at"])
```

The `if new_status not in ...` line blocks `FAILED -> COMPLETED` because `VALID_TRANSITIONS[FAILED]` is empty. The rule belongs in the model method so views, Celery tasks, retry jobs, and shell usage all get the same enforcement.

## Question 5 — The AI Audit

The original scaffold had a money-system bug in the payout service: it created holds with a positive amount and then used custom subtraction logic.

```python
LedgerEntry.objects.create(
    merchant=merchant,
    amount=amount,
    entry_type=LedgerEntry.EntryType.HOLD,
)
```

That is subtle but dangerous because the ledger is supposed to be a signed source of truth. A hold must reduce available balance by being negative; otherwise aggregate balance checks and invariant checks can disagree. The corrected version is:

```python
LedgerEntry.objects.create(
    merchant=locked_merchant,
    amount=-amount_paise,
    entry_type=LedgerEntry.EntryType.HOLD,
    payout=payout,
)
```

The corrected code lets balance remain a single database aggregate instead of special-case Python arithmetic.
