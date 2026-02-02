from django.contrib import admin
from django.urls import path, include
from .views import (
    exchange_rate_view,
    TransactionCRUDView,
    analyze_transaction_image,
    finance_chatbot_view,
    balance_bs,
    balance_usd,
    balance_eur,
)

urlpatterns = [
    path("balance/", balance_bs, name="balance_bs"),
    path("usd/", balance_usd, name="balance_usd"),
    path("eur/", balance_eur, name="balance_eur"),
    path("rates/", exchange_rate_view, name="exchange_rate"),
    path(
        "transactions/analyze-image/", analyze_transaction_image, name="analyze_image"
    ),
    path("finance-chatbot/", finance_chatbot_view, name="finance_chatbot_view"),
]
urlpatterns += TransactionCRUDView.get_urls()
