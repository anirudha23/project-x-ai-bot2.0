from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import shutil
import sys

def capture_chart_screenshot():
    chart_url = "https://in.tradingview.com/chart/vS5KLHQC/?symbol=BITSTAMP:BTCUSD"  # your actual chart

    chrome_path = shutil.which("chromium-browser") or shutil.which("chromium")
    if chrome_path is None:
        print("❌ Chromium not found on system.")
        sys.exit(1)

    options = Options()
    options.binary_location = chrome_path
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1280x720")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    print("🌐 Loading TradingView chart...")
    driver.get(chart_url)
    driver.implicitly_wait(10)  # Wait to ensure chart loads
    driver.save_screenshot("screenshot.png")
    driver.quit()

    print("📸 Screenshot captured and saved as screenshot.png")
