from datetime import datetime, timedelta, timezone

from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.market_data.api.v1.serializers import (
    HistoricalPointSerializer,
    InstrumentSerializer,
    QuoteSerializer,
)
from apps.market_data.models.instrument import Instrument
from apps.market_data.providers.registry import provider_registry
from apps.market_data.services.history_service import MarketHistoryService
from apps.market_data.services.market_data_service import MarketDataService
from apps.market_data.services.movement_service import PriceMovementService
from apps.market_data.services.price_resolver import PriceResolver
from apps.market_data.services.search_service import InstrumentSearchService


class InstrumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing and retrieving standardized financial instruments.
    Supports filtering by asset class, exchange, and active state.
    """

    queryset = Instrument.objects.select_related('reference_data').prefetch_related('data_points')
    serializer_class = InstrumentSerializer
    permission_classes = [permissions.IsAuthenticated]

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
        )
        return Response({
            'instrument_id': str(instrument.id),
            'symbol': instrument.symbol,
            'price': str(resolved.price) if resolved.price is not None else None,
            'currency': resolved.currency,
            'unit': resolved.unit,
            'effective_at': resolved.effective_at.isoformat() if resolved.effective_at else None,
            'status': resolved.status,
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
        if interval not in ('1D', '1W', '1M', '1Y'):
            return Response({'detail': f"Unsupported interval '{interval}'. Use '1D', '1W', '1M', or '1Y'."}, status=status.HTTP_400_BAD_REQUEST)

        price_type = request.query_params.get('price_type')

        try:
            history_res = MarketHistoryService.get_history(
                instrument=instrument,
                period=period,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                price_type=price_type,
            )
            return Response({
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'supported': history_res.supported,
                'period': history_res.period,
                'start_date': history_res.start_date,
                'end_date': history_res.end_date,
                'currency': history_res.currency,
                'unit': history_res.unit,
                'message': history_res.message,
                'points': [
                    {
                        'timestamp': p.timestamp.isoformat(),
                        'date': p.date,
                        'price': str(p.price),
                        'price_type': p.price_type,
                        'currency': p.currency,
                        'unit': p.unit,
                        'source': p.source,
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

    permission_classes = [permissions.IsAuthenticated]

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

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            instrument = Instrument.objects.get(pk=pk)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        interval = request.query_params.get('interval', '1D').upper()
        days_str = request.query_params.get('days')

        today = datetime.now(timezone.utc).date()
        if days_str and days_str.isdigit():
            start_date = today - timedelta(days=int(days_str))
            end_date = today
        else:
            from_str = request.query_params.get('from')
            to_str = request.query_params.get('to')
            start_date = (
                datetime.strptime(from_str, '%Y-%m-%d').date()
                if from_str
                else today - timedelta(days=30)
            )
            end_date = (
                datetime.strptime(to_str, '%Y-%m-%d').date()
                if to_str
                else today
            )

        points = MarketDataService.get_history(instrument, start_date, end_date, interval=interval)
        return Response(HistoricalPointSerializer(points, many=True).data)


class MarketDataOverviewView(APIView):
    """Retrieve market overview summary."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        overview = MarketDataService.get_market_overview()
        return Response(overview)


class MarketDataProvidersView(APIView):
    """List available providers and their capabilities."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        providers = provider_registry.list_providers()
        return Response(providers)


class MarketDataHealthView(APIView):
    """Health check endpoint for all market data providers."""

    permission_classes = [permissions.IsAuthenticated]

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
    """Force refresh latest quote for an instrument."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            instrument = Instrument.objects.get(pk=pk)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        quote = MarketDataService.get_latest_quote(instrument, force_refresh=True)
        return Response(QuoteSerializer(quote).data)
