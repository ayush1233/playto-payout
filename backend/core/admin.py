from django.contrib import admin

from core.models import IdempotencyKey


@admin.register(IdempotencyKey)
class IdempotencyKeyAdmin(admin.ModelAdmin):
    list_display = ("id", "merchant", "key", "response_status", "expires_at", "created_at")
    list_filter = ("response_status",)
    search_fields = ("key", "merchant__name")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
