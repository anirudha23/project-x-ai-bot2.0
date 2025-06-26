from keep_alive import keep_alive
import threading
import subprocess
import time

# Start the Flask keep-alive server
keep_alive()

# Function to run scheduler
def run_scheduler():
    print("📅 Starting Project-X scheduler loop...")
    while True:
        print("⏱️ Triggering strategy engine: ai_engine.py")
        try:
            result = subprocess.run(["python3", "ai_engine.py"], capture_output=True, text=True)
            print(result.stdout)
            if result.stderr:
                print("❌ Error in ai_engine.py:", result.stderr)
        except Exception as e:
            print("❌ Exception in scheduler:", e)

        time.sleep(300)  # Run every 5 minutes

# Run the scheduler in background
threading.Thread(target=run_scheduler).start()
