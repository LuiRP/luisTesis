from django.utils import timezone
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError


def validate_not_future(value):
    if value > timezone.now():
        raise ValidationError(_("La fecha no puede ser posterior a la actual."))


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

    def __str__(self):
        return f"Tasa {self.date} - USD: {self.usd_rate} EUR: {self.eur_rate}"


class Transaction(models.Model):
    class Category(models.TextChoices):
        COMIDA = "comida", "Comida"
        OCIO = "ocio", "Ocio"
        TRANSPORTE = "transporte", "Transporte"
        SALUD = "salud", "Salud"
        EDUCACION = "educacion", "Educación"
        HOGAR = "hogar", "Hogar"
        ROPA = "ropa", "Ropa"
        SERVICIOS = "servicios", "Servicios"
        OTROS = "otros", "Otros"

    class Type(models.TextChoices):
        AJUSTE = "ajuste", "Ajuste"
        FACTURA = "factura", "Factura"
        Pago = "pago", "Pago"

    class Currency(models.TextChoices):
        USD = "USD", "Dólares"
        EUR = "EUR", "Euros"
        VES = "VES", "Bolívares"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_amount = models.DecimalField(
        _("Monto total"), max_digits=15, decimal_places=2
    )
    category = models.CharField(
        _("Categoría"), choices=Category.choices, default=Category.OTROS, max_length=50
    )
    description = models.TextField(_("Artículos"), blank=True, null=True)
    type = models.CharField(
        _("Tipo"), choices=Type.choices, default=Type.FACTURA, max_length=50
    )
    currency = models.CharField(
        _("Divisa"), choices=Currency.choices, default=Currency.VES, max_length=10
    )
    is_custom = models.BooleanField(_("Personalizado"), default=False)
    exchange_rate = models.ForeignKey(
        ExchangeRate, on_delete=models.SET_NULL, null=True, blank=True
    )
    exchange_custom_rate = models.DecimalField(
        _("Tasa de cambio personalizada"),
        max_digits=15,
        decimal_places=4,
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(
        _("Creado el"),
        default=timezone.now,
        validators=[validate_not_future],
    )

    def clean(self):
        super().clean()

        # Validation: If is_custom is True, exchange_custom_rate is required
        if self.is_custom and self.exchange_custom_rate is None:
            raise ValidationError(
                {
                    "exchange_custom_rate": _(
                        "Debe proporcionar una tasa personalizada si marcó la opción 'Personalizado'."
                    )
                }
            )

        # Optional: Clear the custom rate if is_custom is unchecked
        if not self.is_custom and self.exchange_custom_rate is not None:
            self.exchange_custom_rate = None
