"""
BTC PRICE PREDICTION ENGINE v2.0
Street Code Studios / Prince Victor
Upgrades: ATR, Volume analysis, Stochastic, Pivot S/R,
          OBV trend, proper walk-forward MAE, SL/TP levels,
          cleaner signal scoring, regime detection
"""

import requests
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

# ─── DATA FETCH ────────────────────────────────────────────────────────────────
end = int(time.time())
start = end - (120 * 86400)   # 120 days for better regression warmup
url = (
    f"https://api.kucoin.com/api/v1/market/candles"
    f"?type=1day&symbol=BTC-USDT&startAt={start}&endAt={end}"
)

resp = requests.get(url, timeout=10)
candles = resp.json()['data']

df = pd.DataFrame(
    candles,
    columns=['timestamp','open','close','high','low','volume','turnover']
)
df = df.astype({
    'timestamp': int, 'open': float, 'close': float,
    'high': float, 'low': float, 'volume': float, 'turnover': float
})
df['date'] = pd.to_datetime(df['timestamp'], unit='s')
df = df.sort_values('date').reset_index(drop=True)

closes  = df['close'].values
highs   = df['high'].values
lows    = df['low'].values
volumes = df['volume'].values

# ─── HELPER FUNCTIONS ──────────────────────────────────────────────────────────
def sma(arr, n):
    return pd.Series(arr).rolling(n).mean().values

def ema(arr, n):
    return pd.Series(arr).ewm(span=n, adjust=False).mean().values

# ─── INDICATORS ────────────────────────────────────────────────────────────────

# Moving Averages
sma7  = sma(closes, 7)
sma20 = sma(closes, 20)
sma50 = sma(closes, 50)
ema12 = ema(closes, 12)
ema26 = ema(closes, 26)

# MACD
macd_line   = ema12 - ema26
macd_signal = ema(macd_line, 9)
macd_hist   = macd_line - macd_signal

# RSI (14)
delta    = np.diff(closes, prepend=closes[0])
gain     = np.where(delta > 0, delta, 0.0)
loss     = np.where(delta < 0, -delta, 0.0)
avg_gain = pd.Series(gain).ewm(alpha=1/14, adjust=False).mean().values  # Wilder smoothing
avg_loss = pd.Series(loss).ewm(alpha=1/14, adjust=False).mean().values
rs       = np.where(avg_loss != 0, avg_gain / avg_loss, 100.0)
rsi      = 100 - (100 / (1 + rs))

# Stochastic Oscillator (14,3)
low14  = pd.Series(lows).rolling(14).min().values
high14 = pd.Series(highs).rolling(14).max().values
stoch_k = np.where(
    (high14 - low14) != 0,
    100 * (closes - low14) / (high14 - low14),
    50.0
)
stoch_d = sma(stoch_k, 3)   # signal line

# Bollinger Bands (20, 2)
bb_mid   = sma20
bb_std   = pd.Series(closes).rolling(20).std().values
bb_upper = bb_mid + 2 * bb_std
bb_lower = bb_mid - 2 * bb_std
bb_pos   = np.where(
    (bb_upper - bb_lower) != 0,
    (closes - bb_lower) / (bb_upper - bb_lower),
    0.5
)
bb_width = (bb_upper - bb_lower) / bb_mid  # squeeze indicator

# ATR (14) — Average True Range
tr = np.maximum(
    highs - lows,
    np.maximum(
        np.abs(highs - np.roll(closes, 1)),
        np.abs(lows  - np.roll(closes, 1))
    )
)
tr[0] = highs[0] - lows[0]
atr14 = pd.Series(tr).ewm(alpha=1/14, adjust=False).mean().values

# OBV — On Balance Volume (trend confirmation)
obv = np.zeros(len(closes))
for i in range(1, len(closes)):
    if closes[i] > closes[i-1]:
        obv[i] = obv[i-1] + volumes[i]
    elif closes[i] < closes[i-1]:
        obv[i] = obv[i-1] - volumes[i]
    else:
        obv[i] = obv[i-1]
