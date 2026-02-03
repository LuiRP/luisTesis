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
from django.http import JsonResponse
from google import genai
from PIL import Image
from pydantic import BaseModel
from django.http import JsonResponse
import json
from google.genai import types
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
import os
from dotenv import load_dotenv
from django.conf import settings
from django.http import JsonResponse

my_api_key = settings.GEMINI_API_KEY

from django.db.models import Sum, F, Case, When, DecimalField
from django.db.models.functions import Coalesce, TruncMonth


def get_user_balances(user):
    latest_rate = (
        ExchangeRateModel.objects.filter(user=user)
        .order_by("-date", "-created_at")
        .first()
    )

    current_usd_rate = (
        latest_rate.usd_rate if latest_rate and latest_rate.usd_rate > 0 else 1
    )
    current_eur_rate = (
        latest_rate.eur_rate if latest_rate and latest_rate.eur_rate > 0 else 1
    )

    totals = (
        Transaction.objects.filter(user=user)
        .annotate(
            eff_usd=Case(
                When(is_custom=True, then=F("exchange_custom_rate")),
                default=F("exchange_rate__usd_rate"),
                output_field=DecimalField(),
            ),
            eff_eur=Case(
                When(is_custom=True, then=F("exchange_custom_rate")),
                default=F("exchange_rate__eur_rate"),
                output_field=DecimalField(),
            ),
        )
        .aggregate(
            total_ves=Coalesce(
                Sum(
                    Case(
                        When(currency="VES", then=F("total_amount")),
                        When(currency="USD", then=F("total_amount") * F("eff_usd")),
                        When(currency="EUR", then=F("total_amount") * F("eff_eur")),
                        default=0,
                        output_field=DecimalField(),
                    )
                ),
                0,
                output_field=DecimalField(),
            )
        )
    )

    ves_sum = totals["total_ves"]

    return {
        "total_ves": ves_sum,
        "total_usd": ves_sum / current_usd_rate,
        "total_eur": ves_sum / current_eur_rate,
        "latest_rate": latest_rate,
    }


@login_required
def balance_bs(request):
    balances = get_user_balances(request.user)
    return render(request, "balance/bs.html", {"balances": balances})


@login_required
def balance_usd(request):
    balances = get_user_balances(request.user)
    return render(request, "balance/usd.html", {"balances": balances})


@login_required
def balance_eur(request):
    balances = get_user_balances(request.user)
    return render(request, "balance/eur.html", {"balances": balances})


@login_required
def finance_chatbot_view(request):
    if request.method == "POST":
        user_input = request.POST.get("message")
        # Retrieve history from session
        session_history = request.session.get("chat_history", [])

        client = genai.Client(api_key=my_api_key)

        system_instruction = (
            "You are a specialized Personal Finance Assistant for Spanish speakers. "
            "All your responses MUST be in Spanish. "
            "Focus only on budgeting, savings, and financial advice. "
            "If the user asks about unrelated topics, politely decline in Spanish."
        )

        chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=system_instruction),
            history=session_history,
        )

        response = chat.send_message(user_input)

        # FIX: The new SDK stores history in chat.core._history or
        # you can manually append the new turn to your session_history
        new_history = session_history
        new_history.append({"role": "user", "parts": [{"text": user_input}]})
        new_history.append({"role": "model", "parts": [{"text": response.text}]})

        # Save back to session
        request.session["chat_history"] = new_history

        return JsonResponse({"response": response.text})

    return render(request, "core/chatbot/index.html")


class TransactionData(BaseModel):
    articles: str
    date: str
    total_amount: float


@login_required
def analyze_transaction_image(request):
    if request.method == "POST" and request.FILES.get("image"):
        client = genai.Client(api_key=my_api_key)
        img_file = request.FILES["image"]
        img = Image.open(img_file)

        # 2. Use 'response_mime_type' and 'response_schema' for a perfect JSON
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Extract the items with their prices, the date, and the total amount from this receipt.",
                img,
            ],
            config={
                "response_mime_type": "application/json",
                "response_schema": TransactionData,
            },
        )

        # Gemini returns a valid JSON string matching our Pydantic model
        data = json.loads(response.text)
        return JsonResponse(data)


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


@login_required
def exchange_rate_view(request):
    if request.method == "POST":
        data = get_bcv_rates()
        if "error" not in data:
            try:
                usd_val = Decimal(data["USD"].replace(".", "").replace(",", "."))
                eur_val = Decimal(data["EUR"].replace(".", "").replace(",", "."))
                ExchangeRateModel.objects.create(
                    user=request.user,
                    usd_rate=usd_val,
                    eur_rate=eur_val,
                    is_official=True,
                )
            except (IntegrityError, Exception):
                pass
        return redirect("exchange_rate")

    # Pagination Logic
    rate_list = ExchangeRateModel.objects.all().order_by("-created_at")
    paginator = Paginator(rate_list, 4)  # Show 10 rates per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "balance/exchange_rate.html", {"page_obj": page_obj})


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


@login_required
def statistics_view(request):
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    # Calculate expenses in VES
    qs = Transaction.objects.filter(user=request.user)

    if start_date:
        qs = qs.filter(created_at__date__gte=start_date)
    if end_date:
        qs = qs.filter(created_at__date__lte=end_date)

    qs = qs.annotate(
        eff_rate=Case(
            When(is_custom=True, then=F("exchange_custom_rate")),
            When(currency="USD", then=F("exchange_rate__usd_rate")),
            When(currency="EUR", then=F("exchange_rate__eur_rate")),
            default=1,
            output_field=DecimalField(),
        )
    ).annotate(
        amount_ves=Case(
            When(currency="VES", then=F("total_amount")),
            default=F("total_amount") * F("eff_rate"),
            output_field=DecimalField(),
        )
    )

    # By Category
    by_category = (
        qs.values("category").annotate(total=Sum("amount_ves")).order_by("-total")
    )

    cat_labels = []
    cat_data = []
    for item in by_category:
        try:
            label = Transaction.Category(item["category"]).label
        except ValueError:
            label = item["category"]
        cat_labels.append(label)
        cat_data.append(float(item["total"] or 0))

    # By Month
    by_month = (
        qs.annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Sum("amount_ves"))
        .order_by("month")
    )

    month_labels = [item["month"].strftime("%Y-%m") for item in by_month]
    month_data = [float(item["total"] or 0) for item in by_month]

    # By Currency
    by_currency = (
        qs.values("currency").annotate(total=Sum("amount_ves")).order_by("-total")
    )
    curr_labels = [item["currency"] for item in by_currency]
    curr_data = [float(item["total"] or 0) for item in by_currency]

    context = {
        "cat_labels": json.dumps(cat_labels),
        "cat_data": json.dumps(cat_data),
        "month_labels": json.dumps(month_labels),
        "month_data": json.dumps(month_data),
        "curr_labels": json.dumps(curr_labels),
        "curr_data": json.dumps(curr_data),
        "start_date": start_date,
        "end_date": end_date,
        "transactions": qs.order_by("-created_at"),
    }
    return render(request, "statistics/index.html", context)


def advice_view(request):
    return render(request, "advice/index.html")
