from decimal import Decimal
from typing import Any, Dict

from django.utils import timezone
from rest_framework import serializers

from apps.assets.models import (
    BondDetail,
    CashAccountDetail,
    CryptoDetail,
    DepositDetail,
    EquityDetail,
    GoldDetail,
    MutualFundDetail,
    RealEstateDetail,
)

IMMUTABLE_RELATIONSHIP_FIELDS = {
    'id',
    'investment',
    'investment_id',
    'user',
    'user_id',
    'portfolio',
    'portfolio_id',
    'created_at',
    'updated_at',
}


def check_no_immutable_fields(data: Dict[str, Any], is_creation: bool = False):
    """
    Rejects attempted modifications or injections of immutable relationship fields.
    In creation mode, benign client echoes of portfolio/portfolio_id are permitted
    while investment/user hijacking is strictly blocked.
    """
    if not isinstance(data, dict):
        return
    forbidden = IMMUTABLE_RELATIONSHIP_FIELDS
    if is_creation:
        forbidden = IMMUTABLE_RELATIONSHIP_FIELDS - {'portfolio', 'portfolio_id'}
    intersect = set(data.keys()) & forbidden
    if intersect:
        errors = {
            f: "Relationship reassignment or modification of immutable field is strictly prohibited."
            for f in sorted(intersect)
        }
        raise serializers.ValidationError(errors)


class StrictBooleanValueField(serializers.BooleanField):
    """
    Enforces strict boolean validation without Python bool('false') == True pitfalls.
    """

    def to_internal_value(self, data):
        if isinstance(data, bool):
            return data
        if isinstance(data, str):
            val = data.strip().lower()
            if val in ('true', '1'):
                return True
            if val in ('false', '0'):
                return False
        raise serializers.ValidationError("Must be a valid boolean value (true/false).")


# =====================================================================
# 1. CASH / BANKING VALIDATORS
# =====================================================================

class CashAccountDetailCreateValidator(serializers.ModelSerializer):
    bank_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    account_nickname = serializers.CharField(max_length=100, required=False, allow_blank=True)
    account_type = serializers.CharField(max_length=50, required=False, allow_blank=True)
    current_balance = serializers.DecimalField(max_digits=18, decimal_places=4, required=True)
    balance_date = serializers.DateField(required=False)
    interest_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False, default=Decimal('0.00')
    )
    auto_sweep_enabled = StrictBooleanValueField(required=False, default=False)
    overdraft_limit = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.00'), required=False, default=Decimal('0.00')
    )

    class Meta:
        model = CashAccountDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if not attrs.get('balance_date'):
            attrs['balance_date'] = timezone.now().date()

        # Resolve account type without defaulting current account or physical cash to SAVINGS
        acc_type_raw = attrs.get('account_type') or self.initial_data.get('account_type')
        asset_type_ctx = self.context.get('asset_type', '')
        if acc_type_raw:
            attrs['account_type'] = str(acc_type_raw).upper()
        elif asset_type_ctx == 'current_account':
            attrs['account_type'] = 'CURRENT'
        elif asset_type_ctx in ('cash_balance', 'physical_cash'):
            attrs['account_type'] = 'PHYSICAL_CASH'
        else:
            attrs['account_type'] = 'SAVINGS'

        # Bank name is required for bank accounts; physical cash does not require a bank name
        if not attrs.get('bank_name'):
            if attrs['account_type'] in ('PHYSICAL_CASH', 'CASH_BALANCE', 'WALLET'):
                attrs['bank_name'] = 'Physical Cash'
            else:
                raise serializers.ValidationError({'bank_name': 'Bank name is required.'})

        balance = attrs.get('current_balance')
        acc_type = attrs.get('account_type', '').upper()
        if balance is not None and balance < Decimal('0.00') and acc_type != 'OVERDRAFT':
            raise serializers.ValidationError(
                {'current_balance': "Account balance cannot be negative unless account type is OVERDRAFT."}
            )
        if attrs.get('auto_sweep_enabled'):
            thresh = attrs.get('sweep_out_threshold')
            retained = attrs.get('sweep_retained_balance')
            if thresh is not None and retained is not None and thresh < retained:
                raise serializers.ValidationError(
                    {'sweep_out_threshold': "Sweep-out threshold cannot be less than retained balance."}
                )
        return attrs


