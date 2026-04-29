from django.test import TestCase

from merchants.models import BankAccount, Merchant
from payouts.models import LedgerEntry


class MerchantModelTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Corp", email="merchant@example.com")

    def test_balances_are_derived_from_ledger(self):
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=100000,
            entry_type=LedgerEntry.EntryType.CREDIT,
            description="Test credit",
        )
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=-25000,
            entry_type=LedgerEntry.EntryType.HOLD,
            description="Test hold",
        )
        self.assertEqual(self.merchant.get_available_balance(), 75000)


class BankAccountModelTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Corp", email="bank@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Test Corp",
            account_number="1234567890",
            ifsc_code="HDFC0001234",
            is_primary=True,
        )

    def test_bank_account_belongs_to_merchant(self):
        self.assertEqual(self.bank.merchant, self.merchant)
