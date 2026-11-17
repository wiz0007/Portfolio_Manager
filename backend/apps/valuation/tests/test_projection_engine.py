from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models.investment import Investment
from apps.portfolios.models.portfolio import Portfolio
from apps.users.models.user import User
from apps.valuation.services.calculation.decimal_utils import (
    compound_annuity_fv,
    compound_lump_sum,
)
from apps.valuation.services.calculation.projection_engine import ProjectionEngine


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        email="proj_user@example.com",
        password="SecurePassword123!",
        full_name="Projection User",
    )


@pytest.fixture
def test_portfolio(db, test_user):
    return Portfolio.objects.create(
        user=test_user,
        name="Retirement Fund",
        base_currency="INR",
    )


@pytest.fixture
def test_investment(db, test_user, test_portfolio):
    from datetime import date

    from apps.assets.models import MutualFundDetail

    inv = Investment.objects.create(
        user=test_user,
        portfolio=test_portfolio,
        category="mutual_funds",
        asset_type="mutual_fund",
        display_name="Nifty 50 Index Fund",
        currency="INR",
        initial_value=Decimal("100000.00"),
        current_value=Decimal("100000.00"),
        valuation_method="NAV",
    )
    MutualFundDetail.objects.create(
        investment=inv,
        amc_name="HDFC Mutual Fund",
        scheme_name="Nifty 50 Index Fund",
        units=Decimal("1000.0000"),
        average_purchase_nav=Decimal("100.00"),
        purchase_date=date(2026, 1, 15),
    )
    return inv


class TestProjectionEngineFormulas:
    """
    Mathematical formula verification for ProjectionEngine (PROJ-001 to PROJ-004).
    """

    def test_proj_001_lump_sum_compound_growth(self):
        # 100,000 at 12% compounded monthly for 5 years:
        # FV = 100000 * (1 + 0.12/12)^(60) = 100000 * (1.01)^60 = 181,669.67
        fv = compound_lump_sum(
            principal=Decimal("100000.00"),
            annual_rate_pct=Decimal("12.00"),
            compounding_frequency=12,
            years=Decimal("5"),
        )
        assert fv == Decimal("181669.67")

    def test_proj_002_annuity_end_of_period(self):
        # 5,000 per month at 12% compounded monthly for 5 years (ordinary annuity):
        # FV = 5000 * ((1.01^60 - 1) / 0.01) = 5000 * 81.66967 = 408,348.35
        fv = compound_annuity_fv(
            payment=Decimal("5000.00"),
            annual_rate_pct=Decimal("12.00"),
            compounding_frequency=12,
            years=Decimal("5"),
            timing="END_OF_PERIOD",
        )
        assert fv == Decimal("408348.35")

    def test_proj_003_annuity_beginning_of_period(self):
        # Annuity due: ordinary annuity * 1.01 = 408,348.35 * 1.01 = 412,431.83
        fv = compound_annuity_fv(
            payment=Decimal("5000.00"),
            annual_rate_pct=Decimal("12.00"),
            compounding_frequency=12,
            years=Decimal("5"),
            timing="BEGINNING_OF_PERIOD",
        )
        assert fv == Decimal("412431.83")

    def test_proj_004_zero_rate_interest_safety(self):
        # At 0%, FV of annuity is sum of payments: 10,000 * 12 * 2 = 240,000.00
        fv = compound_annuity_fv(
            payment=Decimal("10000.00"),
            annual_rate_pct=Decimal("0.00"),
            compounding_frequency=12,
            years=Decimal("2"),
        )
        assert fv == Decimal("240000.00")


