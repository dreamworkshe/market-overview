import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from calculate_ma import calculate_all_ma

DATA_FILE = "data/history.json"

TICKERS = ["^TNX", "^IRX", "GC=F", "HG=F", "HYG", "LQD", "XLY", "XLP", "KBE", "SPY"]

def parse_date(d_str):
    try:
        parts = d_str.strip().split('/')
        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except:
        return None

def backfill_macro():
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
    print(f"Downloading historical data for {len(TICKERS)} tickers...")
    try:
        # Download last 60 days to ensure enough data for 30 business days
        data = yf.download(TICKERS, period="60d", interval="1d")['Close']
    except Exception as e:
        print(f"Error downloading from Yahoo Finance: {e}")
        return

    # Map dates to row data
    # yfinance returns datetime index. Convert index to YYYY/M/D string
    data.index = data.index.map(lambda x: f"{x.year}/{x.month}/{x.day}")
    
    history_dict = {r['Date']: r for r in history}
    
    updated_count = 0
    
    for date_str, row in data.iterrows():
        if date_str not in history_dict:
            continue
            
        record = history_dict[date_str]
        
        try:
            # 10Y-3M Spread
            if not pd.isna(row['^TNX']) and not pd.isna(row['^IRX']):
                record["10Y-3M Spread"] = round(float(row['^TNX']) - float(row['^IRX']), 3)
            
            # Copper/Gold
            if not pd.isna(row['HG=F']) and not pd.isna(row['GC=F']):
                record["Copper/Gold Ratio"] = round(float(row['HG=F']) / float(row['GC=F']), 4)
                
            # HYG/LQD
            if not pd.isna(row['HYG']) and not pd.isna(row['LQD']):
                record["HYG/LQD Ratio"] = round(float(row['HYG']) / float(row['LQD']), 4)
                
            # XLY/XLP
            if not pd.isna(row['XLY']) and not pd.isna(row['XLP']):
                record["XLY/XLP Ratio"] = round(float(row['XLY']) / float(row['XLP']), 4)
                
            # KBE/SPY
            if not pd.isna(row['KBE']) and not pd.isna(row['SPY']):
                record["KBE/SPY Ratio"] = round(float(row['KBE']) / float(row['SPY']), 4)
                
            updated_count += 1
        except Exception as e:
            print(f"Error calculating for {date_str}: {e}")

    history.sort(key=lambda x: parse_date(x['Date']))

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"Macro Backfill Complete: Updated {updated_count} days.")
    
    # Recalculate MA
    calculate_all_ma()

if __name__ == "__main__":
    backfill_macro()
