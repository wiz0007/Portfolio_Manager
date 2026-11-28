from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from apps.assets.models.transactions import InvestmentTransaction


class RecordTransactionSerializer(serializers.ModelSerializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)

    class Meta:
        model = InvestmentTransaction
        fields = [
            'id',
            'transaction_type',
            'transaction_date',
            'units',
            'price_per_unit',
            'amount',
            'gross_amount',
            'fees',
            'taxes',
            'notes',
        ]
        read_only_fields = ['id']

    def validate_transaction_date(self, value):
        today = timezone.now().date()
        if value > today:
            raise serializers.ValidationError("Future-dated transactions are not permitted.")
        return value

    def validate(self, attrs):
        tx_type = attrs.get('transaction_type', '').upper()
        allowed_types = {'BUY', 'SELL', 'DIVIDEND', 'INTEREST', 'FEE'}
        if tx_type not in allowed_types:
            raise serializers.ValidationError(
                f"Invalid transaction type '{tx_type}'. Allowed types: {', '.join(sorted(allowed_types))}."
            )

        units = attrs.get('units') or Decimal('0')
        price = attrs.get('price_per_unit') or Decimal('0')
        amt = attrs.get('amount') or attrs.get('gross_amount')

        if tx_type in ('BUY', 'SELL'):
            if units <= Decimal('0'):
                raise serializers.ValidationError({"units": "Units must be greater than zero for Buy/Sell transactions."})
            if price <= Decimal('0'):
                raise serializers.ValidationError({"price_per_unit": "Price per unit must be greater than zero."})
            if not amt:
                attrs['gross_amount'] = (units * price).quantize(Decimal('0.0001'))
                attrs['amount'] = attrs['gross_amount']

        return attrs
