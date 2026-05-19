def volatility_adjusted_sizing(account_balance, risk_pct, atr, multiplier=2):
    """Calculates trade size based on Average True Range (ATR) to manage risk."""
    risk_amount = account_balance * (risk_pct / 100)
    stop_loss_distance = atr * multiplier
    if stop_loss_distance == 0: return 0
    position_size = risk_amount / stop_loss_distance
    return round(position_size, 4)