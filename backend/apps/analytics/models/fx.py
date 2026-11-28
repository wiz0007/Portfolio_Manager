import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from apps.portfolios.models.portfolio import (
    SUPPORTED_CURRENCY_CHOICES,
    validate_currency,
)


class FXRate(models.Model):
    """
    Authoritative Foreign Exchange (FX) rate observation.
    
    Quote Convention:
    1 unit of base_currency = rate units of quote_currency.
    Example: base_currency='USD', quote_currency='INR', rate=84.500000
    means 1 USD = 84.50 INR.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    base_currency = models.CharField(
        max_length=3,
        choices=SUPPORTED_CURRENCY_CHOICES,
        validators=[validate_currency],
        db_index=True,
    )
    quote_currency = models.CharField(
        max_length=3,
        choices=SUPPORTED_CURRENCY_CHOICES,
        validators=[validate_currency],
        db_index=True,
    )
    effective_date = models.DateField(db_index=True)
    rate = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        help_text="Units of quote_currency per 1 unit of base_currency",
    )
    source = models.CharField(
        max_length=64,
        default="RBI_REFERENCE",
        help_text="Originating provider or central bank reference (e.g., RBI_REFERENCE, ECB, COINGECKO)",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "analytics_fx_rates"
        ordering = ["-effective_date", "base_currency", "quote_currency"]
        indexes = [
            models.Index(fields=["base_currency", "quote_currency", "-effective_date"], name="fx_pair_date_idx"),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["base_currency", "quote_currency", "effective_date"],
                name="unique_fx_rate_per_day",
            ),
        ]

    def clean(self):
        super().clean()
        if self.base_currency and self.quote_currency:
            if self.base_currency.upper() == self.quote_currency.upper():
                raise ValidationError("base_currency and quote_currency cannot be identical.")
        if self.rate is not None and self.rate <= Decimal("0"):
            raise ValidationError({"rate": "Exchange rate must be strictly positive."})

    def save(self, *args, **kwargs):
        self.base_currency = self.base_currency.upper()
        self.quote_currency = self.quote_currency.upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"1 {self.base_currency} = {self.rate} {self.quote_currency} ({self.effective_date})"
