import asyncio
import json
import random
import time
import websockets
from collections import deque
from config import SYMBOLS, WINDOW_SECONDS
from logger import log_event

funding = {}
mark_price = {}
long_short_ratio = {}
liquidations = {}
liq_sides = {}
last_update = {}

trades_window = {s: deque() for s in SYMBOLS}
liq_window = {s: deque() for s in SYMBOLS}
oi_window = {s: deque() for s in SYMBOLS}
trade_totals = {s: {"long": 0.0, "short": 0.0} for s in SYMBOLS}
liq_totals = {s: {"long": 0.0, "short": 0.0} for s in SYMBOLS}


def touch(symbol):
    last_update[symbol] = int(time.time())


def cleanup_window(dq):
    now = time.time()
    while dq and now - dq[0][0] > WINDOW_SECONDS:
        dq.popleft()


def cleanup_trades(symbol):
    now = time.time()
    dq = trades_window[symbol]
    while dq and now - dq[0][0] > WINDOW_SECONDS:
        _, qty, side = dq.popleft()
        trade_totals[symbol][side] = max(0.0, trade_totals[symbol][side] - qty)


def cleanup_liq(symbol):
    now = time.time()
    dq = liq_window[symbol]
    while dq and now - dq[0][0] > WINDOW_SECONDS:
        _, qty, side = dq.popleft()
        liq_totals[symbol][side] = max(0.0, liq_totals[symbol][side] - qty)


async def binance_ws():
    streams = []
    for s in SYMBOLS:
        s = s.lower()
        streams += [
            f"{s}@markPrice@1s",
            f"{s}@openInterest@1s",
            f"{s}@aggTrade",
            f"{s}@forceOrder"
        ]

    url = f"wss://fstream.binance.com/stream?streams={'/'.join(streams)}"
    backoff = 1
    max_backoff = 60
    while True:
        try:
            async with websockets.connect(url, ping_interval=20) as ws:
                backoff = 1
                async for raw in ws:
                    msg = json.loads(raw)
                    data = msg.get("data", {})
                    stream = msg.get("stream", "")

                    symbol = data.get("s", "").upper()
                    if symbol not in SYMBOLS:
                        continue

                    now = time.time()

                    if "markPrice" in stream:
                        funding[symbol] = float(data["r"])
                        mark_price[symbol] = float(data["p"])
                        touch(symbol)

                    elif "openInterest" in stream:
                        oi = float(data["oi"])
                        oi_window[symbol].append((now, oi))
                        cleanup_window(oi_window[symbol])
                        touch(symbol)

                    elif "aggTrade" in stream:
                        qty = float(data["q"])
                        side = "short" if data["m"] else "long"

                        trades_window[symbol].append((now, qty, side))
                        trade_totals[symbol][side] += qty
                        cleanup_trades(symbol)

                        long_short_ratio[symbol] = {
                            "long": trade_totals[symbol]["long"],
                            "short": trade_totals[symbol]["short"]
                        }
                        touch(symbol)

                    elif "forceOrder" in stream:
                        qty = float(data["o"]["q"])
                        side = "long" if data["o"]["S"] == "SELL" else "short"

                        liq_window[symbol].append((now, qty, side))
                        liq_totals[symbol][side] += qty
                        cleanup_liq(symbol)

                        liq_sides[symbol] = {
                            "long": liq_totals[symbol]["long"],
                            "short": liq_totals[symbol]["short"],
                        }

                        liquidations[symbol] = (
                            liq_sides[symbol]["long"] + liq_sides[symbol]["short"]
                        )
                        touch(symbol)

        except Exception as exc:
            log_event("ws_error", {
                "error_type": type(exc).__name__,
                "error": str(exc),
                "backoff": backoff,
            })
            jitter = random.uniform(0.3, 1.3)
            await asyncio.sleep(backoff * jitter)
            backoff = min(backoff * 2, max_backoff)
