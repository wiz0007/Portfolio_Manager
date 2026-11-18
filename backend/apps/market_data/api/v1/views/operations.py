from datetime import date, datetime

from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.market_data.api.v1.serializers.operations import (
    InstrumentCoverageSerializer,
    InstrumentRequestApproveSerializer,
    InstrumentRequestMatchSerializer,
    InstrumentRequestRejectSerializer,
    InstrumentRequestSerializer,
    MarketDataWorklistSerializer,
    PriceObservationCorrectionSerializer,
    PriceObservationSerializer,
)
from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument import Instrument, InstrumentStatus
from apps.market_data.models.instrument_request import (
    InstrumentRequest,
    InstrumentRequestStatus,
)
from apps.market_data.models.observation import ObservationStatus, PriceObservation
from apps.market_data.models.worklist import MarketDataWorklist
from apps.market_data.permissions import (
    IsMarketDataOperator,
    IsMarketDataPublisher,
    IsRequestOwnerOrStaff,
    IsStaffOrReadOnly,
)
from apps.market_data.services.import_service import PriceImportService
from apps.market_data.services.price_resolver import PriceResolver
from apps.market_data.services.worklist_service import MarketDataWorklistService
from apps.valuation.services.refresh_service import ValuationRefreshService


class InstrumentRequestViewSet(viewsets.ModelViewSet):
    """
    User submission and operator management of unknown-instrument requests.
    """

    queryset = InstrumentRequest.objects.all().select_related('user', 'matched_instrument')
    serializer_class = InstrumentRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsRequestOwnerOrStaff]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(user=user)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def match(self, request, pk=None):
        req_obj = self.get_object()
        serializer = InstrumentRequestMatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instrument_id = serializer.validated_data['instrument_id']

        try:
            instrument = Instrument.objects.get(id=instrument_id)
        except Instrument.DoesNotExist:
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        req_obj.status = InstrumentRequestStatus.MATCHED
        req_obj.matched_instrument = instrument
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.save()

        return Response(InstrumentRequestSerializer(req_obj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    @transaction.atomic
    def approve(self, request, pk=None):
        req_obj = self.get_object()
        serializer = InstrumentRequestApproveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # 1. Create canonical Instrument
        instrument = Instrument.objects.create(
            symbol=data['symbol'].upper(),
            name=data['name'],
            asset_class=data['asset_class'],
            exchange=data.get('exchange', '').upper(),
            currency=data.get('currency', 'INR'),
            isin=data.get('isin') or None,
            scheme_code=data.get('scheme_code') or None,
            product_type=data.get('product_type', ''),
            status=InstrumentStatus.ACTIVE,
        )

        # 2. Create coverage policy atomically
        coverage = InstrumentCoverage.objects.create(
            instrument=instrument,
            price_type=data.get('price_type', 'LTP'),
            currency=data.get('currency', 'INR'),
            unit=data.get('unit', 'UNITS'),
            cadence=data.get('cadence', 'EVERY_TRADING_DAY'),
            freshness_hours=data.get('freshness_hours', 24),
            preferred_source='MANUAL_VERIFIED',
            inclusion_reason=f"Approved from request {req_obj.id}",
        )

        # 3. Mark request as APPROVED
        req_obj.status = InstrumentRequestStatus.APPROVED
        req_obj.matched_instrument = instrument
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.save()

        return Response(
            {
                'request': InstrumentRequestSerializer(req_obj).data,
                'instrument_id': str(instrument.id),
                'coverage_id': str(coverage.id),
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def reject(self, request, pk=None):
        req_obj = self.get_object()
        serializer = InstrumentRequestRejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        req_obj.status = InstrumentRequestStatus.REJECTED
        req_obj.rejection_reason = serializer.validated_data['reason']
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.save()

        return Response(InstrumentRequestSerializer(req_obj).data)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def duplicate(self, request, pk=None):
        req_obj = self.get_object()
        req_obj.status = InstrumentRequestStatus.DUPLICATE
        req_obj.reviewed_by = request.user
        req_obj.reviewed_at = timezone.now()
        req_obj.save()

        return Response(InstrumentRequestSerializer(req_obj).data)


class InstrumentCoverageViewSet(viewsets.ModelViewSet):
    """
    CRUD management of instrument price-coverage policies.
    """

    queryset = InstrumentCoverage.objects.all().select_related('instrument')
    serializer_class = InstrumentCoverageSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        cadence_param = self.request.query_params.get('cadence')
        if cadence_param:
            qs = qs.filter(cadence=cadence_param.upper())
        return qs


class MarketDataWorklistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoints for generating, querying, and exporting daily collection worklists.
    """

    queryset = MarketDataWorklist.objects.all().prefetch_related('items')
    serializer_class = MarketDataWorklistSerializer
    permission_classes = [permissions.IsAuthenticated, IsMarketDataOperator]
    lookup_field = 'worklist_date'

    @action(detail=False, methods=['post'])
    def generate(self, request):
        date_str = request.data.get('date')
        target_date = None
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response({'detail': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)

        worklist = MarketDataWorklistService.generate_worklist(target_date)
        return Response(MarketDataWorklistSerializer(worklist).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='export-md')
    def export_md(self, request, worklist_date=None):
        worklist = self.get_object()
        md_content = MarketDataWorklistService.export_to_markdown(worklist)
        response = HttpResponse(md_content, content_type='text/markdown; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{worklist.worklist_date}-market-data-worklist.md"'
        return response

    @action(detail=True, methods=['get'], url_path='export-csv')
    def export_csv(self, request, worklist_date=None):
        worklist = self.get_object()
        csv_content = MarketDataWorklistService.export_to_csv(worklist)
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{worklist.worklist_date}-market-data-worklist.csv"'
        return response


class PriceObservationViewSet(viewsets.ModelViewSet):
    """
    Append-only observation lifecycle management:
    draft -> pending_review -> published.
    Direct modification via PUT/PATCH is rejected (use correction flow).
    Published observations cannot be deleted.
    """

    queryset = PriceObservation.objects.all().select_related('instrument', 'recorded_by', 'published_by')
    serializer_class = PriceObservationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        # Ordinary users can only see published observations; staff/operators/publishers can see drafts
        if not (
            user.is_staff
            or user.is_superuser
            or user.groups.filter(name__in=['MarketDataOperator', 'MarketDataPublisher']).exists()
        ):
            qs = qs.filter(status=ObservationStatus.PUBLISHED)

        inst_id = self.request.query_params.get('instrument')
        if inst_id:
            qs = qs.filter(instrument_id=inst_id)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param.upper())
        return qs

    def perform_create(self, serializer):
        # Only operators or staff can create observations
        if not (self.request.user.is_staff or self.request.user.groups.filter(name='MarketDataOperator').exists()):
            raise permissions.PermissionDenied("Only market data operators can record price observations.")
        serializer.save(recorded_by=self.request.user, status=ObservationStatus.DRAFT)

    def update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Price observations cannot be directly modified. Use the correction flow.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        return Response(
            {'detail': 'Price observations cannot be directly modified. Use the correction flow.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def destroy(self, request, *args, **kwargs):
        obs = self.get_object()
        if obs.status == ObservationStatus.PUBLISHED:
            return Response(
                {'detail': 'Published price observations cannot be deleted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not (request.user.is_staff or request.user.groups.filter(name='MarketDataOperator').exists()):
            raise permissions.PermissionDenied("Only market data operators can delete draft observations.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataOperator], url_path='submit-for-review')
    def submit_for_review(self, request, pk=None):
        with transaction.atomic():
            obs = PriceObservation.objects.select_for_update().get(pk=pk)
            if obs.status != ObservationStatus.DRAFT:
                return Response(
                    {'detail': f"Cannot submit observation in status '{obs.status}' for review. Must be in DRAFT."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obs.submit_for_review()
        return Response(PriceObservationSerializer(obs).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def publish(self, request, pk=None):
        with transaction.atomic():
            obs = PriceObservation.objects.select_for_update().get(pk=pk)
            if obs.status == ObservationStatus.PUBLISHED:
                return Response({'detail': 'Observation is already published.'}, status=status.HTTP_400_BAD_REQUEST)
            if obs.status != ObservationStatus.PENDING_REVIEW:
                return Response(
                    {'detail': f"Cannot publish observation in status '{obs.status}'. Must be in PENDING_REVIEW."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 1. Publish observation atomically
            obs.publish(request.user)

        # 2. Trigger valuation refresh across affected holdings with failure isolation
        try:
            refresh_stats = ValuationRefreshService.refresh_holdings_for_instrument(obs.instrument)
        except Exception as e:
            refresh_stats = {'error': str(e), 'refreshed_count': 0, 'failed_count': 0}

        return Response(
            {
                'observation': PriceObservationSerializer(obs).data,
                'valuation_refresh': refresh_stats,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def reject(self, request, pk=None):
        obs = self.get_object()
        if obs.status == ObservationStatus.PUBLISHED:
            return Response({'detail': 'Cannot reject an already published observation.'}, status=status.HTTP_400_BAD_REQUEST)
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': 'Rejection reason is required.'}, status=status.HTTP_400_BAD_REQUEST)

        obs.reject(request.user, reason)
        return Response(PriceObservationSerializer(obs).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def correct(self, request, pk=None):
        with transaction.atomic():
            original_obs = PriceObservation.objects.select_for_update().get(pk=pk)
            if original_obs.status != ObservationStatus.PUBLISHED:
                return Response(
                    {'detail': 'Only published observations can be corrected.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if original_obs.corrections.filter(status=ObservationStatus.PUBLISHED).exists():
                return Response(
                    {'detail': 'This observation has already been superseded by an active correction.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = PriceObservationCorrectionSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data

            eff_at = data.get('effective_at') or original_obs.effective_at

            # Create new correction observation
            correction_obs = PriceObservation.objects.create(
                instrument=original_obs.instrument,
                price_type=original_obs.price_type,
                value=data['value'],
                currency=original_obs.currency,
                unit=original_obs.unit,
                effective_at=eff_at,
                source=data.get('source', 'MANUAL_CORRECTION'),
                source_reference=data.get('source_reference', ''),
                notes=data.get('notes', ''),
                status=ObservationStatus.PUBLISHED,
                recorded_by=request.user,
                published_by=request.user,
                published_at=timezone.now(),
                correction_of=original_obs,
                correction_reason=data['correction_reason'],
            )

            # Sync correction to MarketDataPoint
            from apps.market_data.models.market_data_point import MarketDataPoint
            MarketDataPoint.objects.update_or_create(
                instrument=correction_obs.instrument,
                timestamp=correction_obs.effective_at,
                interval='1D',
                provider=correction_obs.source,
                defaults={
                    'price': correction_obs.value,
                    'close_price': correction_obs.value,
                },
            )

        # Trigger valuation refresh with failure isolation outside transaction
        try:
            refresh_stats = ValuationRefreshService.refresh_holdings_for_instrument(correction_obs.instrument)
        except Exception as e:
            refresh_stats = {'error': str(e), 'refreshed_count': 0, 'failed_count': 0}

        return Response(
            {
                'original_id': str(original_obs.id),
                'correction': PriceObservationSerializer(correction_obs).data,
                'valuation_refresh': refresh_stats,
            },
            status=status.HTTP_201_CREATED,
        )


class PriceImportPreviewView(APIView):
    """
    Validates CSV upload without persistence and returns a preview report with row-level errors.
    """

    permission_classes = [permissions.IsAuthenticated, IsMarketDataOperator]

    def post(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file:
            # Fallback to json string body
            csv_content = request.data.get('csv_content')
            filename = request.data.get('filename', 'upload.csv')
        else:
            try:
                csv_content = csv_file.read().decode('utf-8-sig')
                filename = csv_file.name
            except Exception as e:
                return Response({'detail': f'Could not read CSV file: {e!s}'}, status=status.HTTP_400_BAD_REQUEST)

        if not csv_content:
            return Response({'detail': 'No CSV content provided.'}, status=status.HTTP_400_BAD_REQUEST)

        preview = PriceImportService.preview_csv(request.user, csv_content, filename)
        return Response(preview, status=status.HTTP_200_OK)


class PriceImportCommitView(APIView):
    """
    Commits valid previewed rows as draft PriceObservations using server-persisted batch_id.
    """

    permission_classes = [permissions.IsAuthenticated, IsMarketDataOperator]

    def post(self, request):
        batch_id = request.data.get('batch_id')
        if not batch_id:
            return Response({'detail': 'batch_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            batch = PriceImportService.commit_batch(request.user, batch_id)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'batch_id': str(batch.id),
                'status': batch.status,
                'valid_count': batch.valid_rows,
                'error_count': batch.error_rows,
                'message': f"Successfully committed {batch.valid_rows} draft observations.",
            },
            status=status.HTTP_201_CREATED,
        )


class PriceResolverView(APIView):
    """
    Resolves authoritative published market price for an instrument as of a requested date.
    Exposes published_at, price_type, and age_seconds for data freshness and provenance.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, instrument_id):
        try:
            instrument = Instrument.objects.get(id=instrument_id)
        except (Instrument.DoesNotExist, ValueError):
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        as_of_param = request.query_params.get('as_of')
        as_of_dt = None
        if as_of_param:
            try:
                if 'T' in as_of_param:
                    as_of_dt = datetime.fromisoformat(as_of_param.replace('Z', '+00:00'))
                else:
                    d = date.fromisoformat(as_of_param)
                    as_of_dt = datetime.combine(d, datetime.max.time(), tzinfo=timezone.utc)
            except Exception:
                return Response({'detail': 'Invalid as_of date format.'}, status=status.HTTP_400_BAD_REQUEST)

        price_type = request.query_params.get('price_type')
        resolved = PriceResolver.resolve_price(instrument, as_of=as_of_dt, price_type=price_type)

        return Response(
            {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': resolved.status,
                'price': str(resolved.price) if resolved.price is not None else None,
                'price_type': resolved.price_type,
                'currency': resolved.currency,
                'unit': resolved.unit,
                'source': resolved.source,
                'source_reference': resolved.source_reference,
                'effective_at': resolved.effective_at.isoformat() if resolved.effective_at else None,
                'published_at': resolved.published_at.isoformat() if resolved.published_at else None,
                'age_seconds': resolved.age_seconds,
                'is_synthetic': resolved.is_synthetic,
                'notes': resolved.notes,
            },
            status=status.HTTP_200_OK,
        )
