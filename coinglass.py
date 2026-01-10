import requests
import time
from config import COINGLASS_API_KEY

BASE_URL = "https://open-api.coinglass.com/api/pro/v1"

HEADERS = {
    "accept": "application/json",
    "CG-API-KEY": COINGLASS_API_KEY
}

TIMEOUT = 10
RETRIES = 3
RETRY_SLEEP = 1.5

EXCHANGE = "Binance"


class CoinglassError(Exception):
    pass


def _request(endpoint: str, params: dict):
    url = f"{BASE_URL}/{endpoint}"

    last_error = None

    for attempt in range(1, RETRIES + 1):
        try:
            r = requests.get(
                url,
                headers=HEADERS,
                params=params,
                timeout=TIMEOUT
            )

            if r.status_code != 200:
                raise CoinglassError(
                    f"{endpoint} error {r.status_code}: {r.text}"
                )

            data = r.json()

            # Coinglass иногда возвращает success=false с 200
            if isinstance(data, dict) and data.get("success") is False:
                raise CoinglassError(
                    f"{endpoint} logical error: {data}"
                )

            return data.get("data")

        except Exception as e:
            last_error = e
            if attempt < RETRIES:
                time.sleep(RETRY_SLEEP)
            else:
                raise last_error


# -----------------------------
# FUNDING RATE
# -----------------------------
def get_funding_rate(symbol: str) -> float:
    data = _request(
        "futures/funding-rate",
        {
            "symbol": symbol,
            "exchange": EXCHANGE
        }
    )

    # PRO API возвращает объект, не список
    return float(data["fundingRate"])


# -----------------------------
# LONG / SHORT RATIO
# -----------------------------
def get_long_short_ratio(symbol: str) -> float:
    data = _request(
        "futures/long-short-ratio",
        {
            "symbol": symbol,
            "exchange": EXCHANGE,
            "interval": "5m"
        }
    )

    return float(data["longRatio"])


# -----------------------------
# OPEN INTEREST
# -----------------------------
def get_open_interest(symbol: str) -> float:
    data = _request(
        "futures/open-interest",
        {
            "symbol": symbol,
            "exchange": EXCHANGE
        }
    )

    return float(data["openInterest"])


# -----------------------------
# LIQUIDATIONS
# -----------------------------
def get_liquidations(symbol: str) -> float:
    data = _request(
        "futures/liquidation",
        {
            "symbol": symbol,
            "exchange": EXCHANGE,
            "interval": "5m"
        }
    )

    long_liq = float(data.get("longLiquidation", 0))
    short_liq = float(data.get("shortLiquidation", 0))

    return long_liq + short_liq



