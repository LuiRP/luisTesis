from django.contrib import admin
from django.urls import path, include
from .views import exchange_rate_view

urlpatterns = [
    path("rates/", exchange_rate_view, name="exchange_rate"),
]
