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
last_force_order_ts = {}

trades_window = {s: deque() for s in SYMBOLS}
liq_window = {s: deque() for s in SYMBOLS}
trade_totals = {s: {"long": 0.0, "short": 0.0} for s in SYMBOLS}
liq_totals = {s: {"long": 0.0, "short": 0.0} for s in SYMBOLS}

def touch(symbol):
    last_update[symbol] = int(time.time())


def cleanup_trades(symbol):
    now = time.time()
    dq = trades_window[symbol]
    removed = 0
    while dq and now - dq[0][0] > WINDOW_SECONDS:
        _, qty, side = dq.popleft()
        trade_totals[symbol][side] = max(0.0, trade_totals[symbol][side] - qty)
        removed += 1
    return removed


def cleanup_liq(symbol):
    now = time.time()
    dq = liq_window[symbol]
    removed = 0
    while dq and now - dq[0][0] > WINDOW_SECONDS:
        _, qty, side = dq.popleft()
        liq_totals[symbol][side] = max(0.0, liq_totals[symbol][side] - qty)
        removed += 1
    if removed:
        print(
            "liq_chain_cleanup: "
            f"symbol={symbol} "
            f"removed={removed} "
            f"window_seconds={WINDOW_SECONDS} "
            f"liq_long={round(liq_totals[symbol]['long'], 2)} "
            f"liq_short={round(liq_totals[symbol]['short'], 2)}",
            flush=True,
        )

async def binance_ws():
    streams = []

    for s in SYMBOLS:
        s = s.lower()

        streams += [
            f"{s}@markPrice@1s",
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
                        order = data.get("o", {})
                        qty = float(order.get("q", 0) or 0)
                        side = "long" if order.get("S") == "SELL" else "short"

                        liq_price = float(order.get("ap") or order.get("p") or 0)
                        if liq_price <= 0:
                            liq_price = mark_price.get(symbol, 0)

                        liq_notional = qty * liq_price

                        log_event(
                            "force_order_event",
                            {
                                "symbol": symbol,
                                "liq_notional": round(liq_notional, 2),
                                "side": side,
                                "qty": qty,
                                "price": liq_price,
                            }
                        )

                        liq_window[symbol].append((now, liq_notional, side))
                        liq_totals[symbol][side] += liq_notional
                        cleanup_liq(symbol)

                        liq_sides[symbol] = {
                            "long": liq_totals[symbol]["long"],
                            "short": liq_totals[symbol]["short"],
                        }

                        liquidations[symbol] = (
                            liq_sides[symbol]["long"] + liq_sides[symbol]["short"]
                        )
                        print(
                            "liq_chain_ws: "
                            f"symbol={symbol} "
                            f"side={side} "
                            f"event_notional={round(liq_notional, 2)} "
                            f"liq_long={round(liq_sides[symbol]['long'], 2)} "
                            f"liq_short={round(liq_sides[symbol]['short'], 2)} "
                            f"liq_total={round(liquidations[symbol], 2)}",
                            flush=True,
                        )
                        last_force_order_ts[symbol] = int(now)
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
