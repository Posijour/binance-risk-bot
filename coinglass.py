import requests
from config import COINGLASS_API_KEY

BASE_URL = "https://open-api-v4.coinglass.com/api"

HEADERS = {
    "accept": "application/json",
    "CG-API-KEY": COINGLASS_API_KEY,
}

EXCHANGE = "BINANCE"


class CoinGlassError(Exception):
    pass


def _request(path: str, params: dict):
    r = requests.get(
        f"{BASE_URL}{path}",
        headers=HEADERS,
        params=params,
        timeout=15,
    )

    if r.status_code != 200:
        raise CoinGlassError(f"{path} error {r.status_code}: {r.text}")

    data = r.json().get("data")
    if not data:
        raise CoinGlassError(f"{path} api returned no data")

    return data


def get_funding_rate(symbol: str) -> float:
    data = _request(
        "/futures/funding-rate",
        {
            "symbol": symbol,
            "exchange": EXCHANGE,
        },
    )
    return float(data["fundingRate"])


def get_long_short_ratio(symbol: str) -> float:
    data = _request(
        "/futures/global-long-short-account-ratio",
        {
            "symbol": symbol,
        },
    )

    long = float(data["longAccount"])
    short = float(data["shortAccount"])

    if short == 0:
        raise CoinGlassError("shortAccount is zero")

    return long / short


def get_open_interest(symbol: str) -> float:
    data = _request(
        "/futures/open-interest",
        {
            "symbol": symbol,
            "exchange": EXCHANGE,
        },
    )
    return float(data["openInterest"])


def get_liquidations(symbol: str) -> float:
    data = _request(
        "/futures/liquidation",
        {
            "symbol": symbol,
            "exchange_list": EXCHANGE,
        },
    )

    return float(data.get("longLiquidation", 0)) + float(
        data.get("shortLiquidation", 0)
    )
