import requests
from config import COINGLASS_API_KEY

BASE_URL = "https://open-api.coinglass.com/public/v3"

HEADERS = {
    "accept": "application/json",
    "coinglassSecret": COINGLASS_API_KEY
}


def _get(endpoint: str, params: dict):
    r = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=10
    )

    if r.status_code != 200:
        raise Exception(f"{endpoint} error {r.status_code}: {r.text}")

    return r.json()["data"]


def _base_symbol(symbol: str) -> str:
    # BTCUSDT -> BTC
    return symbol.replace("USDT", "")


# ---------- FUNDING RATE ----------
def get_funding_rate(symbol: str, exchange="Binance") -> float:
    data = _get(
        "funding-rate",
        {
            "symbol": symbol,
            "exchange": exchange
        }
    )
    return float(data[0]["fundingRate"])


# ---------- LONG / SHORT RATIO ----------
def get_long_short_ratio(symbol: str, exchange="Binance") -> float:
    data = _get(
        "global-long-short-account-ratio",
        {
            "symbol": symbol,
            "exchange": exchange,
            "interval": "5m"
        }
    )
    return float(data[-1]["longRatio"])


# ---------- OPEN INTEREST ----------
def get_open_interest(symbol: str) -> float:
    base = _base_symbol(symbol)

    data = _get(
        "open_interest",
        {
            "symbol": base,
            "exchange": "Binance"
        }
    )

    if not data:
        raise RuntimeError("empty open_interest data")

    return sum(float(x["openInterest"]) for x in data)


# ---------- LIQUIDATIONS ----------
def get_liquidations(symbol: str, exchange="Binance") -> float:
    data = _get(
        "liquidation",
        {
            "symbol": symbol,
            "exchange": exchange,
            "interval": "5m"
        }
    )
    last = data[-1]
    return float(last["longLiquidation"]) + float(last["shortLiquidation"])

