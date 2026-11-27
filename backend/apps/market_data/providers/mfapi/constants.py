"""MFAPI provider constants and catalogue anchors."""
from typing import Dict, List

DEFAULT_BASE_URL = 'https://api.mfapi.in'
DEFAULT_CURRENCY = 'INR'

# Researched anchor schemes for Indian mutual funds (November 2026)
CURATED_SCHEMES: List[Dict[str, str]] = [
    {
        'scheme_code': '122639',
        'scheme_name': 'Parag Parikh Flexi Cap Fund - Direct Plan - Growth',
        'fund_house': 'PPFAS Mutual Fund',
        'isin': 'INF879O01027',
        'nav': '94.2590',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '118834',
        'scheme_name': 'Mirae Asset Large Cap Fund - Direct Plan - Growth Option',
        'fund_house': 'Mirae Asset Mutual Fund',
        'isin': 'INF769K01EZ3',
        'nav': '124.5000',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '119598',
        'scheme_name': 'SBI Bluechip Fund - Direct Plan - Growth',
        'fund_house': 'SBI Mutual Fund',
        'isin': 'INF200K01HR2',
        'nav': '88.7500',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '101181',
        'scheme_name': 'HDFC Top 100 Fund - Growth',
        'fund_house': 'HDFC Mutual Fund',
        'isin': 'INF179K01133',
        'nav': '1120.3500',
        'plan_type': 'REGULAR',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '120503',
        'scheme_name': 'Tata Digital India Fund - Direct Plan - Growth',
        'fund_house': 'Tata Mutual Fund',
        'isin': 'INF277K01HM3',
        'nav': '48.9200',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '119551',
        'scheme_name': 'Tata Digital India Fund - Regular Plan - Growth',
        'fund_house': 'Tata Mutual Fund',
        'isin': 'INF277K01HL5',
        'nav': '44.1500',
        'plan_type': 'REGULAR',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '120716',
        'scheme_name': 'UTI Nifty 50 Index Fund - Direct Plan - Growth Option',
        'fund_house': 'UTI Mutual Fund',
        'isin': 'INF789F01X09',
        'nav': '178.4500',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '125497',
        'scheme_name': 'ICICI Prudential Technology Fund - Direct Plan - Growth',
        'fund_house': 'ICICI Prudential Mutual Fund',
        'isin': 'INF109K01Z48',
        'nav': '210.6000',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '120828',
        'scheme_name': 'Nippon India Small Cap Fund - Direct Plan - Growth Plan',
        'fund_house': 'Nippon India Mutual Fund',
        'isin': 'INF204K01E03',
        'nav': '182.3500',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
    {
        'scheme_code': '118989',
        'scheme_name': 'Axis Bluechip Fund - Direct Plan - Growth',
        'fund_house': 'Axis Mutual Fund',
        'isin': 'INF846K01DP8',
        'nav': '64.8200',
        'plan_type': 'DIRECT',
        'option_type': 'GROWTH',
    },
]
