import time
import json
from send_signal import send_signal_to_discord

def read_last_signal():
    try:
        with open("last_signal.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

previous_signal = None

while True:
    current_signal = read_last_signal()
    if current_signal != previous_signal:
        print("📡 New signal detected. Sending to Discord...")
        send_signal_to_discord()
        previous_signal = current_signal
    else:
        print("🔁 No new signal. Waiting 5 minutes...")

    time.sleep(300)  # wait 5 min