class CashAccountDetailUpdateValidator(serializers.ModelSerializer):
    auto_sweep_enabled = StrictBooleanValueField(required=False)
    current_balance = serializers.DecimalField(max_digits=18, decimal_places=4, required=False)
    interest_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    overdraft_limit = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.00'), required=False
    )

    class Meta:
        model = CashAccountDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in CashAccountDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        balance = attrs.get('current_balance')
        acc_type = attrs.get('account_type', '').upper()
        if balance is not None and balance < Decimal('0.00') and acc_type != 'OVERDRAFT':
            raise serializers.ValidationError(
                {'current_balance': "Account balance cannot be negative unless account type is OVERDRAFT."}
            )
        return attrs


# =====================================================================
# 2. DEPOSIT VALIDATORS (FD / RD)
# =====================================================================

class DepositDetailCreateValidator(serializers.ModelSerializer):
    deposit_type = serializers.CharField(max_length=50, default='FIXED', required=False)
    tenure_unit = serializers.CharField(max_length=20, default='MONTHS', required=False)
    principal_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    interest_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    start_date = serializers.DateField(required=False)
    maturity_date = serializers.DateField(required=False, allow_null=True)
    tenure_value = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal('0.01'), required=False, allow_null=True
    )
    auto_renewal = StrictBooleanValueField(required=False, default=False)
    is_senior_citizen = StrictBooleanValueField(required=False, default=False)
    is_tax_saver = StrictBooleanValueField(required=False, default=False)

    # Common aliases
    bank_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    deposit_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    deposit_date = serializers.DateField(required=False)
    interest_rate = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    annual_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    installment_due_day = serializers.IntegerField(
        min_value=1, max_value=31, required=False, default=5
    )
    tenure_months = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal('0.01'), required=False
    )
    monthly_installment = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )

    class Meta:
        model = DepositDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        # Normalize aliases
        if 'deposit_amount' in attrs and 'principal_amount' not in attrs:
            attrs['principal_amount'] = attrs['deposit_amount']
        if 'monthly_installment' in attrs and 'principal_amount' not in attrs:
            attrs['principal_amount'] = attrs['monthly_installment']
        if 'deposit_date' in attrs and 'start_date' not in attrs:
            attrs['start_date'] = attrs['deposit_date']
        if 'interest_rate' in attrs and 'interest_rate_pct' not in attrs:
            attrs['interest_rate_pct'] = attrs['interest_rate']
        if 'annual_rate_pct' in attrs and 'interest_rate_pct' not in attrs:
            attrs['interest_rate_pct'] = attrs['annual_rate_pct']
        if 'bank_name' in attrs and 'institution_name' not in attrs:
            attrs['institution_name'] = attrs['bank_name']
        if 'tenure_months' in attrs and 'tenure_value' not in attrs:
            attrs['tenure_value'] = attrs['tenure_months']

        if not attrs.get('start_date'):
            attrs['start_date'] = timezone.now().date()

        # Enforce essential creation fields
        if not attrs.get('principal_amount'):
            raise serializers.ValidationError({'principal_amount': "Principal/deposit amount is required."})
        if attrs.get('interest_rate_pct') is None:
            raise serializers.ValidationError({'interest_rate_pct': "Interest rate percentage is required."})
        if not attrs.get('maturity_date') and not attrs.get('tenure_value'):
            raise serializers.ValidationError({'maturity_date': "Either maturity date or tenure must be provided."})

        # Cross-field: maturity date must be after start date
        if attrs.get('start_date') and attrs.get('maturity_date'):
            if attrs['maturity_date'] <= attrs['start_date']:
                raise serializers.ValidationError({'maturity_date': "Maturity date must be after the deposit start date."})

        return attrs


