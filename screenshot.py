from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import shutil
import time
import sys

def capture_chart_screenshot():
    chart_url = "https://in.tradingview.com/chart/vS5KLHQC/?symbol=BITSTAMP:BTCUSD"

    # Detect Chromium path
    chrome_path = shutil.which("chromium-browser") or shutil.which("chromium")
    if chrome_path is None:
        print("❌ Chromium not found on system.")
        sys.exit(1)

    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280,720")

    # Use the system-installed Chromium driver directly
    driver = webdriver.Chrome(options=options)

    try:
        print("🌐 Loading TradingView chart...")
        driver.get(chart_url)
        time.sleep(10)  # Wait for chart to load
        driver.save_screenshot("screenshot.png")
        print("📸 Screenshot captured and saved as screenshot.png")
    except Exception as e:
        print("❌ Screenshot failed:", e)
    finally:
        driver.quit()
