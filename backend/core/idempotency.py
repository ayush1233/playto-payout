import time
import uuid
from datetime import timedelta
from functools import wraps

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from core.models import IdempotencyKey


def idempotent_request(view_func):
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        if request.method != "POST":
            return view_func(request, *args, **kwargs)

        key = request.headers.get("Idempotency-Key")
        if not key:
            return Response(
                {"error": "Idempotency-Key header is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uuid.UUID(key)
        except ValueError:
            return Response(
                {"error": "Idempotency-Key must be a valid UUID"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        merchant = request.merchant
        now = timezone.now()
        existing = IdempotencyKey.objects.filter(
            merchant=merchant, key=key, expires_at__gt=now
        ).first()
        if existing and existing.response_status is not None:
            return Response(existing.response_body, status=existing.response_status)
        IdempotencyKey.objects.filter(
            merchant=merchant, key=key, expires_at__lte=now
        ).delete()

        try:
            with transaction.atomic():
                IdempotencyKey.objects.create(
                    merchant=merchant,
                    key=key,
                    expires_at=now + timedelta(hours=24),
                )
        except IntegrityError:
            time.sleep(0.05)
            existing = IdempotencyKey.objects.filter(
                merchant=merchant, key=key, expires_at__gt=timezone.now()
            ).first()
            if existing and existing.response_status is not None:
                return Response(existing.response_body, status=existing.response_status)
            return Response(
                {"error": "request with this Idempotency-Key is already processing"},
                status=status.HTTP_409_CONFLICT,
            )

        response = view_func(request, *args, **kwargs)
        IdempotencyKey.objects.filter(merchant=merchant, key=key).update(
            response_body=response.data,
            response_status=response.status_code,
        )
        return response

    return wrapped_view
