
import requests
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# Fetch 90 days of BTC daily candles from KuCoin
end = int(time.time())
start = end - (90 * 86400)
url = f"https://api.kucoin.com/api/v1/market/candles?type=1day&symbol=BTC-USDT&startAt={start}&endAt={end}"

resp = requests.get(url)
candles = resp.json()['data']

# KuCoin: [timestamp, open, close, high, low, volume, turnover]
df = pd.DataFrame(candles, columns=['timestamp','open','close','high','low','volume','turnover'])
df = df.astype({'timestamp': int, 'open': float, 'close': float, 'high': float, 'low': float, 'volume': float})
df['date'] = pd.to_datetime(df['timestamp'], unit='s')
df = df.sort_values('date').reset_index(drop=True)

closes = df['close'].values
highs = df['high'].values
lows = df['low'].values
volumes = df['volume'].values

# --- TECHNICAL INDICATORS (pure numpy/pandas, no sklearn) ---
def sma(arr, n):
    return pd.Series(arr).rolling(n).mean().values

def ema(arr, n):
    return pd.Series(arr).ewm(span=n, adjust=False).mean().values

sma7 = sma(closes, 7)
sma20 = sma(closes, 20)
sma50 = sma(closes, 50)
ema12 = ema(closes, 12)
ema26 = ema(closes, 26)
macd_line = ema12 - ema26
macd_signal = ema(macd_line, 9)

# RSI
delta = np.diff(closes, prepend=closes[0])
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg_gain = pd.Series(gain).rolling(14).mean().values
avg_loss = pd.Series(loss).rolling(14).mean().values
rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
rsi = 100 - (100 / (1 + rs))

# Bollinger Bands
bb_mid = sma20
bb_std = pd.Series(closes).rolling(20).std().values
bb_upper = bb_mid + 2 * bb_std
bb_lower = bb_mid - 2 * bb_std
bb_pos = (closes - bb_lower) / (bb_upper - bb_lower + 1e-9)

# Linear Regression Forecast (manual, no sklearn)
# Use last 30 data points to project next 7 days
n = len(closes)
x = np.arange(n)
x_recent = x[-30:]
y_recent = closes[-30:]

# Polyfit degree 1 (linear)
coeffs = np.polyfit(x_recent, y_recent, 1)
slope = coeffs[0]
intercept = coeffs[1]

# Also try quadratic for curve
coeffs2 = np.polyfit(x_recent, y_recent, 2)

# Forecast
forecast_linear = []
forecast_quad = []
for i in range(1, 8):
    xi = n + i
    forecast_linear.append(slope * xi + intercept)
    forecast_quad.append(coeffs2[0]*xi**2 + coeffs2[1]*xi + coeffs2[2])

# Blend linear + quadratic
forecast = [(l*0.5 + q*0.5) for l, q in zip(forecast_linear, forecast_quad)]

# Recent trend
pct_changes = pd.Series(closes).pct_change().values
trend_7d = np.nanmean(pct_changes[-7:])
trend_30d = np.nanmean(pct_changes[-30:])

# Current values
current_price = closes[-1]
rsi_now = rsi[-1]
macd_now = macd_line[-1]
macd_sig_now = macd_signal[-1]
bb_pos_now = bb_pos[-1]
sma20_now = sma20[-1]
sma50_now = sma50[-1]

recent_high = max(highs[-20:])
recent_low = min(lows[-20:])
support = recent_low
resistance = recent_high

# --- SIGNAL SCORING ---
score = 0
signals = []

if rsi_now < 40:
    score += 2
    signals.append(f"RSI {rsi_now:.1f} — Oversold > BUY signal")
elif rsi_now > 70:
    score -= 2
    signals.append(f"RSI {rsi_now:.1f} — Overbought > SELL signal")
else:
    score += 1
    signals.append(f"RSI {rsi_now:.1f} — Neutral zone")

if macd_now > macd_sig_now:
    score += 2
    signals.append("MACD above signal line — Bullish momentum")
else:
    score -= 1
    signals.append("MACD below signal line — Bearish pressure")

if current_price > sma20_now:
    score += 1
    signals.append(f"Price (${current_price:,.0f}) above SMA20 (${sma20_now:,.0f}) — Uptrend")
else:
    score -= 1
    signals.append(f"Price (${current_price:,.0f}) below SMA20 (${sma20_now:,.0f}) — Downtrend")

