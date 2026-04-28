import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import IdempotencyKey
from merchants.models import BankAccount, Merchant
from payouts.models import LedgerEntry, Payout


class PayoutAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.merchant = Merchant.objects.create(name="Test Corp", email="api@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Test Corp",
            account_number="1234567890",
            ifsc_code="HDFC0001234",
            is_primary=True,
        )
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=100000,
            entry_type=LedgerEntry.EntryType.CREDIT,
            description="Initial credit",
        )
        self.client.credentials(HTTP_X_MERCHANT_ID=str(self.merchant.id))

    def post_payout(self, key=None, amount=5000):
        headers = {}
        if key:
            headers["HTTP_IDEMPOTENCY_KEY"] = key
        with patch("payouts.views.process_payout.delay"):
            return self.client.post(
                "/api/v1/payouts/",
                {"amount_paise": amount, "bank_account_id": self.bank.id},
                format="json",
                **headers,
            )

    def test_missing_idempotency_key_returns_400(self):
        resp = self.post_payout()
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_key_returns_same_payout(self):
        key = str(uuid.uuid4())
        resp1 = self.post_payout(key)
        resp2 = self.post_payout(key)
        self.assertEqual(resp1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp1.data["id"], resp2.data["id"])
        self.assertEqual(Payout.objects.count(), 1)
        self.assertEqual(IdempotencyKey.objects.count(), 1)

    def test_different_keys_create_different_payouts(self):
        resp1 = self.post_payout(str(uuid.uuid4()))
        resp2 = self.post_payout(str(uuid.uuid4()))
        self.assertNotEqual(resp1.data["id"], resp2.data["id"])
        self.assertEqual(Payout.objects.count(), 2)

    def test_expired_key_allows_new_payout(self):
        key = str(uuid.uuid4())
        IdempotencyKey.objects.create(
            merchant=self.merchant,
            key=key,
            response_body={"id": 999},
            response_status=201,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        resp = self.post_payout(key)
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payout.objects.count(), 1)
        self.assertEqual(IdempotencyKey.objects.count(), 1)

    def test_insufficient_funds_returns_422(self):
        resp = self.post_payout(str(uuid.uuid4()), amount=99999999)
        self.assertEqual(resp.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_get_payouts(self):
        Payout.objects.create(
            merchant=self.merchant,
            bank_account=self.bank,
            amount_paise=1000,
            idempotency_key="manual",
        )
        resp = self.client.get("/api/v1/payouts/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)
