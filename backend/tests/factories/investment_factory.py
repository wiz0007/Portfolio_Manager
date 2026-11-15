from decimal import Decimal

from django.utils import timezone

from apps.assets.models import (
    CashAccountDetail,
    EquityDetail,
    Investment,
    InvestmentTransaction,
    InvestmentValuation,
    RealEstateDetail,
)
from apps.portfolios.models import Portfolio
from apps.users.models import User

from .portfolio_factory import create_test_portfolio


def create_test_investment(
    portfolio: Portfolio | None = None,
    user: User | None = None,
    category: str = "cash",
    asset_type: str = "savings_account",
    display_name: str = "Test Savings A/C",
    currency: str = "INR",
    initial_value: Decimal = Decimal("50000.00"),
    current_value: Decimal = Decimal("50000.00"),
    notes: str = "Test investment note",
    details: dict | None = None,
) -> Investment:
    port = portfolio or create_test_portfolio(user=user)
    owner = user or port.user

    inv = Investment.objects.create(
        portfolio=port,
        user=owner,
        category=category,
        asset_type=asset_type,
        display_name=display_name,
        currency=currency,
        initial_value=initial_value,
        current_value=current_value,
        notes=notes,
    )

    det = details or {}
    today = timezone.now().date()

    if category == "cash":
        CashAccountDetail.objects.create(
            investment=inv,
            bank_name=det.get("bank_name", "HDFC Bank"),
            account_nickname=det.get("account_nickname", display_name),
            account_type=det.get("account_type", "SAVINGS"),
            current_balance=initial_value,
            balance_date=det.get("balance_date", today),
            interest_rate_pct=Decimal("3.0"),
        )
    elif category == "equity":
        qty = Decimal(str(det.get("quantity", 25)))
        price = Decimal(str(det.get("average_buy_price", 2000)))
        EquityDetail.objects.create(
            investment=inv,
            company_name=det.get("company_name", "Infosys"),
            symbol=det.get("symbol", "INFY"),
            exchange=det.get("exchange", "NSE"),
            quantity=qty,
            average_buy_price=price,
            purchase_date=det.get("purchase_date", today),
        )
    elif category == "real_estate":
        RealEstateDetail.objects.create(
            investment=inv,
            property_name=det.get("property_name", display_name),
            property_type=det.get("property_type", "LAND"),
            land_classification=det.get("land_classification", "AGRICULTURAL"),
            state=det.get("state", "Uttarakhand"),
            district=det.get("district", "Dehradun"),
            tehsil=det.get("tehsil", "Vikas Nagar"),
            village=det.get("village", "Sahaspur"),
            survey_or_plot_number=det.get("survey_or_plot_number", "Khasra 101"),
            area=Decimal("1.5"),
            area_unit="ACRE",
            ownership_percentage=Decimal("100.0"),
            purchase_price=initial_value,
            acquisition_date=det.get("acquisition_date", today),
            estimated_current_value=current_value,
            valuation_date=today,
        )

    # Initial transaction
    InvestmentTransaction.objects.create(
        investment=inv,
        portfolio=port,
        user=owner,
        transaction_type="INITIAL_PURCHASE",
        transaction_date=today,
        amount=initial_value,
        currency=currency,
    )

    # Valuation snapshot
    InvestmentValuation.objects.create(
        investment=inv,
        valuation_date=today,
        amount=current_value,
        source="TEST_FACTORY",
    )

    return inv
