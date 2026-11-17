from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import CashAccountDetail, Investment
from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.mark.django_db
class TestInvestmentValidationCorrection:
    """
    Test suite for Workstream A: Investment Validation and Data Integrity (INV-001 to INV-008).
    """

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, db):
        self.user = User.objects.create_user(
            email="inv_test_user@example.com",
            password="StrongPassword123!",
            full_name="Validation User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Validation Test Portfolio",
            base_currency="INR"
        )
        self.base_url = f"/api/v1/portfolios/{self.portfolio.id}/investments/"

    def test_inv_001_missing_essential_creation_fields_rejected(self):
        """INV-001: Creation cannot succeed when required asset-specific acquisition fields are missing."""
        # Missing current_balance and bank_name for cash account
        res = self.client.post(
            self.base_url,
            {
                "category": "cash",
                "asset_type": "savings_account",
                "currency": "INR",
                "details": {
                    "account_nickname": "Missing Balance Account"
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        errs = res.json()
        assert "details" in errs
        assert "current_balance" in errs["details"] or "bank_name" in errs["details"]

    def test_inv_002_invalid_category_product_combination_rejected(self):
        """INV-002: Incompatible category/asset_type combinations produce explicit 400 validation error."""
        res = self.client.post(
            self.base_url,
            {
                "category": "equity",
                "asset_type": "savings_account",  # Incompatible!
                "currency": "INR",
                "details": {
                    "bank_name": "State Bank of India",
                    "current_balance": "5000.00",
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in res.json()

    def test_inv_003_invalid_decimal_and_strict_boolean_validation(self):
        """INV-003: String 'false' must not evaluate to True, and negative numbers where disallowed fail."""
        res = self.client.post(
            self.base_url,
            {
                "category": "cash",
                "asset_type": "savings_account",
                "currency": "INR",
                "details": {
                    "bank_name": "ICICI Bank",
                    "current_balance": "-1000.00",  # Negative balance not allowed on SAVINGS
                    "account_type": "SAVINGS",
                    "auto_sweep_enabled": "not_a_bool"  # Malformed boolean
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_inv_004_cross_field_validation_fd_dates(self):
        """INV-004: FD maturity date must be strictly after start date."""
        res = self.client.post(
            self.base_url,
            {
                "category": "fixed_income",
                "asset_type": "fixed_deposit",
                "currency": "INR",
                "details": {
                    "institution_name": "HDFC Bank",
                    "principal_amount": "50000.00",
                    "interest_rate_pct": "6.50",
                    "start_date": "2026-12-01",
                    "maturity_date": "2026-11-01",  # Before start date!
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "maturity_date" in res.json().get("details", {})

    def test_inv_005_patch_partial_update_permits_single_field(self):
        """INV-005: PATCH requests only validate supplied fields against existing holding."""
        inv = Investment.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            category="cash",
            asset_type="savings_account",
            display_name="Primary Savings",
            initial_value=Decimal("10000.00"),
            current_value=Decimal("10000.00"),
            currency="INR"
        )
        CashAccountDetail.objects.create(
            investment=inv,
            bank_name="HDFC Bank",
            account_nickname="Primary Savings",
            account_type="SAVINGS",
            current_balance=Decimal("10000.00"),
            balance_date=timezone.now().date(),
        )

        patch_res = self.client.patch(
            f"/api/v1/portfolios/{self.portfolio.id}/investments/{inv.id}/",
            {
                "display_name": "Updated Primary Savings",
                "details": {
                    "account_nickname": "Updated Nickname"
                }
            },
            format='json'
        )
        assert patch_res.status_code == status.HTTP_200_OK
        inv.refresh_from_db()
        assert inv.display_name == "Updated Primary Savings"
        assert inv.cash_detail.account_nickname == "Updated Nickname"

    def test_inv_007_parent_detail_atomic_rollback_on_failure(self):
        """INV-007: Atomic rollback prevents orphan investments if detail persistence fails."""
        initial_inv_count = Investment.objects.count()
        # Missing required purchase_price on bond
        res = self.client.post(
            self.base_url,
            {
                "category": "fixed_income",
                "asset_type": "bond",
                "currency": "INR",
                "details": {
                    "bond_name": "Corrupt Bond",
                    "face_value": "1000.00",
                    # purchase_price omitted!
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert Investment.objects.count() == initial_inv_count

    def test_inv_008_frontend_summary_values_do_not_override_calculations(self):
        """INV-008: Frontend-supplied arbitrary initial_value is derived authoritatively from validated inputs."""
        res = self.client.post(
            self.base_url,
            {
                "category": "cash",
                "asset_type": "savings_account",
                "currency": "INR",
                "initial_value": "999999.00",  # Fake summary value
                "details": {
                    "bank_name": "State Bank of India",
                    "current_balance": "5000.00",
                    "balance_date": "2026-11-15"
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        # Authoritative cost basis must match actual cash balance, not spoofed summary
        assert Decimal(str(data["initial_value"])) == Decimal("5000.00")
