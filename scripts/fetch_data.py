import json
import os
import re
import time
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from playwright.sync_api import sync_playwright

DATA_FILE = "data/history.json"

def fetch_cnn_fg():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    import requests
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        return round(data['fear_and_greed']['score'], 2)
    except Exception as e:
        print(f"Error CNN F&G: {e}")
        return None

def fetch_vix():
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="1d")
        if not hist.empty:
            return round(float(hist['Close'].iloc[-1]), 2)
    except Exception as e:
        print(f"Error VIX: {e}")
    return None

def fetch_playwright_data():
    """Fetch NAAIM, AAII, CBOE, and StockCharts using reinforced Playwright."""
    results = {
        "NAAIM": None,
        "AAII B-B": None,
        "Total P/C Ratio": None,
        "Equity P/C Ratio": None,
        "NYSE above 20MA": None,
        "NASDAQ above 20MA": None,
        "NYSE above 50MA": None,
        "NASDAQ above 50MA": None
    }
    
    with sync_playwright() as p:
        # Added sandbox flags for better GitHub Actions stability
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        
        # Emulate a more realistic desktop browser
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            device_scale_factor=1,
        )
        page = context.new_page()

        # 1. NAAIM
        try:
            page.goto("https://www.naaim.org/programs/naaim-exposure-index/", wait_until="domcontentloaded", timeout=40000)
            time.sleep(5) # Direct wait for JS data to settle
            content = page.content()
            # Try finding the large number directly in text if selector fails
            match = re.search(r'color:\s*#11317d;">\s*([\d\.]+)', content)
            if match:
                results["NAAIM"] = float(match.group(1))
            else:
                # Fallback search for any exposure number
                match = re.search(r'Exposure Index Number is[\*\s:]+([\d\.]+)', page.inner_text("body"), re.IGNORECASE)
                if match: results["NAAIM"] = float(match.group(1))
        except Exception as e:
            print(f"Error NAAIM: {e}")

        # 2. AAII
        try:
            page.goto("https://www.aaii.com/sentimentsurvey", wait_until="domcontentloaded", timeout=40000)
            time.sleep(5)
            content = page.content()
            # Robust table parsing
            match = re.search(r'([\d\.]+)%</td>\s*<td[^>]*>[\d\.]+%</td>\s*<td[^>]*>([\d\.]+)%', content)
            if match:
                results["AAII B-B"] = round(float(match.group(1)) - float(match.group(2)), 2)
        except Exception as e:
            print(f"Error AAII: {e}")

        # 3. CBOE Put/Call
        try:
            page.goto("https://www.cboe.com/us/options/market_statistics/daily/", wait_until="domcontentloaded", timeout=40000)
            time.sleep(8) # CBOE is heavy
            content = page.content()
            total_match = re.search(r'TOTAL PUT/CALL RATIO[^\d]*([\d\.]+)', content, re.IGNORECASE)
            equity_match = re.search(r'EQUITY PUT/CALL RATIO[^\d]*([\d\.]+)', content, re.IGNORECASE)
            if total_match: results["Total P/C Ratio"] = float(total_match.group(1))
            if equity_match: results["Equity P/C Ratio"] = float(equity_match.group(1))
        except Exception as e:
            print(f"Error CBOE: {e}")

        # 4. StockCharts Breadth
        symbols = {
            "NYSE above 20MA": "%24NYA20R",
            "NASDAQ above 20MA": "%24NAA20R",
            "NYSE above 50MA": "%24NYA50R",
            "NASDAQ above 50MA": "%24NAA50R"
        }
        for label, sym in symbols.items():
            try:
                # Use Sc3 UI which is sometimes more stable or fallback if Sc2 blocked
                page.goto(f"https://stockcharts.com/h-sc/ui?s={sym}", wait_until="domcontentloaded", timeout=40000)
                time.sleep(5) # Wait for Canvas/JS to plot
                content = page.content()
                # Search for "Last: 33.12" in the entire raw HTML
                match = re.search(r'Last:\s*(-?[\d\.]+)', content)
                if match:
                    results[label] = float(match.group(1))
                else:
                    # Alternative search in meta tag description
                    match = re.search(r'content="[^"]+:\s*(-?[\d\.]+)" name="description"', content)
                    if match: results[label] = float(match.group(1))
                    else: print(f"Warning: {label} ({sym}) parsed partially, Title: {page.title()}")
            except Exception as e:
                print(f"Error Breadth {label}: {e}")

        browser.close()
    return results

