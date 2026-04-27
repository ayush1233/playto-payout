from rest_framework import authentication, exceptions

from merchants.models import Merchant


class MerchantHeaderAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        merchant_id = request.headers.get("X-Merchant-ID")
        if not merchant_id:
            raise exceptions.AuthenticationFailed("X-Merchant-ID header is required")

        try:
            merchant = Merchant.objects.get(id=merchant_id)
        except (Merchant.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed("invalid merchant")

        request.merchant = merchant
        return (merchant, None)
