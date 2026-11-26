import uuid
from datetime import date, datetime
from datetime import time as dt_time
from datetime import timezone as dt_timezone
from zoneinfo import ZoneInfo

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
from core.permissions import IsAuthenticatedAndEmailVerified


class InstrumentRequestViewSet(viewsets.ModelViewSet):
    """
    User submission and operator management of unknown-instrument requests.
    """

    queryset = InstrumentRequest.objects.all().select_related('user', 'matched_instrument')
    serializer_class = InstrumentRequestSerializer
    permission_classes = [IsAuthenticatedAndEmailVerified, IsRequestOwnerOrStaff]

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
    permission_classes = [IsAuthenticatedAndEmailVerified, IsStaffOrReadOnly]

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
    permission_classes = [IsAuthenticatedAndEmailVerified, IsMarketDataOperator]
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

    queryset = PriceObservation.objects.all()
    serializer_class = PriceObservationSerializer
    permission_classes = [IsAuthenticatedAndEmailVerified]

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
        with transaction.atomic(using='market_data'):
            obs = PriceObservation.objects.using('market_data').select_for_update().get(pk=pk)
            if obs.status != ObservationStatus.DRAFT:
                return Response(
                    {'detail': f"Cannot submit observation in status '{obs.status}' for review. Must be in DRAFT."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            obs.submit_for_review()
        return Response(PriceObservationSerializer(obs).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def publish(self, request, pk=None):
        with transaction.atomic(using='market_data'):
            obs = PriceObservation.objects.using('market_data').select_for_update().get(pk=pk)
            if obs.status == ObservationStatus.PUBLISHED:
                return Response({'detail': 'Observation is already published.'}, status=status.HTTP_400_BAD_REQUEST)
            if obs.status != ObservationStatus.PENDING_REVIEW:
                return Response(
                    {'detail': f"Cannot publish observation in status '{obs.status}'. Must be in PENDING_REVIEW."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # 1. Publish observation atomically on market_data
            obs.publish(request.user)

        inst = obs.instrument or Instrument.objects.filter(pk=obs.instrument_id).first()
        refresh_res = {}
        if inst:
            from apps.valuation.services.refresh_service import ValuationRefreshService
            refresh_res = ValuationRefreshService.refresh_holdings_for_instrument(inst)

        return Response(
            {
                'observation': PriceObservationSerializer(obs).data,
                'valuation_refresh': {
                    'status': 'COMPLETED' if refresh_res else 'QUEUED',
                    'refreshed_count': refresh_res.get('refreshed_count', refresh_res.get('refreshed', 0)),
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def reject(self, request, pk=None):
        reason = request.data.get('reason', '').strip()
        if not reason:
            return Response({'detail': 'Rejection reason is required.'}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic(using='market_data'):
            obs = PriceObservation.objects.using('market_data').select_for_update().get(pk=pk)
            if obs.status == ObservationStatus.PUBLISHED:
                return Response({'detail': 'Cannot reject an already published observation.'}, status=status.HTTP_400_BAD_REQUEST)
            obs.reject(request.user, reason)
        return Response(PriceObservationSerializer(obs).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsMarketDataPublisher])
    def correct(self, request, pk=None):
        with transaction.atomic(using='market_data'):
            original_obs = PriceObservation.objects.using('market_data').select_for_update().get(pk=pk)
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
            corrected_value = data['value']
            high_candidates = [v for v in (original_obs.high_price, original_obs.open_price, corrected_value) if v is not None]
            low_candidates = [v for v in (original_obs.low_price, original_obs.open_price, corrected_value) if v is not None]
            corrected_high = max(high_candidates) if high_candidates else None
            corrected_low = min(low_candidates) if low_candidates else None

            # The PriceObservation model emits the correction publication event and
            # increments the series version atomically with this insert.
            series = original_obs.series

            # Create new correction observation strictly on market_data
            correction_obs = PriceObservation.objects.using('market_data').create(
                instrument=original_obs.instrument,
                series=series,
                price_type=original_obs.price_type,
                value=corrected_value,
                open_price=original_obs.open_price,
                high_price=corrected_high,
                low_price=corrected_low,
                volume=original_obs.volume,
                currency=original_obs.currency,
                unit=original_obs.unit,
                effective_at=eff_at,
                source=original_obs.source,
                source_reference=data.get('source_reference', ''),
                notes=data.get('notes', ''),
                status=ObservationStatus.DRAFT,
                trust_class=original_obs.trust_class,
                is_synthetic=original_obs.is_synthetic,
                recorded_by=request.user,
                correction_of=original_obs,
                correction_reason=data['correction_reason'],
            )
            correction_obs.status = ObservationStatus.PENDING_REVIEW
            correction_obs.save(using='market_data', update_fields=['status', 'updated_at'])
            correction_obs.publish(request.user)

        # Correction publication uses the same durable outbox processor as normal publication.
        return Response(
            {
                'original_id': str(original_obs.id),
                'correction': PriceObservationSerializer(correction_obs).data,
                'valuation_refresh': {'status': 'QUEUED'},
            },
            status=status.HTTP_201_CREATED,
        )


class PriceImportPreviewView(APIView):
    """
    Validates CSV upload without persistence and returns a preview report with row-level errors.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified, IsMarketDataOperator]

    def post(self, request):
        csv_file = request.FILES.get('file')
        if not csv_file:
            # Fallback to json string body
            csv_content = request.data.get('csv_content')
            filename = request.data.get('filename', 'upload.csv')
        else:
            if csv_file.size > PriceImportService.MAX_CONTENT_BYTES:
                return Response({'detail': 'CSV exceeds the 5 MB upload limit.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
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

    permission_classes = [IsAuthenticatedAndEmailVerified, IsMarketDataOperator]

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


class DatabaseHealthView(APIView):
    """
    Exposes health, connectivity latency, engine types, and identity synchronization status
    across both Primary and Market Data Storage databases (ERD Section 7.6 and 15).
    """

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def get(self, request):
        from apps.market_data.models.instrument_reference import MarketInstrumentReference
        from apps.market_data.services.sync_service import InstrumentIdentitySyncService
        from config.database.connections import get_database_status

        # Restrict detailed engine/raw diagnostics to staff/operators (ERD Section 19.4)
        is_operator = request.user.is_staff or request.user.groups.filter(name__in=['MarketDataOperator', 'MarketDataPublisher']).exists()
        db_status = get_database_status(detailed=is_operator)
        target_db = InstrumentIdentitySyncService._target_db()
        canonical_count = Instrument.objects.using('default').count()
        synced_count = MarketInstrumentReference.objects.using(target_db).count()

        sync_info = {
            'status': 'SYNCHRONIZED' if synced_count >= canonical_count else 'PENDING_RECONCILIATION',
        }
        if is_operator:
            sync_info['canonical_instruments_primary'] = canonical_count
            sync_info['projected_references_storage'] = synced_count
            sync_info['storage_db_alias'] = target_db

        return Response({
            'status': db_status['overall_status'],
            'databases': db_status['databases'],
            'synchronization': sync_info,
        }, status=status.HTTP_200_OK)


class BulkPriceResolverView(APIView):
    """
    Authoritative bulk price resolution for batches of instruments.
    Fulfills ERD Section 7.2: accepts multiple canonical instrument UUIDs and
    returns structured status, provenance, currency, and price.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified]

    def post(self, request):
        instrument_ids = request.data.get('instrument_ids', [])
        if not isinstance(instrument_ids, list) or not instrument_ids:
            return Response(
                {'detail': 'instrument_ids must be a non-empty list of UUIDs.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(instrument_ids) > 100:
            return Response({'detail': 'A maximum of 100 instruments can be resolved per request.'}, status=status.HTTP_400_BAD_REQUEST)
        parsed_ids = {}
        for raw_id in instrument_ids:
            try:
                parsed_ids[str(raw_id)] = uuid.UUID(str(raw_id))
            except (ValueError, TypeError, AttributeError):
                continue

        as_of_param = request.data.get('as_of')
        as_of_dt = None
        if as_of_param:
            try:
                if 'T' in str(as_of_param):
                    as_of_dt = datetime.fromisoformat(str(as_of_param).replace('Z', '+00:00'))
                    if timezone.is_naive(as_of_dt):
                        as_of_dt = as_of_dt.replace(tzinfo=ZoneInfo('Asia/Kolkata'))
                else:
                    d = date.fromisoformat(str(as_of_param))
                    as_of_dt = datetime.combine(d, dt_time.max, tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(dt_timezone.utc)
            except Exception:
                return Response({'detail': 'Invalid as_of date format.'}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve canonical instruments from default database
        instruments = list(Instrument.objects.filter(id__in=list(parsed_ids.values())))
        resolved_map = PriceResolver.resolve_prices_bulk(instruments, as_of=as_of_dt)

        inst_by_id = {inst.id: inst for inst in instruments}
        results = []
        for iid in instrument_ids:
            try:
                parsed_id = parsed_ids[str(iid)]
            except (KeyError, ValueError, TypeError):
                results.append({
                    'instrument_id': str(iid),
                    'status': 'INVALID_UUID',
                    'price': None,
                    'notes': 'Malformed UUID format.',
                })
                continue

            inst = inst_by_id.get(parsed_id)
            if not inst:
                results.append({
                    'instrument_id': str(parsed_id),
                    'status': 'UNREGISTERED_INSTRUMENT',
                    'price': None,
                    'notes': 'Instrument not found in canonical catalogue.',
                })
                continue

            resolved = resolved_map.get(parsed_id)
            if resolved:
                results.append({
                    'instrument_id': str(parsed_id),
                    'symbol': inst.symbol,
                    'status': resolved.status,
                    'price': str(resolved.price) if resolved.price is not None else None,
                    'price_type': resolved.price_type,
                    'series_id': resolved.series_id,
                    'observation_id': resolved.observation_id,
                    'data_version': resolved.data_version,
                    'currency': resolved.currency,
                    'unit': resolved.unit,
                    'source': resolved.source,
                    'effective_date': resolved.effective_at.astimezone(ZoneInfo('Asia/Kolkata')).date().isoformat() if resolved.effective_at else None,
                    'effective_at': resolved.effective_at.isoformat() if resolved.effective_at else None,
                    'is_synthetic': resolved.is_synthetic,
                    'notes': resolved.notes,
                })
            else:
                results.append({
                    'instrument_id': str(parsed_id),
                    'symbol': inst.symbol,
                    'status': 'MISSING',
                    'price': None,
                    'currency': inst.currency,
                    'notes': 'No price resolved for instrument.',
                })

        return Response({
            'as_of': as_of_dt.isoformat() if as_of_dt else timezone.now().isoformat(),
            'total_requested': len(instrument_ids),
            'total_resolved': sum(1 for r in results if r.get('status') == 'AVAILABLE'),
            'results': results,
        }, status=status.HTTP_200_OK)


class PriceResolverView(APIView):
    """
    Resolves authoritative published market price for an instrument as of a requested date.
    Exposes published_at, price_type, and age_seconds for data freshness and provenance.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified]

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
                    if timezone.is_naive(as_of_dt):
                        as_of_dt = as_of_dt.replace(tzinfo=ZoneInfo('Asia/Kolkata'))
                else:
                    d = date.fromisoformat(as_of_param)
                    as_of_dt = datetime.combine(d, dt_time.max, tzinfo=ZoneInfo('Asia/Kolkata')).astimezone(dt_timezone.utc)
            except Exception:
                return Response({'detail': 'Invalid as_of date format.'}, status=status.HTTP_400_BAD_REQUEST)

        price_type = request.query_params.get('price_type')
        series_id = request.query_params.get('series_id')
        resolved = PriceResolver.resolve_price(instrument, as_of=as_of_dt, price_type=price_type, series_id=series_id)

        return Response(
            {
                'instrument_id': str(instrument.id),
                'symbol': instrument.symbol,
                'status': resolved.status,
                'price': str(resolved.price) if resolved.price is not None else None,
                'price_type': resolved.price_type,
                'series_id': resolved.series_id,
                'observation_id': resolved.observation_id,
                'data_version': resolved.data_version,
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


class HistoricalCoverageReportView(APIView):
    """
    Operator-facing historical data coverage and storage audit.
    Shows instrument coverage status, row counts, table/index storage, and plan headroom.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified, IsMarketDataOperator]

    def get(self, request):
        from django.db import connections
        from django.db.models import Count, Max, Min

        total_instruments = Instrument.objects.filter(status=InstrumentStatus.ACTIVE).count()
        published_qs = PriceObservation.objects.using('market_data').filter(
            status=ObservationStatus.PUBLISHED, series_id__isnull=False, is_synthetic=False,
        )
        obs_by_inst = list(
            published_qs.values('instrument_id').annotate(cnt=Count('id'))
        )
        at_least_180 = sum(1 for row in obs_by_inst if row['cnt'] >= 180)
        between_2_179 = sum(1 for row in obs_by_inst if 1 < row['cnt'] < 180)
        one_observation = sum(1 for row in obs_by_inst if row['cnt'] == 1)
        instruments_with_data = len(obs_by_inst)
        no_data_count = max(0, total_instruments - instruments_with_data)

        asset_breakdown = list(
            Instrument.objects.filter(status=InstrumentStatus.ACTIVE)
            .values('asset_class').annotate(total=Count('id')).order_by('-total')
        )
        trust_breakdown = list(
            published_qs.values('trust_class').annotate(count=Count('id')).order_by('-count')
        )
        date_range = published_qs.aggregate(
            min_date=Min('effective_at'), max_date=Max('effective_at'), total_observations=Count('id')
        )

        table_size = index_size = total_size = database_size = 'N/A'
        try:
            with connections['market_data'].cursor() as cursor:
                cursor.execute("""
                    SELECT
                        pg_size_pretty(pg_relation_size('price_observations')),
                        pg_size_pretty(pg_indexes_size('price_observations')),
                        pg_size_pretty(pg_total_relation_size('price_observations')),
                        pg_size_pretty(pg_database_size(current_database()))
                """)
                row = cursor.fetchone()
                if row:
                    table_size, index_size, total_size, database_size = row
        except Exception:
            # SQLite and restricted database roles do not expose PostgreSQL size functions.
            pass

        market_tz = ZoneInfo('Asia/Kolkata')
        return Response({
            'universe': {
                'total_instruments': total_instruments,
                'at_least_180_published_observations': at_least_180,
                'between_2_and_179_published_observations': between_2_179,
                'single_published_observation': one_observation,
                'no_published_history': no_data_count,
                'calendar_completeness_verified': False,
                'note': 'Observation counts are descriptive only; they do not prove expected-session or holiday-aware completeness.',
            },
            'coverage': {
                'total_observations': date_range['total_observations'],
                'earliest_market_date': date_range['min_date'].astimezone(market_tz).date().isoformat() if date_range['min_date'] else None,
                'latest_market_date': date_range['max_date'].astimezone(market_tz).date().isoformat() if date_range['max_date'] else None,
                'trust_distribution': trust_breakdown,
                'asset_breakdown': asset_breakdown,
            },
            'storage': {
                'price_observations_table_size': table_size,
                'price_observations_index_size': index_size,
                'price_observations_total_size': total_size,
                'market_data_database_size': database_size,
                'plan_limit_and_headroom': 'Not inferred; check the active Neon plan and usage dashboard.',
            },
        }, status=status.HTTP_200_OK)



class HistoricalBackfillTriggerView(APIView):
    """
    Operator action to trigger on-demand historical backfill for an instrument.
    """

    permission_classes = [IsAuthenticatedAndEmailVerified, IsMarketDataPublisher]

    def post(self, request):
        from apps.market_data.services.backfill_service import HistoricalBackfillService

        instrument_id = request.data.get('instrument_id')
        symbol = request.data.get('symbol')

        inst = None
        if instrument_id:
            inst = Instrument.objects.filter(id=instrument_id).first()
        elif symbol:
            inst = Instrument.objects.filter(symbol=symbol.upper()).first()

        if not inst:
            return Response({'detail': 'Instrument not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            target_days = int(request.data.get('target_days', 1825))
        except (TypeError, ValueError):
            return Response({'detail': 'target_days must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
        if target_days < 1 or target_days > 1825:
            return Response({'detail': 'target_days must be between 1 and 1825.'}, status=status.HTTP_400_BAD_REQUEST)

        service = HistoricalBackfillService(publisher=request.user)
        result = service.backfill_instrument(inst, target_days=target_days)
        return Response(result, status=status.HTTP_200_OK if result['status'] == 'SUCCESS' else status.HTTP_400_BAD_REQUEST)

