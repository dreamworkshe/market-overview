import json
import os
import re
import time
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from calculate_ma import calculate_all_ma # Import MA calculation

DATA_FILE = "data/history.json"
GSHEET_ID = "18NLQo5n6Ni_NrMWuhIr9dUZFc57AKbxGVzK6M7V-FBg"

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

def fetch_vix(target_dt=None):
    try:
        vix = yf.Ticker("^VIX")
        if target_dt:
            start = target_dt.strftime('%Y-%m-%d')
            end = (target_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            hist = vix.history(start=start, end=end)
        else:
            hist = vix.history(period="1d")
            
        if not hist.empty:
            return round(float(hist['Close'].iloc[-1]), 2)
    except Exception as e:
        print(f"Error VIX: {e}")
    return None

def fetch_gsheet_data(target_date_str):
    """Fetch expert data from private Google Sheet using header-based mapping."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds_path = os.path.join(os.path.dirname(__file__), "..", "credentials.json")
    if not os.path.exists(creds_path):
        creds_path = "credentials.json" # Fallback
        
    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(GSHEET_ID)
        worksheet = sh.worksheet("Log")
        
        # Get all records
        all_data = worksheet.get_all_values()
        header = [h.strip() for h in all_data[0]] # Clean headers
        rows = all_data[1:]
        
        # Mapping: Column Name -> Index
        col_map = {name: i for i, name in enumerate(header)}
        
        # Find target row
        target_row = None
        found = False
        target_dt = datetime.strptime(target_date_str, "%Y/%m/%d") if "/" in target_date_str else None
        
        for row in reversed(rows):
            if not row or not row[0]: continue
            row_date_str = row[0].strip()
            # Try robust matching (handle leading zeros etc.)
            try:
                # Parse sheet date (supports YYYY/M/D or YYYY-M-D etc.)
                parts = re.split(r'[/-]', row_date_str)
                if len(parts) >= 3:
                    row_dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    if target_dt and row_dt.date() == target_dt.date():
                        target_row = row
                        found = True
                        break
            except:
                # Fallback to direct string match if parsing fails
                if row_date_str == target_date_str:
                    target_row = row
                    found = True
                    break
        
        if not found:
            print(f"Warning: Date {target_date_str} not found in Sheet.")
            return {}

        def get_val(col_name):
            if col_name not in col_map: return None
            val = target_row[col_map[col_name]]
            try: return float(val.replace('%', '').replace(',', '').strip())
            except: return None

        return {
            "Total P/C Ratio": get_val("Total P/C Ratio"),
            "Equity P/C Ratio": get_val("Equity P/C Ratio"),
            "NAAIM": get_val("NAAIM"),
            "AAII B-B": get_val("AAII B-B"),
            "NYSE above 20MA": get_val("NYSE above 20MA"),
            "NASDAQ above 20MA": get_val("NASDAQ above 20MA"),
            "NYSE above 50MA": get_val("NYSE above 50MA"),
            "NASDAQ above 50MA": get_val("NASDAQ above 50MA")
        }
    except Exception as e:
        print(f"Error fetching from Google Sheet: {e}")
        return {}

def fetch_dix(target_date_str=None):
    url = "https://squeezemetrics.com/monitor/static/DIX.csv"
    try:
        df = pd.read_csv(url)
        if target_date_str:
            # Match YYYY-MM-DD or YYYY-M-D
            target_dt = datetime.strptime(target_date_str, "%Y/%m/%d")
            df['parsed_date'] = pd.to_datetime(df['date'])
            match = df[df['parsed_date'].dt.date == target_dt.date()]
            if not match.empty:
                latest = match.iloc[-1]
            else:
                return {"DIX": None, "GEX": None}
        else:
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

def fetch_macro_data(target_dt=None):
    try:
        tickers_str = "^TNX ^IRX GC=F HG=F HYG LQD XLY XLP KBE SPY"
        tickers = yf.Tickers(tickers_str)
        prices = {}
        
        start = end = None
        if target_dt:
            start = target_dt.strftime('%Y-%m-%d')
            end = (target_dt + timedelta(days=1)).strftime('%Y-%m-%d')

        for t in tickers_str.split():
            if target_dt:
                hist = tickers.tickers[t].history(start=start, end=end)
            else:
                hist = tickers.tickers[t].history(period="1d")
                
            if not hist.empty:
                prices[t] = hist['Close'].iloc[-1]
            else:
                # If doing historical fetch and one fails, we might just skip the whole macro set
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

def run_fetch_for_date(target_dt):
    date_str = target_dt.strftime("%Y/%-m/%-d")
    print(f"\n>>> Processing Date: {date_str} <<<")
    
    # 1. Fetch Basic / API data
    # CNN and Crypto F&G are mostly "now" APIs, but we'll try for current date
    results = {
        "Date": date_str,
        "CNN": fetch_cnn_fg(),
        "VIX": fetch_vix(target_dt)
    }
    
    # 2. Fetch Expert Data from Google Sheet
    print(f"Fetching expert data from Google Sheet for {date_str}...")
    gsheet_results = fetch_gsheet_data(date_str)
    results.update(gsheet_results)
    
    # 3. Fetch DIX/GEX
    dix_data = fetch_dix(date_str)
    results["DIX"] = dix_data["DIX"]
    results["GEX"] = dix_data["GEX"]

    # 4. Crypto & Macro
    results["Crypto F&G"] = fetch_crypto_fg()
    spread, cg_ratio, hyg_lqd, xly_xlp, kbe_spy = fetch_macro_data(target_dt)
    results["10Y-3M Spread"] = spread
    results["Copper/Gold Ratio"] = cg_ratio
    results["HYG/LQD Ratio"] = hyg_lqd
    results["XLY/XLP Ratio"] = xly_xlp
    results["KBE/SPY Ratio"] = kbe_spy
    
    return results

def main():
    # Load History early
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                history = json.load(f)
        except Exception as e:
            print(f"Error loading {DATA_FILE}: {e}")

    # Determine dates to process
    from datetime import timezone
    ny_now = datetime.now(timezone.utc) - timedelta(hours=5)
    
    # Today's target (weekend adjustment)
    today_dt = ny_now
    if ny_now.weekday() == 5: # Saturday
        today_dt = ny_now - timedelta(days=1)
    elif ny_now.weekday() == 6: # Sunday
        today_dt = ny_now - timedelta(days=2)
    
    dates_to_process = [today_dt]
    
    # Check last 2 records for missing data
    # Essential keys that should not be null on business days
    essential_keys = ["DIX", "NAAIM", "CNN", "VIX", "NYSE above 20MA"]
    
    if len(history) >= 1:
        # Check the last 3 entries in history (could be last 3 days)
        for last_record in history[-3:]:
            missing_count = sum(1 for k in essential_keys if last_record.get(k) is None)
            if missing_count >= 2: # If more than 2 essential keys are missing, retry this date
                try:
                    rdt = datetime.strptime(last_record['Date'], "%Y/%-m/%-d")
                    # Avoid adding today twice
                    if rdt.date() != today_dt.date() and rdt not in [d.date() for d in dates_to_process if isinstance(d, datetime)]:
                         # Only retry if it's a weekday
                        if rdt.weekday() < 5:
                            print(f"Found missing data for {last_record['Date']} ({missing_count} keys), adding to retry list.")
                            dates_to_process.append(rdt)
                except: pass

    # Sort dates to process (oldest first)
    dates_to_process.sort()

    for target_dt in dates_to_process:
        results = run_fetch_for_date(target_dt)
        date_str = results["Date"]
        
        # Update or Append
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
    
    # Sort history by date before writing
    try:
        def sort_key(x):
            try: return datetime.strptime(x['Date'], "%Y/%-m/%-d")
            except: return datetime(1970,1,1)
        history.sort(key=sort_key)
    except: pass

    # Write History
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        print(f"\nSuccessfully updated {len(history)} records in {DATA_FILE}")
        
        # Trigger MA calculation
        calculate_all_ma()
    except Exception as e:
        print(f"CRITICAL ERROR writing to {DATA_FILE}: {e}")

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    main()
