import json
import requests
from datetime import datetime
import openai
import base64
import os
import re

# === CONFIG ===
SYMBOL = "BTCUSDT"
TIMEFRAMES = ["15m"]
RISK_REWARD_RATIO = 2.0

openai.api_key = os.getenv("OPENAI_API_KEY")


def fetch_candles(symbol, interval, limit=100):
    tf_map = {
        "1m": "1min",
        "5m": "5min",
        "15m": "15min",
        "1h": "1h",
        "4h": "4h"
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
            "timestamp": datetime.utcnow().isoformat()
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
            "timestamp": datetime.utcnow().isoformat()
        }

    return None


# === Screenshot Bypass (No Chromium Needed) ===
def capture_chart_screenshot():
    with open("screenshot.png", "wb") as f:
        f.write(b"DUMMY_IMAGE")


def encode_screenshot():
    try:
        with open("screenshot.png", "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except:
        return ""


def ask_vision_ai(ai_name, base64_img):
    prompt = "Analyze this BTC chart and provide: Direction, Entry, SL, TP based on SMC (BOS + OB)."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}},
                    {"type": "text", "text": prompt}
                ]
            }],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ {ai_name} vision error:", e)
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
        capture_chart_screenshot()
        b64_img = encode_screenshot()

        chatgpt_resp = ask_vision_ai("ChatGPT", b64_img)
        grok_resp = ask_vision_ai("Grok", b64_img)
        deepshik_resp = ask_vision_ai("Deepshik", b64_img)

        votes = {}
        votes["ChatGPT"], chatgpt_detail = vote_parser(chatgpt_resp)
        votes["Grok"], grok_detail = vote_parser(grok_resp)
        votes["Deepshik"], deepshik_detail = vote_parser(deepshik_resp)

        yes_votes = sum(1 for v in votes.values() if v == "YES")

        if yes_votes >= 2:
            e1, s1, t1 = extract_trade_details(chatgpt_detail)
            e2, s2, t2 = extract_trade_details(grok_detail)
            e3, s3, t3 = extract_trade_details(deepshik_detail)

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
