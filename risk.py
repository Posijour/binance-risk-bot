def calculate_risk(
    funding,
    prev_funding,
    long_ratio,
    oi_window,
    liquidations,
    liq_threshold,
    price,
    liq_sides
):
    score = 0
    reasons = []
    direction_votes = {"LONG": 0, "SHORT": 0}

    # FUNDING
    if funding is not None:
        if funding > 0.02:
            score += 2
            direction_votes["LONG"] += 1
            reasons.append("Funding экстремально положительный")

        if funding < -0.02:
            score += 2
            direction_votes["SHORT"] += 1
            reasons.append("Funding экстремально отрицательный")

    funding_spike = (
        funding is not None
        and prev_funding is not None
        and abs(funding - prev_funding) > 0.003
    )

    # LONG / SHORT
    if long_ratio > 0.85:
        score += 3
        direction_votes["LONG"] += 2
        reasons.append("Экстремальный перекос в лонги")
    elif long_ratio > 0.7:
        score += 2
        direction_votes["LONG"] += 1
        reasons.append("Перекос в лонги")

    if long_ratio < 0.15:
        score += 3
        direction_votes["SHORT"] += 2
        reasons.append("Экстремальный перекос в шорты")
    elif long_ratio < 0.3:
        score += 2
        direction_votes["SHORT"] += 1
        reasons.append("Перекос в шорты")

    # OI TREND + SPIKE
    oi_spike = False
    if len(oi_window) >= 2:
        oi_start = oi_window[0][1]
        oi_end = oi_window[-1][1]

        if oi_end > oi_start:
            score += 1
            reasons.append("OI растёт")
        elif oi_end < oi_start:
            score += 1
            reasons.append("OI падает")

        if oi_start > 0:
            change_pct = abs(oi_end - oi_start) / oi_start
            if change_pct > 0.03:
                oi_spike = True
                if price is not None:
                    reasons.append("OI spike при движении цены")

    # LIQUIDATIONS
    if liquidations > liq_threshold:
        score += 2
        reasons.append("Крупные ликвидации")

        if liq_sides:
            if liq_sides.get("long", 0) > liq_sides.get("short", 0):
                reasons.append("Преобладают ликвидации лонгов")
            else:
                reasons.append("Преобладают ликвидации шортов")

    direction = None
    if direction_votes["LONG"] != direction_votes["SHORT"]:
        direction = max(direction_votes, key=direction_votes.get)

    return score, direction, reasons, funding_spike, oi_spike

