import requests
import json
import os
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

DATA_FILE = "data/history.json"

def get_cnn_history(start_date="2024-01-01"):
    url = f"https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start_date}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        points = data['fear_and_greed_historical']['data']
        # points are list of {'x': timestamp, 'y': value}
        history = {}
        for p in points:
            date_str = datetime.fromtimestamp(p['x']/1000).strftime("%Y/%-m/%-d")
            history[date_str] = round(p['y'], 2)
        return history
    except Exception as e:
        print(f"Error CNN History: {e}")
        return {}

def get_vix_history(days=730):
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period=f"{days}d")
        history = {}
        for idx, row in hist.iterrows():
            date_str = idx.strftime("%Y/%-m/%-d")
            history[date_str] = round(float(row['Close']), 2)
        return history
    except Exception as e:
        print(f"Error VIX History: {e}")
        return {}

def get_naaim_history():
    url = "https://www.naaim.org/wp-content/uploads/2026/03/NAAIM-Exposure-Index-Data-2026-03-04.xlsx"
    # Note: Filename might change. Let's try to find it on the page.
    # For now, I'll try to use a placeholder or search for it.
    # Alternatively, I can use a hardcoded small list or skip if not found.
    # Let's try to scrape the page for the xlsx link.
    try:
        page = requests.get("https://www.naaim.org/programs/naaim-exposure-index/", headers={"User-Agent": "Mozilla/5.0"})
        import re
        match = re.search(r'href="(.*?\.xlsx)"', page.text)
        if match:
            xlsx_url = match.group(1)
            df = pd.read_excel(xlsx_url)
            # NAAIM excel usually has columns: Date, NAAIM Exposure Index, etc.
            # We need to find columns. Usually 'Date' and 'Average / Mean'
            history = {}
            for _, row in df.iterrows():
                try:
                    d = row.iloc[0] # date
                    v = row.iloc[1] # index
                    if isinstance(d, datetime):
                        date_str = d.strftime("%Y/%-m/%-d")
                        history[date_str] = round(float(v), 2)
                except:
                    continue
            return history
    except Exception as e:
        print(f"Error NAAIM History: {e}")
    return {}

def main():
    print("Fetching historical data...")
    cnn_hist = get_cnn_history()
    vix_hist = get_vix_history()
    naaim_hist = get_naaim_history()

    # Combine into history.json
    # We'll use CNN dates as the primary timeline
    all_dates = sorted(set(list(cnn_hist.keys()) + list(vix_hist.keys())))
    
    merged = []
    for d in all_dates:
        record = {
            "Date": d,
            "CNN": cnn_hist.get(d),
            "VIX": vix_hist.get(d),
            "NAAIM": naaim_hist.get(d),
            # Others we might not have bulk history for for free
            "Total P/C Ratio": None,
            "Equity P/C Ratio": None,
            "AAII B-B": None,
            "NYSE above 20MA": None,
            "NASDAQ above 20MA": None,
            "NYSE above 50MA": None,
            "NASDAQ above 50MA": None
        }
        merged.append(record)

    # Save
    if not os.path.exists("data"):
        os.makedirs("data")
        
    with open(DATA_FILE, 'w') as f:
        json.dump(merged, f, indent=2)
    
    print(f"Imported {len(merged)} historical records.")

if __name__ == "__main__":
    main()
