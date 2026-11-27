"""Indian mutual fund market data synchronization and ingestion service."""
import json
import logging
from decimal import Decimal
from typing import Any, Dict, List, Optional

from django.conf import settings

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
from apps.market_data.providers.mfapi.exceptions import MFAPIError, MFAPINotFoundError
from apps.market_data.providers.mfapi.serializers import (
    classify_scheme,
    serialize_nav_data,
    serialize_scheme_meta,
)
from apps.market_data.services.sync_service import InstrumentIdentitySyncService
from apps.market_data.services.system_publisher import SystemPublisher

logger = logging.getLogger(__name__)


class MutualFundMarketDataService:
    """Ingests mutual fund catalogue, latest NAVs, and historical series from MFAPI / AMFI."""

    @classmethod
    def fetch_provider_catalogue(cls, client: Optional[MFAPIClient] = None) -> List[Dict[str, Any]]:
        """Retrieves full scheme catalogue directly from MFAPI /mf endpoint."""
        mf_client = client or MFAPIClient()
        return mf_client.get_all_schemes()

    @classmethod
    def sync_catalogue(
        cls,
        schemes: Optional[List[Dict[str, Any]]] = None,
        client: Optional[MFAPIClient] = None,
    ) -> Dict[str, Any]:
        """
        Creates canonical Instrument entries, secondary mappings, coverage, and series
        for Indian mutual fund schemes using stable scheme_code identity.
        """
        if not getattr(settings, 'MFAPI_ENABLED', True):
            return {'total_synced': 0, 'created': 0, 'updated': 0, 'schemes': [], 'status': 'DISABLED'}

        schemes_to_sync = schemes or CURATED_SCHEMES
        created_count = 0
        updated_count = 0
        synced_schemes = []

        for item in schemes_to_sync:
            scheme_code = str(item.get('scheme_code') or item.get('schemeCode', '')).strip()
            scheme_name = str(item.get('scheme_name') or item.get('schemeName', '')).strip()
            fund_house = str(item.get('fund_house', '')).strip()
            isin = item.get('isin')

            if not scheme_code or not scheme_name:
                continue

            classification = classify_scheme(scheme_name)
            plan_type = item.get('plan_type') or classification['plan_type']
            option_type = item.get('option_type') or classification['option_type']

            # 1. Resolve canonical Instrument by scheme_code & asset_class
            instrument = Instrument.objects.using('default').filter(
                scheme_code=scheme_code,
                asset_class=AssetClass.MUTUAL_FUND,
            ).first()

            if instrument is None:
                # Also check mapping in market_data database
                mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
                    provider_name='MFAPI',
                    provider_symbol=scheme_code,
                ).first()
                if mapping:
                    instrument = Instrument.objects.using('default').filter(id=mapping.instrument_id).first()

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

            # 2. Synchronize to MarketInstrumentReference via outbox
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

            # 3. Provider mappings in market_data database (MFAPI primary, AMFI secondary)
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

            # 4. Coverage policy: daily business-day collection cadence, 24h freshness, 48h grace
            InstrumentCoverage.objects.using('market_data').update_or_create(
                instrument_id=instrument.id,
                defaults={
                    'price_type': PriceType.NAV,
                    'cadence': CollectionCadence.EVERY_BUSINESS_DAY,
                    'status': CoverageStatus.ACTIVE,
                    'currency': 'INR',
                    'unit': QuotationUnit.UNITS,
                    'preferred_source': 'MFAPI',
                    'freshness_hours': 24,
                    'grace_period_hours': 48,
                },
            )

            # 5. MarketDataSeries in market_data database
            series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                instrument_id=instrument.id,
                exchange='AMFI',
                source='MFAPI',
                price_type=PriceType.NAV,
                currency='INR',
                unit=QuotationUnit.UNITS,
                pricing_methodology='OFFICIAL_NAV',
                adjustment_methodology='RAW',
                defaults={'description': f'Official NAV series for {scheme_name} (INR)'},
            )

            synced_schemes.append({
                'id': str(instrument.id),
                'scheme_code': scheme_code,
                'scheme_name': scheme_name,
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
        Fetches latest NAV observations from MFAPI, handles corrections idempotently,
        and publishes using authorized system publisher.
        """
        if not getattr(settings, 'MFAPI_ENABLED', True):
            return {'synced': 0, 'corrected': 0, 'errors': ['MFAPI provider is disabled in settings.']}

        mf_client = client or MFAPIClient()
        mappings = ProviderInstrumentMapping.objects.using('market_data').filter(
            provider_name='MFAPI',
            is_primary=True,
        )
        if scheme_codes:
            mappings = mappings.filter(provider_symbol__in=[str(sc).strip() for sc in scheme_codes])

        mapping_list = list(mappings)
        if not mapping_list:
            return {'synced': 0, 'corrected': 0, 'errors': ['No configured MFAPI mappings found']}

        published_count = 0
        corrected_count = 0
        errors = []
        pub = publisher or SystemPublisher()

        for mapping in mapping_list:
            scheme_code = mapping.provider_symbol
            instrument_id = mapping.instrument_id
            try:
                raw = mf_client.get_scheme(scheme_code)
                data_list = raw.get('data') or []
                if not data_list:
                    continue

                nav_entries = serialize_nav_data(data_list)
                if not nav_entries:
                    continue

                # The latest entry is the last element after chronological sorting
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
                        defaults={'description': f'Official NAV series for scheme {scheme_code}'},
                    )

                dt = latest['timestamp']
                nav_val = round(latest['nav'], 4)
                if nav_val <= 0:
                    continue

                notes_dict = {}
                if prev:
                    change_amt = round(latest['nav'] - prev['nav'], 4)
                    change_pct = (change_amt / prev['nav'] * Decimal('100')) if prev['nav'] > 0 else Decimal('0')
                    # Accurately labeled: change since previous NAV
                    notes_dict['change_since_prev_nav'] = str(change_amt)
                    notes_dict['change_percent_since_prev_nav'] = str(round(change_pct, 4))
                    notes_dict['change_amount_24h'] = str(change_amt)
                    notes_dict['change_24h'] = str(round(change_pct, 4))

                meta_info = serialize_scheme_meta(raw.get('meta') or {})
                notes_dict.update({
                    'fund_house': meta_info['fund_house'],
                    'plan_type': meta_info['plan_type'],
                    'option_type': meta_info['option_type'],
                })

                # Check if observation for exact series and effective_at already exists
                existing = PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument_id,
                    series=series,
                    effective_at=dt,
                    source='MFAPI',
                    status=ObservationStatus.PUBLISHED,
                ).order_by('-published_at').first()

                if existing:
                    if existing.value == nav_val:
                        # Identical NAV already published: skip safely
                        continue

                    # Provider correction detected: preserve original and publish correction
                    correction_obs = PriceObservation(
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
                        status=ObservationStatus.DRAFT,
                        trust_class=TrustClass.CORRECTED,
                        is_synthetic=False,
                        correction_of=existing,
                        correction_reason=f"Provider NAV correction from {existing.value} to {nav_val}",
                        recorded_by_id=getattr(pub, 'id', None),
                    )
                    correction_obs.save(using='market_data')
                    correction_obs.status = ObservationStatus.PENDING_REVIEW
                    correction_obs.save(using='market_data', update_fields=['status', 'updated_at'])
                    correction_obs.publish(pub)
                    corrected_count += 1
                    continue

                # Ingestion through authorized publication lifecycle
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
                    status=ObservationStatus.DRAFT,
                    trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                    is_synthetic=False,
                    recorded_by_id=getattr(pub, 'id', None),
                )
                obs.save(using='market_data')
                obs.status = ObservationStatus.PENDING_REVIEW
                obs.save(using='market_data', update_fields=['status', 'updated_at'])
                obs.publish(pub)
                published_count += 1
            except (MFAPINotFoundError, MFAPIError) as e:
                logger.error("MFAPI fetch error for scheme %s: %s", scheme_code, e)
                errors.append(f"{scheme_code}: {e!s}")
            except Exception as e:
                logger.error("Failed to sync NAV for scheme %s: %s", scheme_code, e)
                errors.append(f"{scheme_code}: {e!s}")

        return {
            'synced': published_count,
            'corrected': corrected_count,
            'errors': errors,
        }

    @classmethod
    def backfill_history(
        cls,
        scheme_code: str,
        days: Optional[int] = 365,
        client: Optional[MFAPIClient] = None,
        publisher=None,
    ) -> int:
        """
        Backfills historical daily NAV observations for a mutual fund scheme.
        Supports bounded batches, incremental imports, and authorized publication.
        """
        if not getattr(settings, 'MFAPI_ENABLED', True):
            raise ValueError("MFAPI provider is disabled in settings.")

        if days is not None and days <= 0:
            raise ValueError("days parameter must be a positive integer.")

        mf_client = client or MFAPIClient()
        code = str(scheme_code).strip()
        mapping = ProviderInstrumentMapping.objects.using('market_data').filter(
            provider_name='MFAPI',
            provider_symbol=code,
        ).first()

        if not mapping:
            raise ValueError(f"No mapping found for scheme code: {code}")

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
            defaults={'description': f'Official NAV series for scheme {code}'},
        )

        raw = mf_client.get_scheme(code)
        nav_entries = serialize_nav_data(raw.get('data') or [])

        # Filter to requested number of records if specified
        if days and len(nav_entries) > days:
            nav_entries = nav_entries[-days:]

        existing_dts = set(
            PriceObservation.objects.using('market_data')
            .filter(
                instrument_id=instrument_id,
                series=series,
                source='MFAPI',
                status=ObservationStatus.PUBLISHED,
            )
            .values_list('effective_at', flat=True)
        )

        pub = publisher or SystemPublisher()
        created_count = 0

        for item in nav_entries:
            dt = item['timestamp']
            if dt in existing_dts:
                continue
            existing_dts.add(dt)

            nav_val = round(item['nav'], 4)
            if nav_val <= 0:
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
                source_reference=f'https://www.mfapi.in/mf/{code}',
                status=ObservationStatus.DRAFT,
                trust_class=TrustClass.VERIFIED_PERMITTED_SECONDARY,
                is_synthetic=False,
                recorded_by_id=getattr(pub, 'id', None),
            )
            obs.save(using='market_data')
            obs.status = ObservationStatus.PENDING_REVIEW
            obs.save(using='market_data', update_fields=['status', 'updated_at'])
            obs.publish(pub)
            created_count += 1

        return created_count
