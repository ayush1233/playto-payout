from django.urls import path

from merchants import views

urlpatterns = [
    path("merchants/me/", views.me, name="merchant-me"),
    path("merchants/me/ledger/", views.ledger, name="merchant-ledger"),
    path("merchants/me/bank-accounts/", views.bank_accounts, name="merchant-bank-accounts"),
]
