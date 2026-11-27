"""MFAPI serialization and validation."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')


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


def parse_mf_date_to_utc(date_str: str) -> datetime:
    """
    Parses DD-MM-YYYY date string from MFAPI and returns UTC datetime corresponding to NAV effective date.
    Uses midnight UTC convention to represent the calendar valuation date without fabricating an artificial intraday publication timestamp.
    """
    clean = str(date_str).strip()
    d = datetime.strptime(clean, '%d-%m-%Y').date()
    # Reject future dates beyond today in IST
    today_ist = datetime.now(IST).date()
    if d > today_ist:
        raise ValueError(f"Future NAV date rejected: {d} (today: {today_ist})")
    return datetime(d.year, d.month, d.day, 0, 0, tzinfo=timezone.utc)


def classify_scheme(scheme_name: str) -> Dict[str, str]:
    """
    Evidence-based determination of plan type (DIRECT, REGULAR, UNKNOWN)
    and option type (GROWTH, IDCW, UNKNOWN).
    Never silently defaults missing indicators to Regular or Growth.
    """
    name_upper = scheme_name.upper()

    # Plan classification
    if 'DIRECT' in name_upper:
        plan_type = 'DIRECT'
    elif 'REGULAR' in name_upper:
        plan_type = 'REGULAR'
    else:
        plan_type = 'UNKNOWN'

    # Option classification
    if 'GROWTH' in name_upper:
        option_type = 'GROWTH'
    elif any(k in name_upper for k in ('IDCW', 'DIVIDEND', 'INCOME')):
        option_type = 'IDCW'
    elif 'BONUS' in name_upper:
        option_type = 'BONUS'
    else:
        option_type = 'UNKNOWN'

    return {
        'plan_type': plan_type,
        'option_type': option_type,
    }


def serialize_scheme_meta(meta: Dict[str, Any]) -> Dict[str, Any]:
    scheme_code = str(meta.get('scheme_code', '')).strip()
    scheme_name = str(meta.get('scheme_name', '')).strip()
    classification = classify_scheme(scheme_name)

    return {
        'scheme_code': scheme_code,
        'scheme_name': scheme_name,
        'fund_house': str(meta.get('fund_house', '')).strip(),
        'scheme_type': str(meta.get('scheme_type', '')).strip(),
        'scheme_category': str(meta.get('scheme_category', '')).strip(),
        'isin_growth': meta.get('isin_growth'),
        'isin_div_reinvestment': meta.get('isin_div_reinvestment'),
        'plan_type': classification['plan_type'],
        'option_type': classification['option_type'],
    }


def serialize_nav_data(data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Converts raw MFAPI data array into normalized, sorted entries."""
    parsed = []
    for item in data_list:
        date_str = item.get('date')
        nav_val = parse_decimal_safe(item.get('nav'))
        if not date_str or nav_val is None or nav_val <= 0:
            continue
        try:
            dt = parse_mf_date_to_utc(date_str)
            parsed.append({
                'date': date_str,
                'timestamp': dt,
                'nav': nav_val,
            })
        except Exception:
            continue

    # Sort ascending by timestamp for chronological ordering
    parsed.sort(key=lambda x: x['timestamp'])
    return parsed