class DepositDetailUpdateValidator(serializers.ModelSerializer):
    auto_renewal = StrictBooleanValueField(required=False)
    is_senior_citizen = StrictBooleanValueField(required=False)
    is_tax_saver = StrictBooleanValueField(required=False)
    principal_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    interest_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    tenure_value = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal('0.01'), required=False
    )

    bank_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    deposit_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    deposit_date = serializers.DateField(required=False)
    interest_rate = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    annual_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )
    installment_due_day = serializers.IntegerField(
        min_value=1, max_value=31, required=False, default=5
    )
    tenure_months = serializers.DecimalField(
        max_digits=8, decimal_places=2, min_value=Decimal('0.01'), required=False
    )

    class Meta:
        model = DepositDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in DepositDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        if 'deposit_amount' in attrs and 'principal_amount' not in attrs:
            attrs['principal_amount'] = attrs['deposit_amount']
        if 'deposit_date' in attrs and 'start_date' not in attrs:
            attrs['start_date'] = attrs['deposit_date']
        if 'interest_rate' in attrs and 'interest_rate_pct' not in attrs:
            attrs['interest_rate_pct'] = attrs['interest_rate']
        if 'annual_rate_pct' in attrs and 'interest_rate_pct' not in attrs:
            attrs['interest_rate_pct'] = attrs['annual_rate_pct']
        if 'bank_name' in attrs and 'institution_name' not in attrs:
            attrs['institution_name'] = attrs['bank_name']
        if 'tenure_months' in attrs and 'tenure_value' not in attrs:
            attrs['tenure_value'] = attrs['tenure_months']

        s_date = attrs.get('start_date') or getattr(self.instance, 'start_date', None)
        m_date = attrs.get('maturity_date') or getattr(self.instance, 'maturity_date', None)
        if s_date and m_date and m_date <= s_date:
            raise serializers.ValidationError({'maturity_date': "Maturity date must be after the deposit start date."})
        return attrs


# =====================================================================
# 3. BOND VALIDATORS
# =====================================================================

class BondDetailCreateValidator(serializers.ModelSerializer):
    bond_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    face_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=True
    )
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=True
    )
    quantity = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=True
    )
    purchase_date = serializers.DateField(required=False)
    coupon_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False, default=Decimal('0.00')
    )
    maturity_date = serializers.DateField(required=False, allow_null=True)

    class Meta:
        model = BondDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if not attrs.get('purchase_date'):
            attrs['purchase_date'] = timezone.now().date()
        if attrs.get('purchase_date') and attrs.get('maturity_date'):
            if attrs['maturity_date'] <= attrs['purchase_date']:
                raise serializers.ValidationError({'maturity_date': "Maturity date must be after purchase date."})
        return attrs


class BondDetailUpdateValidator(serializers.ModelSerializer):
    face_value = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    quantity = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    coupon_rate_pct = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.00'), required=False
    )

    class Meta:
        model = BondDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in BondDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        p_date = attrs.get('purchase_date') or getattr(self.instance, 'purchase_date', None)
        m_date = attrs.get('maturity_date') or getattr(self.instance, 'maturity_date', None)
        if p_date and m_date and m_date <= p_date:
            raise serializers.ValidationError({'maturity_date': "Maturity date must be after purchase date."})
        return attrs


# =====================================================================
# 4. EQUITY VALIDATORS
# =====================================================================

class EquityDetailCreateValidator(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_date = serializers.DateField(required=False)
    brokerage = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False, default=Decimal('0.00')
    )
    stt_charges = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False, default=Decimal('0.00')
    )

    # Aliases
    shares = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    buy_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    average_buy_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    brokerage_fees = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False
    )
    statutory_taxes = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False
    )

    class Meta:
        model = EquityDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if 'shares' in attrs and 'quantity' not in attrs:
            attrs['quantity'] = attrs['shares']
        if 'buy_price' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['buy_price']
        if 'average_buy_price' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['average_buy_price']
        if 'brokerage_fees' in attrs and 'brokerage' not in attrs:
            attrs['brokerage'] = attrs['brokerage_fees']
        if 'statutory_taxes' in attrs and 'stt_charges' not in attrs:
            attrs['stt_charges'] = attrs['statutory_taxes']

        if not attrs.get('purchase_date'):
            attrs['purchase_date'] = timezone.now().date()

        if not attrs.get('quantity'):
            raise serializers.ValidationError({'quantity': "Quantity of shares is required and must be positive."})
        if not attrs.get('purchase_price'):
            raise serializers.ValidationError({'purchase_price': "Purchase price per share is required."})
        return attrs


class EquityDetailUpdateValidator(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    brokerage = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False
    )
    stt_charges = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False
    )

    shares = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    buy_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    average_buy_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )

    class Meta:
        model = EquityDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in EquityDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        if 'shares' in attrs and 'quantity' not in attrs:
            attrs['quantity'] = attrs['shares']
        if 'buy_price' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['buy_price']
        if 'average_buy_price' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['average_buy_price']
        return attrs


