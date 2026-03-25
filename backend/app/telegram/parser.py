import re

SIGNAL_PATTERN = re.compile(
    r"(OPEN|CLOSE)\s+(BUY|SELL)\s+([A-Z]{6})\s+([\d.]+)\s+([\d.]+)LOT.*ORDER ID:(\d+)",
    re.IGNORECASE
)

def parse_signal(text: str):
    match = SIGNAL_PATTERN.search(text)
    if not match:
        return None

    action, direction, symbol, price, lot, signal_id = match.groups()

    return {
        "action": action.upper(),
        "direction": direction.upper(),
        "symbol": symbol.upper(),
        "price": float(price),
        "signal_lot": float(lot),
        "signal_order_id": signal_id
    }
