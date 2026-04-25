from django.db import models

from merchants.models import Merchant


class IdempotencyKey(models.Model):
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    response_body = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        unique_together = ("merchant", "key")
        indexes = [
            models.Index(fields=["merchant", "key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.merchant_id}:{self.key}"
