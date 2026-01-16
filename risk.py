def calculate_risk(
    funding,
    prev_funding,
    long_ratio,
    oi_window,
    liquidations,
    liq_threshold
):
    score = 0
    reasons = []
    direction_votes = {"LONG": 0, "SHORT": 0}

    # FUNDING
    if funding > 0.02:
        score += 2
        direction_votes["LONG"] += 1
        reasons.append("Funding экстремально положительный")

    if funding < -0.02:
        score += 2
        direction_votes["SHORT"] += 1
        reasons.append("Funding экстремально отрицательный")

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
        change_pct = abs(oi_end - oi_start) / oi_start if oi_start else 0

        if oi_end > oi_start:
            score += 1
            reasons.append("OI растёт")
        elif oi_end < oi_start:
            score += 1
            reasons.append("OI падает")

        if change_pct > 0.03:
            oi_spike = True

    # LIQUIDATIONS
    if liquidations > liq_threshold:
        score += 2
        reasons.append("Крупные ликвидации")

    funding_spike = (
        prev_funding is not None
        and abs(funding - prev_funding) > 0.003
    )

    direction = None
    if direction_votes["LONG"] != direction_votes["SHORT"]:
        direction = max(direction_votes, key=direction_votes.get)

    return score, direction, reasons, funding_spike, oi_spike

