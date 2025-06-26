from keep_alive import keep_alive
import threading
import subprocess

# Start the Flask keep-alive server
keep_alive()

# Function to run scheduler
def run_scheduler():
    subprocess.call(["python3", "scheduler.py"])

# Run the scheduler in background
threading.Thread(target=run_scheduler).start()