# =====================================================================
# 5. MUTUAL FUND VALIDATORS
# =====================================================================

class MutualFundDetailCreateValidator(serializers.ModelSerializer):
    units = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=True
    )
    purchase_nav = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_date = serializers.DateField(required=False)
    is_sip = StrictBooleanValueField(required=False, default=False)
    scheme_name = serializers.CharField(max_length=200, required=False, allow_blank=True)

    # Aliases
    average_purchase_nav = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    plan = serializers.CharField(max_length=50, required=False, allow_blank=True)
    option = serializers.CharField(max_length=50, required=False, allow_blank=True)

    class Meta:
        model = MutualFundDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if 'average_purchase_nav' in attrs and 'purchase_nav' not in attrs:
            attrs['purchase_nav'] = attrs['average_purchase_nav']
        if 'plan' in attrs and 'plan_type' not in attrs:
            attrs['plan_type'] = attrs['plan']
        if 'option' in attrs and 'option_type' not in attrs:
            attrs['option_type'] = attrs['option']

        if not attrs.get('purchase_date'):
            attrs['purchase_date'] = timezone.now().date()
        if not attrs.get('purchase_nav'):
            raise serializers.ValidationError({'purchase_nav': "Purchase NAV is required."})
        if attrs.get('is_sip') and not attrs.get('sip_frequency'):
            attrs['sip_frequency'] = 'MONTHLY'
        return attrs


class MutualFundDetailUpdateValidator(serializers.ModelSerializer):
    units = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_nav = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    is_sip = StrictBooleanValueField(required=False)
    average_purchase_nav = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )

    class Meta:
        model = MutualFundDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in MutualFundDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        if 'average_purchase_nav' in attrs and 'purchase_nav' not in attrs:
            attrs['purchase_nav'] = attrs['average_purchase_nav']
        return attrs


# =====================================================================
# 6. GOLD / COMMODITIES VALIDATORS
# =====================================================================

class GoldDetailCreateValidator(serializers.ModelSerializer):
    weight_grams = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False, allow_null=True
    )
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_date = serializers.DateField(required=False)
    purity_karat = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('1.00'), max_value=Decimal('24.00'), required=False
    )

    # Aliases
    gross_weight_grams = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    weight_in_grams = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    grams = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_price_per_gram = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    units = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purity = serializers.CharField(max_length=20, required=False, allow_blank=True)
    purchase_price_total = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    provider = serializers.CharField(max_length=150, required=False, allow_blank=True)
    series_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    units_grams = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    issue_price_per_gram = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purity_karats = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('1.00'), max_value=Decimal('24.00'), required=False
    )

    class Meta:
        model = GoldDetail
        exclude = ['id', 'investment']

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)
        if 'purity' in mutable_data and 'purity_karat' not in mutable_data and 'purity_karats' not in mutable_data:
            raw_p = str(mutable_data['purity']).strip().upper()
            if raw_p.endswith('K'):
                raw_p = raw_p[:-1]
            try:
                dec_val = Decimal(raw_p)
                if Decimal('1.00') <= dec_val <= Decimal('24.00'):
                    mutable_data['purity_karat'] = dec_val
                else:
                    raise serializers.ValidationError({'purity_karat': "Purity must be between 1.00 and 24.00 karats."})
            except (ValueError, TypeError, serializers.ValidationError):
                raise serializers.ValidationError({'purity_karat': f"Invalid gold purity '{mutable_data['purity']}'. Expected numeric karats (e.g. 24, 22K)."})
        return super().to_internal_value(mutable_data)

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if 'series_name' in attrs and 'sgb_series' not in attrs:
            attrs['sgb_series'] = attrs['series_name']
        if 'units_grams' in attrs and 'weight_grams' not in attrs:
            attrs['weight_grams'] = attrs['units_grams']
        if 'purchase_price_total' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['purchase_price_total']
        elif 'purchase_amount' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['purchase_amount']
        elif 'issue_price_per_gram' in attrs and 'purchase_price' not in attrs:
            if attrs.get('weight_grams'):
                attrs['purchase_price'] = attrs['weight_grams'] * attrs['issue_price_per_gram']
            else:
                attrs['purchase_price'] = attrs['issue_price_per_gram']
        if 'gross_weight_grams' in attrs and 'weight_grams' not in attrs:
            attrs['weight_grams'] = attrs['gross_weight_grams']
        elif 'weight_in_grams' in attrs and 'weight_grams' not in attrs:
            attrs['weight_grams'] = attrs['weight_in_grams']
        elif 'grams' in attrs and 'weight_grams' not in attrs:
            attrs['weight_grams'] = attrs['grams']
        elif 'units' in attrs and 'weight_grams' not in attrs:
            attrs['weight_grams'] = attrs['units']

        if 'purchase_price_per_gram' in attrs and 'purchase_price' not in attrs:
            attrs['purchase_price'] = attrs['purchase_price_per_gram']
        if 'purity_karats' in attrs and 'purity_karat' not in attrs:
            attrs['purity_karat'] = attrs['purity_karats']

        if not attrs.get('purchase_date'):
            attrs['purchase_date'] = timezone.now().date()

        gold_type = attrs.get('gold_type', '').upper()
        # Sovereign gold bond does not strictly require physical weight
        if gold_type == 'SGB' or attrs.get('sgb_series'):
            if not attrs.get('purchase_price'):
                raise serializers.ValidationError({'purchase_price': "Purchase price is required for SGB."})
        else:
            if not attrs.get('weight_grams'):
                raise serializers.ValidationError({'weight_grams': "Weight or units must be specified and positive."})
            if not attrs.get('purchase_price'):
                raise serializers.ValidationError({'purchase_price': "Purchase price is required."})

        return attrs


