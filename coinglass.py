import requests
from config import COINGLASS_API_KEY

BASE_URL = "https://open-api.coinglass.com/api/pro/v1"

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


def get_funding_rate(symbol="BTCUSDT_PERP"):
    data = _get(
        "futures/funding-rate",
        {"symbolId": symbol}
    )
    return float(data["fundingRate"])


def get_long_short_ratio(symbol="BTCUSDT_PERP"):
    data = _get(
        "futures/long-short-ratio",
        {
            "symbolId": symbol,
            "interval": "5m"
        }
    )
    return float(data["longRatio"])


def get_open_interest(symbol="BTCUSDT_PERP"):
    data = _get(
        "futures/open-interest",
        {"symbolId": symbol}
    )
    return float(data["openInterest"])


def get_liquidations(symbol="BTCUSDT_PERP"):
    data = _get(
        "futures/liquidation",
        {
            "symbolId": symbol,
            "interval": "5m"
        }
    )
    return float(data["longLiquidation"]) + float(data["shortLiquidation"])
