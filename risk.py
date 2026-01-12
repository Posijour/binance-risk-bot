def calculate_risk(
    funding,
    prev_funding,
    long_ratio,
    oi_change,
    oi,
    liquidations
):
    score = 0
    reasons = []
    direction = None

    if funding > 0.02:
        score += 2
        direction = "LONG"
        reasons.append("Funding экстремально положительный")

    if funding < -0.02:
        score += 2
        direction = "SHORT"
        reasons.append("Funding экстремально отрицательный")

    if long_ratio > 0.7:
        score += 2
        direction = "LONG"
        reasons.append("Перекос в лонги")

    if long_ratio < 0.3:
        score += 2
        direction = "SHORT"
        reasons.append("Перекос в шорты")

    if oi_change > 0:
        score += 1
        reasons.append("OI растёт")

    if oi_change < 0:
        score += 1
        reasons.append("OI падает")

    if liquidations > 30_000_000:
        score += 2
        reasons.append("Крупные ликвидации")

    funding_spike = (
        prev_funding is not None
        and abs(funding - prev_funding) > 0.003
    )

    oi_spike = oi > 0 and abs(oi_change) / oi > 0.03

    return score, direction, reasons, funding_spike, oi_spike
