import time
import json
import subprocess

def read_last_signal():
    try:
        with open("last_signal.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

previous_signal = None

while True:
    print("⏱️ Scheduler loop running...")
    print("🧠 Running AI strategy engine...")
    try:
        result = subprocess.run(["python3", "ai_engine.py"], capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("⚠️ AI Engine Error:", result.stderr)
    except Exception as e:
        print("❌ Failed to run ai_engine.py:", str(e))

    current_signal = read_last_signal()

    if current_signal != previous_signal:
        print("📡 New signal detected. Sending to Discord via bot...")

        try:
            result = subprocess.run(["python3", "send_signal.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("❌ Bot Send Error:", result.stderr)
        except Exception as e:
            print("❌ Failed to run send_signal.py:", str(e))

        previous_signal = current_signal
    else:
        print("🔁 No new signal. Waiting 5 minutes...")

    time.sleep(300)  # Wait 5 min
