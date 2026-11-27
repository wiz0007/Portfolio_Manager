"""MFAPI serialization and validation."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

IST = ZoneInfo('Asia/Kolkata')


def parse_decimal_safe(val: Any) -> Optional[Decimal]:
    if val is None:
        return None
    try:
        return Decimal(str(val).strip())
    except (InvalidOperation, ValueError, TypeError):
        return None


def parse_mf_date_to_utc(date_str: str) -> datetime:
    """
    Parses DD-MM-YYYY date string from MFAPI and returns UTC datetime corresponding to EOD (21:00 IST).
    """
    clean = str(date_str).strip()
    d = datetime.strptime(clean, '%d-%m-%Y').date()
    # 21:00 IST represents Indian Mutual Fund NAV publication time
    dt_ist = datetime(d.year, d.month, d.day, 21, 0, tzinfo=IST)
    return dt_ist.astimezone(timezone.utc)


def classify_scheme(scheme_name: str) -> Dict[str, str]:
    """
    Determines plan type (DIRECT vs REGULAR) and option type (GROWTH vs IDCW).
    """
    name_upper = scheme_name.upper()
    plan_type = 'DIRECT' if 'DIRECT' in name_upper else 'REGULAR'

    if 'GROWTH' in name_upper:
        option_type = 'GROWTH'
    elif 'IDCW' in name_upper or 'DIVIDEND' in name_upper or 'INCOME' in name_upper:
        option_type = 'IDCW'
    else:
        option_type = 'GROWTH'

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
