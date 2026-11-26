from datetime import datetime, timedelta, timezone

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.market_data.models.coverage import InstrumentCoverage, PriceType, QuotationUnit
from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.reference_data import (
    InstrumentReferenceData,
    MarketCapCategory,
)
from apps.market_data.models.series import MarketDataSeries
from apps.market_data.providers.demo_provider import DemoMarketDataProvider

DEMO_INSTRUMENTS = [
    {
        'symbol': 'NIFTY50',
        'name': 'NIFTY 50 Benchmark Index',
        'asset_class': AssetClass.INDEX,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'IN0000000010',
        'sector': 'Broad Market',
        'industry': 'Equity Index',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'SENSEX',
        'name': 'S&P BSE SENSEX Index',
        'asset_class': AssetClass.INDEX,
        'exchange': 'BSE',
        'currency': 'INR',
        'isin': 'IN0000000020',
        'sector': 'Broad Market',
        'industry': 'Equity Index',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'RELIANCE',
        'name': 'Reliance Industries Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE002A01018',
        'sector': 'Energy & Conglomerate',
        'industry': 'Oil, Gas & Consumables',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'TCS',
        'name': 'Tata Consultancy Services Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE467B01029',
        'sector': 'Information Technology',
        'industry': 'IT Services & Consulting',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'HDFCBANK',
        'name': 'HDFC Bank Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE040A01034',
        'sector': 'Financial Services',
        'industry': 'Private Banking',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'INFY',
        'name': 'Infosys Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE009A01021',
        'sector': 'Information Technology',
        'industry': 'IT Services & Consulting',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'ICICIBANK',
        'name': 'ICICI Bank Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE090A01021',
        'sector': 'Financial Services',
        'industry': 'Private Banking',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'SBIN',
        'name': 'State Bank of India',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE062A01020',
        'sector': 'Financial Services',
        'industry': 'Public Sector Banking',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'BHARTIARTL',
        'name': 'Bharti Airtel Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE397D01024',
        'sector': 'Telecommunication',
        'industry': 'Telecom Services',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'ITC',
        'name': 'ITC Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE154A01025',
        'sector': 'Fast Moving Consumer Goods',
        'industry': 'Diversified FMCG',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': 'LT',
        'name': 'Larsen & Toubro Ltd.',
        'asset_class': AssetClass.EQUITY,
        'exchange': 'NSE',
        'currency': 'INR',
        'isin': 'INE018A01030',
        'sector': 'Construction & Infrastructure',
        'industry': 'Heavy Engineering',
        'cap': MarketCapCategory.LARGE_CAP,
    },
    {
        'symbol': '122639',
        'name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
        'asset_class': AssetClass.MUTUAL_FUND,
        'exchange': 'AMFI',
        'currency': 'INR',
        'isin': 'INF879O01018',
        'sector': 'Mutual Fund',
        'industry': 'Flexi Cap Fund',
        'cap': MarketCapCategory.NOT_APPLICABLE,
    },
    {
        'symbol': '118834',
        'name': 'Mirae Asset Large Cap Fund - Direct Plan - Growth Option',
        'asset_class': AssetClass.MUTUAL_FUND,
        'exchange': 'AMFI',
        'currency': 'INR',
        'isin': 'INF769K01010',
        'sector': 'Mutual Fund',
        'industry': 'Large Cap Fund',
        'cap': MarketCapCategory.NOT_APPLICABLE,
    },
    {
        'symbol': '119598',
        'name': 'SBI Bluechip Fund - Direct Plan - Growth',
        'asset_class': AssetClass.MUTUAL_FUND,
        'exchange': 'AMFI',
        'currency': 'INR',
        'isin': 'INF200K01198',
        'sector': 'Mutual Fund',
        'industry': 'Large Cap Fund',
        'cap': MarketCapCategory.NOT_APPLICABLE,
    },
    {
        'symbol': 'GOLD24K',
        'name': 'Sovereign Gold / 24 Karat Pure Gold (1g)',
        'asset_class': AssetClass.COMMODITY,
        'exchange': 'COMMODITY',
        'currency': 'INR',
        'isin': 'IN000000GOLD',
        'sector': 'Precious Metals',
        'industry': 'Physical Gold / Sovereign Bond',
        'cap': MarketCapCategory.NOT_APPLICABLE,
    },
]


