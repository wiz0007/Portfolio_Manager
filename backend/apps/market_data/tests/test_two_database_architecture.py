from decimal import Decimal

from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.apps import apps

import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.assets.models import Investment
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.instrument_reference import MarketInstrumentReference
from apps.market_data.models.instrument_request import InstrumentRequest
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.models.publication_event import MarketDataPublicationEvent
from apps.market_data.services.price_resolver import PriceResolver, ResolutionStatus
from config.database.registry import get_model_owner, MODEL_OWNERSHIP
from apps.market_data.services.sync_service import InstrumentIdentitySyncService
from apps.portfolios.models import Portfolio
from apps.users.models import User
from apps.watchlists.models import WatchlistItem
from config.database.routers import MarketDataRouter


@pytest.fixture
def auth_client(django_user_model):
    user = django_user_model.objects.create_user(
        email='twodb_operator@portfoliomanager.local',
        password='OperatorPass123!',
        is_staff=True,
    )
    client = APIClient()
    client.force_authenticate(user=user)
    return client, user


@pytest.mark.django_db(databases=['default', 'market_data'])
class TestTwoDatabaseArchitecture:
    """
    Validates the Two-Database Architecture and Application-Wide Market Data Integration.
    Tests database routing, identity synchronization, bulk resolution, and health visibility.
    """

    def test_router_target_mapping(self):
        router = MarketDataRouter()

        # Primary Database Models
        assert router.db_for_read(User) == 'default'
        assert router.db_for_write(User) == 'default'
        assert router.db_for_read(Portfolio) == 'default'
        assert router.db_for_write(Portfolio) == 'default'
        assert router.db_for_read(Investment) == 'default'
        assert router.db_for_write(Investment) == 'default'
        assert router.db_for_read(WatchlistItem) == 'default'
        assert router.db_for_write(WatchlistItem) == 'default'
        assert router.db_for_read(Instrument) == 'default'
        assert router.db_for_write(Instrument) == 'default'
        assert router.db_for_read(InstrumentRequest) == 'default'
        assert router.db_for_write(InstrumentRequest) == 'default'

        # Market Data Storage Database Models (must strictly route to market_data)
        assert router.db_for_read(MarketInstrumentReference) == 'market_data'
        assert router.db_for_write(MarketInstrumentReference) == 'market_data'
        assert router.db_for_read(MarketDataSeries) == 'market_data'
        assert router.db_for_write(MarketDataSeries) == 'market_data'
        assert router.db_for_read(PriceObservation) == 'market_data'
        assert router.db_for_write(PriceObservation) == 'market_data'
        assert router.db_for_read(InstrumentCoverage) == 'market_data'
        assert router.db_for_write(InstrumentCoverage) == 'market_data'

    def test_router_prevents_cross_database_relations(self):
        router = MarketDataRouter()
        user = User(email="test@user.com")
        obs = PriceObservation(value=Decimal('100.00'))

        # Cross-database relation between Primary (User) and Secondary (PriceObservation) MUST be rejected
        relation_allowed = router.allow_relation(user, obs)
        assert relation_allowed is False

        from apps.market_data.models.market_data_point import MarketDataPoint
        from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
        assert router.allow_relation(Instrument(), MarketDataPoint()) is False
        assert router.allow_relation(Instrument(), ProviderInstrumentMapping()) is False

    def test_instrument_identity_synchronization(self):
        test_inst = Instrument.objects.create(
            symbol="SYNC_TEST",
            name="Sync Test Corporation",
            asset_class=AssetClass.EQUITY,
            exchange="NSE",
            currency="INR",
            isin="INE999999999",
        )

        # Synchronization is deliberately deferred until the durable outbox worker runs.
        pending = InstrumentIdentitySyncService.process_pending_sync_events()
        assert pending['processed'] >= 1

        # Verify MarketInstrumentReference was synchronized
        ref = MarketInstrumentReference.objects.filter(id=test_inst.id).first()
        assert ref is not None
        assert ref.symbol == "SYNC_TEST"
        assert ref.name == "Sync Test Corporation"
        assert ref.exchange == "NSE"
        assert ref.isin == "INE999999999"

        # Verify reconciliation pass
        result = InstrumentIdentitySyncService.reconcile_all()
        assert result['status'] == 'SYNCHRONIZED'
        assert result['synced_total'] >= 1

    def test_bulk_price_resolver_api(self, auth_client):
        client, user = auth_client
        inst1 = Instrument.objects.create(symbol="BULK_INST1", name="Bulk 1", asset_class=AssetClass.EQUITY)
        inst2 = Instrument.objects.create(symbol="BULK_INST2", name="Bulk 2", asset_class=AssetClass.EQUITY)

        PriceObservation.objects.create(
            instrument=inst1,
            value=Decimal('2500.00'),
            effective_at=timezone.now(),
            status=ObservationStatus.PUBLISHED,
            trust_class='VERIFIED_OFFICIAL',
            recorded_by=user,
        )

        payload = {
            'instrument_ids': [str(inst1.id), str(inst2.id)],
        }
        response = client.post('/api/v1/market-data/prices/bulk-resolve/', data=payload, format='json')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data['total_requested'] == 2
        assert data['total_resolved'] == 1

        results = {r['symbol']: r for r in data['results']}
        assert results['BULK_INST1']['status'] == 'AVAILABLE'
        assert Decimal(results['BULK_INST1']['price']) == Decimal('2500.00')
        assert results['BULK_INST2']['status'] == 'MISSING'

    def test_market_data_models_require_explicit_registry_ownership(self):
        with pytest.raises(ImproperlyConfigured):
            get_model_owner('market_data', 'new_unregistered_model')

    def test_every_concrete_market_data_model_has_an_explicit_owner(self):
        registered = MODEL_OWNERSHIP['market_data']
        for model in apps.get_app_config('market_data').get_models():
            assert model._meta.model_name in registered, model._meta.label

    def test_published_observation_has_exact_series_and_outbox_event(self, auth_client):
        _, user = auth_client
        instrument = Instrument.objects.create(
            symbol='SERIES_TEST', name='Series Test', asset_class=AssetClass.EQUITY,
            exchange='NSE', currency='INR',
        )
        observation = PriceObservation.objects.create(
            instrument_id=instrument.id,
            value=Decimal('123.4500'),
            effective_at=timezone.now(),
            source='TEST_PERMITTED_FEED',
            status=ObservationStatus.PUBLISHED,
            trust_class='VERIFIED_PERMITTED_SECONDARY',
            recorded_by_id=user.id,
        )
        assert observation.series_id is not None
        series = MarketDataSeries.objects.using('market_data').get(pk=observation.series_id)
        assert series.instrument_id == instrument.id
        assert series.source == observation.source
        assert MarketDataPublicationEvent.objects.using('market_data').filter(
            observation_id=observation.id
        ).exists()
        resolved = PriceResolver.resolve_price(instrument, series_id=str(series.id))
        assert resolved.status == ResolutionStatus.AVAILABLE
        assert resolved.price == Decimal('123.4500')

    def test_synthetic_observation_never_resolves_as_portfolio_price(self, auth_client):
        _, user = auth_client
        instrument = Instrument.objects.create(
            symbol='SYNTH_TEST', name='Synthetic Test', asset_class=AssetClass.EQUITY,
            exchange='NSE', currency='INR',
        )
        observation = PriceObservation.objects.create(
            instrument_id=instrument.id, value=Decimal('50.0000'),
            effective_at=timezone.now(), source='DEMO',
            status=ObservationStatus.PUBLISHED, trust_class='SYNTHETIC',
            is_synthetic=True, recorded_by_id=user.id,
        )
        resolved = PriceResolver.resolve_price(instrument, series_id=str(observation.series_id))
        assert resolved.price is None
        assert resolved.status == ResolutionStatus.SYNTHETIC

    def test_published_observation_cannot_be_mutated(self, auth_client):
        _, user = auth_client
        instrument = Instrument.objects.create(
            symbol='IMMUTABLE_TEST', name='Immutable Test', asset_class=AssetClass.EQUITY,
            exchange='NSE', currency='INR',
        )
        observation = PriceObservation.objects.create(
            instrument_id=instrument.id, value=Decimal('10.0000'),
            effective_at=timezone.now(), source='TEST_FEED',
            status=ObservationStatus.PUBLISHED, trust_class='VERIFIED_PERMITTED_SECONDARY',
            recorded_by_id=user.id,
        )
        with pytest.raises(ValidationError):
            PriceObservation.objects.using('market_data').filter(pk=observation.pk).update(value=Decimal('11.0000'))
        observation.value = Decimal('11.0000')
        with pytest.raises(ValidationError):
            observation.save(using='market_data')

    def test_router_migration_isolation(self):
        router = MarketDataRouter()

        # Primary app migrations must only run on 'default'
        assert router.allow_migrate('default', 'users', 'user') is True
        assert router.allow_migrate('market_data', 'users', 'user') is False
        assert router.allow_migrate('default', 'portfolios', 'portfolio') is True
        assert router.allow_migrate('market_data', 'portfolios', 'portfolio') is False

        # Canonical instrument migrations must run on 'default'
        assert router.allow_migrate('default', 'market_data', 'instrument') is True
        assert router.allow_migrate('market_data', 'market_data', 'instrument') is False

    def test_database_health_api(self, auth_client):
        client, _ = auth_client
        Instrument.objects.create(symbol="HEALTH_INST", name="Health Inst")
        response = client.get('/api/v1/market-data/operations/database-health/')
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert 'status' in data
        assert 'databases' in data
        assert 'synchronization' in data
        assert data['databases']['primary']['status'] == 'HEALTHY'
        assert data['synchronization']['canonical_instruments_primary'] >= 1
