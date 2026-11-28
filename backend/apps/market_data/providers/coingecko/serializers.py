"""CoinGecko payload validation and serialization."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional


def parse_decimal_safe(val: Any) -> Optional[Decimal]:
    if val is None or val == '':
        return None
    try:
        d = Decimal(str(val).strip())
        if d.is_nan() or d.is_infinite():
            return None
        return d
    except (InvalidOperation, ValueError, TypeError):
        return None


def serialize_market_item(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a single coin entry from /coins/markets."""
    price = parse_decimal_safe(data.get('current_price'))
    if price is None or price <= 0:
        raise ValueError("Missing, non-positive, or invalid current_price in CoinGecko market item")

    last_updated_str = data.get('last_updated')
    if not last_updated_str:
        raise ValueError("Missing last_updated timestamp in CoinGecko market item")

    try:
        # Handle ISO format like 2026-11-26T12:00:00.000Z
        dt = datetime.fromisoformat(str(last_updated_str).replace('Z', '+00:00'))
    except Exception as e:
        raise ValueError(f"Malformed last_updated timestamp '{last_updated_str}': {e}") from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    # Reject future timestamps beyond reasonable clock skew (e.g. 10 mins)
    now = datetime.now(timezone.utc)
    if dt > now + timedelta(minutes=10):
        raise ValueError(f"Future timestamp rejected: {dt} (current time: {now})")

    return {
        'id': str(data.get('id', '')).strip().lower(),
        'symbol': str(data.get('symbol', '')).upper().strip(),
        'name': str(data.get('name', '')).strip(),
        'price': price,
        'market_cap': parse_decimal_safe(data.get('market_cap')),
        'total_volume': parse_decimal_safe(data.get('total_volume')),
        'high_24h': parse_decimal_safe(data.get('high_24h')),
        'low_24h': parse_decimal_safe(data.get('low_24h')),
        'price_change_24h': parse_decimal_safe(data.get('price_change_24h')),
        'price_change_percentage_24h': parse_decimal_safe(data.get('price_change_percentage_24h')),
        'timestamp': dt,
    }


def serialize_chart_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalizes price points from /coins/{id}/market_chart."""
    prices = data.get('prices') or []
    volumes = {int(p[0]): parse_decimal_safe(p[1]) for p in (data.get('total_volumes') or []) if len(p) >= 2}
    market_caps = {int(p[0]): parse_decimal_safe(p[1]) for p in (data.get('market_caps') or []) if len(p) >= 2}

    results = []
    now = datetime.now(timezone.utc)
    for item in prices:
        if not isinstance(item, (list, tuple)) or len(item) < 2:
            continue
        ms_timestamp = int(item[0])
        val = parse_decimal_safe(item[1])
        if val is None or val <= 0:
            continue
        dt = datetime.fromtimestamp(ms_timestamp / 1000.0, tz=timezone.utc)
        if dt > now + timedelta(minutes=10):
            continue
        results.append({
            'timestamp': dt,
            'price': val,
            'volume': volumes.get(ms_timestamp),
            'market_cap': market_caps.get(ms_timestamp),
        })
    return results
