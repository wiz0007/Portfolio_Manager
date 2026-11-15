import uuid

from django.db import models

from .investment import Investment


class CashAccountDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='cash_detail',
    )
    bank_name = models.CharField(max_length=150)
    account_nickname = models.CharField(max_length=150, blank=True, default='')
    account_type = models.CharField(max_length=50)  # SAVINGS, SALARY, SENIOR_CITIZEN, NRE_NRO, CURRENT
    masked_account_number = models.CharField(max_length=30, blank=True, default='')
    current_balance = models.DecimalField(max_digits=18, decimal_places=4)
    balance_date = models.DateField()
    interest_rate_pct = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    interest_credit_frequency = models.CharField(max_length=50, blank=True, default='QUARTERLY')
    auto_sweep_enabled = models.BooleanField(default=False)
    sweep_out_threshold = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    sweep_retained_balance = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    sweep_increment = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    overdraft_limit = models.DecimalField(max_digits=18, decimal_places=4, default=0)

    class Meta:
        db_table = 'investment_cash_details'

    def __str__(self) -> str:
        return f"Cash Detail: {self.bank_name} ({self.account_type})"


class DepositDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='deposit_detail',
    )
    institution_name = models.CharField(max_length=150)
    deposit_nickname = models.CharField(max_length=150, blank=True, default='')
    deposit_type = models.CharField(max_length=50)  # FIXED_DEPOSIT, RECURRING_DEPOSIT
    deposit_number = models.CharField(max_length=50, blank=True, default='')
    principal_amount = models.DecimalField(max_digits=18, decimal_places=4)
    monthly_installment = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    start_date = models.DateField()
    tenure_value = models.DecimalField(max_digits=8, decimal_places=2)
    tenure_unit = models.CharField(max_length=20, default='YEARS')  # DAYS, MONTHS, YEARS
    interest_rate_pct = models.DecimalField(max_digits=6, decimal_places=2)
    compounding_frequency = models.CharField(max_length=50, default='QUARTERLY')
    payout_type = models.CharField(max_length=50, default='CUMULATIVE')
    maturity_date = models.DateField(null=True, blank=True)
    maturity_amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    is_senior_citizen = models.BooleanField(default=False)
    is_tax_saver = models.BooleanField(default=False)
    auto_renewal = models.BooleanField(default=False)

    class Meta:
        db_table = 'investment_deposit_details'

    def __str__(self) -> str:
        return f"Deposit: {self.institution_name} ({self.deposit_type})"


class BondDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='bond_detail',
    )
    bond_name = models.CharField(max_length=150)
    issuer_name = models.CharField(max_length=150)
    bond_type = models.CharField(max_length=50)  # GOVERNMENT, CORPORATE, TAX_FREE, INFRASTRUCTURE
    isin = models.CharField(max_length=30, blank=True, default='')
    face_value = models.DecimalField(max_digits=18, decimal_places=4)
    purchase_price = models.DecimalField(max_digits=18, decimal_places=4)
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    coupon_rate_pct = models.DecimalField(max_digits=6, decimal_places=2)
    coupon_frequency = models.CharField(max_length=50, default='SEMI_ANNUALLY')
    purchase_date = models.DateField()
    maturity_date = models.DateField()
    credit_rating = models.CharField(max_length=50, blank=True, default='')
    yield_to_maturity_pct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'investment_bond_details'

    def __str__(self) -> str:
        return f"Bond: {self.bond_name} ({self.issuer_name})"


class EquityDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='equity_detail',
    )
    company_name = models.CharField(max_length=150)
    symbol = models.CharField(max_length=30)
    exchange = models.CharField(max_length=30, default='NSE')
    isin = models.CharField(max_length=30, blank=True, default='')
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    average_buy_price = models.DecimalField(max_digits=18, decimal_places=4)
    purchase_date = models.DateField()
    brokerage_fees = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    statutory_taxes = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    class Meta:
        db_table = 'investment_equity_details'

    def __str__(self) -> str:
        return f"Equity: {self.symbol} ({self.exchange})"


class MutualFundDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='mutual_fund_detail',
    )
    amc_name = models.CharField(max_length=150)
    scheme_name = models.CharField(max_length=200)
    scheme_category = models.CharField(max_length=100, blank=True, default='')
    plan = models.CharField(max_length=30, default='DIRECT')  # DIRECT, REGULAR
    option = models.CharField(max_length=30, default='GROWTH')  # GROWTH, IDCW_PAYOUT, IDCW_REINVESTMENT
    folio_number = models.CharField(max_length=50, blank=True, default='')
    units = models.DecimalField(max_digits=18, decimal_places=4)
    average_purchase_nav = models.DecimalField(max_digits=18, decimal_places=4)
    purchase_date = models.DateField()
    is_sip = models.BooleanField(default=False)
    sip_amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    sip_frequency = models.CharField(max_length=30, blank=True, default='')

    class Meta:
        db_table = 'investment_mutual_fund_details'

    def __str__(self) -> str:
        return f"Mutual Fund: {self.scheme_name}"


class GoldDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='gold_detail',
    )
    item_name = models.CharField(max_length=150)
    gold_type = models.CharField(max_length=50)  # PHYSICAL, DIGITAL, ETF, SGB
    weight_grams = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    purity_karat = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=18, decimal_places=4)
    purchase_date = models.DateField()
    making_charges = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    gst_amount = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    platform_or_provider = models.CharField(max_length=100, blank=True, default='')
    sgb_series = models.CharField(max_length=100, blank=True, default='')
    coupon_rate_pct = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    maturity_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'investment_gold_details'

    def __str__(self) -> str:
        return f"Gold: {self.item_name} ({self.gold_type})"


class RealEstateDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='real_estate_detail',
    )
    property_name = models.CharField(max_length=150, blank=True, default='')
    property_type = models.CharField(max_length=50)  # RESIDENTIAL, COMMERCIAL, LAND, AGRICULTURAL, PLOT
    land_classification = models.CharField(max_length=50, blank=True, default='')
    property_use = models.CharField(max_length=50, blank=True, default='')
    country = models.CharField(max_length=50, default='India')
    state = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, default='')
    district = models.CharField(max_length=100, blank=True, default='')
    tehsil = models.CharField(max_length=100, blank=True, default='')
    locality = models.CharField(max_length=150, blank=True, default='')
    village = models.CharField(max_length=150, blank=True, default='')
    survey_or_plot_number = models.CharField(max_length=100, blank=True, default='')
    address_line = models.TextField(blank=True, default='')
    area = models.DecimalField(max_digits=14, decimal_places=4, null=True, blank=True)
    area_unit = models.CharField(max_length=30, default='SQ_FT')
    ownership_percentage = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    purchase_price = models.DecimalField(max_digits=18, decimal_places=4)
    acquisition_date = models.DateField()
    stamp_duty = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    registration_charges = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    other_acquisition_costs = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    renovation_expenses = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    monthly_rental_income = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    estimated_current_value = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    valuation_date = models.DateField(null=True, blank=True)
    valuation_source = models.CharField(max_length=150, blank=True, default='')
    expected_annual_appreciation = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    class Meta:
        db_table = 'investment_real_estate_details'

    def __str__(self) -> str:
        return f"Real Estate: {self.property_name or self.property_type} in {self.state}"


class CryptoDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.OneToOneField(
        Investment,
        on_delete=models.CASCADE,
        related_name='crypto_detail',
    )
    token_name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=30)
    network = models.CharField(max_length=100)
    contract_address = models.CharField(max_length=150, blank=True, default='')
    quantity = models.DecimalField(max_digits=24, decimal_places=8)
    purchase_price_per_token = models.DecimalField(max_digits=18, decimal_places=4)
    purchase_date = models.DateField()
    wallet_type = models.CharField(max_length=50, blank=True, default='')
    exchange_name = models.CharField(max_length=100, blank=True, default='')
    network_fees = models.DecimalField(max_digits=14, decimal_places=4, default=0)
    transaction_hash = models.CharField(max_length=150, blank=True, default='')

    class Meta:
        db_table = 'investment_crypto_details'

    def __str__(self) -> str:
        return f"Crypto: {self.symbol} on {self.network}"
