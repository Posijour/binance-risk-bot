import time

# Базовый cooldown в секундах по типам дивергенций
BASE_DIVERGENCE_COOLDOWN = {
    "LONG_TRAP": 1800,        # 30 мин
    "SHORT_TRAP": 1800,       # 30 мин
    "SHORT_SQUEEZE": 900,     # 15 мин
    "LONG_SQUEEZE": 900,      # 15 мин
    "FAKE_MOVE": 1200,        # 20 мин
    "FAKE_DUMP": 1200,        # 20 мин
    "CAPITULATION": 1800,     # 30 мин
}

# Классы тикеров для дивергенций
SYMBOL_CLASSES = {
    "BTCUSDT": "L1",
    "ETHUSDT": "L1",
    "SOLUSDT": "L2",
    "DOGEUSDT": "L2",
    "ADAUSDT": "L2",
    "LINKUSDT": "L2",
    "LTCUSDT": "L2",
    "BCHUSDT": "L2",
    "BNBUSDT": "L3",
    "TRXUSDT": "L3",
    "XRPUSDT": "L3",
    "XLMUSDT": "L3",
    "HBARUSDT": "L4",
    "XMRUSDT": "L4",
    "ZECUSDT": "L4",
    "HYPEUSDT": "L4",
}

# Параметры дивергенций по классам
CLASS_DIVERGENCE_PARAMS = {
    "L1": {
        "long_trap_pressure": 0.71,
        "short_trap_sell_pressure": 0.71,
        "short_squeeze_pressure": 0.76,
        "long_squeeze_sell_pressure": 0.76,
        "fake_move_pressure": 0.77,
        "fake_dump_sell_pressure": 0.77,
        "capitulation_pressure": 0.32,
        "price_trend_delta": 0.0008,
        "cooldown_multiplier": 1.35,
    },
    "L2": {
        "long_trap_pressure": 0.70,
        "short_trap_sell_pressure": 0.70,
        "short_squeeze_pressure": 0.75,
        "long_squeeze_sell_pressure": 0.75,
        "fake_move_pressure": 0.76,
        "fake_dump_sell_pressure": 0.76,
        "capitulation_pressure": 0.34,
        "price_trend_delta": 0.0011,
        "cooldown_multiplier": 1.20,
    },
    "L3": {
        "long_trap_pressure": 0.69,
        "short_trap_sell_pressure": 0.69,
        "short_squeeze_pressure": 0.74,
        "long_squeeze_sell_pressure": 0.74,
        "fake_move_pressure": 0.76,
        "fake_dump_sell_pressure": 0.76,
        "capitulation_pressure": 0.35,
        "price_trend_delta": 0.0014,
        "cooldown_multiplier": 1.15,
    },
    "L4": {
        "long_trap_pressure": 0.68,
        "short_trap_sell_pressure": 0.68,
        "short_squeeze_pressure": 0.73,
        "long_squeeze_sell_pressure": 0.73,
        "fake_move_pressure": 0.77,
        "fake_dump_sell_pressure": 0.77,
        "capitulation_pressure": 0.36,
        "price_trend_delta": 0.0018,
        "cooldown_multiplier": 1.10,
    },
}

SYMBOL_PARAM_OVERRIDES = {
    "ETHUSDT": {
        "long_trap_pressure": 0.70,
        "short_trap_sell_pressure": 0.70,
        "short_squeeze_pressure": 0.75,
        "long_squeeze_sell_pressure": 0.75,
        "fake_move_pressure": 0.76,
        "fake_dump_sell_pressure": 0.76,
        "capitulation_pressure": 0.33,
        "cooldown_multiplier": 1.25,
    },
    "DOGEUSDT": {
        "price_trend_delta": 0.0011,
    },
    "ADAUSDT": {
        "price_trend_delta": 0.0011,
    },
    "LINKUSDT": {
        "price_trend_delta": 0.0011,
    },
    "LTCUSDT": {
        "price_trend_delta": 0.0011,
    },
    "BCHUSDT": {
        "price_trend_delta": 0.0011,
    },
    "SOLUSDT": {
        "price_trend_delta": 0.0010,
    },
    "BNBUSDT": {
        "long_trap_pressure": 0.70,
        "short_trap_sell_pressure": 0.70,
        "fake_move_pressure": 0.77,
        "fake_dump_sell_pressure": 0.77,
        "price_trend_delta": 0.0014,
        "cooldown_multiplier": 1.20,
    },
    "TRXUSDT": {
        "long_trap_pressure": 0.71,
        "short_trap_sell_pressure": 0.71,
        "fake_move_pressure": 0.78,
        "fake_dump_sell_pressure": 0.78,
        "price_trend_delta": 0.0015,
        "cooldown_multiplier": 1.35,
    },
    "XRPUSDT": {
        "price_trend_delta": 0.0014,
        "cooldown_multiplier": 1.10,
    },
    "XLMUSDT": {
        "long_trap_pressure": 0.70,
        "short_trap_sell_pressure": 0.70,
        "fake_move_pressure": 0.78,
        "fake_dump_sell_pressure": 0.78,
        "price_trend_delta": 0.0015,
        "cooldown_multiplier": 1.25,
    },
    "HBARUSDT": {
        "long_trap_pressure": 0.69,
        "short_trap_sell_pressure": 0.69,
        "fake_move_pressure": 0.78,
        "fake_dump_sell_pressure": 0.78,
        "price_trend_delta": 0.0017,
        "cooldown_multiplier": 1.20,
    },
    "XMRUSDT": {
        "price_trend_delta": 0.0017,
    },
    "ZECUSDT": {
        "long_trap_pressure": 0.69,
        "short_trap_sell_pressure": 0.69,
        "fake_move_pressure": 0.78,
        "fake_dump_sell_pressure": 0.78,
        "price_trend_delta": 0.0018,
        "cooldown_multiplier": 1.20,
    },
    "HYPEUSDT": {
        "price_trend_delta": 0.0019,
        "cooldown_multiplier": 1.05,
    },
}

