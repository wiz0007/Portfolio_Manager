from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.assets.models import (
    BondDetail,
    CashAccountDetail,
    CryptoDetail,
    DepositDetail,
    EquityDetail,
    GoldDetail,
    Investment,
    InvestmentTransaction,
    InvestmentValuation,
    MutualFundDetail,
    RealEstateDetail,
)

from .details import (
    BondDetailSerializer,
    CashAccountDetailSerializer,
    CryptoDetailSerializer,
    DepositDetailSerializer,
    EquityDetailSerializer,
    GoldDetailSerializer,
    InvestmentTransactionSerializer,
    InvestmentValuationSerializer,
    MutualFundDetailSerializer,
    RealEstateDetailSerializer,
)


class InvestmentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Investment
        fields = [
            'id',
            'portfolio',
            'category',
            'asset_type',
            'display_name',
            'currency',
            'is_active',
            'valuation_method',
            'initial_value',
            'current_value',
            'notes',
            'created_at',
            'updated_at',
        ]


class InvestmentDetailSerializer(serializers.ModelSerializer):
    details = serializers.SerializerMethodField()
    transactions = InvestmentTransactionSerializer(many=True, read_only=True)
    valuations = InvestmentValuationSerializer(many=True, read_only=True)

    class Meta:
        model = Investment
        fields = [
            'id',
            'portfolio',
            'category',
            'asset_type',
            'display_name',
            'currency',
            'is_active',
            'valuation_method',
            'initial_value',
            'current_value',
            'notes',
            'details',
            'transactions',
            'valuations',
            'created_at',
            'updated_at',
        ]

    def get_details(self, obj: Investment):
        if hasattr(obj, 'cash_detail'):
            return CashAccountDetailSerializer(obj.cash_detail).data
        if hasattr(obj, 'deposit_detail'):
            return DepositDetailSerializer(obj.deposit_detail).data
        if hasattr(obj, 'bond_detail'):
            return BondDetailSerializer(obj.bond_detail).data
        if hasattr(obj, 'equity_detail'):
            return EquityDetailSerializer(obj.equity_detail).data
        if hasattr(obj, 'mutual_fund_detail'):
            return MutualFundDetailSerializer(obj.mutual_fund_detail).data
        if hasattr(obj, 'gold_detail'):
            return GoldDetailSerializer(obj.gold_detail).data
        if hasattr(obj, 'real_estate_detail'):
            return RealEstateDetailSerializer(obj.real_estate_detail).data
        if hasattr(obj, 'crypto_detail'):
            return CryptoDetailSerializer(obj.crypto_detail).data
        return None


