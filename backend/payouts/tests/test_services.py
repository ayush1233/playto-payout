import threading

from django.test import TestCase, TransactionTestCase

from core.exceptions import InsufficientFundsError
from merchants.models import BankAccount, Merchant
from payouts.models import LedgerEntry, Payout
from payouts.services import create_payout_request


class PayoutServiceTest(TestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Test Corp", email="test@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Test Corp",
            account_number="1234567890",
            ifsc_code="HDFC0001234",
            is_primary=True,
        )
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=10000,
            entry_type=LedgerEntry.EntryType.CREDIT,
            description="Initial credit",
        )

    def test_create_payout_holds_negative_amount(self):
        payout = create_payout_request(self.merchant, 6000, self.bank, "key-1")
        hold = LedgerEntry.objects.get(payout=payout, entry_type=LedgerEntry.EntryType.HOLD)
        self.assertEqual(payout.amount_paise, 6000)
        self.assertEqual(hold.amount, -6000)
        self.assertEqual(self.merchant.get_available_balance(), 4000)

    def test_insufficient_funds_rolls_back(self):
        with self.assertRaises(InsufficientFundsError):
            create_payout_request(self.merchant, 20000, self.bank, "key-2")
        self.assertEqual(Payout.objects.count(), 0)
        self.assertEqual(
            LedgerEntry.objects.filter(entry_type=LedgerEntry.EntryType.HOLD).count(),
            0,
        )


class ConcurrentPayoutTest(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.merchant = Merchant.objects.create(name="Race Corp", email="race@example.com")
        self.bank = BankAccount.objects.create(
            merchant=self.merchant,
            account_holder_name="Race Corp",
            account_number="1234567890",
            ifsc_code="HDFC0001234",
            is_primary=True,
        )
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount=10000,
            entry_type=LedgerEntry.EntryType.CREDIT,
            description="Initial credit",
        )

    def test_concurrent_requests_cannot_overdraw(self):
        barrier = threading.Barrier(2)
        results = []
        lock = threading.Lock()

        def attempt(key):
            try:
                barrier.wait()
                create_payout_request(self.merchant, 6000, self.bank, key)
                result = "success"
            except InsufficientFundsError:
                result = "insufficient"
            with lock:
                results.append(result)

        threads = [
            threading.Thread(target=attempt, args=("race-a",)),
            threading.Thread(target=attempt, args=("race-b",)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(results.count("success"), 1)
        self.assertEqual(results.count("insufficient"), 1)
        self.merchant.refresh_from_db()
        self.assertEqual(self.merchant.get_available_balance(), 4000)
        self.assertEqual(Payout.objects.filter(merchant=self.merchant).count(), 1)
        self.assertEqual(
            LedgerEntry.objects.filter(
                merchant=self.merchant, entry_type=LedgerEntry.EntryType.HOLD
            ).count(),
            1,
        )
