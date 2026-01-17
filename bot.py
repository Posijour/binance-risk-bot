import asyncio
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

from config import *
from risk import calculate_risk
from ws_binance import (
    funding,
    long_short_ratio,
    liquidations,
    last_update,
    oi_window,
    binance_ws
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

active_chats = set()
last_funding = {}
cache = {}
last_spikes = {"funding": {}, "oi": {}}

ws_task = None


# ---------------- KEEPALIVE ----------------

async def keepalive_loop():
    while True:
        await asyncio.sleep(30)


# ---------------- WS WATCHDOG ----------------

async def ws_watchdog():
    global ws_task

    while True:
        await asyncio.sleep(60)

        if not last_update:
            continue

        now = time.time()
        freshest = max(last_update.values())

        if now - freshest > 180:
            if ws_task:
                ws_task.cancel()

            ws_task = asyncio.create_task(binance_ws())


# ---------------- GLOBAL RISK LOOP ----------------

async def global_risk_loop():
    await asyncio.sleep(10)

    while True:
        for symbol in SYMBOLS:
            try:
                f = funding.get(symbol)
                if f is None:
                    continue

                ls = long_short_ratio.get(symbol, {"long": 0, "short": 0})
                total = ls["long"] + ls["short"]
                long_ratio = ls["long"] / total if total else 0.5

                prev_f = last_funding.get(symbol)
                last_funding[symbol] = f

                score, direction, reasons, funding_spike, oi_spike = calculate_risk(
                    f,
                    prev_f,
                    long_ratio,
                    oi_window[symbol],
                    liquidations.get(symbol, 0),
                    LIQ_THRESHOLDS[symbol]
                )

                cache[symbol] = (score, direction, reasons)
                now = time.time()

                for chat_id in active_chats:
                    if funding_spike and now - last_spikes["funding"].get(symbol, 0) > 900:
                        last_spikes["funding"][symbol] = now
                        await bot.send_message(chat_id, f"📈 {symbol} FUNDING SPIKE")

                    if oi_spike and now - last_spikes["oi"].get(symbol, 0) > 900:
                        last_spikes["oi"][symbol] = now
                        await bot.send_message(chat_id, f"💥 {symbol} OI SPIKE")

                    if score >= HARD_ALERT_LEVEL and direction:
                        prefix = "🚨 HARD RISK ALERT"
                    elif score >= EARLY_ALERT_LEVEL:
                        prefix = "⚠️ RISK BUILDUP"
                    else:
                        continue

                    text = (
                        f"{prefix} {symbol}\n\n"
                        f"Risk score: {score}\n"
                        f"Direction: {direction}\n\n"
                        + "\n".join(f"- {r}" for r in reasons)
                    )

                    await bot.send_message(chat_id, text)

            except Exception:
                pass

        await asyncio.sleep(INTERVAL_SECONDS)


# ---------------- COMMANDS ----------------

async def send_current_risk(chat_id):
    if not cache:
        await bot.send_message(chat_id, "⏳ Данные ещё собираются")
        return

    lines = []
    for symbol, (score, direction, _) in cache.items():
        ts = last_update.get(symbol)
        t = time.strftime("%H:%M:%S", time.localtime(ts)) if ts else "—"
        lines.append(f"{symbol}: {score} ({direction or 'NEUTRAL'}) ⏱ {t}")

    await bot.send_message(chat_id, "\n".join(lines))


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    active_chats.add(message.chat.id)

    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("📊 Текущий риск", callback_data="risk")
    )

    await message.reply(
        "Я слежу за Binance Futures.\n"
        "Пишу только когда реально опасно.\n\n"
        "Тишина = рынок обычный.",
        reply_markup=kb
    )


@dp.message_handler(commands=["risk"])
async def risk_cmd(message: types.Message):
    await send_current_risk(message.chat.id)


@dp.callback_query_handler(lambda c: c.data == "risk")
async def current_risk(call: types.CallbackQuery):
    await send_current_risk(call.message.chat.id)


# ---------------- HEALTH ----------------

class PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/health"):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


def start_http():
    HTTPServer(("0.0.0.0", 8080), PingHandler).serve_forever()


# ---------------- STARTUP ----------------

async def on_startup(dp):
    global ws_task
    await bot.delete_webhook(drop_pending_updates=True)

    ws_task = asyncio.create_task(binance_ws())
    asyncio.create_task(ws_watchdog())
    asyncio.create_task(global_risk_loop())
    asyncio.create_task(keepalive_loop())


if __name__ == "__main__":
    threading.Thread(target=start_http, daemon=True).start()
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

