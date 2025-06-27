import os
import json
import requests
from datetime import datetime, timezone

SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"
RISK_REWARD_RATIO = 2.0

def fetch_candles(symbol, interval, limit=100):
    tf_map = {
        "1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"
    }
    interval_td = tf_map.get(interval, "15min")
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "BTC/USD",
        "interval": interval_td,
        "outputsize": limit,
        "apikey": os.getenv("TWELVE_API_KEY")
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "values" not in data:
            print("❌ API Error:", data)
            return []
        candles = []
        for item in reversed(data["values"]):
            candles.append({
                "time": item["datetime"],
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item.get("volume", 0))
            })
        return candles
    except Exception as e:
        print("❌ Error fetching candles:", e)
        return []

def detect_simple_breakout(candles):
    if len(candles) < 2:
        return None
    prev = candles[-2]
    current = candles[-1]
    if current["high"] > prev["high"]:
        entry = current["high"]
        sl = prev["low"]
        tp = entry + RISK_REWARD_RATIO * (entry - sl)
        return {
            "direction": "BUY",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "time": current["time"],
            "setup": {"bos": prev, "entry_candle": current}
        }
    elif current["low"] < prev["low"]:
        entry = current["low"]
        sl = prev["high"]
        tp = entry - RISK_REWARD_RATIO * (sl - entry)
        return {
            "direction": "SELL",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "time": current["time"],
            "setup": {"bos": prev, "entry_candle": current}
        }
    return None

def main():
    candles = fetch_candles(SYMBOL, TIMEFRAME)
    if not candles:
        print("❌ Candle fetch failed.")
        return

    signal = detect_simple_breakout(candles)
    if signal:
        print("✅ Detected simple breakout signal:")
        print(json.dumps(signal, indent=2))
    else:
        print("❌ No breakout setup.")

if __name__ == "__main__":
    main()
