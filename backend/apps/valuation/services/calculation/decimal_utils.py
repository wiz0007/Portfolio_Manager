from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Union

CURRENCY_QUANT = Decimal('0.01')
UNIT_QUANT = Decimal('0.0001')
RATE_QUANT = Decimal('0.000001')


def to_decimal(val: Union[Decimal, float, int, str, None], default: str = '0.00') -> Decimal:
    """Safe conversion to Decimal."""
    if val is None or val == '':
        return Decimal(default)
    if isinstance(val, Decimal):
        return val
    return Decimal(str(val))


def quantize_currency(amount: Union[Decimal, float, int, str], places: int = 2) -> Decimal:
    """Quantize to specified decimal places (default 2 for currency) with ROUND_HALF_UP."""
    d = to_decimal(amount)
    quant = Decimal('10') ** -places
    return d.quantize(quant, rounding=ROUND_HALF_UP)


def quantize_units(units: Union[Decimal, float, int, str], places: int = 4) -> Decimal:
    """Quantize to specified decimal places (default 4 for units/shares)."""
    d = to_decimal(units)
    quant = Decimal('10') ** -places
    return d.quantize(quant, rounding=ROUND_HALF_UP)


def quantize_rate(rate: Union[Decimal, float, int, str], places: int = 6) -> Decimal:
    """Quantize interest/return rate to specified decimal places."""
    d = to_decimal(rate)
    quant = Decimal('10') ** -places
    return d.quantize(quant, rounding=ROUND_HALF_UP)


def calculate_ear(nominal_annual_rate_pct: Decimal, compounding_frequency: int) -> Decimal:
    """
    Calculates Effective Annual Rate (EAR) percentage:
    EAR = ((1 + r/n)^n - 1) * 100
    where r is decimal rate (nominal / 100) and n is compounding frequency.
    If frequency is 0 or simple interest, returns nominal rate.
    """
    nom = to_decimal(nominal_annual_rate_pct)
    n = int(compounding_frequency)
    if n <= 1:
        return nom

    r = nom / Decimal('100')
    periodic_rate = r / Decimal(str(n))
    base = Decimal('1') + periodic_rate
    # Compute power using base ** n
    compounded = base ** n
    ear = (compounded - Decimal('1')) * Decimal('100')
    return quantize_rate(ear, places=4)


def compound_lump_sum(
    principal: Union[Decimal, float, int, str],
    annual_rate_pct: Union[Decimal, float, int, str],
    compounding_frequency: int,
    years: Union[Decimal, float, int, str],
) -> Decimal:
    """
    Computes future value of a single lump sum:
    FV = P * (1 + r/n)^(n * t)
    where r = annual_rate_pct / 100, n = compounding_frequency, t = years.
    """
    p = to_decimal(principal)
    r = to_decimal(annual_rate_pct) / Decimal('100')
    if r == Decimal('0'):
        return quantize_currency(p)
    n = max(1, int(compounding_frequency))
    t = to_decimal(years)

    periods = Decimal(str(n)) * t
    if periods <= Decimal('0'):
        return quantize_currency(p)

    periodic_rate = r / Decimal(str(n))
    factor = (Decimal('1') + periodic_rate) ** periods
    return quantize_currency(p * factor)


def compound_annuity_fv(
    payment: Union[Decimal, float, int, str],
    annual_rate_pct: Union[Decimal, float, int, str],
    compounding_frequency: int,
    years: Union[Decimal, float, int, str],
    contribution_frequency: Optional[int] = None,
    timing: str = 'END_OF_PERIOD',
) -> Decimal:
    """
    Computes Future Value of regular periodic payments (annuity).
    Supports distinct contribution frequency (k) and compounding frequency (m):
      effective rate i = (1 + r/m)^(m/k) - 1
    timing: 'END_OF_PERIOD' (ordinary annuity) or 'BEGINNING_OF_PERIOD' (annuity due).
    """
    pmt = to_decimal(payment)
    if pmt <= Decimal('0'):
        return Decimal('0.00')

    r = to_decimal(annual_rate_pct) / Decimal('100')
    m = max(1, int(compounding_frequency))
    k = max(1, int(contribution_frequency or compounding_frequency))
    t = to_decimal(years)

    periods_dec = Decimal(str(k)) * t
    periods = int(periods_dec)

    if periods <= 0:
        return Decimal('0.00')

    if r == Decimal('0'):
        # Zero interest: sum of payments
        return quantize_currency(pmt * Decimal(str(periods)))

    # Calculate effective interest rate per contribution period:
    # i = (1 + r/m)^(m/k) - 1
    if m == k:
        i = r / Decimal(str(k))
    else:
        m_dec = Decimal(str(m))
        k_dec = Decimal(str(k))
        periodic_compounding = Decimal('1') + (r / m_dec)
        power = m_dec / k_dec
        i = (periodic_compounding ** power) - Decimal('1')

    if i == Decimal('0'):
        return quantize_currency(pmt * Decimal(str(periods)))

    # Ordinary annuity formula: PMT * ((1 + i)^N - 1) / i
    fv_ordinary = pmt * (((Decimal('1') + i) ** periods - Decimal('1')) / i)

    if timing.upper() in ('BEGINNING_OF_PERIOD', 'BEGINNING', 'DUE'):
        fv_total = fv_ordinary * (Decimal('1') + i)
    else:
        fv_total = fv_ordinary

    return quantize_currency(fv_total)
