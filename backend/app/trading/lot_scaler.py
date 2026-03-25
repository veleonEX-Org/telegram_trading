def calculate_scaled_lot(
    signal_lot: float, 
    balance: float, 
    min_balance_guard: float = 200.0,
    base_balance: float = 1000.0,
    max_lot: float = 1.0
) -> float:
    if balance < min_balance_guard:
        return 0.0

    scaled = (balance / base_balance) * signal_lot
    scaled = min(scaled, max_lot)

    return round(scaled, 2)
