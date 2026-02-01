from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# Create your models here.
class ExchangeRate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField(_("date"), auto_now_add=True)
    usd_rate = models.DecimalField(_("USD rate"), max_digits=10, decimal_places=4)
    eur_rate = models.DecimalField(_("EUR rate"), max_digits=10, decimal_places=4)
    is_official = models.BooleanField(_("active"), default=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["date", "usd_rate", "eur_rate"], name="unique_daily_rate"
            )
        ]
