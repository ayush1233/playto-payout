from django.db import models

from core.exceptions import InvalidStatusTransition
from merchants.models import BankAccount, Merchant


class Payout(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"

    VALID_TRANSITIONS = {
        Status.PENDING: [Status.PROCESSING],
        Status.PROCESSING: [Status.COMPLETED, Status.FAILED],
        Status.COMPLETED: [],
        Status.FAILED: [],
    }

    merchant = models.ForeignKey(
        Merchant, on_delete=models.PROTECT, related_name="payouts"
    )
    bank_account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)
    amount_paise = models.BigIntegerField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    attempt_count = models.IntegerField(default=0)
    idempotency_key = models.CharField(max_length=255, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processing_started_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["merchant", "status"]),
            models.Index(fields=["status", "processing_started_at"]),
        ]

    def transition_to(self, new_status):
        if new_status not in self.VALID_TRANSITIONS[self.status]:
            raise InvalidStatusTransition(self.status, new_status)
        self.status = new_status
        self.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"Payout {self.id} - {self.amount_paise} - {self.status}"


class LedgerEntry(models.Model):
    class EntryType(models.TextChoices):
        CREDIT = "CREDIT", "Credit"
        DEBIT = "DEBIT", "Debit"
        HOLD = "HOLD", "Hold"
        HOLD_RELEASE = "HOLD_RELEASE", "Hold release"

    merchant = models.ForeignKey(
        Merchant, on_delete=models.PROTECT, related_name="ledger_entries"
    )
    amount = models.BigIntegerField()
    entry_type = models.CharField(max_length=20, choices=EntryType.choices)
    payout = models.ForeignKey(
        Payout, null=True, blank=True, on_delete=models.PROTECT, related_name="ledger_entries"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, default="", blank=True)

    class Meta:
        indexes = [models.Index(fields=["merchant", "created_at"])]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.merchant_id} {self.entry_type} {self.amount}"
