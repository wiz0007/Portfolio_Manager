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
    gross_amount = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Gross consideration before costs',
    )
    fees = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    taxes = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=0,
        help_text='Applicable transaction taxes or stamp duty',
    )
    net_cash_flow = models.DecimalField(
        max_digits=18,
        decimal_places=4,
        null=True,
        blank=True,
        help_text='Net cash flow: gross + fees + taxes for purchase, gross - fees - taxes for sale',
    )
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

    def save(self, *args, **kwargs):
        from decimal import Decimal

        if self.gross_amount is None:
            self.gross_amount = self.amount or Decimal('0')
        if self.amount is None:
            self.amount = self.gross_amount or Decimal('0')
        if self.net_cash_flow is None:
            gross = self.gross_amount or Decimal('0')
            f = self.fees or Decimal('0')
            t = self.taxes or Decimal('0')
            if self.transaction_type in ('BUY', 'INITIAL_PURCHASE', 'DEPOSIT'):
                self.net_cash_flow = gross + f + t
            elif self.transaction_type in ('SELL', 'WITHDRAWAL'):
                self.net_cash_flow = gross - f - t
            else:
                self.net_cash_flow = gross
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.transaction_type} {self.currency} {self.amount} for {self.investment.display_name}"
