import requests
import json
import os
import re
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
from bs4 import BeautifulSoup

DATA_FILE = "data/history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

def fetch_cnn_fg():
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
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
            return round(hist['Close'].iloc[-1], 2)
    except Exception as e:
        print(f"Error VIX: {e}")
    return None

def fetch_naaim():
    url = "https://www.naaim.org/programs/naaim-exposure-index/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        # Look for the numeric value in the text
        # Usually: "The NAAIM Exposure Index for the period ending ... is 74.93."
        match = re.search(r'Exposure Index:\s*([\d\.]+)', response.text)
        if match:
            return float(match.group(1))
        # Fallback to a broader search
        match = re.search(r'is\s+([\d\.]+)\.', response.text)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"Error NAAIM: {e}")
    return None

def fetch_aaii():
    url = "https://www.aaii.com/sentimentsurvey"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        bull = re.search(r'Bullish:\s*([\d\.]+)%', response.text)
        bear = re.search(r'Bearish:\s*([\d\.]+)%', response.text)
        if bull and bear:
            return round(float(bull.group(1)) - float(bear.group(1)), 2)
    except Exception as e:
        print(f"Error AAII: {e}")
    return None

def fetch_put_call():
    # CBOE official daily stats
    today = datetime.now()
    for i in range(5): # Try last 5 days
        date_str = (today - timedelta(i)).strftime("%Y-%m-%d")
        url = f"https://cdn.cboe.com/data/us/options/market_statistics/daily_market_statistics/Daily_Market_Statistics_{date_str}.csv"
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                import io
                df = pd.read_csv(io.StringIO(response.text))
                total_pc = df[df['Description'].str.contains('Total Put/Call Ratio', na=False, case=False)]['Ratio'].iloc[0]
                equity_pc = df[df['Description'].str.contains('Equity Put/Call Ratio', na=False, case=False)]['Ratio'].iloc[0]
                return round(float(total_pc), 2), round(float(equity_pc), 2)
        except:
            continue
    return None, None

def fetch_breadth_single(symbol):
    """Scrape StockCharts for a breadth symbol score."""
    # Symbols: $NYA20R, $NYA50R, $NAA20R, $NAA50R
    url = f"https://stockcharts.com/h-sc/ui?s={symbol}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        # Look for the price in the meta tags or script
        # Example: <meta name="description" content="$NYA50R - NYSE stocks above 50-day MA: 50.35">
        match = re.search(r'([\$A-Z0-9]+)\s*:\s*([\d\.]+)', response.text)
        if match:
            return float(match.group(2))
        # Regex search for current price in the chart data or summary
        match = re.search(r'Last:\s*(\d+\.\d+)', response.text)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"Error Breadth {symbol}: {e}")
    return None

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

def fetch_mcclellan():
    return fetch_breadth_single("%24NYMOT")

def fetch_crypto_fg():
    url = "https://api.alternative.me/fng/"
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return int(data['data'][0]['value'])
    except Exception as e:
        print(f"Error fetching Crypto F&G: {e}")
        return None

def fetch_macro_data():
    try:
        # 10Y (^TNX), 3M (^IRX), Gold (GC=F), Silver (SI=F)
        tickers = yf.Tickers("^TNX ^IRX GC=F SI=F")
        prices = {}
        for t in ["^TNX", "^IRX", "GC=F", "SI=F"]:
            p = tickers.tickers[t].history(period="1d")['Close'].iloc[-1]
            prices[t] = p
        
        # Calculate Spread and Ratio
        spread = round(prices["^TNX"] - prices["^IRX"], 3)
        gs_ratio = round(prices["GC=F"] / prices["SI=F"], 2)
        return spread, gs_ratio
    except Exception as e:
        print(f"Error fetching Macro data: {e}")
        return None, None

def main():
    # Use US/New_York time for consistency with market trading days
    from datetime import timezone
    # US Eastern Time is UTC-5 (Standard) or UTC-4 (Daylight)
    # Simple manual offset for now, or use pytz
    ny_now = datetime.now(timezone.utc) - timedelta(hours=5) 
    date_str = ny_now.strftime("%Y/%-m/%-d")
    
    results = {
        "Date": date_str,
        "CNN": fetch_cnn_fg(),
        "VIX": fetch_vix(),
        "NAAIM": fetch_naaim(),
        "AAII B-B": fetch_aaii()
    }
    
    total_pc, equity_pc = fetch_put_call()
    results["Total P/C Ratio"] = total_pc
    results["Equity P/C Ratio"] = equity_pc
    
    results["NYSE above 20MA"] = fetch_breadth_single("%24NYA20R")
    results["NASDAQ above 20MA"] = fetch_breadth_single("%24NAA20R")
    results["NYSE above 50MA"] = fetch_breadth_single("%24NYA50R")
    results["NASDAQ above 50MA"] = fetch_breadth_single("%24NAA50R")

    results["Crypto F&G"] = fetch_crypto_fg()
    spread, gs_ratio = fetch_macro_data()
    results["10Y-3M Spread"] = spread
    results["Gold/Silver Ratio"] = gs_ratio

    dix_data = fetch_dix()
    results["DIX"] = dix_data["DIX"]
    results["GEX"] = dix_data["GEX"]
    results["McClellan"] = fetch_mcclellan()

    print(f"Fetched: {results}")

    # Load and Update History
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []

    # Update or Append
    updated = False
    for i, r in enumerate(history):
        if r['Date'] == date_str:
            # Only update non-None values
            for k, v in results.items():
                if v is not None:
                    history[i][k] = v
            updated = True
            break
    
    if not updated:
        history.append(results)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    main()
