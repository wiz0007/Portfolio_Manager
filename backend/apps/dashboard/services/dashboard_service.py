from typing import Any

from apps.users.models import User


class DashboardService:
    """
    Business logic and aggregations for the user dashboard overview.
    """

    @staticmethod
    def get_user_dashboard_overview(user: User) -> dict[str, Any]:
        """
        Gathers dashboard overview data for the authenticated user.
        In Sprint 2, portfolio models are in preparation for Sprint 3,
        so portfolio_count is accurately 0 and recent_portfolios is an empty list.
        """
        return {
            "user": {
                "id": str(user.id),
                "full_name": user.full_name,
                "email": user.email,
            },
            "portfolio_count": 0,
            "recent_portfolios": [],
        }