class InvestmentCreateSerializer(serializers.ModelSerializer):
    details = serializers.JSONField(write_only=True, required=False, default=dict)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    initial_value = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)
    current_value = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)

    class Meta:
        model = Investment
        fields = [
            'id',
            'portfolio',
            'category',
            'asset_type',
            'display_name',
            'currency',
            'notes',
            'valuation_method',
            'initial_value',
            'current_value',
            'details',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        portfolio = attrs.get('portfolio')

        if request and portfolio:
            if portfolio.user_id != request.user.id:
                raise serializers.ValidationError(
                    {'portfolio': 'Portfolio not found or unauthorized.'}
                )

        return attrs

    def create(self, validated_data):
        details_data = validated_data.pop('details', {}) or {}
        user = self.context['request'].user
        category = validated_data.get('category')
        asset_type = validated_data.get('asset_type')
        portfolio = validated_data.get('portfolio')

        # Derive display name if not provided
        display_name = validated_data.get('display_name')
        if not display_name:
            if details_data.get('symbol') and details_data.get('company_name'):
                display_name = f"{details_data.get('company_name')} ({details_data.get('symbol')})"
            else:
                display_name = (
                    details_data.get('account_nickname')
                    or details_data.get('deposit_nickname')
                    or details_data.get('company_name')
                    or details_data.get('symbol')
                    or details_data.get('scheme_name')
                    or details_data.get('item_name')
                    or details_data.get('property_name')
                    or details_data.get('token_name')
                    or f"{asset_type.replace('_', ' ').title()}"
                )
            validated_data['display_name'] = display_name

        # Calculate initial & current value from details if not set
        initial_val = validated_data.get('initial_value')
        current_val = validated_data.get('current_value')

        with transaction.atomic():
            investment = Investment.objects.create(
                user=user,
                **validated_data
            )

            # Persist asset detail model based on category
            tx_amount = Decimal('0')
            tx_date = timezone.now().date()
            val_amount = None
            val_date = None

            if category == 'cash':
                cur_bal = Decimal(str(details_data.get('current_balance', 0)))
                b_date = details_data.get('balance_date') or timezone.now().date()
                CashAccountDetail.objects.create(
                    investment=investment,
                    bank_name=details_data.get('bank_name', 'Unknown Bank'),
                    account_nickname=details_data.get('account_nickname', ''),
                    account_type=details_data.get('account_type', 'SAVINGS'),
                    masked_account_number=details_data.get('masked_account_number', ''),
                    current_balance=cur_bal,
                    balance_date=b_date,
                    interest_rate_pct=Decimal(str(details_data.get('interest_rate_pct', 0))),
                    interest_credit_frequency=details_data.get('interest_credit_frequency', 'QUARTERLY'),
                    auto_sweep_enabled=bool(details_data.get('auto_sweep_enabled', False)),
                    sweep_out_threshold=details_data.get('sweep_out_threshold'),
                    sweep_retained_balance=details_data.get('sweep_retained_balance'),
                    sweep_increment=details_data.get('sweep_increment'),
                    overdraft_limit=Decimal(str(details_data.get('overdraft_limit', 0))),
                )
                tx_amount = cur_bal
                if not initial_val:
                    investment.initial_value = cur_bal
                if not current_val:
                    investment.current_value = cur_bal

            elif category == 'fixed_income':
                if asset_type == 'bond':
                    face_val = Decimal(str(details_data.get('face_value', 1000)))
                    p_price = Decimal(str(details_data.get('purchase_price', face_val)))
                    qty = Decimal(str(details_data.get('quantity', 1)))
                    p_date = details_data.get('purchase_date') or timezone.now().date()
                    BondDetail.objects.create(
                        investment=investment,
                        bond_name=details_data.get('bond_name', display_name),
                        issuer_name=details_data.get('issuer_name', 'Unknown Issuer'),
                        bond_type=details_data.get('bond_type', 'GOVERNMENT'),
                        isin=details_data.get('isin', ''),
                        face_value=face_val,
                        purchase_price=p_price,
                        quantity=qty,
                        coupon_rate_pct=Decimal(str(details_data.get('coupon_rate_pct', 0))),
                        coupon_frequency=details_data.get('coupon_frequency', 'SEMI_ANNUALLY'),
                        purchase_date=p_date,
                        maturity_date=details_data.get('maturity_date') or p_date,
                        credit_rating=details_data.get('credit_rating', ''),
                        yield_to_maturity_pct=details_data.get('yield_to_maturity_pct'),
                    )
                    cost = p_price * qty
                    tx_amount = cost
                    if not initial_val:
                        investment.initial_value = cost
                    if not current_val:
                        investment.current_value = cost
                else:
                    princ = Decimal(str(details_data.get('principal_amount', 0)))
                    s_date = details_data.get('start_date') or timezone.now().date()
                    DepositDetail.objects.create(
                        investment=investment,
                        institution_name=details_data.get('institution_name', 'Bank'),
                        deposit_nickname=details_data.get('deposit_nickname', ''),
                        deposit_type=details_data.get('deposit_type', 'FIXED_DEPOSIT'),
                        deposit_number=details_data.get('deposit_number', ''),
                        principal_amount=princ,
                        monthly_installment=details_data.get('monthly_installment'),
                        start_date=s_date,
                        tenure_value=Decimal(str(details_data.get('tenure_value', 1))),
                        tenure_unit=details_data.get('tenure_unit', 'YEARS'),
                        interest_rate_pct=Decimal(str(details_data.get('interest_rate_pct', 6))),
                        compounding_frequency=details_data.get('compounding_frequency', 'QUARTERLY'),
                        payout_type=details_data.get('payout_type', 'CUMULATIVE'),
                        maturity_date=details_data.get('maturity_date'),
                        maturity_amount=details_data.get('maturity_amount'),
                        is_senior_citizen=bool(details_data.get('is_senior_citizen', False)),
                        is_tax_saver=bool(details_data.get('is_tax_saver', False)),
                        auto_renewal=bool(details_data.get('auto_renewal', False)),
                    )
                    tx_amount = princ
                    if not initial_val:
                        investment.initial_value = princ
                    if not current_val:
                        investment.current_value = princ

            elif category == 'equity':
                qty = Decimal(str(details_data.get('quantity', 0)))
                buy_price = Decimal(str(details_data.get('average_buy_price', 0)))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                fees = Decimal(str(details_data.get('brokerage_fees', 0)))
                taxes = Decimal(str(details_data.get('statutory_taxes', 0)))
                EquityDetail.objects.create(
                    investment=investment,
                    company_name=details_data.get('company_name', display_name),
                    symbol=details_data.get('symbol', 'UNKNOWN'),
                    exchange=details_data.get('exchange', 'NSE'),
                    isin=details_data.get('isin', ''),
                    quantity=qty,
                    average_buy_price=buy_price,
                    purchase_date=p_date,
                    brokerage_fees=fees,
                    statutory_taxes=taxes,
                )
                total_cost = (qty * buy_price) + fees + taxes
                tx_amount = total_cost
                if not initial_val:
                    investment.initial_value = total_cost
                if not current_val:
                    investment.current_value = qty * buy_price

            elif category == 'mutual_funds':
                units = Decimal(str(details_data.get('units', 0)))
                nav = Decimal(str(details_data.get('average_purchase_nav', 0)))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                MutualFundDetail.objects.create(
                    investment=investment,
                    amc_name=details_data.get('amc_name', 'AMC'),
                    scheme_name=details_data.get('scheme_name', display_name),
                    scheme_category=details_data.get('scheme_category', ''),
                    plan=details_data.get('plan', 'DIRECT'),
                    option=details_data.get('option', 'GROWTH'),
                    folio_number=details_data.get('folio_number', ''),
                    units=units,
                    average_purchase_nav=nav,
                    purchase_date=p_date,
                    is_sip=bool(details_data.get('is_sip', False)),
                    sip_amount=details_data.get('sip_amount'),
                    sip_frequency=details_data.get('sip_frequency', ''),
                )
                invested = units * nav
                tx_amount = invested
                if not initial_val:
                    investment.initial_value = invested
                if not current_val:
                    investment.current_value = invested

            elif category == 'gold':
                p_price = Decimal(str(details_data.get('purchase_price', 0)))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                making = Decimal(str(details_data.get('making_charges', 0)))
                gst = Decimal(str(details_data.get('gst_amount', 0)))
                GoldDetail.objects.create(
                    investment=investment,
                    item_name=details_data.get('item_name', display_name),
                    gold_type=details_data.get('gold_type', 'PHYSICAL'),
                    weight_grams=details_data.get('weight_grams'),
                    purity_karat=details_data.get('purity_karat'),
                    purchase_price=p_price,
                    purchase_date=p_date,
                    making_charges=making,
                    gst_amount=gst,
                    platform_or_provider=details_data.get('platform_or_provider', ''),
                    sgb_series=details_data.get('sgb_series', ''),
                    coupon_rate_pct=details_data.get('coupon_rate_pct'),
                    maturity_date=details_data.get('maturity_date'),
                )
                total_gold_cost = p_price + making + gst
                tx_amount = total_gold_cost
                if not initial_val:
                    investment.initial_value = total_gold_cost
                if not current_val:
                    investment.current_value = p_price

            elif category == 'real_estate':
                p_price = Decimal(str(details_data.get('purchase_price', 0)))
                acq_date = details_data.get('acquisition_date') or details_data.get('purchase_date') or timezone.now().date()
                stamp = Decimal(str(details_data.get('stamp_duty', details_data.get('stamp_duty_paid', 0))))
                reg = Decimal(str(details_data.get('registration_charges', details_data.get('registration_fee_paid', 0))))
                other = Decimal(str(details_data.get('other_acquisition_costs', 0)))
                renov = Decimal(str(details_data.get('renovation_expenses', 0)))
                pct = Decimal(str(details_data.get('ownership_percentage', 100)))
                area_val = details_data.get('land_area') or details_data.get('built_up_area') or details_data.get('plot_area')
                est_val = details_data.get('estimated_current_value')

                RealEstateDetail.objects.create(
                    investment=investment,
                    property_name=details_data.get('property_name', display_name),
                    property_type=details_data.get('property_type', 'LAND' if asset_type == 'land_plot' else 'RESIDENTIAL'),
                    land_classification=details_data.get('land_classification', ''),
                    property_use=details_data.get('property_use', ''),
                    country=details_data.get('country', 'India'),
                    state=details_data.get('state', 'Uttarakhand'),
                    city=details_data.get('city', ''),
                    district=details_data.get('district', ''),
                    tehsil=details_data.get('tehsil', ''),
                    locality=details_data.get('locality', ''),
                    village=details_data.get('village', ''),
                    survey_or_plot_number=details_data.get('survey_or_plot_number', ''),
                    address_line=details_data.get('address_line', ''),
                    area=Decimal(str(area_val)) if area_val is not None else None,
                    area_unit=details_data.get('area_unit', 'ACRE' if asset_type == 'land_plot' else 'SQ_FT'),
                    ownership_percentage=pct,
                    purchase_price=p_price,
                    acquisition_date=acq_date,
                    stamp_duty=stamp,
                    registration_charges=reg,
                    other_acquisition_costs=other,
                    renovation_expenses=renov,
                    monthly_rental_income=Decimal(str(details_data.get('monthly_rental_income', 0))),
                    estimated_current_value=Decimal(str(est_val)) if est_val is not None else None,
                    valuation_date=details_data.get('valuation_date'),
                    valuation_source=details_data.get('valuation_source', ''),
                    expected_annual_appreciation=details_data.get('expected_annual_appreciation'),
                )
                total_outlay = ((p_price + stamp + reg + other + renov) * pct) / Decimal('100')
                tx_amount = total_outlay
                if not initial_val:
                    investment.initial_value = total_outlay
                if not current_val:
                    if est_val:
                        val_amount = (Decimal(str(est_val)) * pct) / Decimal('100')
                        investment.current_value = val_amount
                        val_date = details_data.get('valuation_date') or acq_date
                    else:
                        investment.current_value = total_outlay

            elif category == 'crypto':
                qty = Decimal(str(details_data.get('quantity', 0)))
                p_price = Decimal(str(details_data.get('purchase_price_per_token', 0)))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                fees = Decimal(str(details_data.get('network_fees', 0)))
                CryptoDetail.objects.create(
                    investment=investment,
                    token_name=details_data.get('token_name', display_name),
                    symbol=details_data.get('symbol', 'CRYPTO'),
                    network=details_data.get('network', 'Ethereum'),
                    contract_address=details_data.get('contract_address', ''),
                    quantity=qty,
                    purchase_price_per_token=p_price,
                    purchase_date=p_date,
                    wallet_type=details_data.get('wallet_type', ''),
                    exchange_name=details_data.get('exchange_name', ''),
                    network_fees=fees,
                    transaction_hash=details_data.get('transaction_hash', ''),
                )
                crypto_cost = (qty * p_price) + fees
                tx_amount = crypto_cost
                if not initial_val:
                    investment.initial_value = crypto_cost
                if not current_val:
                    investment.current_value = qty * p_price

            investment.save(update_fields=['display_name', 'initial_value', 'current_value'])

            # Create initial transaction ledger record
            InvestmentTransaction.objects.create(
                investment=investment,
                portfolio=portfolio,
                user=user,
                transaction_type='INITIAL_PURCHASE',
                transaction_date=tx_date,
                amount=tx_amount,
                currency=investment.currency,
                notes='Initial opening position recorded at asset creation.',
            )

            # Record valuation snapshot if present
            if val_amount is not None:
                InvestmentValuation.objects.create(
                    investment=investment,
                    valuation_date=val_date or tx_date,
                    amount=val_amount,
                    source=details_data.get('valuation_source', 'MANUAL'),
                    notes='Initial recorded asset valuation.',
                )

        return investment


class InvestmentUpdateSerializer(serializers.ModelSerializer):
    details = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Investment
        fields = [
            'id',
            'display_name',
            'is_active',
            'notes',
            'valuation_method',
            'current_value',
            'details',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']

    def update(self, instance: Investment, validated_data):
        details_data = validated_data.pop('details', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update child details if provided
        if details_data and isinstance(details_data, dict):
            if hasattr(instance, 'cash_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.cash_detail, k):
                        setattr(instance.cash_detail, k, v)
                instance.cash_detail.save()
            elif hasattr(instance, 'deposit_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.deposit_detail, k):
                        setattr(instance.deposit_detail, k, v)
                instance.deposit_detail.save()
            elif hasattr(instance, 'bond_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.bond_detail, k):
                        setattr(instance.bond_detail, k, v)
                instance.bond_detail.save()
            elif hasattr(instance, 'equity_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.equity_detail, k):
                        setattr(instance.equity_detail, k, v)
                instance.equity_detail.save()
            elif hasattr(instance, 'mutual_fund_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.mutual_fund_detail, k):
                        setattr(instance.mutual_fund_detail, k, v)
                instance.mutual_fund_detail.save()
            elif hasattr(instance, 'gold_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.gold_detail, k):
                        setattr(instance.gold_detail, k, v)
                instance.gold_detail.save()
            elif hasattr(instance, 'real_estate_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.real_estate_detail, k):
                        setattr(instance.real_estate_detail, k, v)
                instance.real_estate_detail.save()
            elif hasattr(instance, 'crypto_detail'):
                for k, v in details_data.items():
                    if hasattr(instance.crypto_detail, k):
                        setattr(instance.crypto_detail, k, v)
                instance.crypto_detail.save()

        return instance
