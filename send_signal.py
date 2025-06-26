import requests
import json
import os
import time  # ✅ Add this

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def send_signal_to_discord():
    with open("last_signal.json", "r") as f:
        signal_data = json.load(f)

    message = f"""
📡 **Project X Signal – {signal_data['symbol']} ({signal_data['timeframe']})**

**Direction:** {signal_data['direction']}  
**Entry:** {signal_data['entry']}  
**Stoploss:** {signal_data['sl']}  
**Take Profit:** {signal_data['tp']}  
**Vote Count:** {signal_data['votes']}

🧠 **AI Votes:**  
• ChatGPT: {signal_data['chatgpt']}  
• Grok: {signal_data['grok']}  
• Deepshik: {signal_data['deepshik']}  
"""

    payload = {"content": message}
    headers = {"Content-Type": "application/json"}

    time.sleep(10)  # ✅ Delay to avoid rate limit

    response = requests.post(WEBHOOK_URL,
                             data=json.dumps(payload),
                             headers=headers)

    if response.status_code == 204:
        print("✅ Signal sent successfully!")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