@pytest.mark.django_db
class TestProjectionEngineIntegrationAndAPIs:
    """
    Scenario generation, non-mutating guarantee, and REST API tests (PROJ-005 to PROJ-008).
    """

    def test_proj_005_multi_scenario_generation(self, test_investment):
        result = ProjectionEngine.calculate_projection(
            investment=test_investment,
            time_horizon_years=5,
            monthly_contribution=Decimal("5000.00"),
        )

        assert "conservative" in result["scenarios"]
        assert "base" in result["scenarios"]
        assert "optimistic" in result["scenarios"]

        cons = result["scenarios"]["conservative"]
        base = result["scenarios"]["base"]
        opt = result["scenarios"]["optimistic"]

        # Higher rate must yield higher projected value
        assert Decimal(opt["projected_future_value"]) > Decimal(base["projected_future_value"])
        assert Decimal(base["projected_future_value"]) > Decimal(cons["projected_future_value"])

    def test_proj_006_custom_rate_simulation(self, test_investment):
        result = ProjectionEngine.calculate_projection(
            investment=test_investment,
            time_horizon_years=3,
            custom_annual_rate=Decimal("10.50"),
        )
        assert "custom" in result["scenarios"]
        custom = result["scenarios"]["custom"]
        assert custom["annual_rate_percent"] == "10.50"
        assert len(custom["schedule"]) == 3

    def test_proj_007_strictly_non_mutating_guarantee(self, test_investment):
        """Calculating projections must NEVER modify actual investment record in database."""
        initial_val = test_investment.current_value
        initial_cost = test_investment.invested_amount
        initial_updated_at = test_investment.updated_at

        ProjectionEngine.calculate_projection(
            investment=test_investment,
            time_horizon_years=10,
            monthly_contribution=Decimal("20000.00"),
            custom_annual_rate=Decimal("25.00"),
        )

        test_investment.refresh_from_db()
        assert test_investment.current_value == initial_val
        assert test_investment.invested_amount == initial_cost
        assert test_investment.updated_at == initial_updated_at

    def test_proj_008_projection_api_endpoint(self, api_client, test_user, test_investment):
        api_client.force_authenticate(user=test_user)
        url = reverse(
            "valuation_api_v1:investment-projection-calculate",
            kwargs={"investment_id": test_investment.id},
        )

        payload = {
            "time_horizon_years": 5,
            "monthly_contribution": "5000.00",
            "contribution_timing": "END_OF_PERIOD",
            "compounding_frequency_per_year": 12,
        }
        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["investment_id"] == str(test_investment.id)
        assert data["formula_id"] == "ANNUITY_COMPOUND_FV_V1"
        assert "assumption_disclosures" in data
        assert "scenarios" in data
        assert "base" in data["scenarios"]
        assert len(data["scenarios"]["base"]["schedule"]) == 5

    def test_proj_009_mixed_compounding_and_contribution_frequency(self, test_investment):
        """
        Mixed frequencies: Monthly contributions (k=12) with Quarterly compounding (m=4).
        Must use effective periodic rate i = (1 + r/m)^(m/k) - 1.
        """
        result = ProjectionEngine.calculate_projection(
            investment=test_investment,
            time_horizon_years=5,
            monthly_contribution=Decimal("5000.00"),
            compounding_frequency_per_year=4,
            contribution_frequency_per_year=12,
            custom_annual_rate=Decimal("12.00"),
        )
        custom = result["scenarios"]["custom"]
        # Because quarterly compounding is less frequent than monthly, FV is slightly less than monthly compounding
        # Monthly compounding was 408,348.35 for annuity; quarterly will be ~407,314.93 + lump sum
        fv = Decimal(custom["projected_future_value"])
        assert fv > Decimal("500000.00")
        assert result["compounding_frequency_per_year"] == 4
        assert result["contribution_frequency_per_year"] == 12

    def test_proj_010_fractional_horizon_years(self, test_investment):
        """Fractional time horizons (e.g. 2.5 years) must be evaluated without integer truncating."""
        result = ProjectionEngine.calculate_projection(
            investment=test_investment,
            time_horizon_years=Decimal("2.5"),
            monthly_contribution=Decimal("2000.00"),
            custom_annual_rate=Decimal("10.00"),
        )
        custom = result["scenarios"]["custom"]
        schedule = custom["schedule"]
        # Steps: 1, 2, 2.5
        assert len(schedule) == 3
        assert schedule[-1]["year"] == 2.5
        # Total contributions for 2.5 years (30 months): 100,000 + (2,000 * 30) = 160,000.00
        assert schedule[-1]["invested_capital"] == "160000.00"

    def test_proj_011_gold_category_default_rates(self, db, test_user, test_portfolio):
        """Gold investments must map explicitly to gold rates (6%, 9%, 12%)."""
        gold_inv = Investment.objects.create(
            user=test_user,
            portfolio=test_portfolio,
            category="gold",
            asset_type="physical_gold",
            display_name="24K Sovereign Coin",
            currency="INR",
            initial_value=Decimal("50000.00"),
            current_value=Decimal("50000.00"),
        )
        result = ProjectionEngine.calculate_projection(investment=gold_inv, time_horizon_years=3)
        assert result["scenarios"]["conservative"]["annual_rate_percent"] == "6.00"
        assert result["scenarios"]["base"]["annual_rate_percent"] == "9.00"
        assert result["scenarios"]["optimistic"]["annual_rate_percent"] == "12.00"
