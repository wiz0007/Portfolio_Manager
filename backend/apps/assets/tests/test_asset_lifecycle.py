from decimal import Decimal

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import (
    CashAccountDetail,
    Investment,
    InvestmentTransaction,
)
from tests.factories import create_test_portfolio, create_test_user


@pytest.fixture
def owner(db):
    return create_test_user(email="asset_owner@example.com", full_name="Holding Owner")


@pytest.fixture
def intruder(db):
    return create_test_user(email="asset_intruder@example.com", full_name="Intruder")


@pytest.fixture
def portfolio(owner):
    return create_test_portfolio(user=owner, name="Main Master Portfolio", base_currency="INR")


@pytest.fixture
def other_portfolio(intruder):
    return create_test_portfolio(user=intruder, name="Intruder Portfolio", base_currency="INR")


@pytest.fixture
def client(owner):
    c = APIClient()
    c.force_authenticate(user=owner)
    return c


@pytest.fixture
def intruder_client(intruder):
    c = APIClient()
    c.force_authenticate(user=intruder)
    return c


@pytest.mark.django_db
class TestAssetLifecycleAndSchemas:
    """
    Exhaustive lifecycle testing for every supported investment subtype,
    multi-model atomicity, referential integrity, and security boundaries.
    """

    def test_cash_current_account_lifecycle(self, client, portfolio):
        """INV-001-CASH: Current account creation with overdraft and transactions."""
        payload = {
            "category": "cash",
            "asset_type": "current_account",
            "display_name": "Business Current A/C",
            "currency": "INR",
            "details": {
                "bank_name": "HDFC Bank",
                "account_nickname": "Business Current A/C",
                "account_type": "CURRENT",
                "masked_account_number": "XX9988",
                "current_balance": 350000.00,
                "balance_date": "2026-11-01",
                "overdraft_limit": 500000.00,
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["display_name"] == "Business Current A/C"
        assert float(data["current_value"]) == 350000.00
        assert data["details"]["overdraft_limit"] == "500000.0000"

        # Verify DB
        inv = Investment.objects.get(id=data["id"])
        assert inv.cash_detail.account_type == "CURRENT"
        assert inv.transactions.count() == 1

    def test_fixed_deposit_lifecycle(self, client, portfolio):
        """INV-001-FD: Fixed deposit with tenure, compounding, and maturity projection."""
        payload = {
            "category": "fixed_income",
            "asset_type": "fixed_deposit",
            "currency": "INR",
            "details": {
                "institution_name": "State Bank of India",
                "deposit_nickname": "3-Year Tax Saver FD",
                "deposit_type": "FIXED_DEPOSIT",
                "deposit_number": "FD-2026-001",
                "principal_amount": 100000.00,
                "start_date": "2026-11-01",
                "tenure_value": 3,
                "tenure_unit": "YEARS",
                "interest_rate_pct": 7.10,
                "compounding_frequency": "QUARTERLY",
                "payout_type": "CUMULATIVE",
                "maturity_date": "2029-11-01",
                "maturity_amount": 123500.00,
                "is_tax_saver": True,
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["display_name"] == "3-Year Tax Saver FD"
        assert data["details"]["is_tax_saver"] is True
        assert float(data["details"]["maturity_amount"]) == 123500.00

        inv = Investment.objects.get(id=data["id"])
        assert inv.deposit_detail.institution_name == "State Bank of India"

    def test_recurring_deposit_lifecycle(self, client, portfolio):
        """INV-001-RD: Recurring deposit with monthly installment."""
        payload = {
            "category": "fixed_income",
            "asset_type": "recurring_deposit",
            "currency": "INR",
            "details": {
                "institution_name": "ICICI Bank",
                "deposit_nickname": "Monthly Wealth RD",
                "deposit_type": "RECURRING_DEPOSIT",
                "principal_amount": 120000.00,
                "monthly_installment": 10000.00,
                "start_date": "2026-11-01",
                "tenure_value": 12,
                "tenure_unit": "MONTHS",
                "interest_rate_pct": 6.85,
                "compounding_frequency": "QUARTERLY",
                "payout_type": "CUMULATIVE",
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["details"]["deposit_type"] == "RECURRING_DEPOSIT"
        assert float(res.json()["details"]["monthly_installment"]) == 10000.00

    def test_bond_holding_lifecycle(self, client, portfolio):
        """INV-001-BOND: Sovereign / corporate bond with coupon rate and maturity."""
        payload = {
            "category": "fixed_income",
            "asset_type": "bond",
            "currency": "INR",
            "details": {
                "bond_name": "7.26% GS 2033",
                "issuer_name": "Government of India",
                "bond_type": "GOVERNMENT",
                "isin": "IN0020230085",
                "face_value": 100.00,
                "purchase_price": 101.50,
                "quantity": 1000,
                "coupon_rate_pct": 7.26,
                "coupon_frequency": "SEMI_ANNUALLY",
                "purchase_date": "2026-10-01",
                "maturity_date": "2033-02-06",
                "credit_rating": "SOVEREIGN",
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert float(data["initial_value"]) == 101500.00  # 1000 * 101.50
        assert data["details"]["bond_type"] == "GOVERNMENT"

    def test_mutual_fund_lifecycle(self, client, portfolio):
        """INV-001-MF: Mutual fund units, purchase NAV, and SIP terms."""
        payload = {
            "category": "mutual_funds",
            "asset_type": "mutual_fund",
            "currency": "INR",
            "details": {
                "amc_name": "Parag Parikh Financial Advisory Services",
                "scheme_name": "Parag Parikh Flexi Cap Fund Direct Growth",
                "scheme_category": "Flexi Cap",
                "plan": "DIRECT",
                "option": "GROWTH",
                "folio_number": "PPFAS-998811",
                "units": 1500.250,
                "average_purchase_nav": 65.40,
                "purchase_date": "2026-09-15",
                "is_sip": True,
                "sip_amount": 10000.00,
                "sip_frequency": "MONTHLY",
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        expected_cost = Decimal("1500.250") * Decimal("65.40")
        assert abs(Decimal(str(data["initial_value"])) - expected_cost) < Decimal("0.01")
        assert data["details"]["plan"] == "DIRECT"

    def test_gold_physical_and_sgb_lifecycle(self, client, portfolio):
        """INV-001-GOLD: Physical gold and Sovereign Gold Bond series."""
        # 1. Physical Gold
        res = client.post(
            f'/api/v1/portfolios/{portfolio.id}/investments/',
            {
                "category": "gold",
                "asset_type": "physical_gold",
                "currency": "INR",
                "details": {
                    "item_name": "24K Gold Bar 50g",
                    "gold_type": "PHYSICAL",
                    "weight_grams": 50.0,
                    "purity_karat": 24.0,
                    "purchase_price": 375000.00,
                    "making_charges": 5000.00,
                    "gst_amount": 11400.00,
                    "purchase_date": "2026-10-20",
                },
            },
            format='json',
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert float(res.json()["initial_value"]) == 391400.00  # 375k + 5k + 11.4k

        # 2. Sovereign Gold Bond
        res = client.post(
            f'/api/v1/portfolios/{portfolio.id}/investments/',
            {
                "category": "gold",
                "asset_type": "sovereign_gold_bond",
                "currency": "INR",
                "details": {
                    "item_name": "SGB 2026-27 Series I",
                    "gold_type": "SGB",
                    "purchase_price": 62000.00,
                    "purchase_date": "2026-06-15",
                    "sgb_series": "2026-27 Series I",
                    "coupon_rate_pct": 2.50,
                    "maturity_date": "2034-06-15",
                },
            },
            format='json',
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["details"]["sgb_series"] == "2026-27 Series I"

    def test_crypto_token_lifecycle(self, client, portfolio):
        """INV-001-CRYPTO: Cryptocurrency token with wallet and network transaction."""
        payload = {
            "category": "crypto",
            "asset_type": "cryptocurrency",
            "currency": "INR",
            "details": {
                "token_name": "Ethereum",
                "symbol": "ETH",
                "network": "Ethereum Mainnet",
                "quantity": 2.5,
                "purchase_price_per_token": 250000.00,
                "purchase_date": "2026-10-10",
                "wallet_type": "HARDWARE_WALLET",
                "network_fees": 1200.00,
                "transaction_hash": "0x4a123f89e...",
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert float(data["initial_value"]) == 626200.00  # (2.5 * 250000) + 1200
        assert data["details"]["symbol"] == "ETH"

    def test_real_estate_agricultural_land_lifecycle(self, client, portfolio):
        """INV-001-LAND: Real Estate Agricultural land with Khasra & circle rate."""
        payload = {
            "category": "real_estate",
            "asset_type": "land_plot",
            "currency": "INR",
            "details": {
                "property_name": "Rishikesh Farm Land",
                "property_type": "AGRICULTURAL",
                "land_classification": "AGRICULTURAL",
                "state": "Uttarakhand",
                "district": "Dehradun",
                "tehsil": "Rishikesh",
                "village": "Shyampur",
                "survey_or_plot_number": "Khasra 219/3",
                "land_area": 3.0,
                "area_unit": "ACRE",
                "ownership_percentage": 50.0,
                "acquisition_date": "2026-03-20",
                "purchase_price": 6000000.00,
                "stamp_duty": 300000.00,
                "registration_charges": 120000.00,
                "other_acquisition_costs": 80000.00,
                "estimated_current_value": 7200000.00,
                "valuation_date": "2026-11-01",
                "valuation_source": "District Circle Rate 2026",
            },
        }

        res = client.post(f'/api/v1/portfolios/{portfolio.id}/investments/', payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # 50% ownership share: (60L + 3L + 1.2L + 0.8L) * 50% = 32.5L
        assert float(data["initial_value"]) == 3250000.00
        # 50% of 72L = 36L
        assert float(data["current_value"]) == 3600000.00
        assert data["details"]["survey_or_plot_number"] == "Khasra 219/3"
        assert data["details"]["state"] == "Uttarakhand"

    def test_patch_investment_and_child_detail(self, client, portfolio):
        """INV-004: PATCH holding updates root fields and child detail fields."""
        create_res = client.post(
            f'/api/v1/portfolios/{portfolio.id}/investments/',
            {
                "category": "cash",
                "asset_type": "savings_account",
                "display_name": "Old Nickname",
                "details": {"bank_name": "SBI", "current_balance": 10000},
            },
            format='json',
        )
        inv_id = create_res.json()["id"]

        patch_res = client.patch(
            f'/api/v1/portfolios/{portfolio.id}/investments/{inv_id}/',
            {
                "display_name": "New Primed Bank",
                "current_value": 15000,
                "notes": "Emergency pool",
                "details": {"account_nickname": "New Primed Bank"},
            },
            format='json',
        )
        assert patch_res.status_code == status.HTTP_200_OK
        data = patch_res.json()
        assert data["display_name"] == "New Primed Bank"
        assert float(data["current_value"]) == 15000.00
        assert data["notes"] == "Emergency pool"

        inv = Investment.objects.get(id=inv_id)
        assert inv.display_name == "New Primed Bank"
        assert inv.cash_detail.account_nickname == "New Primed Bank"

    def test_delete_investment_cascades_cleanly(self, client, portfolio):
        """INV-005: Deleting investment removes child details, transactions, and valuations."""
        create_res = client.post(
            f'/api/v1/portfolios/{portfolio.id}/investments/',
            {
                "category": "cash",
                "asset_type": "savings_account",
                "display_name": "To Delete",
                "details": {"bank_name": "PNB", "current_balance": 5000},
            },
            format='json',
        )
        inv_id = create_res.json()["id"]

        # Confirm existence
        assert Investment.objects.filter(id=inv_id).exists()
        assert CashAccountDetail.objects.filter(investment_id=inv_id).exists()
        assert InvestmentTransaction.objects.filter(investment_id=inv_id).exists()

        # Delete
        del_res = client.delete(f'/api/v1/portfolios/{portfolio.id}/investments/{inv_id}/')
        assert del_res.status_code == status.HTTP_204_NO_CONTENT

        # Confirm cascading cleanup
        assert not Investment.objects.filter(id=inv_id).exists()
        assert not CashAccountDetail.objects.filter(investment_id=inv_id).exists()
        assert not InvestmentTransaction.objects.filter(investment_id=inv_id).exists()

    def test_atomic_rollback_on_failure(self, client, portfolio):
        """INV-ATOM: Failure during creation leaves zero orphaned records."""
        initial_inv_count = Investment.objects.count()
        initial_tx_count = InvestmentTransaction.objects.count()

        # Attempt creation with missing detail requirements or database error
        from unittest.mock import patch
        with patch('apps.assets.models.CashAccountDetail.objects.create', side_effect=Exception("DB Failure")):
            with pytest.raises(Exception):
                client.post(
                    f'/api/v1/portfolios/{portfolio.id}/investments/',
                    {
                        "category": "cash",
                        "asset_type": "savings_account",
                        "details": {"bank_name": "Test", "current_balance": 1000},
                    },
                    format='json',
                )

        # Assert full rollback
        assert Investment.objects.count() == initial_inv_count
        assert InvestmentTransaction.objects.count() == initial_tx_count

    def test_idor_protection_between_users(self, client, intruder_client, portfolio, other_portfolio):
        """SEC-IDOR: Intruder cannot view, update, or delete owner's investment."""
        create_res = client.post(
            f'/api/v1/portfolios/{portfolio.id}/investments/',
            {
                "category": "cash",
                "asset_type": "savings_account",
                "display_name": "Confidential Reserve",
                "details": {"bank_name": "HDFC", "current_balance": 999999},
            },
            format='json',
        )
        inv_id = create_res.json()["id"]

        # 1. Intruder attempts to GET owner's investment
        res = intruder_client.get(f'/api/v1/portfolios/{portfolio.id}/investments/{inv_id}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # 2. Intruder attempts to PATCH owner's investment
        res = intruder_client.patch(
            f'/api/v1/portfolios/{portfolio.id}/investments/{inv_id}/',
            {"display_name": "Hijacked"},
            format='json',
        )
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # 3. Intruder attempts to DELETE owner's investment
        res = intruder_client.delete(f'/api/v1/portfolios/{portfolio.id}/investments/{inv_id}/')
        assert res.status_code == status.HTTP_404_NOT_FOUND

        # Confirm untouched
        inv = Investment.objects.get(id=inv_id)
        assert inv.display_name == "Confidential Reserve"
