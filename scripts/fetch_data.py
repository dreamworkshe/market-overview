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
        # New pattern: <span style="font-size: 65px; color: #11317d;">79.29</span>
        match = re.search(r'color:\s*#11317d;">([\d\.]+)', response.text)
        if match:
            return float(match.group(1))
        # Fallback
        match = re.search(r'Exposure Index:\s*([\d\.]+)', response.text)
        if match:
            return float(match.group(1))
    except Exception as e:
        print(f"Error NAAIM: {e}")
    return None

def fetch_aaii():
    url = "https://www.aaii.com/sentimentsurvey"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        # Look for the latest bullish and bearish numbers in the historical table
        # Searching for the first table row containing percentages
        match_bull = re.search(r'([\d\.]+)%</td>\s*<td[^>]*>[\d\.]+%</td>\s*<td[^>]*>([\d\.]+)%', response.text)
        if match_bull:
            bull = float(match_bull.group(1))
            bear = float(match_bull.group(2))
            return round(bull - bear, 2)
    except Exception as e:
        print(f"Error AAII: {e}")
    return None

def fetch_put_call():
    # Attempt to scrape the CBOE Daily Market Statistics page directly as CSV is often blocked
    url = "https://www.cboe.com/us/options/market_statistics/daily/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            # TOTAL PUT/CALL RATIO 0.96
            total_match = re.search(r'TOTAL PUT/CALL RATIO\s+([\d\.]+)', response.text, re.IGNORECASE)
            # EQUITY PUT/CALL RATIO 0.67
            equity_match = re.search(r'EQUITY PUT/CALL RATIO\s+([\d\.]+)', response.text, re.IGNORECASE)
            if total_match and equity_match:
                return float(total_match.group(1)), float(equity_match.group(1))
    except Exception as e:
        print(f"Error CBOE scraping: {e}")
    
    # Fallback to the original CSV method
    today = datetime.now()
    for i in range(5):
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
    
    # Modern headers to avoid bot detection
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # Regex search for current price which is marked as "Last: 29.88" in the chart legend data
        match = re.search(r'Last:\s*(-?[\d\.]+)', response.text)
        if match:
            return float(match.group(1))
        
        # Alternative meta tag meta description "$NYA50R - ...: 50.35"
        match = re.search(r'description" content="[^:]+:\s*(-?[\d\.]+)', response.text)
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
        # Metals & Rates: 10Y (^TNX), 3M (^IRX), Gold (GC=F), Copper (HG=F)
        # Sector Ratios: HYG (High Yield), LQD (Inv. Grade), XLY (Disc.), XLP (Staples), KBE (Banks), SPY (S&P 500)
        tickers_str = "^TNX ^IRX GC=F HG=F HYG LQD XLY XLP KBE SPY"
        tickers = yf.Tickers(tickers_str)
        prices = {}
        for t in tickers_str.split():
            hist = tickers.tickers[t].history(period="1d")
            if not hist.empty:
                prices[t] = hist['Close'].iloc[-1]
            else:
                return None, None, None, None, None
        
        # Calculate Ratios
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
    spread, cg_ratio, hyg_lqd, xly_xlp, kbe_spy = fetch_macro_data()
    results["10Y-3M Spread"] = spread
    results["Copper/Gold Ratio"] = cg_ratio
    results["HYG/LQD Ratio"] = hyg_lqd
    results["XLY/XLP Ratio"] = xly_xlp
    results["KBE/SPY Ratio"] = kbe_spy
    
    if "Gold/Silver Ratio" in results:
        del results["Gold/Silver Ratio"]


    dix_data = fetch_dix()
    results["DIX"] = dix_data["DIX"]
    results["GEX"] = dix_data["GEX"]

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
