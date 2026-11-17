from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import Investment, InvestmentTransaction
from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.mark.django_db
class TestTransactionLedgerIntegrity:
    """
    Test suite for Workstream B: Transaction Ledger Contract (TXN-001 to TXN-008).
    """

    @pytest.fixture(autouse=True)
    def setup_fixtures(self, db):
        self.user = User.objects.create_user(
            email="txn_test_user@example.com",
            password="StrongPassword123!",
            full_name="Ledger User",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Ledger Test Portfolio",
            base_currency="INR"
        )
        self.base_url = f"/api/v1/portfolios/{self.portfolio.id}/investments/"

    def test_txn_001_correct_acquisition_date_recorded_in_opening_transaction(self):
        """TXN-001: Opening transaction uses the actual historical acquisition/opening date."""
        target_acq_date = "2024-05-10"
        res = self.client.post(
            self.base_url,
            {
                "category": "cash",
                "asset_type": "savings_account",
                "currency": "INR",
                "details": {
                    "bank_name": "State Bank of India",
                    "account_nickname": "Historical Salary Account",
                    "current_balance": "45000.00",
                    "balance_date": target_acq_date
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_201_CREATED
        inv_id = res.json()["id"]

        tx = InvestmentTransaction.objects.filter(investment_id=inv_id, transaction_type="INITIAL_PURCHASE").first()
        assert tx is not None
        assert str(tx.transaction_date) == target_acq_date

    def test_txn_002_gross_amount_fees_and_taxes_semantics(self):
        """TXN-002: Distinct gross amount, fees, taxes, and net cash flow contract."""
        res = self.client.post(
            self.base_url,
            {
                "category": "equity",
                "asset_type": "listed_stock",
                "currency": "INR",
                "details": {
                    "company_name": "Reliance Industries",
                    "symbol": "RELIANCE",
                    "quantity": "100.0000",
                    "purchase_price": "2500.0000",
                    "brokerage": "50.0000",
                    "stt_charges": "25.0000",
                    "purchase_date": "2026-10-01"
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_201_CREATED
        inv_id = res.json()["id"]

        tx = InvestmentTransaction.objects.get(investment_id=inv_id, transaction_type="INITIAL_PURCHASE")
        assert tx.gross_amount == Decimal("250000.0000")  # 100 * 2500
        assert tx.fees == Decimal("50.0000")
        assert tx.taxes == Decimal("25.0000")
        assert tx.net_cash_flow == Decimal("250075.0000")  # Gross + Fees + Taxes
        assert tx.amount == Decimal("250000.0000")

    def test_txn_003_net_cash_flow_purchase_direction(self):
        """TXN-003: Net cash outflow for purchase equals Gross + Fees + Taxes."""
        tx = InvestmentTransaction.objects.create(
            investment=Investment.objects.create(
                user=self.user,
                portfolio=self.portfolio,
                category="equity",
                asset_type="listed_stock",
                display_name="Test Stock",
                currency="INR"
            ),
            portfolio=self.portfolio,
            user=self.user,
            transaction_type="BUY",
            transaction_date=timezone.now().date(),
            units=Decimal("10"),
            price_per_unit=Decimal("100"),
            gross_amount=Decimal("1000.00"),
            fees=Decimal("20.00"),
            taxes=Decimal("10.00"),
            currency="INR"
        )
        assert tx.net_cash_flow == Decimal("1030.00")

    def test_txn_004_net_cash_flow_sale_direction(self):
        """TXN-004: Net cash inflow for sale equals Gross - Fees - Taxes."""
        tx = InvestmentTransaction.objects.create(
            investment=Investment.objects.create(
                user=self.user,
                portfolio=self.portfolio,
                category="equity",
                asset_type="listed_stock",
                display_name="Test Stock Sale",
                currency="INR"
            ),
            portfolio=self.portfolio,
            user=self.user,
            transaction_type="SELL",
            transaction_date=timezone.now().date(),
            units=Decimal("10"),
            price_per_unit=Decimal("150"),
            gross_amount=Decimal("1500.00"),
            fees=Decimal("25.00"),
            taxes=Decimal("15.00"),
            currency="INR"
        )
        assert tx.net_cash_flow == Decimal("1460.00")

    def test_txn_005_initial_transaction_idempotency(self):
        """TXN-005: Repeated requests cannot create duplicate opening transactions."""
        res = self.client.post(
            self.base_url,
            {
                "category": "cash",
                "asset_type": "savings_account",
                "currency": "INR",
                "details": {
                    "bank_name": "Canara Bank",
                    "current_balance": "12000.00",
                    "balance_date": "2026-11-01"
                }
            },
            format='json'
        )
        assert res.status_code == status.HTTP_201_CREATED
        inv_id = res.json()["id"]
        tx_count = InvestmentTransaction.objects.filter(investment_id=inv_id, transaction_type="INITIAL_PURCHASE").count()
        assert tx_count == 1

    def test_txn_006_immutable_historical_transaction_on_investment_patch(self):
        """TXN-006: Investment PATCH operations must not modify historical transaction records."""
        res = self.client.post(
            self.base_url,
            {
                "category": "cash",
                "asset_type": "savings_account",
                "currency": "INR",
                "details": {
                    "bank_name": "Axis Bank",
                    "current_balance": "30000.00",
                    "balance_date": "2026-01-01"
                }
            },
            format='json'
        )
        inv_id = res.json()["id"]
        original_tx = InvestmentTransaction.objects.get(investment_id=inv_id)
        original_amount = original_tx.amount
        original_date = original_tx.transaction_date

        # Patch investment
        patch_res = self.client.patch(
            f"/api/v1/portfolios/{self.portfolio.id}/investments/{inv_id}/",
            {"display_name": "Renamed Axis Account", "current_value": "35000.00"},
            format='json'
        )
        assert patch_res.status_code == status.HTTP_200_OK

        original_tx.refresh_from_db()
        assert original_tx.amount == original_amount
        assert original_tx.transaction_date == original_date

    def test_txn_008_legacy_transaction_compatibility(self):
        """TXN-008: Legacy records with only amount and fees default gross and net cash flow properly."""
        tx = InvestmentTransaction(
            investment=Investment.objects.create(
                user=self.user,
                portfolio=self.portfolio,
                category="cash",
                asset_type="savings_account",
                display_name="Legacy Holding",
                currency="INR"
            ),
            portfolio=self.portfolio,
            user=self.user,
            transaction_type="INITIAL_PURCHASE",
            transaction_date=timezone.now().date(),
            amount=Decimal("5000.00"),
            fees=Decimal("0.00"),
            currency="INR"
        )
        tx.save()
        assert tx.gross_amount == Decimal("5000.00")
        assert tx.net_cash_flow == Decimal("5000.00")
        assert tx.taxes == Decimal("0.00")
