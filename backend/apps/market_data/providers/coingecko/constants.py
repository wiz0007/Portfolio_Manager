"""CoinGecko cryptocurrency provider constants and catalogue definitions."""
from typing import Dict, List

DEFAULT_BASE_URL = 'https://api.coingecko.com/api/v3'
DEMO_API_HEADER = 'x-cg-demo-api-key'

SUPPORTED_COINS: List[Dict[str, str]] = [
    {'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'},
    {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum'},
    {'id': 'solana', 'symbol': 'SOL', 'name': 'Solana'},
    {'id': 'ripple', 'symbol': 'XRP', 'name': 'XRP'},
    {'id': 'binancecoin', 'symbol': 'BNB', 'name': 'BNB'},
    {'id': 'dogecoin', 'symbol': 'DOGE', 'name': 'Dogecoin'},
    {'id': 'cardano', 'symbol': 'ADA', 'name': 'Cardano'},
    {'id': 'tron', 'symbol': 'TRX', 'name': 'TRON'},
    {'id': 'avalanche-2', 'symbol': 'AVAX', 'name': 'Avalanche'},
    {'id': 'chainlink', 'symbol': 'LINK', 'name': 'Chainlink'},
]

SUPPORTED_COIN_IDS = {c['id'] for c in SUPPORTED_COINS}
COIN_ID_TO_SYMBOL = {c['id']: c['symbol'] for c in SUPPORTED_COINS}
SYMBOL_TO_COIN_ID = {c['symbol'].upper(): c['id'] for c in SUPPORTED_COINS}
