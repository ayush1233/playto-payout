from rest_framework import serializers

from merchants.models import BankAccount, Merchant
from payouts.models import LedgerEntry


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = [
            "id",
            "account_holder_name",
            "account_number",
            "ifsc_code",
            "is_primary",
            "created_at",
        ]


class MerchantSerializer(serializers.ModelSerializer):
    available_balance = serializers.SerializerMethodField()
    held_balance = serializers.SerializerMethodField()
    bank_accounts = BankAccountSerializer(many=True, read_only=True)

    class Meta:
        model = Merchant
        fields = [
            "id",
            "name",
            "email",
            "available_balance",
            "held_balance",
            "bank_accounts",
            "created_at",
        ]

    def get_available_balance(self, obj):
        return obj.get_available_balance()

    def get_held_balance(self, obj):
        return obj.get_held_balance()


class LedgerEntrySerializer(serializers.ModelSerializer):
    amount = serializers.IntegerField()
    payout_id = serializers.IntegerField(source="payout.id", read_only=True)
    payout_status = serializers.CharField(source="payout.status", read_only=True)

    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "amount",
            "entry_type",
            "description",
            "created_at",
            "payout_id",
            "payout_status",
        ]
