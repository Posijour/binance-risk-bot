from config import FUNDING_SPIKE_THRESHOLD, OI_SPIKE_PERCENT

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

    # ----- FUNDING SPIKE -----
    if prev_funding is not None:
        funding_delta = funding - prev_funding
        if abs(funding_delta) >= FUNDING_SPIKE_THRESHOLD:
            score += 2
            reasons.append("Резкий funding spike")
            direction = "LONG" if funding > 0 else "SHORT"

    # ----- LONG RISK -----
    if funding > 0.02:
        score += 2
        direction = "LONG"
        reasons.append("Funding экстремально положительный")

    if long_ratio > 0.7:
        score += 2
        direction = "LONG"
        reasons.append("Сильный перекос в лонги")

    # ----- SHORT RISK -----
    if funding < -0.02:
        score += 2
        direction = "SHORT"
        reasons.append("Funding экстремально отрицательный")

    if long_ratio < 0.3:
        score += 2
        direction = "SHORT"
        reasons.append("Сильный перекос в шорты")

    # ----- OI SPIKE -----
    if oi > 0:
        oi_pct = oi_change / oi
        if abs(oi_pct) >= OI_SPIKE_PERCENT:
            score += 2
            reasons.append("Резкий рост Open Interest")

    # ----- LIQUIDATIONS -----
    if liquidations > 50_000_000:
        score += 2
        reasons.append("Аномальные ликвидации")

    return score, direction, reasons
