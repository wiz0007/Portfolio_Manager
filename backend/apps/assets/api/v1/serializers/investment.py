from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.assets.constants.asset_mapping import is_category_product_compatible
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
from apps.market_data.models.instrument import Instrument

from .detail_validators import (
    IMMUTABLE_RELATIONSHIP_FIELDS,
    check_no_immutable_fields,
    get_detail_validator,
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
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Investment
        fields = [
            'id',
            'portfolio',
            'instrument',
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
    instrument = serializers.PrimaryKeyRelatedField(read_only=True)
    details = serializers.SerializerMethodField()
    transactions = InvestmentTransactionSerializer(many=True, read_only=True)
    valuations = InvestmentValuationSerializer(many=True, read_only=True)

    class Meta:
        model = Investment
        fields = [
            'id',
            'portfolio',
            'instrument',
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
    instrument = serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    details = serializers.JSONField(write_only=True, required=False, default=dict)
    display_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    initial_value = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)
    current_value = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)

    class Meta:
        model = Investment
        fields = [
            'id',
            'portfolio',
            'instrument',
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

        category = attrs.get('category')
        asset_type = attrs.get('asset_type')

        # Strictly enforce authoritative category and product compatibility
        if category and asset_type and not is_category_product_compatible(category, asset_type):
            raise serializers.ValidationError(
                {'category': f"Category '{category}' is incompatible with asset type '{asset_type}'."}
            )

        instrument = attrs.get('instrument')
        if instrument and category:
            compat_map = {
                'equity': ['EQUITY', 'INDEX'],
                'mutual_funds': ['MUTUAL_FUND'],
                'gold': ['COMMODITY'],
                'fixed_income': ['FIXED_INCOME'],
                'crypto': ['CRYPTO'],
            }
            allowed = compat_map.get(category, [])
            if instrument.asset_class not in allowed:
                raise serializers.ValidationError(
                    {'instrument': f"Instrument asset class '{instrument.asset_class}' is incompatible with category '{category}'."}
                )

        # Validate category-specific details payload
        raw_details = self.initial_data.get('details') or {}
        if not isinstance(raw_details, dict):
            raise serializers.ValidationError({'details': 'Details must be an object.'})

        # Sanitize empty string values for numeric fields commonly emitted by HTML forms
        clean_details = {}
        for k, v in raw_details.items():
            if v == '' and k in (
                'interest_rate_pct', 'interest_rate', 'overdraft_limit',
                'sweep_out_threshold', 'sweep_retained_balance', 'sweep_increment',
                'area', 'land_area', 'brokerage', 'stt_charges', 'gst_paid',
                'gst_amount', 'network_fees', 'tenure_value', 'tenure_months',
                'coupon_rate_pct', 'other_acquisition_costs', 'stamp_duty',
                'registration_charges', 'making_charges'
            ):
                continue
            clean_details[k] = v

        check_no_immutable_fields(clean_details, is_creation=True)
        validator_cls = get_detail_validator(category, asset_type, is_creation=True)
        if validator_cls:
            validator = validator_cls(data=clean_details)
            if not validator.is_valid():
                raise serializers.ValidationError({'details': validator.errors})
            # Store validated details preserving original raw inputs
            self._validated_details = {**clean_details, **validator.validated_data}
        else:
            self._validated_details = clean_details

        return attrs

    def create(self, validated_data):
        details_data = getattr(self, '_validated_details', {}) or validated_data.pop('details', {}) or {}
        validated_data.pop('details', None)
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

        initial_val = validated_data.get('initial_value')
        current_val = validated_data.get('current_value')

        with transaction.atomic():
            investment = Investment.objects.create(
                user=user,
                **validated_data
            )

            tx_gross = Decimal('0')
            tx_fees = Decimal('0')
            tx_taxes = Decimal('0')
            tx_net = Decimal('0')
            tx_date = timezone.now().date()
            tx_units = Decimal('0')
            tx_price = Decimal('0')
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
                tx_gross = cur_bal
                tx_net = cur_bal
                tx_date = b_date
                investment.initial_value = cur_bal
                investment.current_value = cur_bal

            elif category == 'fixed_income':
                if asset_type in ('bond_holding', 'corporate_bond', 'sovereign_bond', 'bond', 'government_bond'):
                    face_val = Decimal(str(details_data.get('face_value', 1000)))
                    p_price = Decimal(str(details_data.get('purchase_price', face_val)))
                    qty = Decimal(str(details_data.get('quantity', 1)))
                    p_date = details_data.get('purchase_date') or timezone.now().date()
                    BondDetail.objects.create(
                        investment=investment,
                        bond_name=details_data.get('bond_name', display_name),
                        issuer_name=details_data.get('issuer', details_data.get('issuer_name', 'Unknown Issuer')),
                        bond_type=details_data.get('bond_type', 'SOVEREIGN'),
                        isin=details_data.get('isin', ''),
                        face_value=face_val,
                        purchase_price=p_price,
                        quantity=qty,
                        coupon_rate_pct=Decimal(str(details_data.get('coupon_rate_pct', 0))),
                        coupon_frequency=details_data.get('coupon_frequency', 'ANNUALLY'),
                        purchase_date=p_date,
                        maturity_date=details_data.get('maturity_date') or p_date,
                        credit_rating=details_data.get('credit_rating', ''),
                    )
                    cost = p_price * qty
                    tx_gross = cost
                    tx_net = cost
                    tx_date = p_date
                    tx_units = qty
                    tx_price = p_price
                    if not initial_val:
                        investment.initial_value = cost
                    if not current_val:
                        investment.current_value = cost
                else:
                    princ = Decimal(str(details_data.get('principal_amount', 0)))
                    s_date = details_data.get('start_date') or timezone.now().date()
                    tenure_val = details_data.get('tenure_value') or details_data.get('tenure_months', 12)
                    tenure_u = details_data.get('tenure_unit', 'YEARS' if details_data.get('tenure_value') else 'MONTHS')
                    DepositDetail.objects.create(
                        investment=investment,
                        institution_name=details_data.get('institution_name', details_data.get('bank_name', 'Bank')),
                        deposit_nickname=details_data.get('deposit_nickname', ''),
                        deposit_type=details_data.get('deposit_type', 'FIXED_DEPOSIT'),
                        deposit_number=details_data.get('deposit_number', ''),
                        principal_amount=princ,
                        monthly_installment=details_data.get('monthly_installment'),
                        start_date=s_date,
                        tenure_value=Decimal(str(tenure_val)),
                        tenure_unit=tenure_u,
                        interest_rate_pct=Decimal(str(details_data.get('interest_rate_pct', 6))),
                        compounding_frequency=details_data.get('compounding_frequency', 'QUARTERLY'),
                        payout_type=details_data.get('payout_type', 'CUMULATIVE'),
                        maturity_date=details_data.get('maturity_date'),
                        maturity_amount=details_data.get('maturity_amount'),
                        is_senior_citizen=bool(details_data.get('is_senior_citizen', False)),
                        is_tax_saver=bool(details_data.get('is_tax_saver', False)),
                        auto_renewal=bool(details_data.get('auto_renewal', details_data.get('auto_renew', False))),
                    )
                    tx_gross = princ
                    tx_net = princ
                    tx_date = s_date
                    if not initial_val:
                        investment.initial_value = princ
                    if not current_val:
                        investment.current_value = princ

            elif category == 'equity':
                qty = Decimal(str(details_data.get('quantity', 0)))
                buy_price = Decimal(str(details_data.get('purchase_price') or details_data.get('purchase_price_per_share') or details_data.get('average_buy_price') or details_data.get('buy_price', 0)))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                fees = Decimal(str(details_data.get('brokerage') or details_data.get('brokerage_fees', 0)))
                taxes = Decimal(str(details_data.get('stt_charges') or details_data.get('statutory_taxes', 0)))
                EquityDetail.objects.create(
                    investment=investment,
                    company_name=details_data.get('stock_name', details_data.get('company_name', display_name)),
                    symbol=details_data.get('ticker_symbol', details_data.get('symbol', 'UNKNOWN')),
                    exchange=details_data.get('exchange', 'NSE'),
                    isin=details_data.get('isin', ''),
                    quantity=qty,
                    average_buy_price=buy_price,
                    purchase_date=p_date,
                    brokerage_fees=fees,
                    statutory_taxes=taxes,
                )
                gross = qty * buy_price
                total_cost = gross + fees + taxes
                tx_gross = gross
                tx_fees = fees
                tx_taxes = taxes
                tx_net = total_cost
                tx_date = p_date
                tx_units = qty
                tx_price = buy_price
                investment.initial_value = total_cost
                investment.current_value = gross

            elif category == 'mutual_funds':
                units = Decimal(str(details_data.get('units', 0)))
                nav = Decimal(str(details_data.get('purchase_nav', details_data.get('average_purchase_nav', 0))))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                MutualFundDetail.objects.create(
                    investment=investment,
                    amc_name=details_data.get('amc_name', 'AMC'),
                    scheme_name=details_data.get('scheme_name', display_name),
                    plan=details_data.get('plan_type', details_data.get('plan', 'DIRECT')),
                    folio_number=details_data.get('folio_number', ''),
                    units=units,
                    average_purchase_nav=nav,
                    purchase_date=p_date,
                    is_sip=bool(details_data.get('is_sip', False)),
                    sip_amount=details_data.get('sip_amount'),
                    sip_frequency=details_data.get('sip_frequency', ''),
                )
                invested = units * nav
                tx_gross = invested
                tx_net = invested
                tx_date = p_date
                tx_units = units
                tx_price = nav
                if not initial_val:
                    investment.initial_value = invested
                if not current_val:
                    investment.current_value = invested

            elif category == 'gold':
                p_price = Decimal(str(details_data.get('purchase_price_per_gram', details_data.get('purchase_price', 0))))
                p_date = details_data.get('purchase_date') or timezone.now().date()
                making = Decimal(str(details_data.get('making_charges', 0)))
                gst = Decimal(str(details_data.get('gst_paid', details_data.get('gst_amount', 0))))
                weight = details_data.get('gross_weight_grams') or details_data.get('weight_grams')
                weight_dec = Decimal(str(weight)) if weight is not None else None
                GoldDetail.objects.create(
                    investment=investment,
                    item_name=details_data.get('item_name', display_name),
                    gold_type=details_data.get('form_factor', details_data.get('gold_type', 'PHYSICAL')),
                    weight_grams=weight_dec,
                    purity_karat=Decimal(str(details_data.get('purity_karats', details_data.get('purity_karat', 24)))),
                    purchase_price=p_price,
                    purchase_date=p_date,
                    making_charges=making,
                    gst_amount=gst,
                    sgb_series=details_data.get('sgb_series', ''),
                    coupon_rate_pct=details_data.get('coupon_rate_pct'),
                    maturity_date=details_data.get('maturity_date'),
                )
                if 'purchase_price_per_gram' in details_data and weight_dec:
                    base_cost = weight_dec * p_price
                else:
                    base_cost = p_price
                total_gold_cost = base_cost + making + gst
                tx_gross = base_cost
                tx_fees = making
                tx_taxes = gst
                tx_net = total_gold_cost
                tx_date = p_date
                tx_units = weight_dec or Decimal('1')
                tx_price = p_price
                if not initial_val:
                    investment.initial_value = total_gold_cost
                if not current_val:
                    investment.current_value = base_cost

            elif category == 'real_estate':
                units_val = details_data.get('units') or details_data.get('quantity')
                area_val = (
                    units_val
                    if asset_type == 'reit' and units_val is not None
                    else (details_data.get('area_value') or details_data.get('land_area') or details_data.get('built_up_area') or details_data.get('area'))
                )
                p_price = Decimal(str(details_data.get('purchase_price', 0)))
                acq_date = details_data.get('acquisition_date') or details_data.get('purchase_date') or timezone.now().date()
                stamp = Decimal(str(details_data.get('stamp_duty_paid', details_data.get('stamp_duty', 0))))
                reg = Decimal(str(details_data.get('registration_charges', details_data.get('registration_fee_paid', 0))))
                other_costs = Decimal(str(details_data.get('other_acquisition_costs', 0)))
                pct = Decimal(str(details_data.get('ownership_percentage', 100)))
                est_val = details_data.get('estimated_current_value')
                renovation = Decimal(str(details_data.get('renovation_expenses', 0)))
                rental = Decimal(str(details_data.get('monthly_rental_income', 0)))
                appreciation = details_data.get('expected_annual_appreciation')
                apprec_dec = Decimal(str(appreciation)) if appreciation is not None else None

                prop_type_default = 'REIT' if asset_type == 'reit' else ('LAND' if asset_type == 'land_plot' else 'RESIDENTIAL')
                area_unit_default = 'UNITS' if asset_type == 'reit' else ('ACRE' if asset_type == 'land_plot' else 'SQ_FT')
                RealEstateDetail.objects.create(
                    investment=investment,
                    property_name=details_data.get('property_nickname', details_data.get('property_name', display_name)),
                    property_type=details_data.get('property_type', prop_type_default),
                    land_classification=details_data.get('land_classification', ''),
                    property_use=details_data.get('property_use', ''),
                    country=details_data.get('country', 'India'),
                    state=details_data.get('state', 'Uttarakhand'),
                    city=details_data.get('city', ''),
                    district=details_data.get('district', ''),
                    tehsil=details_data.get('tehsil', ''),
                    locality=details_data.get('locality', ''),
                    village=details_data.get('village', ''),
                    survey_or_plot_number=details_data.get('khasra_number', details_data.get('survey_or_plot_number', '')),
                    address_line=details_data.get('address_line', ''),
                    area=Decimal(str(area_val)) if area_val is not None else None,
                    area_unit=details_data.get('area_unit', area_unit_default),
                    ownership_percentage=pct,
                    purchase_price=p_price,
                    acquisition_date=acq_date,
                    stamp_duty=stamp,
                    registration_charges=reg,
                    other_acquisition_costs=other_costs,
                    renovation_expenses=renovation,
                    monthly_rental_income=rental,
                    estimated_current_value=Decimal(str(est_val)) if est_val is not None else None,
                    valuation_date=details_data.get('last_appraisal_date') or acq_date,
                    valuation_source=details_data.get('valuation_source', details_data.get('valuation_method', 'USER_ESTIMATE')),
                    expected_annual_appreciation=apprec_dec,
                )
                total_outlay = ((p_price + stamp + reg + other_costs) * pct) / Decimal('100')
                tx_gross = (p_price * pct) / Decimal('100')
                tx_fees = ((stamp + reg + other_costs) * pct) / Decimal('100')
                tx_net = total_outlay
                tx_date = acq_date
                if not initial_val:
                    investment.initial_value = total_outlay
                if not current_val:
                    if est_val:
                        val_amount = (Decimal(str(est_val)) * pct) / Decimal('100')
                        investment.current_value = val_amount
                        val_date = details_data.get('last_appraisal_date') or acq_date
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
                tx_gross = qty * p_price
                tx_fees = fees
                tx_net = crypto_cost
                tx_date = p_date
                tx_units = qty
                tx_price = p_price
                if not initial_val:
                    investment.initial_value = crypto_cost
                if not current_val:
                    investment.current_value = qty * p_price

            investment.save(update_fields=['display_name', 'initial_value', 'current_value'])

            # Create initial transaction ledger record idempotently with canonical contract
            if not InvestmentTransaction.objects.filter(investment=investment, transaction_type='INITIAL_PURCHASE').exists():
                InvestmentTransaction.objects.create(
                    investment=investment,
                    portfolio=portfolio,
                    user=user,
                    transaction_type='INITIAL_PURCHASE',
                    transaction_date=tx_date,
                    units=tx_units,
                    price_per_unit=tx_price,
                    amount=tx_gross,
                    gross_amount=tx_gross,
                    fees=tx_fees,
                    taxes=tx_taxes,
                    net_cash_flow=tx_net,
                    currency=investment.currency,
                    notes='Initial acquisition position recorded at asset creation.',
                )

            # Record initial valuation snapshot
            InvestmentValuation.objects.create(
                investment=investment,
                valuation_date=val_date or tx_date,
                amount=val_amount if val_amount is not None else investment.current_value,
                currency=investment.currency,
                valuation_method=investment.valuation_method,
                source=details_data.get('valuation_source', 'MANUAL'),
                notes='Initial recorded asset valuation.',
                created_by=user,
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

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        details = self.initial_data.get('details')
        if details is not None:
            if not isinstance(details, dict):
                raise serializers.ValidationError({'details': 'Details must be an object.'})
            check_no_immutable_fields(details, is_creation=False)
            # Revalidate using category-specific validator in update mode
            instance = getattr(self, 'instance', None)
            if instance:
                validator_cls = get_detail_validator(instance.category, instance.asset_type, is_creation=False)
                if validator_cls:
                    val = validator_cls(data=details, partial=True)
                    if not val.is_valid():
                        raise serializers.ValidationError({'details': val.errors})
                    self._validated_details = {**details, **val.validated_data}
        return attrs

    def update(self, instance: Investment, validated_data):
        details_data = getattr(self, '_validated_details', None) or validated_data.pop('details', None)
        validated_data.pop('details', None)

        with transaction.atomic():
            old_current_val = instance.current_value
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()

            # Record new valuation snapshot if current_value was explicitly modified
            new_current_val = validated_data.get('current_value')
            if new_current_val is not None and new_current_val != old_current_val:
                request = self.context.get('request')
                user = request.user if request else None
                InvestmentValuation.objects.create(
                    investment=instance,
                    valuation_date=timezone.now().date(),
                    amount=new_current_val,
                    currency=instance.currency,
                    valuation_method=instance.valuation_method,
                    source='MANUAL_UPDATE',
                    notes='Updated via investment edit.',
                    created_by=user,
                )

            # Securely update child details if provided
            if details_data and isinstance(details_data, dict):
                detail_model = None
                for attr_name in [
                    'cash_detail',
                    'deposit_detail',
                    'bond_detail',
                    'equity_detail',
                    'mutual_fund_detail',
                    'gold_detail',
                    'real_estate_detail',
                    'crypto_detail',
                ]:
                    if hasattr(instance, attr_name):
                        detail_model = getattr(instance, attr_name)
                        break

                if detail_model:
                    # Explicit whitelist of non-relational fields
                    model_field_names = {
                        f.name for f in detail_model._meta.get_fields()
                        if not f.is_relation and f.name not in IMMUTABLE_RELATIONSHIP_FIELDS
                    }
                    for k, v in details_data.items():
                        if k in model_field_names:
                            setattr(detail_model, k, v)
                    detail_model.save()

        return instance
