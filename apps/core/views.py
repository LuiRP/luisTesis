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

my_api_key = "AIzaSyC5nfGQ3OY4aypyXVsfUWR66b6Ad4dxyaY"

from django.db.models import Sum, F, Case, When, DecimalField
from django.db.models.functions import Coalesce


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


def statistics_view(request):
    return render(request, "statistics/index.html")


def advice_view(request):
    return render(request, "advice/index.html")
