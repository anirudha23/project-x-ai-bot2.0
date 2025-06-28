import json
from collections import defaultdict
import os

TRADE_HISTORY_PATH = "trade_history.json"

def load_trade_history():
    if not os.path.exists(TRADE_HISTORY_PATH):
        return []

    with open(TRADE_HISTORY_PATH, "r") as f:
        try:
            return json.load(f)
        except:
            return []

def analyze_ai_performance():
    history = load_trade_history()
    ai_stats = defaultdict(lambda: {"TP HIT": 0, "SL HIT": 0, "Total": 0})

    for trade in history:
        outcome = trade.get("outcome")
        if outcome not in ["TP HIT", "SL HIT"]:
            continue

        for ai in ["cohere", "deepshik", "donut"]:
            ai_vote = trade.get("votes", {}).get(ai, "").upper()
            if ai_vote == "YES":
                ai_stats[ai][outcome] += 1
                ai_stats[ai]["Total"] += 1

    ai_weights = {}
    for ai, stats in ai_stats.items():
        total = stats["Total"]
        tp = stats["TP HIT"]
        ai_weights[ai] = round(tp / total, 2) if total else 0.5

    return ai_weights

if __name__ == "__main__":
    memory = analyze_ai_performance()
    print("📈 AI Learning Memory:")
    for ai, weight in memory.items():
        print(f"{ai}: {weight * 100}% TP success rate")
