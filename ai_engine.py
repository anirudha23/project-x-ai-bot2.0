# ✅ FILE: ai_engine.py (Final version using CoinGecko)

import json
import requests
from datetime import datetime
from screenshot import capture_chart_screenshot
import openai
import base64
import os
import re

# === CONFIG ===
SYMBOL = "bitcoin"
TIMEFRAMES = ["5m", "15m"]
RISK_REWARD_RATIO = 2
MIN_BOS_DISTANCE = 100
MIN_OB_VOLUME = 100

# Load OpenAI Key
openai.api_key = os.getenv("OPENAI_API_KEY")

# === Fetch candles using CoinGecko ===
def fetch_candles(symbol, interval, limit=100):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=1&interval=minute"
    try:
        response = requests.get(url)
        data = response.json()
        prices = data.get("prices", [])[-limit:]
        volumes = data.get("total_volumes", [])[-limit:]

        if not prices or not volumes:
            print("❌ Failed to get data from CoinGecko.")
            return []

        candles = []
        for i in range(len(prices)):
            t = prices[i][0]
            close = prices[i][1]
            volume = volumes[i][1]
            candles.append({
                "time": t,
                "open": close,
                "high": close * 1.002,
                "low": close * 0.998,
                "close": close,
                "volume": volume
            })
        return candles

    except Exception as e:
        print("❌ Error fetching CoinGecko data:", e)
        return []

# === Evaluate trade ===
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

# === Detect strategy match ===
def detect_trade(candles, tf):
    if len(candles) < 10:
        return None

    last_high = candles[-2]["high"]
    prev_high = candles[-3]["high"]
    last_low = candles[-2]["low"]
    prev_low = candles[-3]["low"]

    bos_up = last_high > prev_high + MIN_BOS_DISTANCE
    bos_down = last_low < prev_low - MIN_BOS_DISTANCE

    ob_candle = candles[-4]
    ob_volume = ob_candle["volume"]
    ob_body = abs(ob_candle["close"] - ob_candle["open"])
    valid_ob = ob_volume > MIN_OB_VOLUME and ob_body > 0

    if (bos_up or bos_down) and valid_ob:
        return True
    return False

# === Screenshot to base64 ===
def encode_screenshot():
    with open("screenshot.png", "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# === Ask OpenAI Vision ===
def ask_vision_ai(ai_name, base64_img):
    prompt = "Analyze this BTC chart and provide: Direction, Entry, SL, TP based on SMC (BOS + OB)."
    response = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64_img}"
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        max_tokens=500
    )
    return response.choices[0].message.content

# === Parse vote ===
def vote_parser(ai_response):
    vote = "NO"
    if "entry" in ai_response.lower() and "sl" in ai_response.lower() and "tp" in ai_response.lower():
        vote = "YES"
    return vote, ai_response

# === Extract Entry/SL/TP ===
def extract_trade_details(text):
    entry = sl = tp = ""
    entry_match = re.search(r"entry[:\s]*([\d\.]+)", text, re.IGNORECASE)
    sl_match = re.search(r"sl[:\s]*([\d\.]+)", text, re.IGNORECASE)
    tp_match = re.search(r"tp[:\s]*([\d\.]+)", text, re.IGNORECASE)

    if entry_match:
        entry = entry_match.group(1)
    if sl_match:
        sl = sl_match.group(1)
    if tp_match:
        tp = tp_match.group(1)

    return entry, sl, tp

# === Check for duplicates ===
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

# === Save signal ===
def track_signal_outcome(signal):
    with open("trade_history.json", "a") as f:
        signal["timestamp"] = datetime.utcnow().isoformat()
        json.dump(signal, f)
        f.write(",\n")
    print("📘 Trade recorded in trade_history.json")

# === Main Strategy Logic ===
def main():
    for tf in TIMEFRAMES:
        candles = fetch_candles(SYMBOL, tf)
        if not candles:
            print(f"❌ No candle data received for {tf}. Skipping.")
            continue

        print(f"📊 Live BTC ({tf}) Price: {candles[-1]['close']}")
        if detect_trade(candles, tf):
            print("✅ Valid strategy setup found. Taking screenshot...")
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
        else:
            print("❌ No trade found. Market doesn't match strategy.")

if __name__ == "__main__":
    main()
