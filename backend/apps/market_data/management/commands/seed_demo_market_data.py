from datetime import datetime, timedelta, timezone

from django.core.management.base import BaseCommand

from apps.market_data.models.instrument import AssetClass, Instrument
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.models.provider_mapping import ProviderInstrumentMapping
from apps.market_data.models.reference_data import (
    InstrumentReferenceData,
    MarketCapCategory,
)
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
        self.stdout.write(self.style.NOTICE("Seeding market instruments and deterministic demo data..."))
        demo_provider = DemoMarketDataProvider()
        today = datetime.now(timezone.utc).date()
        start_date = today - timedelta(days=30)

        created_count = 0
        updated_count = 0
        points_to_create = []

        for item in DEMO_INSTRUMENTS:
            instrument, created = Instrument.objects.update_or_create(
                symbol=item['symbol'],
                defaults={
                    'name': item['name'],
                    'asset_class': item['asset_class'],
                    'exchange': item['exchange'],
                    'currency': item['currency'],
                    'isin': item['isin'],
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

            # Reference data
            InstrumentReferenceData.objects.update_or_create(
                instrument=instrument,
                defaults={
                    'sector': item['sector'],
                    'industry': item['industry'],
                    'market_cap_category': item['cap'],
                },
            )

            # Provider mappings
            ProviderInstrumentMapping.objects.update_or_create(
                provider_name='DEMO',
                provider_symbol=item['symbol'],
                defaults={
                    'instrument': instrument,
                    'is_primary': True,
                },
            )

            if item['asset_class'] == AssetClass.MUTUAL_FUND:
                ProviderInstrumentMapping.objects.update_or_create(
                    provider_name='AMFI',
                    provider_symbol=item['symbol'],
                    defaults={
                        'instrument': instrument,
                        'is_primary': False,
                    },
                )
            elif item['asset_class'] == AssetClass.EQUITY:
                ProviderInstrumentMapping.objects.update_or_create(
                    provider_name='TRUEDATA',
                    provider_symbol=f"{item['symbol']}-EQ",
                    defaults={
                        'instrument': instrument,
                        'is_primary': False,
                    },
                )

            # Generate historical timeseries points
            history = demo_provider.get_history(instrument, start_date, today, interval='1D')
            for pt in history:
                points_to_create.append(
                    MarketDataPoint(
                        instrument=instrument,
                        timestamp=pt.timestamp,
                        price=pt.price,
                        open_price=pt.open_price,
                        high_price=pt.high_price,
                        low_price=pt.low_price,
                        close_price=pt.close_price,
                        volume=pt.volume,
                        change_amount=pt.change_amount,
                        change_percent=pt.change_percent,
                        provider='DEMO',
                        is_synthetic=True,
                        interval='1D',
                    )
                )

            # Latest quote point
            latest_quote = demo_provider.get_quote(instrument)
            points_to_create.append(
                MarketDataPoint(
                    instrument=instrument,
                    timestamp=latest_quote.timestamp,
                    price=latest_quote.price,
                    open_price=latest_quote.open_price,
                    high_price=latest_quote.high_price,
                    low_price=latest_quote.low_price,
                    close_price=latest_quote.close_price,
                    volume=latest_quote.volume,
                    change_amount=latest_quote.change_amount,
                    change_percent=latest_quote.change_percent,
                    provider='DEMO',
                    is_synthetic=True,
                    interval='1D',
                )
            )

        # Bulk create all data points with ignore_conflicts for speed and idempotency
        if points_to_create:
            MarketDataPoint.objects.bulk_create(points_to_create, ignore_conflicts=True, batch_size=200)

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded demo market data: {created_count} created, {updated_count} updated. "
                f"Generated {len(points_to_create)} synthetic points. All marked is_synthetic=True."
            )
        )