class GoldDetailUpdateValidator(serializers.ModelSerializer):
    weight_grams = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purity_karat = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal('1.00'), max_value=Decimal('24.00'), required=False
    )

    class Meta:
        model = GoldDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in GoldDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        return attrs


# =====================================================================
# 7. REAL ESTATE VALIDATORS
# =====================================================================

class RealEstateDetailCreateValidator(serializers.ModelSerializer):
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=True
    )
    acquisition_date = serializers.DateField(required=False)
    ownership_percentage = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('100.00'), required=False, default=Decimal('100.00')
    )
    area = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False, allow_null=True
    )
    property_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    property_type = serializers.CharField(max_length=50, default='RESIDENTIAL')

    # Aliases
    property_nickname = serializers.CharField(max_length=200, required=False, allow_blank=True)
    land_area = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    plot_area = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    built_up_area = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    area_value = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    khasra_number = serializers.CharField(max_length=100, required=False, allow_blank=True)
    purchase_date = serializers.DateField(required=False)
    stamp_duty_paid = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False
    )
    registration_fee_paid = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.00'), required=False
    )

    class Meta:
        model = RealEstateDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if 'property_nickname' in attrs and 'property_name' not in attrs:
            attrs['property_name'] = attrs['property_nickname']
        if 'land_area' in attrs and 'area' not in attrs:
            attrs['area'] = attrs['land_area']
        elif 'plot_area' in attrs and 'area' not in attrs:
            attrs['area'] = attrs['plot_area']
        elif 'built_up_area' in attrs and 'area' not in attrs:
            attrs['area'] = attrs['built_up_area']
        elif 'area_value' in attrs and 'area' not in attrs:
            attrs['area'] = attrs['area_value']

        if 'khasra_number' in attrs and 'survey_or_plot_number' not in attrs:
            attrs['survey_or_plot_number'] = attrs['khasra_number']

        if 'purchase_date' in attrs and 'acquisition_date' not in attrs:
            attrs['acquisition_date'] = attrs['purchase_date']
        if not attrs.get('acquisition_date'):
            attrs['acquisition_date'] = timezone.now().date()

        if 'stamp_duty_paid' in attrs and 'stamp_duty' not in attrs:
            attrs['stamp_duty'] = attrs['stamp_duty_paid']
        if 'registration_fee_paid' in attrs and 'registration_charges' not in attrs:
            attrs['registration_charges'] = attrs['registration_fee_paid']

        pct = attrs.get('ownership_percentage')
        if pct is not None and (pct <= Decimal('0') or pct > Decimal('100')):
            raise serializers.ValidationError({'ownership_percentage': "Ownership percentage must be between 0.01 and 100.00%."})
        return attrs


