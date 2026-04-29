from django.contrib import admin

from merchants.models import BankAccount, Merchant


@admin.register(Merchant)
class MerchantAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "created_at")
    search_fields = ("name", "email")


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "merchant",
        "account_holder_name",
        "account_number",
        "ifsc_code",
        "is_primary",
        "created_at",
    )
    search_fields = ("account_holder_name", "account_number", "merchant__name")
