from django.db import transaction
from django.db.models import Sum

from core.exceptions import InsufficientFundsError
from merchants.models import Merchant
from payouts.models import LedgerEntry, Payout


def _available_balance_for_locked_merchant(merchant):
    result = LedgerEntry.objects.filter(merchant=merchant).aggregate(total=Sum("amount"))
    return result["total"] or 0


def create_payout_request(merchant, amount_paise, bank_account, idempotency_key):
    with transaction.atomic():
        locked_merchant = Merchant.objects.select_for_update().get(id=merchant.id)
        available_balance = _available_balance_for_locked_merchant(locked_merchant)

        if available_balance < amount_paise:
            raise InsufficientFundsError(available_balance, amount_paise)

        payout = Payout.objects.create(
            merchant=locked_merchant,
            bank_account=bank_account,
            amount_paise=amount_paise,
            idempotency_key=idempotency_key,
        )
        LedgerEntry.objects.create(
            merchant=locked_merchant,
            amount=-amount_paise,
            entry_type=LedgerEntry.EntryType.HOLD,
            payout=payout,
            description=f"Hold for payout #{payout.id}",
        )
        return payout
