from django.db import models
from django.db.models import Sum


class Merchant(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_available_balance(self):
        from payouts.models import LedgerEntry

        result = LedgerEntry.objects.filter(
            merchant=self,
            entry_type__in=[
                LedgerEntry.EntryType.CREDIT,
                LedgerEntry.EntryType.DEBIT,
                LedgerEntry.EntryType.HOLD,
                LedgerEntry.EntryType.HOLD_RELEASE,
            ],
        ).aggregate(total=Sum("amount"))
        return result["total"] or 0

    def get_held_balance(self):
        from payouts.models import Payout

        result = Payout.objects.filter(
            merchant=self,
            status__in=[Payout.Status.PENDING, Payout.Status.PROCESSING],
        ).aggregate(total=Sum("amount_paise"))
        return result["total"] or 0

    @property
    def is_authenticated(self):
        return True

    def __str__(self):
        return self.name


class BankAccount(models.Model):
    merchant = models.ForeignKey(
        Merchant, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    account_holder_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    ifsc_code = models.CharField(max_length=20)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account_holder_name} - {self.account_number[-4:]}"
