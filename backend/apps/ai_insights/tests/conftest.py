from datetime import datetime, timezone
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.assets.models.investment import AssetCategory, Investment
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.portfolios.models import Portfolio
from apps.users.models import User


@pytest.fixture
def auth_user():
    return User.objects.create_user(
        email='ai_user@example.com',
        password='Password123!',
        full_name='AI Test User',
        email_verified_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def other_user():
    return User.objects.create_user(
        email='other_ai_user@example.com',
        password='Password123!',
        full_name='Other AI User',
        email_verified_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def auth_client(auth_user):
    client = APIClient()
    client.force_authenticate(user=auth_user)
    return client


@pytest.fixture
def sample_portfolio(auth_user):
    return Portfolio.objects.create(
        user=auth_user,
        name='Main Wealth Portfolio',
        base_currency='USD',
    )


@pytest.fixture
def other_portfolio(other_user):
    return Portfolio.objects.create(
        user=other_user,
        name='Other User Portfolio',
        base_currency='USD',
    )


@pytest.fixture
def sample_instrument():
    return Instrument.objects.create(
        symbol='AAPL',
        name='Apple Inc.',
        asset_class=AssetClass.EQUITY,
        exchange='NASDAQ',
        currency='USD',
    )


@pytest.fixture
def sample_investment(auth_user, sample_portfolio, sample_instrument):
    return Investment.objects.create(
        user=auth_user,
        portfolio=sample_portfolio,
        instrument=sample_instrument,
        category=AssetCategory.EQUITY,
        asset_type='EQUITY',
        display_name='Apple Stock Holding',
        currency='USD',
        initial_value=Decimal('7500'),
        current_value=Decimal('9000'),
    )
