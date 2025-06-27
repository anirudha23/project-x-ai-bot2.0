import json
import requests
from datetime import datetime
from screenshot import capture_chart_screenshot
import openai
import base64
import os
import re

# === CONFIG ===
SYMBOL = "BTCUSDT"  # ✅ Correct Binance symbol
TIMEFRAMES = ["15m"]
RISK_REWARD_RATIO = 2
MIN_BOS_DISTANCE = 50  # lowered from 100
MIN_OB_VOLUME = 50     # lowered from 100

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

    url = f"https://api.twelvedata.com/time_series"
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

def detect_trade(candles, tf):
    if len(candles) < 10:
        return None

    # --- Trend Detection (3-candle bias) ---
    bullish_trend = candles[-5]["close"] < candles[-4]["close"] < candles[-3]["close"]
    bearish_trend = candles[-5]["close"] > candles[-4]["close"] > candles[-3]["close"]

    # --- BOS Check (50 points distance) ---
    last_high = candles[-2]["high"]
    prev_high = candles[-3]["high"]
    last_low = candles[-2]["low"]
    prev_low = candles[-3]["low"]

    bos_up = last_high > prev_high + MIN_BOS_DISTANCE
    bos_down = last_low < prev_low - MIN_BOS_DISTANCE

    # --- Liquidity Sweep (Wick > 2× body in last 3 candles) ---
    def large_wick(c):
        body = abs(c["close"] - c["open"])
        wick_up = c["high"] - max(c["close"], c["open"])
        wick_down = min(c["close"], c["open"]) - c["low"]
        return wick_up > 2 * body or wick_down > 2 * body

    wick_signal = any(large_wick(candles[-i]) for i in range(2, 5))

    # --- Order Block Check ---
    valid_ob = False
    for i in range(2, 5):  # check last 3 candles
        ob = candles[-i]
        ob_range = ob["high"] - ob["low"]
        ob_body = abs(ob["close"] - ob["open"])
        if ob["volume"] > MIN_OB_VOLUME and ob_body >= 0.1 * ob_range:
            valid_ob = True
            break

    # --- Final Confirmation ---
    if (bullish_trend and bos_up and valid_ob) or \
       (bearish_trend and bos_down and valid_ob):
        return True

    return False

def encode_screenshot():
    with open("screenshot.png", "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def ask_vision_ai(ai_name, base64_img):
    prompt = "Analyze this BTC chart and provide: Direction, Entry, SL, TP based on SMC (BOS + OB)."
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

def track_signal_outcome(signal):
    with open("trade_history.json", "a") as f:
        signal["timestamp"] = datetime.utcnow().isoformat()
        json.dump(signal, f)
        f.write(",\n")
    print("📘 Trade recorded in trade_history.json")

def main():
    for tf in TIMEFRAMES:
        candles = fetch_candles(SYMBOL, tf)
        if not candles:
            print(f"❌ No candle data received for {tf}. Skipping.")
            continue

        print(f"📊 BTC ({tf}) Last Price: {candles[-1]['close']}")
        if detect_trade(candles, tf):
            print("✅ Strategy matched: BOS + OB pattern detected.")
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

                result = {
                    "symbol": SYMBOL,
                    "timeframe": tf,
                    "direction": "BUY" if "buy" in chatgpt_resp.lower() or "buy" in grok_resp.lower() or "buy" in deepshik_resp.lower() else "SELL",
                    "votes": f"{yes_votes} YES / {3 - yes_votes} NO",
                    "chatgpt": chatgpt_detail,
                    "grok": grok_detail,
                    "deepshik": deepshik_detail,
                    "entry": e1 or e2 or e3,
                    "sl": s1 or s2 or s3,
                    "tp": t1 or t2 or t3
                }

                try:
                    rr = abs(float(result["tp"]) - float(result["entry"])) / abs(float(result["entry"]) - float(result["sl"]))
                    if rr < RISK_REWARD_RATIO:
                        print("❌ Skipped: R/R ratio too low.")
                        return
                except:
                    print("❌ Invalid SL/TP values. Skipping.")
                    return

                if is_duplicate_signal(result):
                    print("🔁 Duplicate signal detected. Skipping.")
                    return

                future_candles = fetch_candles(SYMBOL, tf, limit=10)
                result["outcome"] = evaluate_trade_outcome(result, future_candles)

                with open("last_signal.json", "w") as f:
                    json.dump(result, f, indent=2)
                print("✅ Final AI signal written to last_signal.json")
                track_signal_outcome(result)
                return
            else:
                print("❌ Not enough YES votes from AIs.")
                return
        else:
            print("❌ No trade setup matched strategy.")

if __name__ == "__main__":
    main()
