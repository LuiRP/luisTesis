from django.shortcuts import render, redirect
from neapolitan.views import CRUDView
from django.db import IntegrityError
from .models import ExchangeRate as ExchangeRateModel
from .models import Transaction
from .scrap import get_bcv_rates
from decimal import Decimal
from django import forms
from django.utils import timezone
import django_filters
from .models import Transaction
from django import forms


class TransactionFilter(django_filters.FilterSet):
    start_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Desde",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Hasta",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    class Meta:
        model = Transaction
        fields = ["category", "type", "currency"]


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


class TransactionCRUDView(CRUDView):
    model = Transaction
    fields = [
        "total_amount",
        "category",
        "description",
        "type",
        "currency",
        "is_custom",
        "exchange_rate",
        "exchange_custom_rate",
        "created_at",
    ]

    filterset_class = TransactionFilter
    paginate_by = 10

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