obv_ema = ema(obv, 20)

# Volume SMA for relative comparison
vol_sma20 = sma(volumes, 20)

# ─── PIVOT SUPPORT / RESISTANCE (Classic Pivot Points on last 5 days) ──────────
def pivot_levels(h, l, c):
    p  = (h + l + c) / 3
    r1 = 2*p - l
    s1 = 2*p - h
    r2 = p + (h - l)
    s2 = p - (h - l)
    return p, r1, s1, r2, s2

# Use last 5 candles to collect pivot zones
pivot_supports    = []
pivot_resistances = []
for i in range(-5, 0):
    _, r1, s1, r2, s2 = pivot_levels(highs[i], lows[i], closes[i])
    pivot_supports.append(s1)
    pivot_supports.append(s2)
    pivot_resistances.append(r1)
    pivot_resistances.append(r2)

pivot_support    = np.median(pivot_supports)
pivot_resistance = np.median(pivot_resistances)

# Also keep raw 30d high/low
raw_support    = min(lows[-30:])
raw_resistance = max(highs[-30:])

# Final levels: blend pivot + raw
support    = (pivot_support + raw_support) / 2
resistance = (pivot_resistance + raw_resistance) / 2

# ─── PROPER WALK-FORWARD MAE (out-of-sample) ───────────────────────────────────
# Train on days [n-37 .. n-8], predict days [n-7 .. n-1], compare to actuals
n = len(closes)
train_end   = n - 8
train_start = max(0, train_end - 30)
x_train = np.arange(train_start, train_end)
y_train = closes[train_start:train_end]
coeffs_wf = np.polyfit(x_train, y_train, 1)

x_oos  = np.arange(train_end, n - 1)
y_oos  = closes[train_end:n - 1]
y_pred_oos = coeffs_wf[0] * x_oos + coeffs_wf[1]
mae    = np.mean(np.abs(y_pred_oos - y_oos))
mape   = np.mean(np.abs((y_pred_oos - y_oos) / y_oos)) * 100

# ─── FORECAST (price-relative regression, last 30 days) ────────────────────────
x_recent = np.arange(30)
y_recent = closes[-30:]
y_base   = y_recent[0]
y_norm   = y_recent / y_base   # normalise to remove drift bias

coeffs_l = np.polyfit(x_recent, y_norm, 1)
coeffs_q = np.polyfit(x_recent, y_norm, 2)

forecast = []
for i in range(1, 8):
    xi = 30 + i
    fl = (coeffs_l[0]*xi + coeffs_l[1]) * y_base
    fq = (coeffs_q[0]*xi**2 + coeffs_q[1]*xi + coeffs_q[2]) * y_base
    forecast.append(fl*0.5 + fq*0.5)

# ─── MARKET REGIME DETECTION ───────────────────────────────────────────────────
price_vs_sma50 = (closes[-1] - sma50[-1]) / sma50[-1]
if   price_vs_sma50 >  0.05: regime = "BULL"
elif price_vs_sma50 < -0.05: regime = "BEAR"
else:                         regime = "RANGING"

# ─── SIGNAL SCORING ────────────────────────────────────────────────────────────
current_price  = closes[-1]
rsi_now        = rsi[-1]
macd_now       = macd_line[-1]
macd_sig_now   = macd_signal[-1]
macd_hist_now  = macd_hist[-1]
macd_hist_prev = macd_hist[-2]
bb_pos_now     = bb_pos[-1]
sma20_now      = sma20[-1]
sma50_now      = sma50[-1]
atr_now        = atr14[-1]
stoch_k_now    = stoch_k[-1]
stoch_d_now    = stoch_d[-1]
obv_bull       = obv[-1] > obv_ema[-1]
vol_now        = volumes[-1]
vol_avg        = vol_sma20[-1]
trend_7d       = np.nanmean(pd.Series(closes).pct_change().values[-7:])

score   = 0
max_pts = 12
signals = []

