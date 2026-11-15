import uuid

from django.db import models

from .investment import Investment


class InvestmentValuation(models.Model):
    """
    Historical point-in-time valuation snapshot for an investment holding.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='valuations',
        db_index=True,
    )
    valuation_date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    source = models.CharField(max_length=100, default='MANUAL')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'investment_valuations'
        ordering = ['-valuation_date', '-created_at']
        indexes = [
            models.Index(fields=['investment', '-valuation_date'], name='inv_val_inv_date_idx'),
        ]

    def __str__(self) -> str:
        return f"Valuation {self.amount} on {self.valuation_date} ({self.investment.display_name})"
