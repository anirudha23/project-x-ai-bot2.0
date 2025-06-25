import json
from collections import defaultdict
import os

TRADE_HISTORY_PATH = "trade_history.json"

# AI memory module that learns accuracy of each AI

def load_trade_history():
    if not os.path.exists(TRADE_HISTORY_PATH):
        return []

    with open(TRADE_HISTORY_PATH, "r") as f:
        raw = f.read().strip().rstrip(",")
        if not raw:
            return []
        json_data = json.loads("[" + raw + "]")
        return json_data

def analyze_ai_performance():
    history = load_trade_history()
    ai_stats = defaultdict(lambda: {"TP HIT": 0, "SL HIT": 0, "Total": 0})

    for trade in history:
        outcome = trade.get("outcome")
        if outcome not in ["TP HIT", "SL HIT"]:
            continue

        for ai in ["chatgpt", "grok", "deepshik"]:
            ai_vote = trade.get(ai, "").upper()
            if "YES" in ai_vote:
                ai_name = ai.capitalize()
                ai_stats[ai_name][outcome] += 1
                ai_stats[ai_name]["Total"] += 1

    # Calculate accuracy weight
    ai_weights = {}
    for ai, stats in ai_stats.items():
        total = stats["Total"]
        tp = stats["TP HIT"]
        if total == 0:
            ai_weights[ai] = 0.5  # neutral weight
        else:
            ai_weights[ai] = round(tp / total, 2)

    return ai_weights

if __name__ == "__main__":
    memory = analyze_ai_performance()
    print("📈 AI Learning Memory:")
    for ai, weight in memory.items():
        print(f"{ai}: {weight * 100}% TP success rate")
