from flask import Flask, jsonify
from flask_cors import CORS
import requests
import pandas as pd
import numpy as np
import ta

app = Flask(__name__)
CORS(app)

symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT']
interval = '5m'
limit = 100

def fetch_klines(symbol):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])

    df['close'] = df['close'].astype(float)
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)

    return df

def analyze_symbol(symbol):
    df = fetch_klines(symbol)
    if df is None or df.empty:
        return None

    df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ema_fast'] = ta.trend.EMAIndicator(close=df['close'], window=9).ema_indicator()
    df['ema_slow'] = ta.trend.EMAIndicator(close=df['close'], window=21).ema_indicator()
    bb = ta.volatility.BollingerBands(close=df['close'])
    df['bb_upper'] = bb.bollinger_hband()
    df['bb_lower'] = bb.bollinger_lband()
    df['adx'] = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close']).adx()

    latest = df.iloc[-1]
    previous = df.iloc[-2]

    entry_price = latest['close']
    stop_loss = entry_price * 0.995
    target = entry_price * 1.005

    confirmations = []

    if latest['rsi'] < 30:
        confirmations.append("شراء - RSI منخفض")
    elif latest['rsi'] > 70:
        confirmations.append("بيع - RSI مرتفع")

    if latest['macd'] > latest['macd_signal']:
        confirmations.append("شراء - MACD إيجابي")
    elif latest['macd'] < latest['macd_signal']:
        confirmations.append("بيع - MACD سلبي")

    if latest['ema_fast'] > latest['ema_slow']:
        confirmations.append("شراء - تقاطع EMA إيجابي")
    elif latest['ema_fast'] < latest['ema_slow']:
        confirmations.append("بيع - تقاطع EMA سلبي")

    if latest['close'] < latest['bb_lower']:
        confirmations.append("شراء - Bollinger منخفض")
    elif latest['close'] > latest['bb_upper']:
        confirmations.append("بيع - Bollinger مرتفع")

    if latest['adx'] > 25:
        confirmations.append("اتجاه قوي - ADX")

    # حساب عدد المؤشرات المؤيدة
    buy_signals = sum("شراء" in c for c in confirmations)
    sell_signals = sum("بيع" in c for c in confirmations)

    # تحديد الإشارة النهائية
    if buy_signals > sell_signals:
        signal = "شراء"
    elif sell_signals > buy_signals:
        signal = "بيع"
    else:
        return None

    # حساب نسبة الثقة
    total_signals = max(buy_signals, sell_signals)
    confidence_percent = int((total_signals / 6) * 100)

    # تحديد الرافعة حسب الثقة
    if confidence_percent >= 95:
        leverage = "3x"
    elif confidence_percent >= 85:
        leverage = "2x"
    elif confidence_percent >= 70:
        leverage = "1x"
    else:
        leverage = "0x (بدون رافعة)"

    return {
        "الرمز": symbol,
        "الإشارة": signal,
        "سعر الدخول": round(entry_price, 2),
        "الهدف": round(target, 2),
        "وقف الخسارة": round(stop_loss, 2),
        "نسبة الثقة": f"{confidence_percent}%",
        "الرافعة المقترحة": leverage
    }

@app.route('/')
def home():
    results = []
    for symbol in symbols:
        result = analyze_symbol(symbol)
        if result:
            results.append(result)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
