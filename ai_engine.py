import json
import requests
from datetime import datetime, timezone
from openai import OpenAI
import os
import re

SYMBOL = "BTCUSDT"
TIMEFRAMES = ["15m"]
RISK_REWARD_RATIO = 2.0
CANDLE_CONTEXT_COUNT = 20  # Number of candles to send to GPT-3.5

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
            print("❌ TwelveData API Error:", data)
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
        print("❌ Error fetching from TwelveData:", e)
        return []

def detect_trade(candles, tf):
    if len(candles) < 2:
        return None
    prev = candles[-2]
    current = candles[-1]
    if current["high"] > prev["high"]:
        entry = current["high"]
        sl = prev["low"]
        tp = entry + RISK_REWARD_RATIO * (entry - sl)
        return {
            "symbol": SYMBOL,
            "timeframe": tf,
            "direction": "BUY",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "time": current["time"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "setup_candles": {
                "bos": prev,
                "entry_candle": current
            }
        }
    elif current["low"] < prev["low"]:
        entry = current["low"]
        sl = prev["high"]
        tp = entry - RISK_REWARD_RATIO * (sl - entry)
        return {
            "symbol": SYMBOL,
            "timeframe": tf,
            "direction": "SELL",
            "entry": entry,
            "sl": sl,
            "tp": tp,
            "time": current["time"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "setup_candles": {
                "bos": prev,
                "entry_candle": current
            }
        }
    return None

def ask_gpt35(ai_name, candles):
    prompt = (
        "Analyze the following BTC 15m candle data for any trade setup based on SMC (Structure Break, OB, CHoCH). "
        "If a trade is found, return clearly:\nDirection: Long/Short\nEntry:\nSL:\nTP:\nReason:\n\n"
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
        print(f"❌ {ai_name} error:", e)
        return ""

def vote_parser(ai_response):
    vote = "NO"
    if "entry" in ai_response.lower() and "sl" in ai_response.lower() and "tp" in ai_response.lower():
        vote = "YES"
    return vote, ai_response

def extract_trade_details(text):
    entry = sl = tp = ""
    entry_match = re.search(r"entry[:\s]*([\d\.]+)", text, re.IGNORECASE)
    sl_match = re.search(r"sl[:\s]*([\d\.]+)", text, re.IGNORECASE)
    tp_match = re.search(r"tp[:\s]*([\d\.]+)", text, re.IGNORECASE)
    if entry_match: entry = entry_match.group(1)
    if sl_match: sl = sl_match.group(1)
    if tp_match: tp = tp_match.group(1)
    return entry, sl, tp

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

def evaluate_trade_outcome(signal, candles_after):
    entry = float(signal["entry"])
    sl = float(signal["sl"])
    tp = float(signal["tp"])
    for c in candles_after:
        if signal["direction"] == "BUY":
            if c["low"] <= sl:
                return "SL HIT"
            elif c["high"] >= tp:
                return "TP HIT"
        elif signal["direction"] == "SELL":
            if c["high"] >= sl:
                return "SL HIT"
            elif c["low"] <= tp:
                return "TP HIT"
    return "NOT HIT"

def track_signal_outcome(signal):
    with open("trade_history.json", "a") as f:
        json.dump(signal, f)
        f.write(",\n")
    print("📘 Trade recorded in trade_history.json")

# === MAIN ===
def main():
    for tf in TIMEFRAMES:
        candles = fetch_candles(SYMBOL, tf)
        if not candles:
            print(f"❌ No candles for {tf}")
            continue
        signal = detect_trade(candles, tf)
        if not signal:
            print("❌ No breakout setup.")
            return
        print("✅ Breakout setup found.")

        chatgpt_resp = ask_gpt35("ChatGPT", candles)
        grok_resp = ask_gpt35("Grok", candles)
        deepshik_resp = ask_gpt35("Deepshik", candles)

        votes = {}
        votes["ChatGPT"], chatgpt_detail = vote_parser(chatgpt_resp)
        votes["Grok"], grok_detail = vote_parser(grok_resp)
        votes["Deepshik"], deepshik_detail = vote_parser(deepshik_resp)

        yes_votes = sum(1 for v in votes.values() if v == "YES")

        if yes_votes >= 2:
            signal["votes"] = f"{yes_votes} YES / {3 - yes_votes} NO"
            signal["ai_analysis"] = {
                "chatgpt": chatgpt_detail,
                "grok": grok_detail,
                "deepshik": deepshik_detail
            }
            if is_duplicate_signal(signal):
                print("🔁 Duplicate signal. Skipping.")
                return

            future = fetch_candles(SYMBOL, tf, limit=10)
            signal["outcome"] = evaluate_trade_outcome(signal, future)

            with open("last_signal.json", "w") as f:
                json.dump(signal, f, indent=2)
            print("✅ Signal saved to last_signal.json")
            track_signal_outcome(signal)
        else:
            print("❌ Not enough AI confirmations.")

if __name__ == "__main__":
    main()
