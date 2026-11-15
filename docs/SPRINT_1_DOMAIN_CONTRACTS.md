# Sprint 1 — Backend Domain Models & Serializer Contracts Specification

**Sprint:** Sprint 1  
**Target Delivery:** Sprint 2 Persistence Implementation  
**Architecture:** Django + Django REST Framework + PostgreSQL (Neon)

---

## 1. Relational Schema Architecture

The investment domain implements a clean **Compositional / Extension Model** rather than a single monolithic table with hundreds of nullable columns or loose schemaless JSON.

```
                    +-------------------+
                    |   User (Auth)     |
                    +---------+---------+
                              | 1
                              |
                              | *
                    +---------+---------+
                    |    Portfolio      |
                    +---------+---------+
                              | 1
                              |
                              | *
                    +---------+---------+
                    |    Investment     |<--------------------+
                    +----+----+----+----+                     |
                         |    |    |                          |
        +----------------+    |    +----------------+         |
        | 1:1                 | 1:1                 | 1:1     |
+-------+-------+     +-------+-------+     +-------+-------+ |
|CashAccountDet |     | DepositDetail |     |  EquityDetail | |
+---------------+     +---------------+     +-------+-------+ |
                                                    | *       |
                                                    |         |
                                            +-------+-------+ |
                                            |  Instrument   | |
                                            |    Master     | |
                                            +---------------+ |
                                                              |
                    +-------------------+                     |
                    |    Transaction    |---------------------+ 1:*
                    +-------------------+
                                                              |
                    +-------------------+                     |
                    | ValuationHistory  |---------------------+ 1:*
                    +-------------------+
```

---

## 2. Core Django Models Specification

### 2.1 `Investment` (Base Holding Container)
```python
from django.db import models
import uuid
from users.models import User
from portfolios.models import Portfolio

class AssetCategory(models.TextChoices):
    CASH = 'cash', 'Cash & Banking'
    FIXED_INCOME = 'fixed_income', 'Fixed Income & Deposits'
    EQUITY = 'equity', 'Listed Equities'
    MUTUAL_FUNDS = 'mutual_funds', 'Mutual Funds & ETFs'
    GOLD = 'gold', 'Gold & Precious Metals'
    REAL_ESTATE = 'real_estate', 'Real Estate & Property'
    CRYPTO = 'crypto', 'Cryptocurrencies'

class ValuationMethod(models.TextChoices):
    MANUAL = 'MANUAL', 'Manual Cost Basis'
    MARKET_FEED = 'MARKET_FEED', 'Live Market Feed'
    CONTRACTUAL = 'CONTRACTUAL_CALCULATION', 'Contractual Calculation'
    NAV_FEED = 'NAV_FEED', 'Mutual Fund Daily NAV'
    USER_ESTIMATE = 'USER_ESTIMATE', 'User Estimate'

class Investment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='investments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    category = models.CharField(max_length=30, choices=AssetCategory.choices)
    asset_type = models.CharField(max_length=50) # e.g. 'savings_account', 'fixed_deposit', 'stock'
    display_name = models.CharField(max_length=200)
    currency = models.CharField(max_length=10, default='INR')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, default='')
    valuation_method = models.CharField(max_length=40, choices=ValuationMethod.choices, default=ValuationMethod.MANUAL)
    last_valuation_amount = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)
    last_valuation_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'investments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['portfolio', 'category']),
            models.Index(fields=['user', 'asset_type']),
        ]
```

### 2.2 Asset Extension Detail Models

#### `CashAccountDetail`
- `investment` (OneToOneField)
- `bank_name` (CharField 100)
- `account_type` (SAVINGS, SALARY, SENIOR_CITIZEN, NRE_NRO, CURRENT)
- `masked_account_number` (CharField 20, blank)
- `interest_rate_pct` (DecimalField 5,2)
- `interest_credit_frequency` (QUARTERLY, MONTHLY, etc.)
- `auto_sweep_enabled` (BooleanField default False)
- `sweep_out_threshold` (DecimalField 15,2, null=True)
- `sweep_retained_balance` (DecimalField 15,2, null=True)
- `sweep_increment` (DecimalField 15,2, null=True)
- `overdraft_limit` (DecimalField 15,2, default=0)

#### `DepositDetail` (FD / RD)
- `investment` (OneToOneField)
- `institution_name` (CharField 100)
- `deposit_type` (FIXED_DEPOSIT, RECURRING_DEPOSIT)
- `principal_amount` (DecimalField 15,2)
- `monthly_installment` (DecimalField 15,2, null=True)
- `start_date` (DateField)
- `maturity_date` (DateField, null=True)
- `tenure_value` (DecimalField 6,2)
- `tenure_unit` (days, months, years)
- `annual_rate_pct` (DecimalField 5,2)
- `compounding_frequency` (quarterly, monthly, simple, etc.)
- `payout_type` (cumulative, monthly_payout, quarterly_payout)
- `is_senior_citizen` (BooleanField)
- `is_tax_saver` (BooleanField)
- `auto_renewal` (BooleanField)
- `projected_maturity_amount` (DecimalField 18,2, null=True)

