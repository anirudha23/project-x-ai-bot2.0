import undetected_chromedriver as uc
import time

def capture_chart_screenshot():
    chart_url = "https://in.tradingview.com/chart/vS5KLHQC/?symbol=BITSTAMP:BTCUSD"

    try:
        print("🌐 Launching undetected Chrome browser...")
        options = uc.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1280,720")

        driver = uc.Chrome(options=options)

        print("🌐 Loading TradingView chart...")
        driver.get(chart_url)
        time.sleep(10)  # Wait for full load

        driver.save_screenshot("screenshot.png")
        print("📸 Screenshot saved as screenshot.png")

    except Exception as e:
        print("❌ Screenshot failed:", e)

    finally:
        try:
            driver.quit()
        except:
            pass
