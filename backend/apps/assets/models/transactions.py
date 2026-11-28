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
        on_delete=models.PROTECT,
        related_name='transactions',
        db_index=True,
    )
    portfolio = models.ForeignKey(
        Portfolio,
        on_delete=models.PROTECT,
        related_name='investment_transactions',
        db_index=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
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
    reversal_of = models.OneToOneField(
        'self',
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='reversed_by',
        help_text='Reference to original transaction if this transaction is a reversal',
    )
    reversal_reason = models.TextField(blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'investment_transactions'
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['investment', '-transaction_date'], name='inv_tx_inv_date_idx'),
            models.Index(fields=['portfolio', '-transaction_date'], name='inv_tx_port_date_idx'),
        ]

    def clean(self):
        from decimal import Decimal

        from django.core.exceptions import ValidationError

        super().clean()
        errors = {}
        if self.investment_id and self.portfolio_id and self.investment.portfolio_id != self.portfolio_id:
            errors['portfolio'] = 'Transaction portfolio must match the investment portfolio.'
        if self.investment_id and self.user_id and self.investment.user_id != self.user_id:
            errors['user'] = 'Transaction owner must match the investment owner.'
        if self.portfolio_id and self.user_id and self.portfolio.user_id != self.user_id:
            errors['portfolio'] = 'Transaction portfolio must belong to the transaction owner.'
        if self.amount is not None and self.amount < Decimal('0'):
            errors['amount'] = 'Transaction amount cannot be negative.'
        if self.gross_amount is not None and self.gross_amount < Decimal('0'):
            errors['gross_amount'] = 'Gross amount cannot be negative.'
        if self.fees is not None and self.fees < Decimal('0'):
            errors['fees'] = 'Fees cannot be negative.'
        if self.taxes is not None and self.taxes < Decimal('0'):
            errors['taxes'] = 'Taxes cannot be negative.'
        if self.units is not None and self.units < Decimal('0'):
            errors['units'] = 'Units cannot be negative.'
        if self.price_per_unit is not None and self.price_per_unit < Decimal('0'):
            errors['price_per_unit'] = 'Price per unit cannot be negative.'
        if self.reversal_of_id:
            if self.reversal_of.reversal_of_id:
                errors['reversal_of'] = 'Cannot reverse a transaction that is itself a reversal.'
            if self.investment_id and self.reversal_of.investment_id != self.investment_id:
                errors['reversal_of'] = 'Reversal investment must match original transaction investment.'
            if self.user_id and self.reversal_of.user_id != self.user_id:
                errors['reversal_of'] = 'Reversal owner must match original transaction owner.'
            if self.portfolio_id and self.reversal_of.portfolio_id != self.portfolio_id:
                errors['reversal_of'] = 'Reversal portfolio must match original transaction portfolio.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        from decimal import Decimal

        from django.core.exceptions import ValidationError

        if not self._state.adding and self.pk:
            raise ValidationError("Existing investment transaction records are immutable and cannot be modified.")

        if self.gross_amount is None:
            self.gross_amount = self.amount or Decimal('0')
        if self.amount is None:
            self.amount = self.gross_amount or Decimal('0')
        if self.net_cash_flow is None:
            if self.transaction_type == 'REVERSAL' and self.reversal_of_id:
                orig_net = self.reversal_of.net_cash_flow or self.reversal_of.amount or Decimal('0')
                self.net_cash_flow = -orig_net
            else:
                gross = self.gross_amount or Decimal('0')
                f = self.fees or Decimal('0')
                t = self.taxes or Decimal('0')
                if self.transaction_type in ('BUY', 'INITIAL_PURCHASE', 'DEPOSIT'):
                    self.net_cash_flow = gross + f + t
                elif self.transaction_type in ('SELL', 'WITHDRAWAL'):
                    self.net_cash_flow = gross - f - t
                else:
                    self.net_cash_flow = gross

        FOUR_PLACES = Decimal('0.0001')
        for field in ('amount', 'gross_amount', 'net_cash_flow', 'fees', 'taxes', 'units', 'price_per_unit'):
            val = getattr(self, field, None)
            if val is not None and isinstance(val, Decimal):
                setattr(self, field, val.quantize(FOUR_PLACES))

        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        from django.core.exceptions import ValidationError
        raise ValidationError("Investment transactions cannot be deleted. Use a reversal or adjustment transaction.")

    def __str__(self) -> str:
        return f"{self.transaction_type} {self.currency} {self.amount} for {self.investment.display_name}"
