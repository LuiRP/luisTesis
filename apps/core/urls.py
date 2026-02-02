from django.contrib import admin
from django.urls import path, include
from .views import exchange_rate_view, TransactionCRUDView, analyze_transaction_image


urlpatterns = [
    path("rates/", exchange_rate_view, name="exchange_rate"),
    path(
        "transactions/analyze-image/", analyze_transaction_image, name="analyze_image"
    ),
]
urlpatterns += TransactionCRUDView.get_urls()
