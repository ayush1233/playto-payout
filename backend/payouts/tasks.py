import random
import time
from datetime import timedelta

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from payouts.models import LedgerEntry, Payout


@shared_task(bind=True)
def process_payout(self, payout_id):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().filter(id=payout_id).first()
        if not payout or payout.status != Payout.Status.PENDING:
            return
        payout.transition_to(Payout.Status.PROCESSING)
        payout.attempt_count += 1
        payout.processing_started_at = timezone.now()
        payout.save(
            update_fields=["attempt_count", "processing_started_at", "updated_at"]
        )

    time.sleep(random.randint(1, 3))
    outcome_roll = random.random()

    if outcome_roll <= 0.69:
        _complete_payout(payout_id)
    elif outcome_roll <= 0.89:
        _fail_payout(payout_id)
    else:
        return


def _complete_payout(payout_id):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)
        if payout.status != Payout.Status.PROCESSING:
            return
        payout.transition_to(Payout.Status.COMPLETED)
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            amount=payout.amount_paise,
            entry_type=LedgerEntry.EntryType.HOLD_RELEASE,
            payout=payout,
            description=f"Release hold for completed payout #{payout.id}",
        )
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            amount=-payout.amount_paise,
            entry_type=LedgerEntry.EntryType.DEBIT,
            payout=payout,
            description=f"Debit for completed payout #{payout.id}",
        )


def _fail_payout(payout_id):
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(id=payout_id)
        if payout.status != Payout.Status.PROCESSING:
            return
        payout.transition_to(Payout.Status.FAILED)
        LedgerEntry.objects.create(
            merchant=payout.merchant,
            amount=payout.amount_paise,
            entry_type=LedgerEntry.EntryType.HOLD_RELEASE,
            payout=payout,
            description=f"Release hold for failed payout #{payout.id}",
        )


@shared_task
def retry_stuck_payouts():
    cutoff = timezone.now() - timedelta(seconds=30)
    retry_ids = list(
        Payout.objects.filter(
            status=Payout.Status.PROCESSING,
            processing_started_at__lt=cutoff,
            attempt_count__lt=3,
        ).values_list("id", flat=True)
    )

    for payout_id in retry_ids:
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout_id)
            if payout.status != Payout.Status.PROCESSING or payout.attempt_count >= 3:
                continue
            # Explicit scheduler reset for stuck external calls; this bypass is intentional.
            payout.status = Payout.Status.PENDING
            payout.processing_started_at = None
            payout.save(
                update_fields=["status", "processing_started_at", "updated_at"]
            )
        process_payout.delay(payout_id)

    exhausted_ids = list(
        Payout.objects.filter(
            status=Payout.Status.PROCESSING,
            processing_started_at__lt=cutoff,
            attempt_count__gte=3,
        ).values_list("id", flat=True)
    )

    for payout_id in exhausted_ids:
        _fail_payout(payout_id)

    return {"retried": len(retry_ids), "failed": len(exhausted_ids)}