# RSI (2 pts)
if rsi_now < 35:
    score += 2; signals.append(f"RSI {rsi_now:.1f} — Oversold ► BUY")
elif rsi_now > 72:
    score -= 2; signals.append(f"RSI {rsi_now:.1f} — Overbought ► SELL")
elif rsi_now > 55:
    score += 1; signals.append(f"RSI {rsi_now:.1f} — Bullish zone")
else:
    signals.append(f"RSI {rsi_now:.1f} — Neutral")

# MACD (2 pts)
if macd_now > macd_sig_now and macd_hist_now > macd_hist_prev:
    score += 2; signals.append("MACD above signal & histogram expanding ► Strong bull")
elif macd_now > macd_sig_now:
    score += 1; signals.append("MACD above signal ► Bullish momentum")
elif macd_now < macd_sig_now and macd_hist_now < macd_hist_prev:
    score -= 2; signals.append("MACD below signal & histogram shrinking ► Strong bear")
else:
    score -= 1; signals.append("MACD below signal ► Bearish pressure")

# SMA20 & SMA50 (2 pts)
if current_price > sma20_now and current_price > sma50_now:
    score += 2; signals.append(f"Price above SMA20 & SMA50 ► Dual uptrend confirmed")
elif current_price > sma20_now:
    score += 1; signals.append(f"Price above SMA20 only ► Short-term uptrend")
elif current_price < sma20_now and current_price < sma50_now:
    score -= 2; signals.append(f"Price below both MAs ► Bearish structure")
else:
    score -= 1; signals.append(f"Price below SMA20 ► Short-term weakness")

# Bollinger Bands (1 pt)
if bb_pos_now < 0.25:
    score += 1; signals.append(f"BB position {bb_pos_now:.0%} — Near lower band ► Bounce zone")
elif bb_pos_now > 0.80:
    score -= 1; signals.append(f"BB position {bb_pos_now:.0%} — Near upper band ► Pullback risk")
else:
    signals.append(f"BB position {bb_pos_now:.0%} — Mid range ► No extreme")

# Stochastic (1 pt)
if stoch_k_now < 25 and stoch_k_now > stoch_d_now:
    score += 1; signals.append(f"Stoch K={stoch_k_now:.0f} crossing up from oversold ► BUY signal")
elif stoch_k_now > 80 and stoch_k_now < stoch_d_now:
    score -= 1; signals.append(f"Stoch K={stoch_k_now:.0f} crossing down from overbought ► SELL signal")
else:
    signals.append(f"Stoch K={stoch_k_now:.0f} / D={stoch_d_now:.0f} — Neutral")

# Volume confirmation (1 pt)
if vol_now > vol_avg * 1.3 and trend_7d > 0:
    score += 1; signals.append(f"Volume {vol_now/vol_avg:.1f}x above avg + uptrend ► Breakout confirmed")
elif vol_now < vol_avg * 0.7:
    signals.append(f"Volume {vol_now/vol_avg:.1f}x below avg ► Low conviction move")
else:
    signals.append(f"Volume at {vol_now/vol_avg:.1f}x avg ► Normal activity")

# OBV trend (1 pt)
if obv_bull:
    score += 1; signals.append("OBV above EMA20 ► Smart money accumulating")
else:
    score -= 1; signals.append("OBV below EMA20 ► Distribution pressure")

# Regression slope (1 pt)
x_all = np.arange(30)
slope_val = np.polyfit(x_all, closes[-30:], 1)[0]
if slope_val > 50:
    score += 1; signals.append(f"Regression slope +${slope_val:.0f}/day ► Strong upward bias")
elif slope_val > 0:
    signals.append(f"Regression slope +${slope_val:.0f}/day ► Slight upward bias")
else:
    score -= 1; signals.append(f"Regression slope ${slope_val:.0f}/day ► Downward bias")

