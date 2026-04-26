from django.core.management.base import BaseCommand
from django.db import transaction

from merchants.models import BankAccount, Merchant
from payouts.models import LedgerEntry, Payout


class Command(BaseCommand):
    help = "Seed demo merchants, bank accounts, ledger entries, and payouts"

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            pixel = self._merchant("PixelCraft Studio", "pixelcraft@example.com")
            pixel_bank = self._bank(pixel, "Priya Shah", "50100012345678", "HDFC0001234")
            self._credit(pixel, 45000, "Payment from Acme Corp - Invoice #1042")
            self._credit(pixel, 125000, "Payment from Northstar Retail - Invoice #1051")
            self._credit(pixel, 200000, "Payment from Orbit Foods - Invoice #1060")
            self._completed_payout(pixel, pixel_bank, 80000, "seed-pixel-completed")

            word = self._merchant("WordFlow Agency", "wordflow@example.com")
            word_bank = self._bank(word, "Rohan Mehta", "50200023456789", "ICIC0002345")
            self._credit(word, 95000, "Payment from ClearDesk - Blog package")
            self._credit(word, 85000, "Payment from Finlytics - Case study")
            self._pending_payout(word, word_bank, 30000, "seed-word-pending")

            dev = self._merchant("DevSprint Labs", "devsprint@example.com")
            self._bank(dev, "Anika Rao", "50300034567890", "SBIN0003456")
            self._credit(dev, 75000, "Payment from Atlas CRM - Sprint 18")
            self._credit(dev, 110000, "Payment from BlueCart - API integration")
            self._credit(dev, 60000, "Payment from ZenOps - Retainer")
            self._credit(dev, 140000, "Payment from LaunchPad - Milestone 2")

        for merchant in Merchant.objects.order_by("id"):
            self.stdout.write(
                f"{merchant.id}: {merchant.name} | available={merchant.get_available_balance()} "
                f"| held={merchant.get_held_balance()}"
            )

    def _merchant(self, name, email):
        merchant, _ = Merchant.objects.get_or_create(
            email=email,
            defaults={"name": name},
        )
        return merchant

    def _bank(self, merchant, holder, number, ifsc):
        bank, _ = BankAccount.objects.get_or_create(
            merchant=merchant,
            account_number=number,
            defaults={
                "account_holder_name": holder,
                "ifsc_code": ifsc,
                "is_primary": True,
            },
        )
        return bank

    def _credit(self, merchant, amount, description):
        LedgerEntry.objects.get_or_create(
            merchant=merchant,
            amount=amount,
            entry_type=LedgerEntry.EntryType.CREDIT,
            description=description,
            payout=None,
        )

    def _completed_payout(self, merchant, bank, amount, key):
        payout, _ = Payout.objects.get_or_create(
            merchant=merchant,
            idempotency_key=key,
            defaults={
                "bank_account": bank,
                "amount_paise": amount,
                "status": Payout.Status.COMPLETED,
                "attempt_count": 1,
            },
        )
        self._ledger_once(merchant, payout, -amount, LedgerEntry.EntryType.HOLD)
        self._ledger_once(merchant, payout, amount, LedgerEntry.EntryType.HOLD_RELEASE)
        self._ledger_once(merchant, payout, -amount, LedgerEntry.EntryType.DEBIT)

    def _pending_payout(self, merchant, bank, amount, key):
        payout, _ = Payout.objects.get_or_create(
            merchant=merchant,
            idempotency_key=key,
            defaults={
                "bank_account": bank,
                "amount_paise": amount,
                "status": Payout.Status.PENDING,
            },
        )
        self._ledger_once(merchant, payout, -amount, LedgerEntry.EntryType.HOLD)

    def _ledger_once(self, merchant, payout, amount, entry_type):
        LedgerEntry.objects.get_or_create(
            merchant=merchant,
            payout=payout,
            entry_type=entry_type,
            defaults={
                "amount": amount,
                "description": f"{entry_type} for payout #{payout.id}",
            },
        )
