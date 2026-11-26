import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional, Sequence

from django.utils import timezone as dj_timezone

from apps.market_data.models.coverage import InstrumentCoverage
from apps.market_data.models.instrument import Instrument
from apps.market_data.models.observation import ObservationStatus, PriceObservation, TrustClass
from apps.market_data.models.series import MarketDataSeries


class ResolutionStatus:
    AVAILABLE = 'AVAILABLE'
    STALE = 'STALE'
    MISSING = 'MISSING'
    SYNTHETIC = 'SYNTHETIC'
    AWAITING_VERIFICATION = 'AWAITING_VERIFICATION'
    UNVERIFIED = 'UNVERIFIED'
    INCOMPATIBLE = 'INCOMPATIBLE'
    UNSUPPORTED = 'UNSUPPORTED'


@dataclass
class ResolvedPrice:
    price: Optional[Decimal]
    status: str
    source: str
    source_reference: str
    effective_at: Optional[datetime]
    currency: str
    unit: str
    published_at: Optional[datetime] = None
    price_type: Optional[str] = None
    is_synthetic: bool = False
    notes: str = ''
    age_seconds: Optional[int] = None
    series_id: Optional[str] = None
    observation_id: Optional[str] = None
    data_version: Optional[int] = None


class PriceResolver:
    """Canonical exact-series resolver; bulk and single paths share identical policy."""

    TRUSTED_CLASSES = {
        TrustClass.VERIFIED_OFFICIAL,
        TrustClass.VERIFIED_PERMITTED_SECONDARY,
        TrustClass.MANUAL_VERIFIED,
        TrustClass.CORRECTED,
    }

    @classmethod
    def _resolve_selected(cls, instrument, coverage, series, observation, pending, now, as_of):
        target_type = series.price_type if series else (coverage.price_type if coverage else None)
        expected_currency = series.currency if series else (coverage.currency if coverage else instrument.currency)
        expected_unit = series.unit if series else (coverage.unit if coverage else 'UNITS')
        if series is None:
            return ResolvedPrice(None, ResolutionStatus.MISSING, 'NONE', instrument.symbol, None,
                                 expected_currency, expected_unit, price_type=target_type,
                                 notes='No active exact price series is configured.')
        if observation is None:
            return ResolvedPrice(None,
                ResolutionStatus.AWAITING_VERIFICATION if pending else ResolutionStatus.MISSING,
                'MANUAL_OPERATOR' if pending else 'NONE', instrument.symbol, None,
                series.currency, series.unit, price_type=series.price_type, series_id=str(series.id),
                data_version=series.data_version,
                notes='An observation is awaiting verification.' if pending else 'No published observation exists in this series.')

        if observation.currency != series.currency or observation.unit != series.unit:
            return ResolvedPrice(None, ResolutionStatus.INCOMPATIBLE, observation.source, instrument.symbol, None,
                                 series.currency, series.unit, price_type=series.price_type,
                                 series_id=str(series.id), observation_id=str(observation.id),
                                 data_version=series.data_version,
                                 notes='Observation currency or quotation unit conflicts with its series definition.')
        if coverage and coverage.currency and observation.currency != coverage.currency:
            return ResolvedPrice(None, ResolutionStatus.INCOMPATIBLE, observation.source, instrument.symbol, None,
                                 coverage.currency, coverage.unit, price_type=series.price_type,
                                 series_id=str(series.id), observation_id=str(observation.id),
                                 data_version=series.data_version,
                                 notes='Observation currency conflicts with coverage policy.')
        if observation.is_synthetic or observation.trust_class == TrustClass.SYNTHETIC:
            return ResolvedPrice(None, ResolutionStatus.SYNTHETIC, observation.source,
                                 observation.source_reference or instrument.symbol, observation.effective_at,
                                 observation.currency, observation.unit, observation.published_at,
                                 observation.price_type, True,
                                 'Synthetic observations are excluded from portfolio valuation.',
                                 series_id=str(series.id), observation_id=str(observation.id),
                                 data_version=series.data_version)
        if observation.trust_class not in cls.TRUSTED_CLASSES:
            return ResolvedPrice(None, ResolutionStatus.UNVERIFIED, observation.source,
                                 observation.source_reference or instrument.symbol, observation.effective_at,
                                 observation.currency, observation.unit, observation.published_at,
                                 observation.price_type, False,
                                 'Unverified observations are excluded from portfolio valuation.',
                                 series_id=str(series.id), observation_id=str(observation.id),
                                 data_version=series.data_version)

        reference_dt = as_of or now
        age_seconds = max(0, int((reference_dt - observation.effective_at).total_seconds()))
        stale = bool(coverage and coverage.freshness_hours and
                     (reference_dt - observation.effective_at).total_seconds() > coverage.freshness_hours * 3600)
        return ResolvedPrice(observation.value, ResolutionStatus.STALE if stale else ResolutionStatus.AVAILABLE,
                             observation.source, observation.source_reference or instrument.symbol,
                             observation.effective_at, observation.currency, observation.unit,
                             observation.published_at, observation.price_type, False,
                             'Observation exceeds configured freshness threshold.' if stale else observation.notes,
                             age_seconds, str(series.id), str(observation.id), series.data_version)

    @classmethod
    def resolve_price(cls, instrument: Instrument, as_of=None, price_type=None, series_id=None) -> ResolvedPrice:
        now = dj_timezone.now()
        obs_dt = as_of or now
        coverage = InstrumentCoverage.objects.using('market_data').filter(instrument_id=instrument.id).first()
        # An explicit series selection is authoritative. Coverage.price_type is
        # only the default when the caller has not selected a concrete series.
        target_type = price_type or (coverage.price_type if coverage and not series_id else None)
        series_qs = MarketDataSeries.objects.using('market_data').filter(
            instrument_id=instrument.id, is_active=True
        )
        if target_type:
            series_qs = series_qs.filter(price_type=target_type)
        if series_id:
            try:
                series_qs = series_qs.filter(pk=uuid.UUID(str(series_id)))
            except (ValueError, TypeError, AttributeError):
                return ResolvedPrice(None, ResolutionStatus.UNSUPPORTED, 'NONE', instrument.symbol, None,
                                     instrument.currency, coverage.unit if coverage else 'UNITS',
                                     price_type=target_type, notes='series_id must be a valid UUID.')
        series_rows = list(series_qs.order_by('id')[:2])
        if len(series_rows) > 1 and not series_id and coverage and coverage.preferred_source:
            preferred_rows = list(series_qs.filter(source=coverage.preferred_source).order_by('id')[:2])
            if len(preferred_rows) == 1:
                series_rows = preferred_rows
        if len(series_rows) > 1:
            return ResolvedPrice(None, ResolutionStatus.UNSUPPORTED, 'NONE', instrument.symbol, None,
                                 instrument.currency, coverage.unit if coverage else 'UNITS',
                                 price_type=target_type, notes='Multiple active series match. An exact series_id is required.')
        series = series_rows[0] if series_rows else None
        observation = None
        pending = False
        if series:
            observation = (PriceObservation.objects.using('market_data').filter(
                instrument_id=instrument.id,
                series_id=series.id,
                price_type=series.price_type,
                status=ObservationStatus.PUBLISHED,
                effective_at__lte=obs_dt,
                # Historical resolution must not expose observations that were
                # published after the requested as-of instant. This also prevents
                # later corrections from rewriting what the system knew earlier.
                published_at__isnull=False,
                published_at__lte=obs_dt,
            ).exclude(
                corrections__status=ObservationStatus.PUBLISHED,
                corrections__published_at__isnull=False,
                corrections__published_at__lte=obs_dt,
                corrections__effective_at__lte=obs_dt,
            ).order_by('-effective_at', '-published_at', '-created_at').first())
            if observation is None:
                pending = PriceObservation.objects.using('market_data').filter(
                    instrument_id=instrument.id, series_id=series.id,
                    status=ObservationStatus.PENDING_REVIEW, effective_at__lte=obs_dt,
                ).exists()
        return cls._resolve_selected(instrument, coverage, series, observation, pending, now, obs_dt)

    @classmethod
    def resolve_prices_bulk(cls, instruments: Sequence[Instrument], as_of=None) -> Dict[uuid.UUID, ResolvedPrice]:
        if not instruments:
            return {}
        now = dj_timezone.now()
        obs_dt = as_of or now
        unique = {inst.id: inst for inst in instruments}
        ids = list(unique)
        coverages = {
            row.instrument_id: row for row in InstrumentCoverage.objects.using('market_data').filter(instrument_id__in=ids)
        }
        series_by_instrument = defaultdict(list)
        for series in MarketDataSeries.objects.using('market_data').filter(instrument_id__in=ids, is_active=True).order_by('id'):
            coverage = coverages.get(series.instrument_id)
            if coverage and series.price_type != coverage.price_type:
                continue
            series_by_instrument[series.instrument_id].append(series)

        selected = {}
        for inst_id, rows in series_by_instrument.items():
            coverage = coverages.get(inst_id)
            if len(rows) > 1 and coverage and coverage.preferred_source:
                preferred_rows = [row for row in rows if row.source == coverage.preferred_source]
                if len(preferred_rows) == 1:
                    rows = preferred_rows
                    series_by_instrument[inst_id] = rows
            if len(rows) == 1:
                selected[inst_id] = rows[0]

        series_ids = [row.id for row in selected.values()]
        latest_by_series = {}
        if series_ids:
            observations = (PriceObservation.objects.using('market_data').filter(
                series_id__in=series_ids,
                status=ObservationStatus.PUBLISHED,
                effective_at__lte=obs_dt,
                published_at__isnull=False,
                published_at__lte=obs_dt,
            ).exclude(
                corrections__status=ObservationStatus.PUBLISHED,
                corrections__published_at__isnull=False,
                corrections__published_at__lte=obs_dt,
                corrections__effective_at__lte=obs_dt,
            ).order_by('series_id', '-effective_at', '-published_at', '-created_at'))
            for obs in observations:
                latest_by_series.setdefault(obs.series_id, obs)
        missing_series_ids = [sid for sid in series_ids if sid not in latest_by_series]
        pending_series = set(PriceObservation.objects.using('market_data').filter(
            series_id__in=missing_series_ids, status=ObservationStatus.PENDING_REVIEW,
            effective_at__lte=obs_dt,
        ).values_list('series_id', flat=True)) if missing_series_ids else set()

        results = {}
        for inst_id, instrument in unique.items():
            coverage = coverages.get(inst_id)
            rows = series_by_instrument.get(inst_id, [])
            if len(rows) > 1:
                results[inst_id] = ResolvedPrice(
                    None, ResolutionStatus.UNSUPPORTED, 'NONE', instrument.symbol, None,
                    instrument.currency, coverage.unit if coverage else 'UNITS',
                    price_type=coverage.price_type if coverage else None,
                    notes='Multiple active series match. An exact series_id is required.',
                )
                continue
            series = selected.get(inst_id)
            obs = latest_by_series.get(series.id) if series else None
            pending = bool(series and series.id in pending_series)
            results[inst_id] = cls._resolve_selected(instrument, coverage, series, obs, pending, now, obs_dt)
        return results
