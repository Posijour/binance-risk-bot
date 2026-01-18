def detect_divergence(
    oi_window,
    funding,
    long_ratio,
    price_window,
    liq_sides
):
    divergences = []

    if len(oi_window) < 2 or len(price_window) < 2:
        return divergences

    oi_up = oi_window[-1][1] > oi_window[0][1]
    price_up = price_window[-1][1] > price_window[0][1]
    price_down = price_window[-1][1] < price_window[0][1]

    if oi_up and funding and funding > 0 and price_down and long_ratio > 0.7:
        divergences.append("Bearish divergence: OI↑ Funding↑ Price↓")

    if oi_up and funding and funding < 0 and price_up and long_ratio < 0.3:
        divergences.append("Bullish divergence: OI↑ Funding↓ Price↑")

    if liq_sides:
        dominant = (
            "long" if liq_sides.get("long", 0) > liq_sides.get("short", 0)
            else "short"
        )
        divergences.append(f"Liquidation imbalance ({dominant})")

    return divergences
