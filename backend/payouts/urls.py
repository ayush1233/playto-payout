from django.urls import path

from payouts import views

urlpatterns = [
    path("payouts/", views.payouts_collection, name="payouts-collection"),
    path("payouts/<int:pk>/", views.retrieve_payout, name="retrieve-payout"),
]
