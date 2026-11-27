"""Cryptocurrency market data synchronization and ingestion service."""
import json
import logging
from typing import Any, Dict, List, Optional

from django.utils import timezone as dj_timezone

from apps.market_data.models.coverage import (
    CollectionCadence,
    CoverageStatus,
    InstrumentCoverage,
    PriceType,
    QuotationUnit,
)
from apps.market_data.models.instrument import AssetClass, Instrument, InstrumentStatus
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.providers.coingecko.client import CoinGeckoClient
from apps.market_data.providers.coingecko.constants import (
    SUPPORTED_COINS,
)
from apps.market_data.providers.coingecko.serializers import (
    serialize_chart_data,
    serialize_market_item,
)
from apps.market_data.services.sync_service import InstrumentIdentitySyncService

logger = logging.getLogger(__name__)


class CryptoMarketDataService:
    """Ingests cryptocurrency catalogue, current quotes, and historical series from CoinGecko."""

    @classmethod
    def sync_catalogue(cls, coins: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Creates canonical Instrument entries, secondary mappings, coverage, and series
        for supported cryptocurrencies.
        """
        coins_to_sync = coins or SUPPORTED_COINS
        created_count = 0
        updated_count = 0
        synced_instruments = []

        for item in coins_to_sync:
            coin_id = item['id'].lower().strip()
            symbol = item['symbol'].upper().strip()
            name = item['name'].strip()

            # 1. Canonical Instrument in primary database ('default')
            # Save individually so outbox sync event is generated
            instrument = Instrument.objects.using('default').filter(symbol=symbol, asset_class=AssetClass.CRYPTO).first()
            if instrument is None:
                instrument = Instrument(
                    symbol=symbol,
                    name=name,
                    asset_class=AssetClass.CRYPTO,
                    exchange='CRYPTO',
                    currency='INR',
                    status=InstrumentStatus.ACTIVE,
                    is_active=True,
                )
                instrument.save(using='default')
                created_count += 1
            else:
                updated = False
                if instrument.name != name:
                    instrument.name = name
                    updated = True
                if not instrument.is_active:
                    instrument.is_active = True
                    updated = True
                if updated:
                    instrument.save(using='default')
                    updated_count += 1

            # Synchronize to MarketInstrumentReference in market_data database
            from apps.market_data.models.sync_event import InstrumentSyncEvent
            event = InstrumentSyncEvent.objects.using('default').filter(
                instrument_id=instrument.id,
                identity_version=instrument.identity_version or 1,
            ).first()
            if event:
                InstrumentIdentitySyncService.apply_sync_event(event)

            # 2. Provider mapping in market_data database
            ProviderInstrumentMapping.objects.using('market_data').update_or_create(
                provider_name='COINGECKO',
                provider_symbol=coin_id,
                defaults={
                    'instrument_id': instrument.id,
                    'is_primary': True,
                    'metadata': {'coingecko_id': coin_id, 'symbol': symbol, 'name': name},
                },
            )

            # 3. Coverage policy in market_data database
            InstrumentCoverage.objects.using('market_data').update_or_create(
                instrument_id=instrument.id,
                defaults={
                    'price_type': PriceType.LTP,
                    'cadence': CollectionCadence.WEEKLY,
                    'status': CoverageStatus.ACTIVE,
                    'currency': 'INR',
                    'unit': QuotationUnit.UNITS,
                    'preferred_source': 'COINGECKO',
                    'freshness_hours': 168,
                },
            )

            # 4. MarketDataSeries in market_data database
            series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                instrument_id=instrument.id,
                exchange='CRYPTO',
                source='COINGECKO',
                price_type=PriceType.LTP,
                currency='INR',
                unit=QuotationUnit.UNITS,
                pricing_methodology='SPOT',
                adjustment_methodology='RAW',
                defaults={'description': f'CoinGecko spot series for {symbol} (INR)'},
            )

            synced_instruments.append({
                'id': str(instrument.id),
                'symbol': symbol,
                'name': name,
                'coin_id': coin_id,
                'series_id': str(series.id),
            })

        return {
            'total_synced': len(synced_instruments),
            'created': created_count,
            'updated': updated_count,
            'instruments': synced_instruments,
        }

    @classmethod
    def sync_prices(
        cls,
        coin_ids: Optional[List[str]] = None,
        client: Optional[CoinGeckoClient] = None,
        publisher=None,
    ) -> Dict[str, Any]:
        """
        Fetches latest quotes from CoinGecko, writes and publishes PriceObservation records.
        """
        cg_client = client or CoinGeckoClient()
        mappings = ProviderInstrumentMapping.objects.using('market_data').filter(
            provider_name='COINGECKO',
            is_primary=True,
        )
        if coin_ids:
            mappings = mappings.filter(provider_symbol__in=[cid.lower() for cid in coin_ids])

        mapping_list = list(mappings)
        if not mapping_list:
            return {'synced': 0, 'errors': ['No configured CoinGecko mappings found']}

        id_to_mapping = {m.provider_symbol.lower(): m for m in mapping_list}
        markets = cg_client.get_markets(ids=list(id_to_mapping.keys()), vs_currency='inr')

        published_count = 0
        errors = []

        for raw_item in markets:
            try:
                item = serialize_market_item(raw_item)
                cid = item['id'].lower()
                mapping = id_to_mapping.get(cid)
                if not mapping:
                    continue

                instrument_id = mapping.instrument_id
                series = MarketDataSeries.objects.using('market_data').filter(
                    instrument_id=instrument_id,
                    source='COINGECKO',
                    price_type=PriceType.LTP,
                    currency='INR',
                    unit=QuotationUnit.UNITS,
                ).first()

                if not series:
                    series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                        instrument_id=instrument_id,
                        exchange='CRYPTO',
                        source='COINGECKO',
                        price_type=PriceType.LTP,
                        currency='INR',
                        unit=QuotationUnit.UNITS,
                        pricing_methodology='SPOT',
                        adjustment_methodology='RAW',
                    )

                price = round(item['price'], 4)
                high_24h = round(item['high_24h'], 4) if item['high_24h'] is not None else None
                low_24h = round(item['low_24h'], 4) if item['low_24h'] is not None else None
                vol = int(item['total_volume']) if item['total_volume'] is not None else None
                dt = item['timestamp']

                metadata_notes = {
                    'market_cap': str(item['market_cap']) if item['market_cap'] is not None else None,
                    'volume_24h': str(item['total_volume']) if item['total_volume'] is not None else None,
                    'change_24h': str(item['price_change_percentage_24h']) if item['price_change_percentage_24h'] is not None else None,
                    'change_amount_24h': str(item['price_change_24h']) if item['price_change_24h'] is not None else None,
                }

                # Check if observation for exact series and effective_at already exists
                existing = PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument_id,
                    series=series,
                    effective_at=dt,
                    source='COINGECKO',
                    status=ObservationStatus.PUBLISHED,
                ).first()

                if existing:
                    continue

                open_p = None
                if item['price_change_24h'] is not None:
                    open_p = round(price - item['price_change_24h'], 4)

                if high_24h is not None and high_24h < price:
                    high_24h = price
                if low_24h is not None and low_24h > price:
                    low_24h = price
                if open_p is not None:
                    if high_24h is not None and high_24h < open_p:
                        high_24h = open_p
                    if low_24h is not None and low_24h > open_p:
                        low_24h = open_p

                obs = PriceObservation(
                    instrument_id=instrument_id,
                    series=series,
                    price_type=PriceType.LTP,
                    value=price,
                    open_price=open_p,
                    high_price=high_24h,
                    low_price=low_24h,
                    volume=vol,
                    currency='INR',
                    unit=QuotationUnit.UNITS,
                    effective_at=dt,
                    source='COINGECKO',
                    source_reference=f'https://www.coingecko.com/en/coins/{cid}',
                    notes=json.dumps(metadata_notes),
                    status=ObservationStatus.PUBLISHED,
                    trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                    is_synthetic=False,
                    published_at=dj_timezone.now(),
                    published_by_id=getattr(publisher, 'id', None),
                )
                obs.save(using='market_data')
                published_count += 1
            except Exception as e:
                logger.error("Failed to sync price for crypto item %s: %s", raw_item.get('id'), str(e))
                errors.append(f"{raw_item.get('id')}: {e!s}")

        return {
            'synced': published_count,
            'errors': errors,
        }

    @classmethod
    def backfill_history(
        cls,
        coin_id: str,
        days: int = 30,
        client: Optional[CoinGeckoClient] = None,
        publisher=None,
    ) -> int:
        """
        Backfills historical daily price observations for a cryptocurrency.
        """
        cg_client = client or CoinGeckoClient()
        mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
            provider_name='COINGECKO',
            provider_symbol=coin_id.lower(),
        ).first()

        if not mapping:
            raise ValueError(f"No mapping found for CoinGecko coin ID: {coin_id}")

        instrument_id = mapping.instrument_id
        series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
            instrument_id=instrument_id,
            exchange='CRYPTO',
            source='COINGECKO',
            price_type=PriceType.LTP,
            currency='INR',
            unit=QuotationUnit.UNITS,
            pricing_methodology='SPOT',
            adjustment_methodology='RAW',
        )

        raw_chart = cg_client.get_market_chart(coin_id=coin_id.lower(), days=days, interval='daily')
        points = serialize_chart_data(raw_chart)

        created_count = 0
        for p in points:
            dt = p['timestamp']
            price = round(p['price'], 4)
            vol = int(p['volume']) if p['volume'] is not None else None
            mcap = p['market_cap']

            if PriceObservation.objects.using('market_data').filter(
                instrument_id=instrument_id,
                series=series,
                effective_at=dt,
                source='COINGECKO',
                status=ObservationStatus.PUBLISHED,
            ).exists():
                continue

            metadata_notes = {
                'market_cap': str(mcap) if mcap is not None else None,
                'volume_24h': str(vol) if vol is not None else None,
            }

            obs = PriceObservation(
                instrument_id=instrument_id,
                series=series,
                price_type=PriceType.LTP,
                value=price,
                open_price=price,
                high_price=price,
                low_price=price,
                volume=vol,
                currency='INR',
                unit=QuotationUnit.UNITS,
                effective_at=dt,
                source='COINGECKO',
                source_reference=f'https://www.coingecko.com/en/coins/{coin_id}',
                notes=json.dumps(metadata_notes),
                status=ObservationStatus.PUBLISHED,
                trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                is_synthetic=False,
                published_at=dj_timezone.now(),
                published_by_id=getattr(publisher, 'id', None),
            )
            obs.save(using='market_data')
            created_count += 1

        return created_count
