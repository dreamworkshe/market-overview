import json
import os
import yfinance as yf
import pandas as pd
from datetime import datetime
from calculate_ma import calculate_all_ma
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

DATA_FILE = "data/history.json"
TICKERS = ["^TNX", "^IRX", "GC=F", "HG=F", "HYG", "LQD", "XLY", "XLP", "KBE", "SPY", "QQQ", "RSP", "IEF", "DX-Y.NYB", "TLT"]

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
        df = yf.download(TICKERS, period="2y", interval="1d")['Close']
    except Exception as e:
        print(f"Error downloading from Yahoo Finance: {e}")
        return

    df.index = df.index.map(lambda x: f"{x.year}/{x.month}/{x.day}")
    history_dict = {r['Date']: r for r in history}
    updated_count = 0
    
    for date_str, row in df.iterrows():
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
                
            # QQQ/SPY
            if not pd.isna(row['QQQ']) and not pd.isna(row['SPY']):
                record["QQQ/SPY Ratio"] = round(float(row['QQQ']) / float(row['SPY']), 4)
                
            # RSP/SPY
            if not pd.isna(row['RSP']) and not pd.isna(row['SPY']):
                record["RSP/SPY Ratio"] = round(float(row['RSP']) / float(row['SPY']), 4)
                
            # HYG/IEF
            if not pd.isna(row['HYG']) and not pd.isna(row['IEF']):
                record["HYG/IEF Ratio"] = round(float(row['HYG']) / float(row['IEF']), 4)

            # DXY
            if 'DX-Y.NYB' in row and not pd.isna(row['DX-Y.NYB']):
                record["DXY"] = round(float(row['DX-Y.NYB']), 2)
                
            # TLT
            if 'TLT' in row and not pd.isna(row['TLT']):
                record["TLT"] = round(float(row['TLT']), 2)
                
            updated_count += 1
        except Exception as e:
            print(f"Error calculating for {date_str}: {e}")

    # 3. Backfill HY OAS, Fed Liquidity from FRED
    if FRED_KEY:
        print("Backfilling FRED data (HY OAS, Liquidity)...")
        try:
            fred = Fred(api_key=FRED_KEY)
            # WALCL (Weekly), RRPONTSYD, WTREGEN
            walcl = fred.get_series('WALCL')
            rrp = fred.get_series('RRPONTSYD')
            tga = fred.get_series('WTREGEN')
            hy_oas = fred.get_series('BAMLH0A0HYM2')

            for date_obj, val in hy_oas.items():
                d_str = f"{date_obj.year}/{date_obj.month}/{date_obj.day}"
                if d_str in history_dict and not pd.isna(val):
                    history_dict[d_str]["HY OAS"] = round(float(val), 2)

            # For liquidity, we need to interpolate or just match
            for d_str, record in history_dict.items():
                dt = parse_date(d_str)
                if not dt: continue
                # Match closest or exact
                try:
                    assets = walcl.asof(dt)
                    r_val = rrp.asof(dt)
                    t_val = tga.asof(dt)
                    if not pd.isna(assets) and not pd.isna(r_val) and not pd.isna(t_val):
                        liqv = round((assets / 1000.0) - r_val - t_val, 2)
                        record["Fed Liquidity"] = liqv
                        record["RRP"] = round(float(r_val), 2)
                        record["TGA"] = round(float(t_val), 2)
                except:
                    pass
        except Exception as e:
            print(f"Error FRED backfill: {e}")

    history.sort(key=lambda x: parse_date(x['Date']))

    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"Macro Backfill Complete: Updated {updated_count} days.")
    calculate_all_ma()

if __name__ == "__main__":
    backfill_macro()
