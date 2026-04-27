from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from core.exceptions import InsufficientFundsError
from core.idempotency import idempotent_request
from merchants.models import BankAccount
from payouts.models import Payout
from payouts.serializers import CreatePayoutSerializer, PayoutSerializer
from payouts.services import create_payout_request
from payouts.tasks import process_payout


class PayoutPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 50


@api_view(["GET", "POST"])
@idempotent_request
def payouts_collection(request):
    if request.method == "GET":
        payouts = (
            Payout.objects.filter(merchant=request.merchant)
            .select_related("bank_account")
            .order_by("-created_at")
        )
        paginator = PayoutPagination()
        page = paginator.paginate_queryset(payouts, request)
        serializer = PayoutSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    serializer = CreatePayoutSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    bank_account = BankAccount.objects.filter(
        id=serializer.validated_data["bank_account_id"],
        merchant=request.merchant,
    ).first()
    if not bank_account:
        return Response(
            {"error": "bank account not found"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payout = create_payout_request(
            merchant=request.merchant,
            amount_paise=serializer.validated_data["amount_paise"],
            bank_account=bank_account,
            idempotency_key=request.headers["Idempotency-Key"],
        )
    except InsufficientFundsError as exc:
        return Response(
            {
                "error": "insufficient funds",
                "available_balance": exc.available_balance,
                "requested_amount": exc.requested_amount,
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    response = Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)
    process_payout.delay(payout.id)
    return response


@api_view(["GET"])
def retrieve_payout(request, pk):
    payout = (
        Payout.objects.filter(id=pk, merchant=request.merchant)
        .select_related("bank_account")
        .first()
    )
    if not payout:
        return Response({"error": "not found"}, status=status.HTTP_404_NOT_FOUND)
    return Response(PayoutSerializer(payout).data)
