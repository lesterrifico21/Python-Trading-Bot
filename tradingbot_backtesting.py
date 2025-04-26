import os
import time
import requests
import hmac
import hashlib 
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Lester Luis\Desktop\Tradingbot\MEXC_API_KEY.env")


base_url = "https://api.mexc.com"
endpoint = "/api/v3/account"
timestamp = int(time.time() * 1000)

query_string = f"timestamp={timestamp}"
signature = hmac.new(
    os.getenv("MEXC_SECRET_KEY").encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

url = f"{base_url}{endpoint}?{query_string}&signature={signature}"      
headers = {
    "X-MEXC-APIKEY": os.getenv("MEXC_API_KEY")
}

response = requests.get(url, headers=headers)
print(response.status_code, response.text)


print("✅ Current working directory:", os.getcwd())

API_KEY = os.getenv("MEXC_API_KEY") 
print("🔐 API key loaded:", "Yes" if API_KEY else "No")
 

def datetime_to_millis(dt_str):
    dt = datetime.strptime(dt_str, '%Y-%m-%d')
    return int(dt.timestamp() * 1000)


def fetch_historical_data(symbol='BTCUSDT', interval='1m', start_date=None, end_date=None):
    print(f"\n📡 Fetching data from {start_date} to {end_date} [{interval}]...")

    base_url = "https://api.mexc.com"
    endpoint = "/api/v3/klines"
    
    start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
    end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)

    all_data = []
    limit = 1000
    while start_ts < end_ts:
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ts,
            "limit": limit
        }

        response = requests.get(f"{base_url}{endpoint}", params=params)
        data = response.json()

        if isinstance(data, dict) and 'code' in data:
            print(f"❌ No data fetched. Response: {data}")
            break

        if not data:
            print("❌ No data returned.")
            break

        print(f"🕐 Getting data starting from {datetime.fromtimestamp(start_ts / 1000).strftime('%Y-%m-%d %H:%M:%S')}")
        all_data += data
        start_ts = data[-1][0] + 1  # move to next candle

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(all_data, columns=[
    'timestamp', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_volume'
])                  
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)


    df[['open', 'high', 'low', 'close', 'volume', 'quote_volume']] = df[[
    'open', 'high', 'low', 'close', 'volume', 'quote_volume'
]].astype(float)

    return df       




# ✅ Simple backtest
def simple_backtest(df):
    initial_capital = 1000
    position = 0
    capital = initial_capital
    trades = []


    print("\n🚦 Starting backtest...")

    for i in range(1, len(df)):
        price_now = df['close'].iloc[i]
        price_prev = df['close'].iloc[i - 1]
        timestamp = df.index[i]

        print(f"🔍 price_now: {price_now} ({type(price_now)}), price_prev: {price_prev} ({type(price_prev)})")

        price_change = (price_now - price_prev) / price_prev

        if position == 0 and price_change > 0.02:
            position = capital / price_now
            capital = 0
            trades.append((timestamp, 'BUY', price_now))
            print(f"🟢 BUY at {timestamp} - ${price_now:.2f}")

        elif position > 0 and price_change < -0.02:
            capital = position * price_now
            position = 0
            trades.append((timestamp, 'SELL', price_now))
            print(f"🔴 SELL at {timestamp} - ${price_now:.2f}")

    final_value = capital + (position * df['close'].iloc[-1])
    profit = final_value - initial_capital

    print(f"\n📈 Final Portfolio Value: ${final_value:.2f}")
    print(f"💰 Total Profit: ${profit:.2f}")

    return trades

# ✅ Execute
if __name__ == '__main__':
    df = fetch_historical_data(
        symbol='BTCUSDT',
        interval='60m',
        start_date='2025-04-01',
        end_date='2025-04-03'  
    )

    if df.empty:
        print("⚠️ Exiting: No data to backtest.")   
    else:
        trades = simple_backtest(df)

        for t in trades:
            print(f"{t[0]} - {t[1]} at ${t[2]:.2f}")

