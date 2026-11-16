from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

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
from apps.market_data.models.market_data_point import MarketDataPoint
from apps.market_data.providers.registry import provider_registry
from apps.market_data.services.market_data_service import MarketDataService


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
        active_only = self.request.query_params.get('is_active')
        if active_only is not None:
            qs = qs.filter(is_active=active_only.lower() in ['true', '1'])
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(symbol__icontains=search)
                | Q(name__icontains=search)
                | Q(isin__icontains=search)
            )
        return qs

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Fuzzy search endpoint for instrument selectors and autocompletes."""
        query = request.query_params.get('q', '').strip()
        if not query:
            return Response([])

        instruments = Instrument.objects.filter(
            Q(symbol__icontains=query)
            | Q(name__icontains=query)
            | Q(isin__icontains=query)
        ).filter(is_active=True)[:20]

        serializer = self.get_serializer(instruments, many=True)
        return Response(serializer.data)


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
