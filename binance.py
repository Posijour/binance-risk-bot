import requests
import time

BASE_URL = "https://fapi.binance.com"

class BinanceError(Exception):
    pass


def _get(path: str, params: dict):
    r = requests.get(BASE_URL + path, params=params, timeout=10)
    if r.status_code != 200:
        raise BinanceError(f"{path} error {r.status_code}: {r.text}")
    return r.json()


# ---------- FUNDING RATE ----------
def get_funding_rate(symbol: str) -> float:
    data = _get("/fapi/v1/fundingRate", {
        "symbol": symbol,
        "limit": 1
    })
    if not data:
        raise BinanceError("fundingRate returned empty")
    return float(data[0]["fundingRate"])


# ---------- LONG / SHORT RATIO ----------
def get_long_short_ratio(symbol: str) -> float:
    data = _get("/futures/data/globalLongShortAccountRatio", {
        "symbol": symbol,
        "period": "5m",
        "limit": 1
    })
    if not data:
        raise BinanceError("longShortRatio returned empty")
    return float(data[0]["longShortRatio"])


# ---------- OPEN INTEREST ----------
def get_open_interest(symbol: str) -> float:
    data = _get("/fapi/v1/openInterest", {
        "symbol": symbol
    })
    return float(data["openInterest"])


# ---------- LIQUIDATIONS (APPROX) ----------
def get_liquidations(symbol: str) -> float:
    end_time = int(time.time() * 1000)
    start_time = end_time - 5 * 60 * 1000

    trades = _get("/fapi/v1/aggTrades", {
        "symbol": symbol,
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1000
    })

    liquidation_volume = 0.0
    for t in trades:
        if t["m"]:  # taker sell → long liquidation
            liquidation_volume += float(t["q"])

    return liquidation_volume