if current_price > sma50_now:
    score += 1
    signals.append(f"Price above SMA50 (${sma50_now:,.0f}) — Strong bull structure")
else:
    score -= 1
    signals.append(f"Price below SMA50 (${sma50_now:,.0f}) — Weak structure")

if bb_pos_now < 0.3:
    score += 1
    signals.append(f"Near Bollinger lower band ({bb_pos_now:.0%}) — Bounce potential")
elif bb_pos_now > 0.7:
    score -= 1
    signals.append(f"Near Bollinger upper band ({bb_pos_now:.0%}) — Pullback risk")
else:
    signals.append(f"Bollinger mid range ({bb_pos_now:.0%}) — No extreme")

if trend_7d > 0.005:
    score += 1
    signals.append(f"7-day trend: +{trend_7d*100:.2f}%/day avg — Bullish momentum")
elif trend_7d > 0:
    signals.append(f"7-day trend: +{trend_7d*100:.2f}%/day avg — Slight positive")
else:
    score -= 1
    signals.append(f"7-day trend: {trend_7d*100:.2f}%/day avg — Negative drift")

if slope > 0:
    score += 1
    signals.append(f"Regression slope positive (${slope:+.0f}/day) — Upward bias")
else:
    score -= 1
    signals.append(f"Regression slope negative (${slope:+.0f}/day) — Downward bias")

# Verdict
if score >= 5:
    verdict = "STRONG BUY"
    color = "VERY BULLISH"
elif score >= 3:
    verdict = "BUY"
    color = "BULLISH"
elif score >= 1:
    verdict = "CAUTIOUSLY BULLISH"
    color = "SLIGHT BULLISH"
elif score == 0:
    verdict = "NEUTRAL"
    color = "NEUTRAL"
elif score >= -2:
    verdict = "CAUTIOUS"
    color = "SLIGHT BEARISH"
else:
    verdict = "SELL / AVOID"
    color = "BEARISH"

# Accuracy estimate from regression residuals on last 7 days
x_test = x[-7:]
y_test = closes[-7:]
y_pred_test = coeffs[0]*x_test + coeffs[1]
mae = np.mean(np.abs(y_pred_test - y_test))
mape = np.mean(np.abs((y_pred_test - y_test) / y_test)) * 100

print("=" * 45)
print("   BTC PRICE PREDICTION ENGINE v1.0")
print("=" * 45)
print(f"Current BTC Price:  ${current_price:,.2f}")
print(f"Model Error (MAE):  ${mae:,.0f}")
print(f"Accuracy Est.:      {100-mape:.1f}%")
print()
print("TECHNICAL SIGNALS:")
for s in signals:
    print(f"  > {s}")
print()
print(f"SIGNAL SCORE: {score}/8")
print(f"VERDICT: {verdict} ({color})")
print()
print("KEY PRICE LEVELS:")
print(f"  Strong Support:    ${support:,.0f}")
print(f"  Strong Resistance: ${resistance:,.0f}")
print(f"  SMA20:             ${sma20_now:,.0f}")
print(f"  SMA50:             ${sma50_now:,.0f}")
print(f"  BB Upper:          ${bb_upper[-1]:,.0f}")
print(f"  BB Lower:          ${bb_lower[-1]:,.0f}")
print()
print("7-DAY BTC FORECAST:")
today = datetime.utcnow()
for i, price in enumerate(forecast):
    day = (today + timedelta(days=i+1)).strftime("%a %b %d")
    change = ((price - current_price) / current_price) * 100
    direction = "UP" if price > current_price else "DOWN"
    print(f"  {day}: ${price:,.0f}  [{direction} {change:+.1f}%]")

print()
max_forecast = max(forecast)
min_forecast = min(forecast)
if max_forecast >= 83000:
    sol_outlook = "HIGH — BTC heading toward $83K+ supports SOL TP"
elif max_forecast >= 81000:
    sol_outlook = "MODERATE — BTC range-bound, SOL needs its own catalyst"
else:
    sol_outlook = "LOW — BTC weakness could pressure SOL below SL"

print(f"SOL TP ($100.87) Probability:")
print(f"  {sol_outlook}")
print(f"  Forecast BTC range: ${min_forecast:,.0f} - ${max_forecast:,.0f}")
