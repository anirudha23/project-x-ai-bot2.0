import json
import requests
from datetime import datetime, timezone
from openai import OpenAI
import os
import re

SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"
RISK_REWARD_RATIO = 2.0
CANDLE_CONTEXT_COUNT = 20  # Number of candles to send to GPT-3.5

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Must be set

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

def ask_gpt35(candles):
    prompt = (
        "Analyze this BTC 15m candle data for possible trade setup based on SMC (Structure Break, OB, CHoCH).\n"
        "Return result as:\nDirection: Long or Short\nEntry:\nSL:\nTP:\nReason:\n\n"
        f"Candle Data (latest last):\n{json.dumps(candles[-CANDLE_CONTEXT_COUNT:], indent=2)}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        return response.choices[0].message.content
    except Exception as e:
        print("❌ GPT-3.5 Error:", e)
        return ""

def extract_trade_details(text):
    entry = sl = tp = ""
    entry_match = re.search(r"entry[:\s]*([\d\.]+)", text, re.IGNORECASE)
    sl_match = re.search(r"sl[:\s]*([\d\.]+)", text, re.IGNORECASE)
    tp_match = re.search(r"tp[:\s]*([\d\.]+)", text, re.IGNORECASE)
    if entry_match: entry = entry_match.group(1)
    if sl_match: sl = sl_match.group(1)
    if tp_match: tp = tp_match.group(1)
    return entry, sl, tp

def main():
    candles = fetch_candles(SYMBOL, TIMEFRAME)
    if not candles:
        print("❌ Candle fetch failed.")
        return

    # Step 1: Try basic strategy
    signal = detect_simple_breakout(candles)
    if signal:
        print("✅ Detected simple breakout signal:")
        print(json.dumps(signal, indent=2))
    else:
        print("❌ No breakout setup.")

    # Step 2: Ask GPT-3.5 to analyze last 20 candles
    print("\n🤖 Asking GPT-3.5 to detect SMC trade...")
    gpt_response = ask_gpt35(candles)
    print("\n📨 GPT-3.5 Response:\n")
    print(gpt_response)

    # Step 3: Try to parse it
    entry, sl, tp = extract_trade_details(gpt_response)
    if entry and sl and tp:
        print("\n✅ Valid trade details found:")
        print(f"Entry: {entry}, SL: {sl}, TP: {tp}")
    else:
        print("\n❌ GPT response missing required fields.")

    # Optional: save to file for test output
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gpt_response": gpt_response,
        "parsed": {
            "entry": entry,
            "sl": sl,
            "tp": tp
        }
    }
    with open("test_gpt_trade_output.json", "w") as f:
        json.dump(output, f, indent=2)
    print("\n📝 Output saved to test_gpt_trade_output.json")

if __name__ == "__main__":
    main()
