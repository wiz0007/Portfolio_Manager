from typing import List, Optional

from django.db.models import Q

from apps.market_data.models.instrument import Instrument, InstrumentStatus


class InstrumentSearchService:
    """
    Search service for canonical catalogue instruments.
    Enforces that only active, verified instruments are returned,
    filtering across symbols, ISINs, scheme codes, and reference metadata.
    """

    @classmethod
    def search(
        cls,
        query: str = '',
        asset_class: Optional[str] = None,
        exchange: Optional[str] = None,
        product_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Instrument]:
        qs = Instrument.objects.filter(
            status=InstrumentStatus.ACTIVE,
            is_active=True,
        ).select_related('reference_data', 'coverage').prefetch_related('data_points')

        if asset_class:
            qs = qs.filter(asset_class=asset_class.upper())

        if exchange:
            qs = qs.filter(exchange__iexact=exchange)

        if product_type:
            qs = qs.filter(product_type__iexact=product_type)

        clean_q = query.strip()
        if clean_q:
            qs = qs.filter(
                Q(symbol__icontains=clean_q)
                | Q(name__icontains=clean_q)
                | Q(isin__icontains=clean_q)
                | Q(scheme_code__icontains=clean_q)
                | Q(exchange__icontains=clean_q)
                | Q(product_type__icontains=clean_q)
                | Q(reference_data__sector__icontains=clean_q)
                | Q(reference_data__industry__icontains=clean_q)
            )

        return list(qs[offset : offset + limit])
