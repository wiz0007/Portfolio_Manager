from typing import Optional, Type

from django.conf import settings
from django.db import models

from config.database.registry import (
    MARKET_DATA_DATABASE,
    PRIMARY_DATABASE,
    get_model_owner,
)


class MarketDataRouter:
    """
    Two-Database Architecture Router.

    Enforces strict architectural separation defined in the Model Ownership Registry:
    1. Primary Portfolio Database ('default'):
       - Users, Authentication, Sessions
       - Portfolios, Holdings, Transactions, Valuations
       - Watchlists
       - Canonical Instrument Master identity (Instrument, InstrumentRequest, InstrumentReferenceData, InstrumentSyncEvent)

    2. Market Data Storage Database ('market_data'):
       - MarketInstrumentReference (synchronized local identity projection)
       - MarketDataSeries (series metadata)
       - PriceObservation (daily OHLCV, NAV, verified provenance)
       - InstrumentCoverage, PriceImportBatch, PriceImportRowError,
         MarketDataWorklist, MarketDataWorklistItem, ProviderInstrumentMapping,
         MarketDataPublicationEvent
       - (Deprecated) MarketDataPoint
    """

    MARKET_DATA_APP = 'market_data'

    def _is_market_data_configured(self) -> bool:
        databases = getattr(settings, 'DATABASES', {})
        return MARKET_DATA_DATABASE in databases

    def _target_db_for_model(self, model: Type[models.Model]) -> str:
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        target_db = get_model_owner(app_label, model_name)

        if target_db == MARKET_DATA_DATABASE:
            # If the secondary database is configured, route strictly to it.
            # In testing/CI or when configured, it always returns 'market_data'.
            if self._is_market_data_configured():
                return MARKET_DATA_DATABASE
            # In development fallback when secondary DB is pending configuration,
            # warn or route to market_data alias so operations fail fast rather than corrupting default.
            return MARKET_DATA_DATABASE

        return PRIMARY_DATABASE

    def db_for_read(self, model: Type[models.Model], **hints) -> str:
        """Determines the database alias for read operations."""
        return self._target_db_for_model(model)

    def db_for_write(self, model: Type[models.Model], **hints) -> str:
        """Determines the database alias for write operations."""
        return self._target_db_for_model(model)

    def allow_relation(self, obj1: models.Model, obj2: models.Model, **hints) -> Optional[bool]:
        """
        Denies cross-database relations.
        Objects may only share ORM relations if they reside in the same database.
        Cross-database references must be maintained via scalar UUIDs or local projections.
        """
        db1 = self._target_db_for_model(obj1.__class__)
        db2 = self._target_db_for_model(obj2.__class__)

        if db1 == db2:
            return True
        if obj1._meta.model_name == 'marketdatapoint' or obj2._meta.model_name == 'marketdatapoint':
            return True
        return False

    def allow_migrate(
        self,
        db: str,
        app_label: str,
        model_name: Optional[str] = None,
        **hints,
    ) -> bool:
        """
        Ensures migrations run only against their designated owner database.
        Secondary market data schema runs strictly on 'market_data'.
        Primary portfolio and user apps run strictly on 'default'.
        """
        if not model_name:
            # If model_name is not provided, check app level
            if app_label == self.MARKET_DATA_APP:
                return True
            return db == PRIMARY_DATABASE

        target_db = get_model_owner(app_label, model_name)
        return db == target_db
