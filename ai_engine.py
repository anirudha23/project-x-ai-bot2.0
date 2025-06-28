# FILE: ai_engine.py
import os
import json
import requests
from datetime import datetime, timezone
from screenshot import capture_chart_screenshot
from transformers import BlipProcessor, BlipForConditionalGeneration
import torch
import cohere
from PIL import Image

# === Config ===
SYMBOL = "BTCUSDT"
TIMEFRAME = "15m"
RISK_REWARD_RATIO = 2.0
MIN_BOS_DISTANCE = 50
MIN_OB_VOLUME = 50
co = cohere.Client(os.getenv("COHERE_API_KEY"))

# === AI Models ===
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base", use_fast=False)
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# === Captioning ===
def blip2_caption(image_path):
    image = Image.open(image_path).convert("RGB")
    inputs = blip_processor(images=image, return_tensors="pt").to(device)
    out = blip_model.generate(**inputs)
    return blip_processor.decode(out[0], skip_special_tokens=True)

# === AI Decision ===
def load_training_examples():
    examples = []
    try:
        with open("trade_history.json", "r") as f:
            trades = json.load(f)
            for trade in trades[-50:]:
                if "caption" in trade and "outcome" in trade:
                    label = "YES" if trade["outcome"] == "TP HIT" else "NO"
                    examples.append({"text": trade["caption"], "label": label})
    except:
        pass
    examples.extend([
        {"text": "Bullish BOS formed, clean OB, possible reversal setup.", "label": "YES"},
        {"text": "No clear structure, sideways price action.", "label": "NO"},
    ])
    return examples

def cohere_decision(caption):
    try:
        response = co.classify(
            model='large',
            inputs=[caption],
            examples=load_training_examples()
        )
        return response.classifications[0].prediction
    except Exception as e:
        print("❌ Cohere error:", e)
        return "NO"

def deepshik_vote(signal):
    if signal and abs(signal['entry'] - signal['sl']) >= 50 and signal['setup']['entry_candle']['volume'] > MIN_OB_VOLUME:
        return "YES"
    return "NO"

def donut_decision(image_path):
    return "YES"  # Placeholder

# === Candle Fetch ===
def fetch_candles(symbol, interval, limit=100):
    tf_map = {"1m": "1min", "5m": "5min", "15m": "15min", "1h": "1h", "4h": "4h"}
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": "BTC/USD",
        "interval": tf_map.get(interval, "15min"),
        "outputsize": limit,
        "apikey": os.getenv("TWELVE_API_KEY")
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "values" not in data:
            print("❌ API Error:", data)
            return []
        candles = [
            {
                "time": i["datetime"],
                "open": float(i["open"]),
                "high": float(i["high"]),
                "low": float(i["low"]),
                "close": float(i["close"]),
                "volume": float(i.get("volume", 0))
            } for i in reversed(data["values"])
        ]
        print(f"✅ Fetched {len(candles)} candles from BTC/USD ({interval})")
        return candles
    except Exception as e:
        print("❌ Error:", e)
        return []

# === Trade Detection ===
def detect_trade(candles):
    if len(candles) < 60:
        print("⚠️ Not enough candles to detect trade.")
        return None
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]
    ema = lambda arr, l: sum(arr[-l:]) / l
    ema9, ema21 = ema(closes, 9), ema(closes, 21)
    mtf_bull = ema(closes[-60:], 9) > ema(closes[-60:], 21)
    mtf_bear = ema(closes[-60:], 9) < ema(closes[-60:], 21)
    tr = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(1, len(candles))]
    atr = sum(tr[-14:]) / 14

    last_high, prev_high = candles[-2]["high"], candles[-3]["high"]
    last_low, prev_low = candles[-2]["low"], candles[-3]["low"]
    bos_up, bos_down = last_high > prev_high + MIN_BOS_DISTANCE, last_low < prev_low - MIN_BOS_DISTANCE

    valid_ob = any(
        ob["volume"] > MIN_OB_VOLUME and abs(ob["close"] - ob["open"]) >= 0.1 * (ob["high"] - ob["low"])
        for ob in candles[-5:-2]
    )

    last, prev = candles[-1], candles[-2]
    volume_spike = volumes[-1] > 1.5 * sum(volumes[-5:-1]) / 4
    if mtf_bull and bos_up and valid_ob and last["low"] <= min(ema9, ema21) and last["close"] > max(last["open"], prev["close"]) and volume_spike:
        entry, sl = last["high"], last["low"] - atr * 0.5
        tp = entry + RISK_REWARD_RATIO * (entry - sl)
        return {"direction": "BUY", "entry": entry, "sl": sl, "tp": tp,
                "time": last["time"], "timestamp": datetime.now(timezone.utc).isoformat(),
                "setup": {"bos": candles[-3], "entry_candle": last}}

    if mtf_bear and bos_down and valid_ob and last["high"] >= max(ema9, ema21) and last["close"] < min(last["open"], prev["close"]) and volume_spike:
        entry, sl = last["low"], last["high"] + atr * 0.5
        tp = entry - RISK_REWARD_RATIO * (sl - entry)
        return {"direction": "SELL", "entry": entry, "sl": sl, "tp": tp,
                "time": last["time"], "timestamp": datetime.now(timezone.utc).isoformat(),
                "setup": {"bos": candles[-3], "entry_candle": last}}

    print("⚠️ Strategy conditions not met.")
    return None

# === Signal Tracker ===
def is_duplicate_signal(signal):
    try:
        with open("last_signal.json", "r") as f:
            last = json.load(f)
            return all(last.get(k) == signal.get(k) for k in ["entry", "sl", "tp", "direction"])
    except:
        return False

def save_trade_result(signal, votes, caption):
    try:
        with open("trade_history.json", "r") as f:
            history = json.load(f)
    except:
        history = []
    signal["votes"] = votes
    signal["caption"] = caption
    signal["outcome"] = "PENDING"
    signal["logged_at"] = datetime.now(timezone.utc).isoformat()
    history.append(signal)
    with open("trade_history.json", "w") as f:
        json.dump(history, f, indent=2)

# === Main ===
def main():
    print("📡 Starting AI engine...")
    candles = fetch_candles(SYMBOL, TIMEFRAME)
    if not candles:
        print("❌ No candles fetched.")
        return

    signal = detect_trade(candles)
    if not signal:
        print("❌ No valid trade setup detected.")
        return

    capture_chart_screenshot()
    caption = blip2_caption("screenshot.png")
    vote1 = cohere_decision(caption)
    vote2 = deepshik_vote(signal)
    vote3 = donut_decision("screenshot.png")
    votes = {"cohere": vote1, "deepshik": vote2, "donut": vote3}

    print("📌 Signal Candidate:", json.dumps(signal, indent=2))
    print(f"🧠 Caption: {caption}")
    print(f"🤖 Votes: {votes}")

    if list(votes.values()).count("YES") >= 2:
        if is_duplicate_signal(signal):
            print("🔁 Duplicate signal.")
            return
        with open("last_signal.json", "w") as f:
            json.dump(signal, f, indent=2)
        save_trade_result(signal, votes, caption)
        print("✅ Trade signal confirmed and saved.")
    else:
        save_trade_result(signal, votes, caption)
        print("❌ Rejected by AI.")

if __name__ == "__main__":
    main()
