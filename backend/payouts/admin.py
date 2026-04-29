from django.contrib import admin

from payouts.models import LedgerEntry, Payout


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "merchant",
        "amount_paise",
        "status",
        "attempt_count",
        "bank_account",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("merchant__name", "idempotency_key")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "entry_type", "amount", "payout", "created_at")
    list_filter = ("entry_type",)
    search_fields = ("merchant__name", "description")
    ordering = ("-created_at",)
