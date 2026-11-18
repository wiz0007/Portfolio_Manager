import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class WatchlistItem(models.Model):
    """
    User-specific watchlist relationship to a canonical financial instrument.
    Tracks user-defined targets and notes while resolving live market prices
    strictly through the central market data resolver.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist_items',
        db_index=True,
    )
    instrument = models.ForeignKey(
        'market_data.Instrument',
        on_delete=models.CASCADE,
        related_name='watched_by',
        db_index=True,
    )
    notes = models.TextField(blank=True, default='')
    target_price = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Optional user-defined price alert trigger threshold.',
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'watchlist_items'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'instrument'],
                name='unique_user_instrument_watchlist',
            )
        ]
        indexes = [
            models.Index(fields=['user', '-created_at'], name='watchlist_user_created_idx'),
            models.Index(fields=['instrument'], name='watchlist_inst_idx'),
        ]

    def clean(self):
        super().clean()
        if self.target_price is not None and self.target_price <= Decimal('0'):
            raise ValidationError({'target_price': 'Target price must be strictly positive.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Watchlist({self.user.email} -> {self.instrument.symbol})"
