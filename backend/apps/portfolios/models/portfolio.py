import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

SUPPORTED_CURRENCIES = [
    'INR',
    'USD',
    'EUR',
    'GBP',
    'JPY',
    'AUD',
    'CAD',
    'SGD',
    'CHF',
    'AED',
]

SUPPORTED_CURRENCY_CHOICES = [(c, c) for c in SUPPORTED_CURRENCIES]


def validate_currency(value: str):
    if value.upper() not in SUPPORTED_CURRENCIES:
        raise ValidationError(
            f"Unsupported currency '{value}'. Supported currencies: {', '.join(SUPPORTED_CURRENCIES)}."
        )


class Portfolio(models.Model):
    """
    User portfolio representing an investment container.
    Scoped strictly to a single authenticated user.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='portfolios',
        db_index=True,
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, default='')
    base_currency = models.CharField(
        max_length=3,
        default='INR',
        choices=SUPPORTED_CURRENCY_CHOICES,
        validators=[validate_currency],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portfolios'
        verbose_name = 'portfolio'
        verbose_name_plural = 'portfolios'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='portfolio_user_created_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.base_currency})"

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
        if self.base_currency:
            self.base_currency = self.base_currency.upper()