def fetch_dix():
    url = "https://squeezemetrics.com/monitor/static/DIX.csv"
    try:
        df = pd.read_csv(url)
        latest = df.iloc[-1]
        return {
            "DIX": round(float(latest['dix']) * 100, 2),
            "GEX": round(float(latest['gex']) / 1e9, 2)
        }
    except Exception as e:
        print(f"Error DIX: {e}")
        return {"DIX": None, "GEX": None}

def fetch_crypto_fg():
    url = "https://api.alternative.me/fng/"
    import requests
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return int(data['data'][0]['value'])
    except Exception as e:
        print(f"Error fetching Crypto F&G: {e}")
        return None

def fetch_macro_data():
    try:
        tickers_str = "^TNX ^IRX GC=F HG=F HYG LQD XLY XLP KBE SPY"
        tickers = yf.Tickers(tickers_str)
        prices = {}
        for t in tickers_str.split():
            hist = tickers.tickers[t].history(period="1d")
            if not hist.empty:
                prices[t] = hist['Close'].iloc[-1]
            else:
                return None, None, None, None, None
        
        spread = round(prices["^TNX"] - prices["^IRX"], 3)
        cg_ratio = round(prices["HG=F"] / prices["GC=F"], 4)
        hyg_lqd = round(prices["HYG"] / prices["LQD"], 4)
        xly_xlp = round(prices["XLY"] / prices["XLP"], 4)
        kbe_spy = round(prices["KBE"] / prices["SPY"], 4)
        
        return spread, cg_ratio, hyg_lqd, xly_xlp, kbe_spy
    except Exception as e:
        print(f"Error fetching Macro data: {e}")
        return None, None, None, None, None

def main():
    from datetime import timezone
    ny_now = datetime.now(timezone.utc) - timedelta(hours=5) 
    date_str = ny_now.strftime("%Y/%-m/%-d")
    
    # 1. Fetch Basic / Request-based data
    results = {
        "Date": date_str,
        "CNN": fetch_cnn_fg(),
        "VIX": fetch_vix(),
    }
    
    # 2. Fetch Selenium/Playwright-based data (Heavy)
    pw_results = fetch_playwright_data()
    results.update(pw_results)
    
    # 3. Fetch DIX/GEX
    dix_data = fetch_dix()
    results["DIX"] = dix_data["DIX"]
    results["GEX"] = dix_data["GEX"]

    # 4. Crypto & Macro
    results["Crypto F&G"] = fetch_crypto_fg()
    spread, cg_ratio, hyg_lqd, xly_xlp, kbe_spy = fetch_macro_data()
    results["10Y-3M Spread"] = spread
    results["Copper/Gold Ratio"] = cg_ratio
    results["HYG/LQD Ratio"] = hyg_lqd
    results["XLY/XLP Ratio"] = xly_xlp
    results["KBE/SPY Ratio"] = kbe_spy
    
    print(f"Fetched: {results}")

    # Load and Update History
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                history = json.load(f)
            print(f"Loaded existing history: {len(history)} entries")
        except Exception as e:
            print(f"Error loading {DATA_FILE}: {e}")
            history = []

    # Update or Append (Ensuring matched date format)
    updated = False
    for i, r in enumerate(history):
        if r['Date'] == date_str:
            print(f"Updating existing record for {date_str}")
            for k, v in results.items():
                if v is not None:
                    history[i][k] = v
            updated = True
            break
    
    if not updated:
        print(f"Adding new record for {date_str}")
        history.append(results)
    
    # Explicit Sync and Write
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        print(f"Successfully wrote {len(history)} records to {DATA_FILE}")
    except Exception as e:
        print(f"CRITICAL ERROR writing to {DATA_FILE}: {e}")

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    main()