class Command(BaseCommand):
    help = 'Seeds standard Indian market instruments with deterministic researched synthetic demo data.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding market instruments and explicitly synthetic demo observations..."))
        publisher = get_user_model().objects.filter(is_superuser=True, is_active=True).first()
        if publisher is None:
            raise CommandError('Create an active superuser before publishing synthetic demo observations.')

        demo_provider = DemoMarketDataProvider()
        today = datetime.now(timezone.utc).date()
        start_date = today - timedelta(days=30)
        created_count = updated_count = observations_created = 0

        for item in DEMO_INSTRUMENTS:
            instrument, created = Instrument.objects.update_or_create(
                symbol=item['symbol'],
                defaults={
                    'name': item['name'], 'asset_class': item['asset_class'],
                    'exchange': item['exchange'], 'currency': item['currency'],
                    'isin': item['isin'], 'is_active': True,
                },
            )
            created_count += int(created)
            updated_count += int(not created)

            InstrumentReferenceData.objects.update_or_create(
                instrument=instrument,
                defaults={
                    'sector': item['sector'], 'industry': item['industry'],
                    'market_cap_category': item['cap'],
                },
            )
            ProviderInstrumentMapping.objects.using('market_data').update_or_create(
                provider_name='DEMO', provider_symbol=item['symbol'],
                defaults={'instrument_id': instrument.id, 'is_primary': True},
            )

            if item['asset_class'] == AssetClass.MUTUAL_FUND:
                price_type, unit = PriceType.NAV, QuotationUnit.UNITS
            elif item['asset_class'] == AssetClass.INDEX:
                price_type, unit = PriceType.CLOSE, QuotationUnit.UNITS
            elif item['asset_class'] == AssetClass.COMMODITY:
                price_type, unit = PriceType.INDICATIVE_VALUATION, QuotationUnit.GRAMS_24K
            else:
                price_type, unit = PriceType.LTP, QuotationUnit.SHARES

            InstrumentCoverage.objects.using('market_data').update_or_create(
                instrument_id=instrument.id,
                defaults={
                    'price_type': price_type, 'currency': 'INR', 'unit': unit,
                    'preferred_source': 'DEMO', 'freshness_hours': 24,
                },
            )
            series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
                instrument_id=instrument.id, exchange=instrument.exchange or '',
                source='DEMO', price_type=price_type, currency='INR', unit=unit,
                pricing_methodology='DEMO_FIXTURE', adjustment_methodology='RAW',
                defaults={'description': f'Synthetic development-only series for {instrument.symbol}'},
            )

            for point in demo_provider.get_history(instrument, start_date, today, interval='1D'):
                if PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument.id, series_id=series.id,
                    effective_at=point.timestamp, price_type=price_type, source='DEMO',
                    status=ObservationStatus.PUBLISHED,
                ).exists():
                    continue
                observation = PriceObservation(
                    instrument_id=instrument.id, series=series,
                    price_type=price_type, value=point.price,
                    open_price=point.open_price, high_price=point.high_price,
                    low_price=point.low_price, volume=point.volume,
                    currency='INR', unit=unit, effective_at=point.timestamp,
                    source='DEMO', source_reference='DEMO_FIXTURE',
                    status=ObservationStatus.DRAFT, trust_class=TrustClass.SYNTHETIC,
                    is_synthetic=True, recorded_by_id=publisher.id,
                )
                observation.save(using='market_data')
                observation.status = ObservationStatus.PENDING_REVIEW
                observation.save(using='market_data', update_fields=['status', 'updated_at'])
                observation.publish(publisher)
                observations_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'Seed complete: {created_count} instruments created, {updated_count} updated, '
            f'{observations_created} synthetic PriceObservation records published. '
            'No MarketDataPoint legacy records were written.'
        ))
