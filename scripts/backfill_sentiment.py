import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from calculate_ma import calculate_all_ma

DATA_FILE = "data/history.json"
TICKERS = ["^VIX", "^VIX3M", "^SKEW"]

def parse_date(d_str):
    try:
        parts = d_str.strip().split('/')
        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except:
        return None

def backfill_sentiment():
    # 1. Load history
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    if not history:
        print("No history found to update.")
        return

    # 2. Download history from Yahoo Finance
    print(f"Downloading historical data for {TICKERS}...")
    try:
        # Download 2 years to cover all historical records
        df = yf.download(TICKERS, period="2y", interval="1d")['Close']
    except Exception as e:
        print(f"Error downloading from Yahoo Finance: {e}")
        return

    # Map dates to row data
    # yfinance returns datetime index. Convert index to YYYY/M/D string
    df.index = df.index.map(lambda x: f"{x.year}/{x.month}/{x.day}")
    
    history_dict = {r['Date']: r for r in history}
    
    updated_count = 0
    
    # We need to handle potential missing business days match
    for date_str, row in df.iterrows():
        if date_str not in history_dict:
            continue
            
        record = history_dict[date_str]
        
        try:
            # VIX3M
            if not pd.isna(row['^VIX3M']):
                record["VIX3M"] = round(float(row['^VIX3M']), 2)
            
            # SKEW
            if not pd.isna(row['^SKEW']):
                record["SKEW"] = round(float(row['^SKEW']), 2)
                
            # Ratio
            if not pd.isna(row['^VIX']) and not pd.isna(row['^VIX3M']):
                record["VIX/VIX3M Ratio"] = round(float(row['^VIX']) / float(row['^VIX3M']), 4)
                
            updated_count += 1
        except Exception as e:
            print(f"Error calculating for {date_str}: {e}")

    # Sort history
    history.sort(key=lambda x: parse_date(x['Date']))

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"Sentiment Backfill Complete: Updated {updated_count} days.")
    
    # Recalculate MA
    calculate_all_ma()

if __name__ == "__main__":
    backfill_sentiment()
