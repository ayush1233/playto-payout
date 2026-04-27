from rest_framework import serializers

from merchants.serializers import BankAccountSerializer
from payouts.models import Payout


class PayoutSerializer(serializers.ModelSerializer):
    merchant_id = serializers.IntegerField(source="merchant.id", read_only=True)
    bank_account_id = serializers.IntegerField(source="bank_account.id", read_only=True)
    amount_paise = serializers.IntegerField()
    bank_account = BankAccountSerializer(read_only=True)

    class Meta:
        model = Payout
        fields = [
            "id",
            "merchant_id",
            "amount_paise",
            "bank_account_id",
            "bank_account",
            "status",
            "created_at",
            "updated_at",
            "attempt_count",
            "idempotency_key",
        ]
        read_only_fields = fields


class CreatePayoutSerializer(serializers.Serializer):
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.IntegerField()
