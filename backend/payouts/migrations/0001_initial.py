# Generated manually for the Playto payout engine schema.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("merchants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Payout",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount_paise", models.BigIntegerField()),
                ("status", models.CharField(choices=[("PENDING", "Pending"), ("PROCESSING", "Processing"), ("COMPLETED", "Completed"), ("FAILED", "Failed")], default="PENDING", max_length=20)),
                ("attempt_count", models.IntegerField(default=0)),
                ("idempotency_key", models.CharField(db_index=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("processing_started_at", models.DateTimeField(null=False)),
                (
                    "bank_account",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="merchants.bankaccount"),
                ),
                (
                    "merchant",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="payouts", to="merchants.merchant"),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LedgerEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("amount", models.BigIntegerField()),
                ("entry_type", models.CharField(choices=[("CREDIT", "Credit"), ("DEBIT", "Debit"), ("HOLD", "Hold"), ("HOLD_RELEASE", "Hold release")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("description", models.CharField(blank=True, default="", max_length=255)),
                (
                    "merchant",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="ledger_entries", to="merchants.merchant"),
                ),
                (
                    "payout",
                    models.ForeignKey(null=False, on_delete=django.db.models.deletion.PROTECT, related_name="ledger_entries", to="payouts.payout"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="payout",
            index=models.Index(fields=["merchant", "status"], name="payouts_pay_merchan_9a626f_idx"),
        ),
        migrations.AddIndex(
            model_name="payout",
            index=models.Index(fields=["status", "processing_started_at"], name="payouts_pay_status_d373c4_idx"),
        ),
        migrations.AddIndex(
            model_name="ledgerentry",
            index=models.Index(fields=["merchant", "created_at"], name="payouts_led_merchan_37f31e_idx"),
        ),
    ]
