import os
import json
import requests
from datetime import datetime, timezone
from openai import OpenAI
from screenshot import capture_chart_screenshot
import base64

# === Configuration ===
SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"
RISK_REWARD_RATIO = 2.0
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def detect_body_breakout(candles):
    if len(candles) < 2:
        return None
    prev = candles[-2]
    current = candles[-1]

    if current["close"] > current["open"] and current["close"] > prev["high"]:
        entry = current["close"]
        sl = prev["low"]
        tp = entry + RISK_REWARD_RATIO * (entry - sl)
        return {
            "direction": "BUY",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "time": current["time"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "setup": {"bos": prev, "entry_candle": current}
        }

    elif current["close"] < current["open"] and current["close"] < prev["low"]:
        entry = current["close"]
        sl = prev["high"]
        tp = entry - RISK_REWARD_RATIO * (sl - entry)
        return {
            "direction": "SELL",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "time": current["time"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "setup": {"bos": prev, "entry_candle": current}
        }

    return None

def is_duplicate_signal(new_signal):
    try:
        with open("last_signal.json", "r") as f:
            last = json.load(f)
            return (
                last.get("entry") == new_signal.get("entry") and
                last.get("sl") == new_signal.get("sl") and
                last.get("tp") == new_signal.get("tp") and
                last.get("direction") == new_signal.get("direction")
            )
    except:
        return False

def analyze_chart_with_gpt4_vision():
    capture_chart_screenshot()
    try:
        with open("screenshot.png", "rb") as img:
            image_data = base64.b64encode(img.read()).decode("utf-8")

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze the BTC chart using SMC (Break of Structure, Order Block, CHoCH). Return trade signal in this format:\nDirection: Long/Short\nEntry:\nSL:\nTP:\nReason:"
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )

        print("\n🤖 GPT-4 Vision Response:\n")
        print(response.choices[0].message.content)

    except Exception as e:
        print("❌ GPT-4 Vision error:", e)

def main():
    candles = fetch_candles(SYMBOL, TIMEFRAME)
    if not candles:
        print("❌ Candle fetch failed.")
        return

    signal = detect_body_breakout(candles)
    if signal:
        print("✅ Body breakout detected:")
        print(json.dumps(signal, indent=2))

        if is_duplicate_signal(signal):
            print("🔁 Duplicate signal. Skipping.")
            return

        with open("last_signal.json", "w") as f:
            json.dump(signal, f, indent=2)
        print("✅ Signal saved to last_signal.json")

        analyze_chart_with_gpt4_vision()

    else:
        print("❌ No valid candle body breakout.")

if __name__ == "__main__":
    main()
