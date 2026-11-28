"""
Authoritative Model Ownership Registry for Portfolio Manager.
Enforces the strict two-database architecture boundary across the entire application.

Primary Portfolio Database ('default'):
- Users, authentication, profiles, permissions, sessions
- Portfolios, investments, asset-specific details, investment transactions, valuation snapshots
- Watchlists
- Canonical instruments (Instrument, InstrumentRequest, InstrumentReferenceData)
- Primary Outbox: InstrumentSyncEvent (for durable identity sync to secondary DB)

Market Data Storage Database ('market_data'):
- MarketInstrumentReference (local projection of canonical instrument)
- MarketDataSeries (time-series series metadata)
- PriceObservation (sole authoritative historical time-series observation store)
- InstrumentCoverage (collection policies)
- MarketDataWorklist & MarketDataWorklistItem
- ProviderInstrumentMapping
- PriceImportBatch & PriceImportRowError
- Secondary Outbox: MarketDataPublicationEvent (for durable valuation refresh)
- (Deprecated) MarketDataPoint
"""

from typing import Dict, Set

from django.core.exceptions import ImproperlyConfigured

PRIMARY_DATABASE = 'default'
MARKET_DATA_DATABASE = 'market_data'

# Every model in the application has exactly one intended database owner
MODEL_OWNERSHIP: Dict[str, Dict[str, str]] = {
    # Core Primary Models
    'users': {
        'user': PRIMARY_DATABASE,
    },
    'auth': {
        'group': PRIMARY_DATABASE,
        'permission': PRIMARY_DATABASE,
    },
    'contenttypes': {
        'contenttype': PRIMARY_DATABASE,
    },
    'sessions': {
        'session': PRIMARY_DATABASE,
    },
    'admin': {
        'logentry': PRIMARY_DATABASE,
    },
    'portfolios': {
        'portfolio': PRIMARY_DATABASE,
    },
    'assets': {
        'investment': PRIMARY_DATABASE,
        'investmenttransaction': PRIMARY_DATABASE,
        'investmentvaluation': PRIMARY_DATABASE,
        'equitydetail': PRIMARY_DATABASE,
        'mutualfunddetail': PRIMARY_DATABASE,
        'depositdetail': PRIMARY_DATABASE,
        'bonddetail': PRIMARY_DATABASE,
        'realestatedetail': PRIMARY_DATABASE,
        'golddetail': PRIMARY_DATABASE,
        'cryptodetail': PRIMARY_DATABASE,
        'cashaccountdetail': PRIMARY_DATABASE,
    },
    'watchlists': {
        'watchlistitem': PRIMARY_DATABASE,
    },
    'analytics': {
        'fxrate': PRIMARY_DATABASE,
    },
    # Market Data App Models partitioned by ownership boundary
    'market_data': {
        # Primary canonical reference entities
        'instrument': PRIMARY_DATABASE,
        'instrumentrequest': PRIMARY_DATABASE,
        'instrumentreferencedata': PRIMARY_DATABASE,
        'instrumentsyncevent': PRIMARY_DATABASE,

        # Secondary Market Data entities
        'marketinstrumentreference': MARKET_DATA_DATABASE,
        'marketdataseries': MARKET_DATA_DATABASE,
        'priceobservation': MARKET_DATA_DATABASE,
        'marketdatapoint': MARKET_DATA_DATABASE,
        'instrumentcoverage': MARKET_DATA_DATABASE,
        'marketdataworklist': MARKET_DATA_DATABASE,
        'marketdataworklistitem': MARKET_DATA_DATABASE,
        'providerinstrumentmapping': MARKET_DATA_DATABASE,
        'priceimportbatch': MARKET_DATA_DATABASE,
        'priceimportrowerror': MARKET_DATA_DATABASE,
        'marketdatapublicationevent': MARKET_DATA_DATABASE,
    },
}


def get_model_owner(app_label: str, model_name: str) -> str:
    """Returns the owning database alias for a given app_label and model_name."""
    app_models = MODEL_OWNERSHIP.get(app_label.lower())
    if app_models and model_name.lower() in app_models:
        return app_models[model_name.lower()]
    if app_label.lower() == 'market_data':
        raise ImproperlyConfigured(
            f"Model ownership is missing for market_data.{model_name}. Add it explicitly to MODEL_OWNERSHIP."
        )
    # Non-market-data application models remain primary-owned by default.
    return PRIMARY_DATABASE


def get_market_data_models() -> Set[str]:
    """Returns all model names owned by the market_data database."""
    return {
        model_name
        for app, models in MODEL_OWNERSHIP.items()
        for model_name, db in models.items()
        if db == MARKET_DATA_DATABASE
    }


def get_primary_models() -> Set[str]:
    """Returns all model names owned by the primary default database."""
    return {
        model_name
        for app, models in MODEL_OWNERSHIP.items()
        for model_name, db in models.items()
        if db == PRIMARY_DATABASE
    }
