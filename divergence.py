import time

# cooldown в секундах по типам дивергенций
DIVERGENCE_COOLDOWN = {
    "LONG_TRAP": 1800,        # 30 мин
    "SHORT_SQUEEZE": 900,     # 15 мин
    "FAKE_MOVE": 1200,        # 20 мин
    "CAPITULATION": 1800,
}

_last_seen = {}  # (symbol, type) -> ts


def _cooldown_ok(symbol, div_type):
    now = time.time()
    key = (symbol, div_type)
    ttl = DIVERGENCE_COOLDOWN.get(div_type, 900)

    last = _last_seen.get(key)
    if last and now - last < ttl:
        return False

    _last_seen[key] = now
    return True


def detect_divergence(
    symbol,
    state,
    pressure_ratio,
    oi_window,
    price_trend,
    liquidations,
):
    """
    WS-only divergence detection.
    Возвращает список human-readable строк.
    """

    divergences = []

    # --- базовые вычисления ---
    oi_trend = None
    if len(oi_window) >= 2:
        start = oi_window[0][1]
        end = oi_window[-1][1]
        if end > start:
            oi_trend = "UP"
        elif end < start:
            oi_trend = "DOWN"

    pressure = pressure_ratio

    # ---------------- STATE-AWARE RULES ----------------

    # ❌ В CALM — ничего не показываем
    if state == "CALM":
        return []

    # 🔻 LONG TRAP
    if (
        state in ("LATENT_STRESS", "NEUTRAL", "CROWD_IMBALANCE", "STRESS")
        and pressure > 0.65
        and oi_trend == "UP"
        and price_trend in ("FLAT", "DOWN")
    ):
        if _cooldown_ok(symbol, "LONG_TRAP"):
            divergences.append(
                "LONG TRAP — активные покупки, позиции растут, но цена не идёт. "
                "Риск: покупатели могут остаться без продолжения движения."
            )

    # 🔺 SHORT SQUEEZE
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and pressure > 0.7
        and oi_trend == "UP"
        and liquidations > 0
    ):
        if _cooldown_ok(symbol, "SHORT_SQUEEZE"):
            divergences.append(
                "SHORT SQUEEZE — агрессивные покупки при росте открытого интереса. "
                "Риск: шорты могут быть вынуждены закрываться выше."
            )

    # 🔻 FAKE MOVE
    if (
        state in ("LATENT_STRESS", "NEUTRAL", "CROWD_IMBALANCE", "STRESS")
        and pressure > 0.7
        and oi_trend == "DOWN"
        and price_trend in ("UP", "FLAT")
    ):
        if _cooldown_ok(symbol, "FAKE_MOVE"):
            divergences.append(
                "FAKE MOVE — сделки есть, но позиции сокращаются. "
                "Риск: движение не подтверждено интересом."
            )

    # 🧨 CAPITULATION
    if (
        state == "STRESS"
        and pressure < 0.35
        and oi_trend == "DOWN"
        and liquidations > 0
    ):
        if _cooldown_ok(symbol, "CAPITULATION"):
            divergences.append(
                "CAPITULATION — закрытие позиций под давлением ликвидаций. "
                "Риск: это выход, а не начало тренда."
            )

    return divergences
