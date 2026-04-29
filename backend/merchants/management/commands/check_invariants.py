import sys

from django.core.management.base import BaseCommand
from django.db.models import Sum

from merchants.models import Merchant
from payouts.models import LedgerEntry, Payout


class Command(BaseCommand):
    help = "Verify payout ledger invariants"

    def handle(self, *args, **kwargs):
        failed = False
        for merchant in Merchant.objects.order_by("id"):
            derived = (
                LedgerEntry.objects.filter(merchant=merchant).aggregate(total=Sum("amount"))[
                    "total"
                ]
                or 0
            )
            held = merchant.get_held_balance()
            self.stdout.write(
                f"{merchant.name}: derived_balance={derived} held={held} available={derived}"
            )

            for payout in merchant.payouts.all():
                counts = {
                    entry_type: LedgerEntry.objects.filter(
                        payout=payout, entry_type=entry_type
                    ).count()
                    for entry_type in [
                        LedgerEntry.EntryType.HOLD,
                        LedgerEntry.EntryType.HOLD_RELEASE,
                        LedgerEntry.EntryType.DEBIT,
                    ]
                }
                if payout.status == Payout.Status.COMPLETED:
                    ok = (
                        counts[LedgerEntry.EntryType.HOLD] == 1
                        and counts[LedgerEntry.EntryType.HOLD_RELEASE] == 1
                        and counts[LedgerEntry.EntryType.DEBIT] == 1
                    )
                elif payout.status == Payout.Status.FAILED:
                    ok = (
                        counts[LedgerEntry.EntryType.HOLD] == 1
                        and counts[LedgerEntry.EntryType.HOLD_RELEASE] == 1
                        and counts[LedgerEntry.EntryType.DEBIT] == 0
                    )
                else:
                    ok = (
                        counts[LedgerEntry.EntryType.HOLD] == 1
                        and counts[LedgerEntry.EntryType.HOLD_RELEASE] == 0
                        and counts[LedgerEntry.EntryType.DEBIT] == 0
                    )
                if not ok:
                    failed = True
                    self.stderr.write(
                        f"invariant failed for payout {payout.id}: {payout.status} {counts}"
                    )

        if failed:
            sys.exit(1)
        self.stdout.write(self.style.SUCCESS("all invariants pass"))
