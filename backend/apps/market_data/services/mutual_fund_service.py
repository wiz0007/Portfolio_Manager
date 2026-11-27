"""Indian mutual fund market data synchronization and ingestion service."""
import json
import logging
from decimal import Decimal
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
from apps.market_data.models.sync_event import InstrumentSyncEvent
from apps.market_data.providers.mfapi.client import MFAPIClient
from apps.market_data.providers.mfapi.constants import CURATED_SCHEMES
from apps.market_data.providers.mfapi.serializers import (
    classify_scheme,
    serialize_nav_data,
    serialize_scheme_meta,
)
from apps.market_data.services.sync_service import InstrumentIdentitySyncService

logger = logging.getLogger(__name__)


class MutualFundMarketDataService:
    """Ingests Indian mutual fund scheme catalogues, latest NAVs, and historical series."""

    @classmethod
    def sync_catalogue(cls, schemes: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Creates canonical Instrument entries, secondary mappings, coverage, and series
        for Indian mutual fund schemes.
        """
        schemes_to_sync = schemes or CURATED_SCHEMES
        created_count = 0
        updated_count = 0
        synced_schemes = []

        for item in schemes_to_sync:
            scheme_code = str(item['scheme_code']).strip()
            scheme_name = item['scheme_name'].strip()
            fund_house = item.get('fund_house', '').strip()
            isin = item.get('isin')
            classification = classify_scheme(scheme_name)
            plan_type = item.get('plan_type') or classification['plan_type']
            option_type = item.get('option_type') or classification['option_type']

            # 1. Canonical Instrument in primary database ('default')
            # Saved individually so outbox event is generated
            instrument = Instrument.objects.using('default').filter(
                scheme_code=scheme_code,
                asset_class=AssetClass.MUTUAL_FUND,
            ).first()

            if instrument is None:
                instrument = Instrument(
                    symbol=scheme_code,
                    name=scheme_name,
                    asset_class=AssetClass.MUTUAL_FUND,
                    exchange='AMFI',
                    currency='INR',
                    scheme_code=scheme_code,
                    isin=isin,
                    status=InstrumentStatus.ACTIVE,
                    is_active=True,
                )
                instrument.save(using='default')
                created_count += 1
            else:
                updated = False
                if instrument.name != scheme_name:
                    instrument.name = scheme_name
                    updated = True
                if isin and instrument.isin != isin:
                    instrument.isin = isin
                    updated = True
                if not instrument.is_active:
                    instrument.is_active = True
                    updated = True
                if updated:
                    instrument.save(using='default')
                    updated_count += 1

            # Synchronize to MarketInstrumentReference in market_data database
            event = InstrumentSyncEvent.objects.using('default').filter(
                instrument_id=instrument.id,
                identity_version=instrument.identity_version or 1,
            ).first()
            if event:
                InstrumentIdentitySyncService.apply_sync_event(event)

            metadata = {
                'scheme_code': scheme_code,
                'scheme_name': scheme_name,
                'fund_house': fund_house,
                'plan_type': plan_type,
                'option_type': option_type,
                'isin': isin,
            }

            # 2. Provider mappings in market_data database (MFAPI & AMFI)
            ProviderInstrumentMapping.objects.using('market_data').update_or_create(
                provider_name='MFAPI',
                provider_symbol=scheme_code,
                defaults={
                    'instrument_id': instrument.id,
                    'is_primary': True,
                    'metadata': metadata,
                },
            )
            ProviderInstrumentMapping.objects.using('market_data').update_or_create(
                provider_name='AMFI',
                provider_symbol=scheme_code,
                defaults={
                    'instrument_id': instrument.id,
                    'is_primary': False,
                    'metadata': metadata,
                },
            )

            # 3. Coverage policy in market_data database
            InstrumentCoverage.objects.using('market_data').update_or_create(
                instrument_id=instrument.id,
                defaults={
                    'price_type': PriceType.NAV,
                    'cadence': CollectionCadence.WEEKLY,
                    'status': CoverageStatus.ACTIVE,
                    'currency': 'INR',
                    'unit': QuotationUnit.UNITS,
                    'preferred_source': 'MFAPI',
                    'freshness_hours': 168,
                },
            )

            # 4. MarketDataSeries in market_data database
            series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                instrument_id=instrument.id,
                exchange='AMFI',
                source='MFAPI',
                price_type=PriceType.NAV,
                currency='INR',
                unit=QuotationUnit.UNITS,
                pricing_methodology='OFFICIAL_NAV',
                adjustment_methodology='RAW',
                defaults={'description': f'Official NAV series for {scheme_name}'},
            )

            synced_schemes.append({
                'id': str(instrument.id),
                'scheme_code': scheme_code,
                'scheme_name': scheme_name,
                'fund_house': fund_house,
                'plan_type': plan_type,
                'option_type': option_type,
                'series_id': str(series.id),
            })

        return {
            'total_synced': len(synced_schemes),
            'created': created_count,
            'updated': updated_count,
            'schemes': synced_schemes,
        }

    @classmethod
    def sync_nav(
        cls,
        scheme_codes: Optional[List[str]] = None,
        client: Optional[MFAPIClient] = None,
        publisher=None,
    ) -> Dict[str, Any]:
        """
        Fetches latest NAV for mutual fund schemes from MFAPI and publishes observations.
        """
        mf_client = client or MFAPIClient()
        mappings = ProviderInstrumentMapping.objects.using('market_data').filter(
            provider_name='MFAPI',
            is_primary=True,
        )
        if scheme_codes:
            mappings = mappings.filter(provider_symbol__in=[str(sc).strip() for sc in scheme_codes])

        mapping_list = list(mappings)
        if not mapping_list:
            return {'synced': 0, 'errors': ['No configured mutual fund scheme mappings found']}

        published_count = 0
        errors = []

        for mapping in mapping_list:
            scheme_code = mapping.provider_symbol
            instrument_id = mapping.instrument_id

            try:
                raw = mf_client.get_scheme(scheme_code)
                nav_entries = serialize_nav_data(raw.get('data') or [])
                if not nav_entries:
                    errors.append(f"{scheme_code}: No NAV entries found")
                    continue

                latest = nav_entries[-1]
                prev = nav_entries[-2] if len(nav_entries) >= 2 else None

                series = MarketDataSeries.objects.using('market_data').filter(
                    instrument_id=instrument_id,
                    source='MFAPI',
                    price_type=PriceType.NAV,
                    currency='INR',
                    unit=QuotationUnit.UNITS,
                ).first()

                if not series:
                    series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                        instrument_id=instrument_id,
                        exchange='AMFI',
                        source='MFAPI',
                        price_type=PriceType.NAV,
                        currency='INR',
                        unit=QuotationUnit.UNITS,
                        pricing_methodology='OFFICIAL_NAV',
                        adjustment_methodology='RAW',
                    )

                dt = latest['timestamp']
                nav_val = latest['nav']

                # Check if observation for exact series and effective_at already exists
                existing = PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument_id,
                    series=series,
                    effective_at=dt,
                    source='MFAPI',
                    status=ObservationStatus.PUBLISHED,
                ).first()

                if existing:
                    continue

                notes_dict = {}
                if prev:
                    change_amt = latest['nav'] - prev['nav']
                    change_pct = (change_amt / prev['nav'] * Decimal('100')) if prev['nav'] > 0 else Decimal('0')
                    notes_dict['change_amount_24h'] = str(change_amt)
                    notes_dict['change_24h'] = str(change_pct)

                meta_info = serialize_scheme_meta(raw.get('meta') or {})
                notes_dict.update({
                    'fund_house': meta_info['fund_house'],
                    'plan_type': meta_info['plan_type'],
                    'option_type': meta_info['option_type'],
                })

                obs = PriceObservation(
                    instrument_id=instrument_id,
                    series=series,
                    price_type=PriceType.NAV,
                    value=nav_val,
                    open_price=nav_val,
                    high_price=nav_val,
                    low_price=nav_val,
                    currency='INR',
                    unit=QuotationUnit.UNITS,
                    effective_at=dt,
                    source='MFAPI',
                    source_reference=f'https://www.mfapi.in/mf/{scheme_code}',
                    notes=json.dumps(notes_dict),
                    status=ObservationStatus.PUBLISHED,
                    trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                    is_synthetic=False,
                    published_at=dj_timezone.now(),
                    published_by_id=getattr(publisher, 'id', None),
                )
                obs.save(using='market_data')
                published_count += 1
            except Exception as e:
                logger.error("Failed to sync NAV for scheme %s: %s", scheme_code, str(e))
                errors.append(f"{scheme_code}: {e!s}")

        return {
            'synced': published_count,
            'errors': errors,
        }

    @classmethod
    def backfill_history(
        cls,
        scheme_code: str,
        days: int = 90,
        client: Optional[MFAPIClient] = None,
        publisher=None,
    ) -> int:
        """
        Backfills historical daily NAV observations for a mutual fund scheme.
        """
        mf_client = client or MFAPIClient()
        mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
            provider_name='MFAPI',
            provider_symbol=str(scheme_code).strip(),
        ).first()

        if not mapping:
            raise ValueError(f"No mapping found for scheme code: {scheme_code}")

        instrument_id = mapping.instrument_id
        series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
            instrument_id=instrument_id,
            exchange='AMFI',
            source='MFAPI',
            price_type=PriceType.NAV,
            currency='INR',
            unit=QuotationUnit.UNITS,
            pricing_methodology='OFFICIAL_NAV',
            adjustment_methodology='RAW',
        )

        raw = mf_client.get_scheme(scheme_code)
        nav_entries = serialize_nav_data(raw.get('data') or [])

        # Filter to the requested number of days
        if days and len(nav_entries) > days:
            nav_entries = nav_entries[-days:]

        created_count = 0
        for item in nav_entries:
            dt = item['timestamp']
            nav_val = item['nav']

            if PriceObservation.objects.using('market_data').filter(
                instrument_id=instrument_id,
                series=series,
                effective_at=dt,
                source='MFAPI',
                status=ObservationStatus.PUBLISHED,
            ).exists():
                continue

            obs = PriceObservation(
                instrument_id=instrument_id,
                series=series,
                price_type=PriceType.NAV,
                value=nav_val,
                open_price=nav_val,
                high_price=nav_val,
                low_price=nav_val,
                currency='INR',
                unit=QuotationUnit.UNITS,
                effective_at=dt,
                source='MFAPI',
                source_reference=f'https://www.mfapi.in/mf/{scheme_code}',
                status=ObservationStatus.PUBLISHED,
                trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                is_synthetic=False,
                published_at=dj_timezone.now(),
                published_by_id=getattr(publisher, 'id', None),
            )
            obs.save(using='market_data')
            created_count += 1

        return created_count