class RealEstateDetailUpdateValidator(serializers.ModelSerializer):
    purchase_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    ownership_percentage = serializers.DecimalField(
        max_digits=6, decimal_places=2, min_value=Decimal('0.01'), max_value=Decimal('100.00'), required=False
    )
    area = serializers.DecimalField(
        max_digits=14, decimal_places=4, min_value=Decimal('0.0001'), required=False, allow_null=True
    )

    class Meta:
        model = RealEstateDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in RealEstateDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        pct = attrs.get('ownership_percentage')
        if pct is not None and (pct <= Decimal('0') or pct > Decimal('100')):
            raise serializers.ValidationError({'ownership_percentage': "Ownership percentage must be between 0.01 and 100.00%."})
        return attrs


# =====================================================================
# 8. CRYPTO VALIDATORS
# =====================================================================

class CryptoDetailCreateValidator(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=Decimal('0.00000001'), required=False
    )
    purchase_price_per_token = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )
    purchase_date = serializers.DateField(required=False)

    # Aliases
    buy_price = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )

    class Meta:
        model = CryptoDetail
        exclude = ['id', 'investment']

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=True)
        if 'buy_price' in attrs and 'purchase_price_per_token' not in attrs:
            attrs['purchase_price_per_token'] = attrs['buy_price']

        if not attrs.get('purchase_date'):
            attrs['purchase_date'] = timezone.now().date()

        if not attrs.get('quantity'):
            raise serializers.ValidationError({'quantity': "Token quantity is required and must be positive."})
        if not attrs.get('purchase_price_per_token'):
            raise serializers.ValidationError({'purchase_price_per_token': "Purchase price per token is required."})
        return attrs


class CryptoDetailUpdateValidator(serializers.ModelSerializer):
    quantity = serializers.DecimalField(
        max_digits=24, decimal_places=8, min_value=Decimal('0.00000001'), required=False
    )
    purchase_price_per_token = serializers.DecimalField(
        max_digits=18, decimal_places=4, min_value=Decimal('0.0001'), required=False
    )

    class Meta:
        model = CryptoDetail
        exclude = ['id', 'investment']
        extra_kwargs = {f.name: {'required': False} for f in CryptoDetail._meta.fields}

    def validate(self, attrs):
        check_no_immutable_fields(self.initial_data, is_creation=False)
        return attrs


# =====================================================================
# REGISTRY DISPATCHER
# =====================================================================

CREATION_VALIDATOR_MAP = {
    'cash': CashAccountDetailCreateValidator,
    'fixed_income': DepositDetailCreateValidator,
    'bond': BondDetailCreateValidator,
    'equity': EquityDetailCreateValidator,
    'mutual_funds': MutualFundDetailCreateValidator,
    'gold': GoldDetailCreateValidator,
    'commodities': GoldDetailCreateValidator,
    'real_estate': RealEstateDetailCreateValidator,
    'crypto': CryptoDetailCreateValidator,
}

UPDATE_VALIDATOR_MAP = {
    'cash': CashAccountDetailUpdateValidator,
    'fixed_income': DepositDetailUpdateValidator,
    'bond': BondDetailUpdateValidator,
    'equity': EquityDetailUpdateValidator,
    'mutual_funds': MutualFundDetailUpdateValidator,
    'gold': GoldDetailUpdateValidator,
    'commodities': GoldDetailUpdateValidator,
    'real_estate': RealEstateDetailUpdateValidator,
    'crypto': CryptoDetailUpdateValidator,
}


def get_detail_validator(category: str, asset_type: str = '', is_creation: bool = False):
    """
    Returns the appropriate detail validator serializer for a category / asset_type,
    selecting either strict creation validation or partial update validation.
    """
    cat_lower = (category or '').lower()
    asset_lower = (asset_type or '').lower()

    if is_creation:
        if 'gold' in cat_lower or 'sgb' in asset_lower or 'sovereign_gold' in asset_lower:
            return GoldDetailCreateValidator
        if 'bond' in asset_lower:
            return BondDetailCreateValidator
        if 'deposit' in asset_lower:
            return DepositDetailCreateValidator
        return CREATION_VALIDATOR_MAP.get(cat_lower)

    if 'gold' in cat_lower or 'sgb' in asset_lower or 'sovereign_gold' in asset_lower:
        return GoldDetailUpdateValidator
    if 'bond' in asset_lower:
        return BondDetailUpdateValidator
    if 'deposit' in asset_lower:
        return DepositDetailUpdateValidator
    return UPDATE_VALIDATOR_MAP.get(cat_lower)
