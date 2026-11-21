import uuid

from django.conf import settings
from django.db import models

from .investment import Investment


class InvestmentValuation(models.Model):
    """
    Historical point-in-time valuation snapshot for an investment holding.
    Stores immutable valuation records with data provenance.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.ForeignKey(
        Investment,
        on_delete=models.PROTECT,
        related_name='valuations',
        db_index=True,
    )
    valuation_date = models.DateField(db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    currency = models.CharField(max_length=10, default='INR')
    valuation_method = models.CharField(max_length=50, default='MANUAL', db_index=True)
    source = models.CharField(max_length=100, default='MANUAL')
    source_reference = models.CharField(max_length=128, blank=True, default='')
    observed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='recorded_valuations',
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'investment_valuations'
        ordering = ['-valuation_date', '-created_at']
        indexes = [
            models.Index(fields=['investment', '-valuation_date'], name='inv_val_inv_date_idx'),
            models.Index(fields=['investment', 'source', '-created_at'], name='inv_val_src_created_idx'),
            models.Index(fields=['investment', 'valuation_method'], name='inv_val_meth_idx'),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding and self.pk:
            from django.core.exceptions import ValidationError
            raise ValidationError("Valuation snapshots are immutable point-in-time audit records and cannot be modified.")
        if self.amount is None or self.amount < 0:
            raise ValidationError({'amount': 'Valuation amount cannot be negative.'})
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError("Valuation snapshots cannot be deleted.")

    def __str__(self) -> str:
        return f"Valuation {self.currency} {self.amount} on {self.valuation_date} ({self.investment.display_name})"
