def generate_macd_signal(fast_ema, slow_ema, signal_line):
    """Generates buy/sell signals based on MACD crossover."""
    macd_line = fast_ema - slow_ema
    if macd_line > signal_line:
        return 'BUY'
    elif macd_line < signal_line:
        return 'SELL'
    return 'HOLD' 