_last_seen = {}  # (symbol, type) -> ts


def get_divergence_params(symbol):
    symbol_class = SYMBOL_CLASSES.get(symbol, "L3")
    params = dict(CLASS_DIVERGENCE_PARAMS[symbol_class])
    params.update(SYMBOL_PARAM_OVERRIDES.get(symbol, {}))
    return params


def get_price_trend_delta(symbol):
    return get_divergence_params(symbol)["price_trend_delta"]


def _cooldown_ok(symbol, div_type):
    now = time.time()
    key = (symbol, div_type)
    params = get_divergence_params(symbol)
    base_ttl = BASE_DIVERGENCE_COOLDOWN.get(div_type, 900)
    ttl = int(base_ttl * params["cooldown_multiplier"])

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
    Production version:
    - без дублей
    - с приоритетом более сильных событий
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
    sell_pressure = 1.0 - pressure_ratio
    params = get_divergence_params(symbol)

    # ---------------- STATE-AWARE RULES ----------------

    if state == "CALM":
        return []

    # ---------------------------------------------------
    # PRIORITY 1: squeeze / liquidation events
    # ---------------------------------------------------

    # SHORT SQUEEZE
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and pressure > params["short_squeeze_pressure"]
        and oi_trend == "UP"
        and liquidations > 0
        and price_trend == "UP"
    ):
        if _cooldown_ok(symbol, "SHORT_SQUEEZE"):
            divergences.append(
                "SHORT SQUEEZE — агрессивные покупки при росте открытого интереса и движении цены вверх. "
                "Риск: шорты могут быть вынуждены закрываться ещё выше."
            )
        return divergences

    # LONG SQUEEZE
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and sell_pressure > params["long_squeeze_sell_pressure"]
        and oi_trend == "UP"
        and liquidations > 0
        and price_trend == "DOWN"
    ):
        if _cooldown_ok(symbol, "LONG_SQUEEZE"):
            divergences.append(
                "LONG SQUEEZE — агрессивные продажи при росте открытого интереса и движении цены вниз. "
                "Риск: лонги могут быть вынуждены закрываться ещё ниже."
            )
        return divergences

    # CAPITULATION
    if (
        state == "STRESS"
        and pressure < params["capitulation_pressure"]
        and oi_trend == "DOWN"
        and liquidations > 0
    ):
        if _cooldown_ok(symbol, "CAPITULATION"):
            divergences.append(
                "CAPITULATION — закрытие позиций под давлением ликвидаций. "
                "Риск: это выход, а не начало тренда."
            )
        return divergences

    # ---------------------------------------------------
    # PRIORITY 2: trap events
    # ---------------------------------------------------

    # LONG TRAP
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and pressure > params["long_trap_pressure"]
        and oi_trend == "UP"
        and price_trend == "DOWN"
    ):
        if _cooldown_ok(symbol, "LONG_TRAP"):
            divergences.append(
                "LONG TRAP — активные покупки, позиции растут, но цена уже давится вниз. "
                "Риск: покупатели могут остаться без продолжения движения."
            )
        return divergences

    # SHORT TRAP
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and sell_pressure > params["short_trap_sell_pressure"]
        and oi_trend == "UP"
        and price_trend == "UP"
    ):
        if _cooldown_ok(symbol, "SHORT_TRAP"):
            divergences.append(
                "SHORT TRAP — активные продажи, позиции растут, но цена уже идёт вверх. "
                "Риск: продавцы могут оказаться в ловушке против движения."
            )
        return divergences

    # ---------------------------------------------------
    # PRIORITY 3: fake continuation / exhaustion
    # ---------------------------------------------------

    # FAKE MOVE
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and pressure > params["fake_move_pressure"]
        and oi_trend == "DOWN"
        and price_trend == "UP"
    ):
        if _cooldown_ok(symbol, "FAKE_MOVE"):
            divergences.append(
                "FAKE MOVE — цена ещё идёт вверх, но позиции уже сокращаются. "
                "Риск: движение не подтверждено интересом."
            )
        return divergences

    # FAKE DUMP
    if (
        state in ("CROWD_IMBALANCE", "STRESS")
        and sell_pressure > params["fake_dump_sell_pressure"]
        and oi_trend == "DOWN"
        and price_trend == "DOWN"
    ):
        if _cooldown_ok(symbol, "FAKE_DUMP"):
            divergences.append(
                "FAKE DUMP — цена ещё идёт вниз, но позиции уже сокращаются. "
                "Риск: движение не подтверждено интересом и может быстро выдохнуться."
            )
        return divergences

    return divergences