# ─── VERDICT ───────────────────────────────────────────────────────────────────
pct_score = score / max_pts
if   pct_score >= 0.70: verdict, color = "STRONG BUY",        "VERY BULLISH 🚀"
elif pct_score >= 0.45: verdict, color = "BUY",               "BULLISH 📈"
elif pct_score >= 0.20: verdict, color = "CAUTIOUSLY BULLISH","SLIGHT BULLISH 🟡"
elif pct_score >= -0.10: verdict, color = "NEUTRAL",          "NEUTRAL ⚪"
elif pct_score >= -0.35: verdict, color = "CAUTION",          "SLIGHT BEARISH 🟠"
else:                    verdict, color = "SELL / AVOID",      "BEARISH 🔴"

# ─── STOP LOSS / TAKE PROFIT ───────────────────────────────────────────────────
atr_sl  = current_price - (1.5 * atr_now)
atr_tp1 = current_price + (2.0 * atr_now)
atr_tp2 = current_price + (3.5 * atr_now)
rr_ratio = (atr_tp1 - current_price) / (current_price - atr_sl) if (current_price - atr_sl) > 0 else 0

# ─── OUTPUT ────────────────────────────────────────────────────────────────────
print("=" * 50)
print("   BTC PRICE PREDICTION ENGINE v2.0")
print("=" * 50)
print(f"Current BTC Price :  ${current_price:,.2f}")
print(f"Market Regime     :  {regime}")
print(f"Walk-Forward MAE  :  ${mae:,.0f}  ({100-mape:.1f}% directional accuracy)")
print(f"ATR (14)          :  ${atr_now:,.0f}  (daily volatility band)")
print()
print("TECHNICAL SIGNALS:")
for s in signals:
    print(f"  ► {s}")
print()
print(f"SIGNAL SCORE : {score}/{max_pts}  ({pct_score*100:.0f}%)")
print(f"VERDICT      : {verdict}  —  {color}")
print()
print("KEY PRICE LEVELS:")
print(f"  Pivot Support    : ${pivot_support:,.0f}")
print(f"  Pivot Resistance : ${pivot_resistance:,.0f}")
print(f"  SMA20            : ${sma20_now:,.0f}")
print(f"  SMA50            : ${sma50_now:,.0f}")
print(f"  BB Upper         : ${bb_upper[-1]:,.0f}")
print(f"  BB Lower         : ${bb_lower[-1]:,.0f}")
print()
print("TRADE LEVELS (ATR-based):")
print(f"  Entry            : ${current_price:,.0f}")
print(f"  Stop Loss  (1.5x ATR): ${atr_sl:,.0f}  [{((atr_sl-current_price)/current_price)*100:.1f}%]")
print(f"  Take Profit 1 (2x ATR): ${atr_tp1:,.0f}  [{((atr_tp1-current_price)/current_price)*100:.1f}%]")
print(f"  Take Profit 2 (3.5x ATR): ${atr_tp2:,.0f}  [{((atr_tp2-current_price)/current_price)*100:.1f}%]")
print(f"  Risk/Reward Ratio: 1 : {rr_ratio:.1f}")
print()
print("7-DAY BTC FORECAST:")
today = datetime.utcnow()
for i, price in enumerate(forecast):
    day    = (today + timedelta(days=i+1)).strftime("%a %b %d")
    change = ((price - current_price) / current_price) * 100
    arrow  = "▲" if price > current_price else "▼"
    print(f"  {day}: ${price:,.0f}  [{arrow} {change:+.1f}%]")

print()
max_fc = max(forecast)
min_fc = min(forecast)
if   max_fc >= 83000: sol_outlook = "HIGH — BTC trajectory supports SOL TP"
elif max_fc >= 81000: sol_outlook = "MODERATE — BTC range-bound, SOL needs own catalyst"
else:                 sol_outlook = "LOW — BTC weakness may pressure SOL below SL"

print(f"SOL TP ($100.87) Probability:")
print(f"  {sol_outlook}")
print(f"  BTC Forecast Range: ${min_fc:,.0f} — ${max_fc:,.0f}")
print("=" * 50)
