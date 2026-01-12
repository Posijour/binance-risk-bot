import requests
import time

BASE = "https://fapi.binance.com"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "risk-bot"})

LAST_CALL = {}
MIN_DELAY = 2  # секунд между одинаковыми эндпоинтами


class BinanceError(Exception):
    pass


def _throttle(key: str):
    now = time.time()
    last = LAST_CALL.get(key, 0)
    if now - last < MIN_DELAY:
        time.sleep(MIN_DELAY - (now - last))
    LAST_CALL[key] = time.time()


def _get(path, params=None):
    _throttle(path)
    r = SESSION.get(BASE + path, params=params, timeout=10)
    if r.status_code != 200:
        raise BinanceError(f"{path} {r.status_code}")
    return r.json()


def get_funding_rate(symbol: str) -> float:
    data = _get("/fapi/v1/fundingRate", {
        "symbol": symbol,
        "limit": 1
    })
    return float(data[0]["fundingRate"])


def get_long_short_ratio(symbol: str) -> float:
    data = _get(
        "/futures/data/globalLongShortAccountRatio",
        {
            "symbol": symbol,
            "period": "5m",
            "limit": 1
        }
    )
    return float(data[0]["longAccount"])


def get_open_interest(symbol: str) -> float:
    data = _get("/fapi/v1/openInterest", {"symbol": symbol})
    return float(data["openInterest"])


def get_liquidations(symbol: str) -> float:
    data = _get(
        "/fapi/v1/forceOrders",
        {"symbol": symbol, "limit": 50}
    )
    total = 0.0
    for row in data:
        total += float(row["price"]) * float(row["origQty"])
    return total

