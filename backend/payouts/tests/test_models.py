from django.test import TestCase

from core.exceptions import InvalidStatusTransition
from merchants.models import BankAccount, Merchant
from payouts.models import Payout


class PayoutStateMachineTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Corp", email="state@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Test Corp",
            account_number="1234567890",
            ifsc_code="HDFC0001234",
        )

    def payout(self, status=Payout.Status.PENDING):
        return Payout.objects.create(
            merchant=self.merchant,
            bank_account=self.bank,
            amount_paise=5000,
            status=status,
            idempotency_key=f"key-{status}-{Payout.objects.count()}",
        )

    def test_legal_transitions(self):
        payout = self.payout()
        payout.transition_to(Payout.Status.PROCESSING)
        self.assertEqual(payout.status, Payout.Status.PROCESSING)
        payout.transition_to(Payout.Status.COMPLETED)
        self.assertEqual(payout.status, Payout.Status.COMPLETED)

        payout = self.payout()
        payout.transition_to(Payout.Status.PROCESSING)
        payout.transition_to(Payout.Status.FAILED)
        self.assertEqual(payout.status, Payout.Status.FAILED)

    def test_illegal_transitions(self):
        cases = [
            (Payout.Status.COMPLETED, Payout.Status.FAILED),
            (Payout.Status.FAILED, Payout.Status.COMPLETED),
            (Payout.Status.PROCESSING, Payout.Status.PENDING),
            (Payout.Status.PENDING, Payout.Status.COMPLETED),
        ]
        for current, attempted in cases:
            with self.subTest(current=current, attempted=attempted):
                payout = self.payout(status=current)
                with self.assertRaises(InvalidStatusTransition):
                    payout.transition_to(attempted)
