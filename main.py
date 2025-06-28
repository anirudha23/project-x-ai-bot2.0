from keep_alive import keep_alive
import threading
import subprocess
import json
import time

previous_signal = None

def read_last_signal():
    try:
        with open("last_signal.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def run_scheduler():
    global previous_signal
    print("\U0001F4C5 Starting Project-X scheduler loop...")
    while True:
        print("⏱️ Running ai_engine.py...")
        try:
            subprocess.run(["python3", "ai_engine.py"], check=True)
        except Exception as e:
            print("❌ ai_engine.py failed:", e)

        current_signal = read_last_signal()
        if current_signal != previous_signal:
            print("📡 New signal detected. Sending to Discord...")
            try:
                subprocess.run(["python3", "send_signal.py"], check=True)
            except Exception as e:
                print("❌ send_signal.py failed:", e)
            previous_signal = current_signal
        else:
            print("🔁 No new signal. Waiting...")

        time.sleep(300)

# Start Flask server
keep_alive()

# Run background scheduler
threading.Thread(target=run_scheduler).start()
