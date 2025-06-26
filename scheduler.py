# ✅ FILE: scheduler.py
import time
import json
import subprocess

def read_last_signal():
    try:
        with open("last_signal.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

print("📅 Starting Project-X scheduler loop...")

previous_signal = None

while True:
    print("⏱️ Triggering strategy engine: ai_engine.py")
    
    try:
        # Run AI engine to generate signal (if any)
        subprocess.run(["python3", "ai_engine.py"], check=True)
    except Exception as e:
        print(f"❌ Error running ai_engine: {e}")

    # Check if new signal exists
    current_signal = read_last_signal()
    if current_signal != previous_signal:
        print("📡 New signal detected. Sending to Discord via bot...")

        try:
            result = subprocess.run(["python3", "send_signal.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("❌ Error:", result.stderr)
        except Exception as e:
            print("❌ Subprocess failed:", str(e))

        previous_signal = current_signal
    else:
        print("🔁 No new signal. Waiting 5 minutes...")

    time.sleep(300)  # Wait 5 minutes
