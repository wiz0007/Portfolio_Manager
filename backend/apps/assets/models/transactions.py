import uuid

from django.conf import settings
from django.db import models

from apps.portfolios.models import Portfolio

from .investment import Investment


class InvestmentTransaction(models.Model):
    """
    Immutable ledger entry recording an acquisition, buy, sell, payout, or fee
    associated with an investment holding.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='transactions',
        db_index=True,
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.CASCADE,
        related_name='investment_transactions',
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investment_transactions',
        db_index=True,
    )
    transaction_type = models.CharField(
        max_length=50,
        default='INITIAL_PURCHASE',
        help_text='BUY, INITIAL_PURCHASE, SELL, DIVIDEND, INTEREST, FEE',
    )
    transaction_date = models.DateField()
    units = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    price_per_unit = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    fees = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    currency = models.CharField(max_length=10, default='INR')
    notes = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'investment_transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['investment', '-transaction_date'], name='inv_tx_inv_date_idx'),
            models.Index(fields=['portfolio', '-transaction_date'], name='inv_tx_port_date_idx'),
        ]

    def __str__(self) -> str:
        return f"{self.transaction_type} {self.currency} {self.amount} for {self.investment.display_name}"
