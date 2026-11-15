from apps.portfolios.models import Portfolio
from apps.users.models import User

from .user_factory import create_test_user


def create_test_portfolio(
    user: User = None,
    name: str = "Test Growth Portfolio",
    description: str = "Automated test portfolio container",
    base_currency: str = "INR",
) -> Portfolio:
    portfolio_owner = user or create_test_user()
    return Portfolio.objects.create(
        user=portfolio_owner,
        name=name,
        description=description,
        base_currency=base_currency,
    )
