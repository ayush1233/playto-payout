from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from merchants.serializers import (
    BankAccountSerializer,
    LedgerEntrySerializer,
    MerchantSerializer,
)


class LedgerPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


@api_view(["GET"])
def me(request):
    return Response(MerchantSerializer(request.merchant).data)


@api_view(["GET"])
def ledger(request):
    entries = request.merchant.ledger_entries.select_related("payout").order_by("-created_at")
    paginator = LedgerPagination()
    page = paginator.paginate_queryset(entries, request)
    serializer = LedgerEntrySerializer(page, many=True)
    return paginator.get_paginated_response(serializer.data)


@api_view(["GET"])
def bank_accounts(request):
    return Response(BankAccountSerializer(request.merchant.bank_accounts.all(), many=True).data)
