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
    current_signal = read_last_signal()

    if current_signal != previous_signal:
        print("📡 New signal detected. Sending to Discord via bot...")

        try:
            # Call the bot as a subprocess
            result = subprocess.run(["python3", "send_signal.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("❌ Error:", result.stderr)
        except Exception as e:
            print("❌ Subprocess failed:", str(e))

        previous_signal = current_signal
    else:
        print("🔁 No new signal. Waiting 5 minutes...")

    time.sleep(300)  # 5 minutes
