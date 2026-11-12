from typing import Any

from apps.portfolios.models import Portfolio
from apps.users.models import User


class DashboardService:
    """
    Business logic and aggregations for the user dashboard overview.
    Connects to real user portfolios.
    """

    @staticmethod
    def get_user_dashboard_overview(user: User) -> dict[str, Any]:
        """
        Gathers real dashboard overview data for the authenticated user.
        Queries real portfolio counts and recent portfolios, scoped strictly to the user.
        """
        user_portfolios = Portfolio.objects.filter(user=user).order_by('-updated_at')
        count = user_portfolios.count()

        recent = [
            {
                "id": p.id,
                "name": p.name,
                "base_currency": p.base_currency,
                "created_at": p.created_at,
                "updated_at": p.updated_at,
            }
            for p in user_portfolios[:5]
        ]
        return {
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
            },
            "portfolio_count": count,
            "recent_portfolios": recent,
        }
