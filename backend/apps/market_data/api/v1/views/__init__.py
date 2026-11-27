from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils import timezone as dj_timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.market_data.api.v1.serializers import (
    InstrumentSerializer,
    QuoteSerializer,
)
from apps.market_data.models.coverage import PriceType, QuotationUnit
from apps.market_data.models.instrument import Instrument
from apps.market_data.permissions import IsMarketDataOperator
from apps.market_data.providers.registry import provider_registry
from apps.market_data.services.history_service import MarketHistoryService
from apps.market_data.services.market_data_service import MarketDataService
from apps.market_data.services.movement_service import PriceMovementService
from apps.market_data.services.price_resolver import PriceResolver
from apps.market_data.services.search_service import InstrumentSearchService
from core.permissions import IsAuthenticatedAndEmailVerified


class InstrumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving standardized financial instruments.
    Supports filtering by asset class, exchange, and active state.
    """

    queryset = Instrument.objects.select_related('reference_data')
    serializer_class = InstrumentSerializer
    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get_queryset(self):
        qs = super().get_queryset()
        asset_class = self.request.query_params.get('asset_class')
        if asset_class:
            qs = qs.filter(asset_class=asset_class.upper())
        exchange = self.request.query_params.get('exchange')
        if exchange:
            qs = qs.filter(exchange__iexact=exchange)
        product_type = self.request.query_params.get('product_type')
        if product_type:
            qs = qs.filter(product_type__iexact=product_type)
        active_only = self.request.query_params.get('is_active')
        if active_only is not None:
            qs = qs.filter(is_active=active_only.lower() in ['true', '1'])
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(symbol__icontains=search)
                | Q(name__icontains=search)
                | Q(isin__icontains=search)
                | Q(scheme_code__icontains=search)
                | Q(exchange__icontains=search)
                | Q(product_type__icontains=search)
                | Q(reference_data__sector__icontains=search)
                | Q(reference_data__industry__icontains=search)
            )
        return qs

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        instruments = list(page if page is not None else queryset)
        resolved_prices = PriceResolver.resolve_prices_bulk(instruments)
        serializer = self.get_serializer(
            instruments, many=True,
            context={**self.get_serializer_context(), 'resolved_prices': resolved_prices},
        )
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Fuzzy search endpoint for instrument selectors and autocompletes."""
        query = request.query_params.get('q', request.query_params.get('search', '')).strip()
        asset_class = request.query_params.get('asset_class')
        exchange = request.query_params.get('exchange')
        product_type = request.query_params.get('product_type')
        limit = min(int(request.query_params.get('limit', 20)), 100)

        if not query and not asset_class and not exchange and not product_type:
            return Response([])

        instruments = InstrumentSearchService.search(
            query=query,
            asset_class=asset_class,
            exchange=exchange,
            product_type=product_type,
            limit=limit,
        )

        serializer = self.get_serializer(instruments, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='mutual-funds/search')
    def mutual_funds_search(self, request):
        """Search Indian mutual fund schemes with classification filters."""
        query = request.query_params.get('q', request.query_params.get('search', '')).strip()
        plan_type = request.query_params.get('plan_type')
        option_type = request.query_params.get('option_type')
        limit = min(int(request.query_params.get('limit', 50)), 100)

        qs = Instrument.objects.filter(
            asset_class='MUTUAL_FUND',
            is_active=True,
        )
        if query:
            qs = qs.filter(
                Q(symbol__icontains=query)
                | Q(name__icontains=query)
                | Q(scheme_code__icontains=query)
                | Q(isin__icontains=query)
            )
        if plan_type:
            if plan_type.upper() == 'DIRECT':
                qs = qs.filter(name__icontains='Direct')
            elif plan_type.upper() == 'REGULAR':
                qs = qs.exclude(name__icontains='Direct')
        if option_type:
            if option_type.upper() == 'GROWTH':
                qs = qs.filter(name__icontains='Growth')
            elif option_type.upper() == 'IDCW':
                qs = qs.filter(Q(name__icontains='IDCW') | Q(name__icontains='Dividend') | Q(name__icontains='Income'))

        instruments = list(qs[:limit])
        resolved_prices = PriceResolver.resolve_prices_bulk(instruments)
        serializer = self.get_serializer(
            instruments, many=True,
            context={**self.get_serializer_context(), 'resolved_prices': resolved_prices},
        )
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='market-data/latest')
    def market_data_latest(self, request, pk=None):
        """Retrieve authoritative resolved latest price and movement."""
        instrument = self.get_object()
        resolved = PriceResolver.resolve_price(instrument)
        movement = PriceMovementService.calculate_movement(
            instrument=instrument,
            current_price=resolved.price,
            current_dt=resolved.effective_at,
            currency=resolved.currency,
            unit=resolved.unit,
            price_type=resolved.price_type,
            series_id=resolved.series_id,
        )
        return Response({
            'instrument_id': str(instrument.id),
            'symbol': instrument.symbol,
            'price': str(resolved.price) if resolved.price is not None else None,
            'currency': resolved.currency,
            'unit': resolved.unit,
            'effective_at': resolved.effective_at.isoformat() if resolved.effective_at else None,
            'status': resolved.status,
            'series_id': resolved.series_id,
            'observation_id': resolved.observation_id,
            'data_version': resolved.data_version,
            'price_type': resolved.price_type,
            'source': resolved.source,
            'source_reference': resolved.source_reference,
            'is_synthetic': resolved.is_synthetic,
            'notes': resolved.notes,
            'movement': {
                'change_amount': str(movement.change_amount) if movement.change_amount is not None else None,
                'change_percent': str(movement.change_percent) if movement.change_percent is not None else None,
                'previous_price': str(movement.previous_price) if movement.previous_price is not None else None,
                'previous_effective_at': movement.previous_effective_at.isoformat() if movement.previous_effective_at else None,
                'status': movement.status,
                'notes': movement.notes,
            },
        })

    @action(detail=True, methods=['get'], url_path='market-data/history')
    def market_data_history(self, request, pk=None):
        """Retrieve bounded, chronologically sorted historical market observations."""
        instrument = self.get_object()
        period = request.query_params.get('period', '1M')
        from_str = request.query_params.get('from')
        to_str = request.query_params.get('to')

        try:
            start_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else None
            end_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else None
        except ValueError:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        interval = request.query_params.get('interval', '1D').upper()
        if interval != '1D':
            return Response({'detail': 'Only 1D frequency is currently supported; weekly/monthly aggregation is not implemented.'}, status=status.HTTP_400_BAD_REQUEST)

        price_type = request.query_params.get('price_type')

        try:
            history_res = MarketHistoryService.get_history(
                instrument=instrument,
                period=period,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                price_type=price_type,
                series_id=request.query_params.get('series_id'),
            )
            latest_point = history_res.points[-1] if history_res.points else None
            last_eff_date = latest_point.date if latest_point else None
            last_pub_at = (
                latest_point.published_at.isoformat()
                if latest_point and latest_point.published_at
                else None
            )
            series_id = history_res.series_id
            data_version = history_res.data_version

            # Chart-ready format as specified in ERD Section 9.1
            chart_data = [
                {
                    'date': p.date,
                    'close': str(p.price),
                    'open': str(p.open_price) if p.open_price is not None else None,
                    'high': str(p.high_price) if p.high_price is not None else None,
                    'low': str(p.low_price) if p.low_price is not None else None,
                    'volume': p.volume,
                }
                for p in history_res.points
            ]

            return Response({
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'series_id': series_id,
                'frequency': 'daily',
                'currency': history_res.currency,
                'unit': history_res.unit,
                'price_type': price_type or (history_res.points[-1].price_type if history_res.points else None),
                'data_version': data_version,
                'last_effective_date': last_eff_date,
                'last_published_at': history_res.last_published_at.isoformat() if history_res.last_published_at else last_pub_at,
                'supported': history_res.supported,
                'period': history_res.period,
                'start_date': history_res.start_date,
                'end_date': history_res.end_date,
                'trust_class': history_res.trust_class,
                'message': history_res.message,
                'data': chart_data,
                'points': [
                    {
                        'timestamp': p.timestamp.isoformat(),
                        'date': p.date,
                        'price': str(p.price),
                        'price_type': p.price_type,
                        'currency': p.currency,
                        'unit': p.unit,
                        'source': p.source,
                        'trust_class': p.trust_class,
                        'is_synthetic': p.is_synthetic,
                        'open_price': str(p.open_price) if p.open_price is not None else None,
                        'high_price': str(p.high_price) if p.high_price is not None else None,
                        'low_price': str(p.low_price) if p.low_price is not None else None,
                        'volume': p.volume,
                        'published_at': p.published_at.isoformat() if p.published_at else None,
                    }
                    for p in history_res.points
                ],
            })
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='market-data/status')
    def market_data_status(self, request, pk=None):
        """Retrieve market-data coverage status and observation freshness."""
        instrument = self.get_object()
        resolved = PriceResolver.resolve_price(instrument)
        cov = getattr(instrument, 'coverage', None)
        return Response({
            'instrument_id': str(instrument.id),
            'symbol': instrument.symbol,
            'coverage_configured': cov is not None,
            'price_type': cov.price_type if cov else 'LTP',
            'quotation_unit': cov.unit if cov else 'UNITS',
            'freshness_hours': cov.freshness_hours if cov else None,
            'resolution_status': resolved.status,
            'last_effective_at': resolved.effective_at.isoformat() if resolved.effective_at else None,
            'source': resolved.source,
            'is_synthetic': resolved.is_synthetic,
            'notes': resolved.notes,
        })


