from django.shortcuts import render, redirect
from neapolitan.views import CRUDView
from django.db import IntegrityError
from .models import ExchangeRate as ExchangeRateModel
from .scrap import get_bcv_rates
from decimal import Decimal


def exchange_rate_view(request):
    if request.method == "POST":
        data = get_bcv_rates()

        if "error" not in data:
            try:
                usd_val = Decimal(data["USD"].replace(".", "").replace(",", "."))
                eur_val = Decimal(data["EUR"].replace(".", "").replace(",", "."))
                try:
                    ExchangeRateModel.objects.create(
                        user=request.user,
                        usd_rate=usd_val,
                        eur_rate=eur_val,
                        is_official=True,
                    )
                except IntegrityError:
                    pass

            except Exception:
                pass

        return redirect("exchange_rate")
    latest_rate = ExchangeRateModel.objects.order_by("-created_at").first()
    return render(request, "balance/exchange_rate.html", {"latest_rate": latest_rate})
