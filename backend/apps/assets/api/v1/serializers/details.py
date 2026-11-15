from rest_framework import serializers

from apps.assets.models import (
    BondDetail,
    CashAccountDetail,
    CryptoDetail,
    DepositDetail,
    EquityDetail,
    GoldDetail,
    InvestmentTransaction,
    InvestmentValuation,
    MutualFundDetail,
    RealEstateDetail,
)


class CashAccountDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashAccountDetail
        exclude = ['investment']


class DepositDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositDetail
        exclude = ['investment']


class BondDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BondDetail
        exclude = ['investment']


class EquityDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EquityDetail
        exclude = ['investment']


class MutualFundDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MutualFundDetail
        exclude = ['investment']


class GoldDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldDetail
        exclude = ['investment']


class RealEstateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = RealEstateDetail
        exclude = ['investment']


class CryptoDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CryptoDetail
        exclude = ['investment']


class InvestmentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentTransaction
        fields = [
            'id',
            'transaction_type',
            'transaction_date',
            'units',
            'price_per_unit',
            'amount',
            'fees',
            'currency',
            'notes',
            'created_at',
        ]


class InvestmentValuationSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentValuation
        fields = [
            'id',
            'valuation_date',
            'amount',
            'source',
            'notes',
            'created_at',
        ]