#### `EquityDetail` (Stocks)
- `investment` (OneToOneField)
- `company_name` (CharField 150)
- `symbol` (CharField 20)
- `exchange` (NSE, BSE, NASDAQ, etc.)
- `isin` (CharField 12, blank)
- `quantity` (DecimalField 14,4)
- `average_buy_price` (DecimalField 15,4)
- `brokerage_fees` (DecimalField 10,2, default=0)
- `statutory_taxes` (DecimalField 10,2, default=0)

#### `MutualFundDetail`
- `investment` (OneToOneField)
- `amc_name` (CharField 100)
- `scheme_name` (CharField 200)
- `scheme_category` (CharField 100)
- `plan` (DIRECT, REGULAR)
- `option` (GROWTH, IDCW_PAYOUT, IDCW_REINVESTMENT)
- `units` (DecimalField 14,3)
- `average_purchase_nav` (DecimalField 12,4)
- `is_sip` (BooleanField default False)
- `sip_amount` (DecimalField 12,2, null=True)
- `sip_frequency` (CharField 20, blank)

#### `RealEstateDetail`
- `investment` (OneToOneField)
- `property_name` (CharField 150)
- `property_type` (RESIDENTIAL, COMMERCIAL, LAND, INDUSTRIAL)
- `property_use` (SELF_OCCUPIED, RENTED, VACANT, UNDER_CONSTRUCTION)
- `state` (CharField 80)
- `city` (CharField 80)
- `locality` (CharField 100)
- `built_up_area` (DecimalField 10,2, null=True)
- `plot_area` (DecimalField 10,2, null=True)
- `area_unit` (SQ_FT, SQ_METER, BIGHA, ACRE)
- `ownership_percentage` (DecimalField 5,2 default 100.00)
- `purchase_price` (DecimalField 16,2)
- `stamp_duty_paid` (DecimalField 14,2 default 0)
- `registration_fee_paid` (DecimalField 14,2 default 0)
- `renovation_expenses` (DecimalField 14,2 default 0)
- `monthly_rental_income` (DecimalField 12,2 default 0)
- `estimated_current_value` (DecimalField 16,2)

#### `CryptoDetail`
- `investment` (OneToOneField)
- `token_name` (CharField 80)
- `symbol` (CharField 20)
- `network` (CharField 60)
- `contract_address` (CharField 100, blank)
- `quantity` (DecimalField 20,8)
- `purchase_price_per_token` (DecimalField 18,4)
- `wallet_type` (HARDWARE_WALLET, SOFTWARE_WALLET, EXCHANGE, OTHER)
- `exchange_name` (CharField 80, blank)
- `transaction_hash` (CharField 150, blank)

---

## 3. DRF Serializer Design

```python
from rest_framework import serializers

class InvestmentCreateSerializer(serializers.ModelSerializer):
    # Dynamic nested detail serializer according to category & asset_type
    details = serializers.JSONField(write_only=True)

    class Meta:
        model = Investment
        fields = [
            'id', 'portfolio', 'category', 'asset_type',
            'display_name', 'currency', 'notes', 'valuation_method',
            'details', 'created_at', 'updated_at'
        ]

    def validate(self, attrs):
        # 1. Enforce portfolio ownership by authenticated request.user
        portfolio = attrs['portfolio']
        user = self.context['request'].user
        if portfolio.user_id != user.id:
            raise serializers.ValidationError({"portfolio": "Access denied to portfolio."})
        
        # 2. Match detail payload against asset category validator
        category = attrs['category']
        details = attrs.get('details', {})
        # Dispatch to sub-validator (e.g. FixedDepositDetailValidator)
        ...
        return attrs
```

---

## 4. API Endpoints for Sprint 2

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/investments/?portfolio_id=<uuid>` | List holdings filtered by portfolio or category |
| `POST` | `/api/investments/` | Create holding with validated asset detail & ledger transaction |
| `GET` | `/api/investments/<uuid>/` | Retrieve holding with child details and transactions |
| `PUT/PATCH` | `/api/investments/<uuid>/` | Update investment holding details |
| `DELETE` | `/api/investments/<uuid>/` | Archive or delete holding |
| `POST` | `/api/investments/<uuid>/transactions/` | Record buy/sell/dividend ledger entry |
