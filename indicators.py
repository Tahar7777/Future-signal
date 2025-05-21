import requests
import pandas as pd
import ta

def get_signal(symbol):
    url = f'https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval=1m&limit=100'
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_volume', 'taker_buy_quote_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])

    # حساب المؤشرات الفنية
    df['rsi'] = ta.momentum.RSIIndicator(close=df['close']).rsi()
    macd = ta.trend.MACD(close=df['close'])
    df['macd'] = macd.macd()
    df['macd_signal'] = macd.macd_signal()
    df['ema_fast'] = ta.trend.EMAIndicator(close=df['close'], window=12).ema_indicator()
    df['ema_slow'] = ta.trend.EMAIndicator(close=df['close'], window=26).ema_indicator()

    latest = df.iloc[-1]

    # تحديد الإشارة
    if latest['rsi'] < 30 and latest['macd'] > latest['macd_signal'] and latest['ema_fast'] > latest['ema_slow']:
        signal = 'شراء (LONG)'
        confidence = 'مرتفعة'
    elif latest['rsi'] > 70 and latest['macd'] < latest['macd_signal'] and latest['ema_fast'] < latest['ema_slow']:
        signal = 'بيع (SHORT)'
        confidence = 'مرتفعة'
    else:
        signal = 'انتظار'
        confidence = 'منخفضة'

    return {
        'symbol': symbol,
        'signal': signal,
        'confidence': confidence,
        'rsi': round(latest['rsi'], 2),
        'macd': round(latest['macd'], 2),
        'macd_signal': round(latest['macd_signal'], 2),
        'ema_fast': round(latest['ema_fast'], 2),
        'ema_slow': round(latest['ema_slow'], 2),
        'price': latest['close']
    }