class MarketDataQuoteView(APIView):
    """Retrieve quote for a single instrument or bulk quotes."""

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request, pk=None):
        if pk:
            try:
                instrument = Instrument.objects.get(pk=pk)
            except (Instrument.DoesNotExist, ValueError):
                return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

            force_refresh = request.query_params.get('refresh', '').lower() in ['true', '1']
            quote = MarketDataService.get_latest_quote(instrument, force_refresh=force_refresh)
            return Response(QuoteSerializer(quote).data)

        # Bulk quote retrieval by symbol list
        symbols_str = request.query_params.get('symbols', '')
        if not symbols_str:
            return Response({'detail': 'Missing symbols or instrument id.'}, status=status.HTTP_400_BAD_REQUEST)

        symbols = [s.strip().upper() for s in symbols_str.split(',') if s.strip()]
        instruments = Instrument.objects.filter(symbol__in=symbols)

        results = {}
        for inst in instruments:
            q = MarketDataService.get_latest_quote(inst)
            results[inst.symbol] = QuoteSerializer(q).data

        return Response(results)


class MarketDataHistoryView(APIView):
    """Retrieve historical timeseries for an instrument."""

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request, pk):
        try:
            instrument = Instrument.objects.get(pk=pk)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        interval = request.query_params.get('interval', '1D').upper()
        try:
            days_str = request.query_params.get('days')
            period = request.query_params.get('period')
            from_str = request.query_params.get('from')
            to_str = request.query_params.get('to')
            if days_str and days_str.isdigit() and not period:
                period = 'ALL' if int(days_str) >= 1825 else None
                today = dj_timezone.now().astimezone(ZoneInfo('Asia/Kolkata')).date()
                start_date = today - timedelta(days=min(int(days_str), 1825))
                end_date = today
            else:
                start_date = datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else None
                end_date = datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else None
            history_res = MarketHistoryService.get_history(
                instrument=instrument,
                period=period or '1M',
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                price_type=request.query_params.get('price_type'),
                series_id=request.query_params.get('series_id'),
            )
        except (ValueError, ValidationError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        points_payload = [
            {
                'timestamp': point.timestamp.isoformat(),
                'price': str(point.price),
                'open_price': str(point.open_price) if point.open_price is not None else None,
                'high_price': str(point.high_price) if point.high_price is not None else None,
                'low_price': str(point.low_price) if point.low_price is not None else None,
                'close_price': str(point.price),
                'volume': point.volume,
                'interval': '1D',
                'is_synthetic': point.is_synthetic,
                'source': point.source,
                'trust_class': point.trust_class,
                'price_type': point.price_type,
                'currency': point.currency,
                'unit': point.unit,
            }
            for point in history_res.points
        ]
        if not points_payload and getattr(settings, 'MARKET_DATA_PROVIDER_MODE', 'DEMO') == 'DEMO':
            provider = provider_registry.get_provider_for_instrument(instrument)
            if provider and getattr(provider, 'provider_name', '') == 'DEMO':
                demo_points = provider.get_history(
                    instrument,
                    start_date or (dj_timezone.now().date() - timedelta(days=30)),
                    end_date or dj_timezone.now().date(),
                    interval,
                )
                points_payload = [
                    {
                        'timestamp': point.timestamp.isoformat(),
                        'price': str(point.price),
                        'open_price': str(point.open_price) if point.open_price is not None else None,
                        'high_price': str(point.high_price) if point.high_price is not None else None,
                        'low_price': str(point.low_price) if point.low_price is not None else None,
                        'close_price': str(point.close_price or point.price),
                        'volume': point.volume,
                        'interval': interval,
                        'is_synthetic': True,
                        'source': 'DEMO',
                        'trust_class': 'SYNTHETIC',
                        'price_type': 'LTP',
                        'currency': instrument.currency,
                        'unit': 'UNITS',
                    }
                    for point in demo_points
                ]

        if request.query_params.get('period') or request.query_params.get('series_id'):
            return Response({
                'instrument_id': str(instrument.id),
                'series_id': history_res.series_id,
                'data_version': history_res.data_version,
                'frequency': 'daily',
                'price_type': request.query_params.get('price_type') or (history_res.points[-1].price_type if history_res.points else None),
                'currency': history_res.currency,
                'unit': history_res.unit,
                'start_date': history_res.start_date,
                'end_date': history_res.end_date,
                'last_published_at': history_res.last_published_at.isoformat() if history_res.last_published_at else None,
                'trust_class': history_res.trust_class,
                'message': history_res.message,
                'points': points_payload,
            })
        return Response(points_payload)



class MarketDataSeriesListView(APIView):
    """List exact active series for a canonical instrument; clients must select one."""

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticatedAndEmailVerified(), IsMarketDataOperator()]
        return [IsAuthenticatedAndEmailVerified()]

    def get(self, request):
        from apps.market_data.models.series import MarketDataSeries
        instrument_id = request.query_params.get('instrument_id')
        if not instrument_id:
            return Response({'detail': 'instrument_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            instrument = Instrument.objects.get(pk=instrument_id)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)
        rows = MarketDataSeries.objects.using('market_data').filter(
            instrument_id=instrument.id, is_active=True
        ).order_by('price_type', 'source', 'exchange')
        return Response([
            {
                'id': str(series.id), 'instrument_id': str(series.instrument_id),
                'exchange': series.exchange, 'source': series.source,
                'price_type': series.price_type, 'currency': series.currency,
                'unit': series.unit, 'data_version': series.data_version,
                'last_published_at': series.last_published_at.isoformat() if series.last_published_at else None,
            }
            for series in rows
        ])

    def post(self, request):
        from rest_framework.exceptions import ValidationError as DRFValidationError

        from apps.market_data.models.series import MarketDataSeries

        instrument_id = request.data.get('instrument_id')
        price_type = str(request.data.get('price_type', '')).upper()
        unit = str(request.data.get('unit', '')).upper()
        try:
            instrument = Instrument.objects.get(pk=instrument_id)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)
        if price_type not in PriceType.values:
            raise DRFValidationError({'price_type': 'Unsupported price type.'})
        if unit not in QuotationUnit.values:
            raise DRFValidationError({'unit': 'Unsupported quotation unit.'})
        currency = instrument.currency or 'INR'
        series, _ = MarketDataSeries.objects.using('market_data').get_or_create(
            instrument_id=instrument.id, exchange=instrument.exchange or '',
            source='MANUAL_VERIFIED', price_type=price_type, currency=currency,
            unit=unit, pricing_methodology='MANUAL_OPERATOR', adjustment_methodology='RAW',
            defaults={'description': f'Publisher-reviewed manual series for {instrument.symbol}'},
        )
        from apps.market_data.models.coverage import InstrumentCoverage
        InstrumentCoverage.objects.using('market_data').update_or_create(
            instrument_id=instrument.id,
            defaults={
                'price_type': price_type, 'currency': currency, 'unit': unit,
                'preferred_source': 'MANUAL_VERIFIED',
            },
        )
        return Response({
            'id': str(series.id), 'instrument_id': str(series.instrument_id),
            'exchange': series.exchange, 'source': series.source,
            'price_type': series.price_type, 'currency': series.currency,
            'unit': series.unit, 'data_version': series.data_version,
            'last_published_at': series.last_published_at.isoformat() if series.last_published_at else None,
        }, status=status.HTTP_201_CREATED)


class MarketDataSeriesVersionView(APIView):
    """
    Lightweight series-version check endpoint (ERD Section 15.3 & 16.2).
    Returns series_id, data_version, and last_published_at without transmitting full history.
    Used by frontend TanStack Query to invalidate cache only when data actually mutated.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request, pk):
        from apps.market_data.models.series import MarketDataSeries

        try:
            series = MarketDataSeries.objects.using('market_data').get(pk=pk)
        except (MarketDataSeries.DoesNotExist, ValueError):
            return Response({'detail': 'Series not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'series_id': str(series.id),
            'instrument_id': str(series.instrument_id),
            'data_version': series.data_version,
            'last_published_at': series.last_published_at.isoformat() if series.last_published_at else None,
        })


class MarketDataOverviewView(APIView):
    """Retrieve market overview summary."""

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request):
        overview = MarketDataService.get_market_overview()
        return Response(overview)


class MarketDataProvidersView(APIView):
    """List available providers and their capabilities."""

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request):
        providers = provider_registry.list_providers()
        return Response(providers)


class MarketDataHealthView(APIView):
    """Health check endpoint for configured market-data providers."""

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request):
        health_reports = provider_registry.check_all_health()
        data = [
            {
                'name': h.name,
                'is_available': h.is_available,
                'latency_ms': h.latency_ms,
                'last_checked': h.last_checked.isoformat(),
                'message': h.message,
                'mode': h.mode,
                'metadata': h.metadata,
            }
            for h in health_reports
        ]
        return Response(data)


class MarketDataRefreshView(APIView):
    """Operator-only refresh trigger; public users cannot initiate provider work."""

    permission_classes = [IsAuthenticatedAndEmailVerified, IsMarketDataOperator]

    def post(self, request, pk):
        try:
            instrument = Instrument.objects.get(pk=pk)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        quote = MarketDataService.get_latest_quote(instrument, force_refresh=True)
        return Response(QuoteSerializer(quote).data)
