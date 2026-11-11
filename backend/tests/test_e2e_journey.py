import pytest
from django.core import mail
from rest_framework import status
from rest_framework.test import APIClient

from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def other_client():
    return APIClient()


@pytest.mark.django_db
class TestEndToEndMVPJourney:
    """
    Validates the complete Sprint 4 end-to-end user journey across all modules:
    Registration -> Verification -> Login -> Dashboard -> Portfolio CRUD ->
    Cross-user isolation -> Logout -> Protected Route Enforcement.
    """

    def test_complete_mvp_workflow(self, client, other_client):
        mail.outbox.clear()

        # Step 1: User Registration
        reg_payload = {
            "full_name": "Satish Sharma",
            "email": "satish@example.com",
            "password": "SecurePassword123!",
            "password_confirmation": "SecurePassword123!",
        }
        reg_res = client.post('/api/v1/auth/register/', reg_payload, format='json')
        assert reg_res.status_code == status.HTTP_201_CREATED
        user_data = reg_res.json()["user"]
        assert user_data["email"] == "satish@example.com"
        assert user_data["is_email_verified"] is False
        assert len(mail.outbox) == 1

        # Step 2: Extract verification token from sent email and verify account
        sent_email = mail.outbox[0]
        assert "satish@example.com" in sent_email.to
        token = sent_email.body.split("token=")[1].split("\n")[0].strip()

        verify_res = client.post('/api/v1/auth/verify-email/', {"token": token}, format='json')
        assert verify_res.status_code == status.HTTP_200_OK
        assert verify_res.json()["status"] == "verified"

        # Verify user is now marked verified in DB
        satish = User.objects.get(email="satish@example.com")
        assert satish.is_email_verified is True
        assert satish.email_verified_at is not None

        # Step 3: Login
        login_res = client.post('/api/v1/auth/login/', {
            "email": "satish@example.com",
            "password": "SecurePassword123!",
        }, format='json')
        assert login_res.status_code == status.HTTP_200_OK

        # Step 4: Access Protected Dashboard (Initial Empty State)
        dash_res = client.get('/api/v1/dashboard/overview/')
        assert dash_res.status_code == status.HTTP_200_OK
        dash_data = dash_res.json()
        assert dash_data["portfolio_count"] == 0
        assert dash_data["recent_portfolios"] == []
        assert "base_currency" not in dash_data

        # Step 5: Create First Portfolio
        port_a_res = client.post('/api/v1/portfolios/', {
            "name": "Retirement Fund",
            "description": "Long term index fund allocations",
            "base_currency": "USD",
        }, format='json')
        assert port_a_res.status_code == status.HTTP_201_CREATED
        port_a_id = port_a_res.json()["id"]

        # Step 6: Verify Dashboard Reflects Portfolio Creation
        dash_res_2 = client.get('/api/v1/dashboard/overview/')
        assert dash_res_2.status_code == status.HTTP_200_OK
        assert dash_res_2.json()["portfolio_count"] == 1
        assert dash_res_2.json()["recent_portfolios"][0]["id"] == port_a_id
        assert dash_res_2.json()["recent_portfolios"][0]["name"] == "Retirement Fund"
        assert dash_res_2.json()["recent_portfolios"][0]["base_currency"] == "USD"
        assert "base_currency" not in dash_res_2.json()

        # Step 7: View Portfolio Details
        detail_res = client.get(f'/api/v1/portfolios/{port_a_id}/')
        assert detail_res.status_code == status.HTTP_200_OK
        assert detail_res.json()["name"] == "Retirement Fund"

        # Step 8: Edit Portfolio
        update_res = client.patch(f'/api/v1/portfolios/{port_a_id}/', {
            "name": "Global Retirement Fund",
        }, format='json')
        assert update_res.status_code == status.HTTP_200_OK
        assert update_res.json()["name"] == "Global Retirement Fund"

        # Step 9: Verify Dashboard Reflects Portfolio Edit
        dash_res_3 = client.get('/api/v1/dashboard/overview/')
        assert dash_res_3.json()["recent_portfolios"][0]["name"] == "Global Retirement Fund"

        # Step 10: Create Second Portfolio
        port_b_res = client.post('/api/v1/portfolios/', {
            "name": "India Equities",
            "description": "Nifty 50 and Midcap index",
            "base_currency": "INR",
        }, format='json')
        assert port_b_res.status_code == status.HTTP_201_CREATED
        port_b_id = port_b_res.json()["id"]

        dash_res_4 = client.get('/api/v1/dashboard/overview/')
        assert dash_res_4.json()["portfolio_count"] == 2
        assert len(dash_res_4.json()["recent_portfolios"]) == 2

        # Step 11: Cross-User Isolation Enforcement
        # Register and log in as a second user
        other_client.post('/api/v1/auth/register/', {
            "full_name": "Sneha Patel",
            "email": "sneha@example.com",
            "password": "SecurePassword123!",
            "password_confirmation": "SecurePassword123!",
        }, format='json')

        # Sneha's dashboard must have 0 portfolios
        other_dash = other_client.get('/api/v1/dashboard/overview/')
        assert other_dash.json()["portfolio_count"] == 0
        assert other_dash.json()["recent_portfolios"] == []

        # Sneha cannot access, modify, or delete Satish's portfolio
        assert other_client.get(f'/api/v1/portfolios/{port_a_id}/').status_code == status.HTTP_404_NOT_FOUND
        assert other_client.patch(f'/api/v1/portfolios/{port_a_id}/', {"name": "Hacked"}).status_code == status.HTTP_404_NOT_FOUND
        assert other_client.delete(f'/api/v1/portfolios/{port_a_id}/').status_code == status.HTTP_404_NOT_FOUND

        # Step 12: Delete Portfolio A as Owner
        del_res = client.delete(f'/api/v1/portfolios/{port_a_id}/')
        assert del_res.status_code == status.HTTP_204_NO_CONTENT
        assert not Portfolio.objects.filter(id=port_a_id).exists()

        # Step 13: Verify Dashboard Reflects Deletion
        dash_res_5 = client.get('/api/v1/dashboard/overview/')
        assert dash_res_5.json()["portfolio_count"] == 1
        assert dash_res_5.json()["recent_portfolios"][0]["id"] == port_b_id

        # Step 14: System Health Check
        health_res = client.get('/api/v1/health/')
        assert health_res.status_code == status.HTTP_200_OK
        assert health_res.json() == {"status": "healthy", "database": "connected"}

        # Step 15: Logout
        logout_res = client.post('/api/v1/auth/logout/')
        assert logout_res.status_code == status.HTTP_200_OK

        # Step 16: Verify Protected Route Access is Blocked
        blocked_dash = client.get('/api/v1/dashboard/overview/')
        assert blocked_dash.status_code == status.HTTP_401_UNAUTHORIZED
        blocked_port = client.get('/api/v1/portfolios/')
        assert blocked_port.status_code == status.HTTP_401_UNAUTHORIZED
