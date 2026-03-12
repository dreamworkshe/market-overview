import json
import os
import re
import time
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from fredapi import Fred
from calculate_ma import calculate_all_ma # Import MA calculation

load_dotenv()
FRED_KEY = os.getenv("FRED_API_KEY")

DATA_FILE = "data/history.json"
GSHEET_ID = "18NLQo5n6Ni_NrMWuhIr9dUZFc57AKbxGVzK6M7V-FBg"

def fetch_cnn_fg(target_dt=None):
    url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    import requests
    try:
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        def get_exact(comp):
            if comp is None: return None
            if target_dt is None:
                return round(comp.get('score', 0), 2)
            from datetime import timezone
            target_date = target_dt.date()
            for d in comp.get('data', []):
                pt_date = datetime.fromtimestamp(d['x'] / 1000.0, timezone.utc).date()
                if pt_date == target_date:
                    return round(d['y'], 2)
            return None
            
        return {
            "score": get_exact(data.get('fear_and_greed_historical') or data.get('fear_and_greed')),
            "net_new_highs": get_exact(data['stock_price_strength']),
            "mc_breadth": get_exact(data['stock_price_breadth'])
        }
    except Exception as e:
        print(f"Error CNN F&G: {e}")
        return {"score": None, "net_new_highs": None, "mc_breadth": None}

def fetch_fed_liquidity(target_dt=None):
    if not FRED_KEY: return None, None, None
    try:
        fred = Fred(api_key=FRED_KEY)
        
        def get_exact_val(series_id):
            if target_dt:
                date_str = target_dt.strftime('%Y-%m-%d')
                data = fred.get_series(series_id, observation_start=date_str, observation_end=date_str)
            else:
                data = fred.get_series(series_id)
            if not data.empty:
                return data.iloc[-1]
            return None
            
        assets = get_exact_val('WALCL')
        rrp = get_exact_val('RRPONTSYD')
        tga = get_exact_val('WTREGEN')
        
        assets_b = assets / 1000.0 if assets is not None else None
        tga_b = tga / 1000.0 if tga is not None else None
        
        if assets_b is not None and rrp is not None and tga_b is not None:
            liquidity = round(assets_b - rrp - tga_b, 2)
        else:
            liquidity = None
            
        return liquidity, (round(rrp, 2) if rrp is not None else None), (round(tga_b, 2) if tga is not None else None)
    except Exception as e:
        print(f"Error Fed Liquidity: {e}")
        return None, None, None

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

def fetch_hy_oas(target_dt=None):
    if not FRED_KEY or FRED_KEY == "your_api_key_here":
        print("FRED API Key not set.")
        return None
    try:
        fred = Fred(api_key=FRED_KEY)
        series_id = 'BAMLH0A0HYM2'
        if target_dt:
            date_str = target_dt.strftime('%Y-%m-%d')
            data = fred.get_series(series_id, observation_start=date_str, observation_end=date_str)
            if not data.empty:
                return round(float(data.iloc[-1]), 2)
        else:
            data = fred.get_series(series_id)
            if not data.empty:
                return round(float(data.iloc[-1]), 2)
    except Exception as e:
        print(f"Error FRED HY OAS: {e}")
    return None

def fetch_indices(target_dt=None):
    try:
        tickers_str = "^GSPC ^IXIC"
        tickers = yf.Tickers(tickers_str)
        results = {}
        
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
                name = "SPX" if t == "^GSPC" else "NASDAQ"
                results[name] = round(float(hist['Close'].iloc[-1]), 2)
            else:
                return {"SPX": None, "NASDAQ": None}
        return results
    except Exception as e:
        print(f"Error fetching Indices: {e}")
        return {"SPX": None, "NASDAQ": None}

def fetch_sentiment_indicators(target_dt=None):
    try:
        tickers_str = "^VIX3M ^SKEW"
        tickers = yf.Tickers(tickers_str)
        results = {}
        
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
                name = "VIX3M" if t == "^VIX3M" else "SKEW"
                results[name] = round(float(hist['Close'].iloc[-1]), 2)
            else:
                results["VIX3M" if t == "^VIX3M" else "SKEW"] = None
        return results
    except Exception as e:
        print(f"Error fetching Sentiment Indicators: {e}")
        return {"VIX3M": None, "SKEW": None}

def fetch_macro_data(target_dt=None):
    try:
        tickers_str = "^TNX ^IRX GC=F HG=F HYG LQD XLY XLP KBE SPY QQQ RSP IEF DX-Y.NYB TLT"
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
                prices[t] = None
                
        def calc_ratio(n, d):
            if prices.get(n) is not None and prices.get(d) is not None:
                return round(prices[n] / prices[d], 4)
            return None
        
        spread = round(prices["^TNX"] - prices["^IRX"], 3) if prices.get("^TNX") is not None and prices.get("^IRX") is not None else None
        cg_ratio = calc_ratio("HG=F", "GC=F")
        hyg_lqd = calc_ratio("HYG", "LQD")
        xly_xlp = calc_ratio("XLY", "XLP")
        kbe_spy = calc_ratio("KBE", "SPY")
        qqq_spy = calc_ratio("QQQ", "SPY")
        rsp_spy = calc_ratio("RSP", "SPY")
        hyg_ief = calc_ratio("HYG", "IEF")
        dxy = round(prices["DX-Y.NYB"], 2) if prices.get("DX-Y.NYB") is not None else None
        tlt = round(prices["TLT"], 2) if prices.get("TLT") is not None else None
        
        return spread, cg_ratio, hyg_lqd, xly_xlp, kbe_spy, qqq_spy, rsp_spy, hyg_ief, dxy, tlt
    except Exception as e:
        print(f"Error fetching Macro data: {e}")
        return None, None, None, None, None, None, None, None, None, None

def run_fetch_for_date(target_dt):
    date_str = target_dt.strftime("%Y/%-m/%-d")
    print(f"\n>>> Processing Date: {date_str} <<<")
    
    # 1. Fetch Basic / API data
    cnn_data = fetch_cnn_fg(target_dt)
    results = {
        "Date": date_str,
        "CNN": cnn_data.get("score"),
        "Net New Highs": cnn_data.get("net_new_highs"),
        "McClellan Summation": cnn_data.get("mc_breadth"),
        "VIX": fetch_vix(target_dt),
        "HY OAS": fetch_hy_oas(target_dt)
    }

    # Liquidity
    liq, rrp, tga = fetch_fed_liquidity(target_dt)
    results["Fed Liquidity"] = liq
    results["RRP"] = rrp
    results["TGA"] = tga

    # Add VIX3M and SKEW
    sent_ind = fetch_sentiment_indicators(target_dt)
    results.update(sent_ind)
    if results.get("VIX") is not None and results.get("VIX3M") is not None:
        results["VIX/VIX3M Ratio"] = round(results["VIX"] / results["VIX3M"], 4)
    else:
        results["VIX/VIX3M Ratio"] = None
    
    # 2. Fetch Expert Data from Google Sheet
    print(f"Fetching expert data from Google Sheet for {date_str}...")
    gsheet_results = fetch_gsheet_data(date_str)
    results.update(gsheet_results)
    
    # 3. Fetch DIX/GEX
    dix_data = fetch_dix(date_str)
    results["DIX"] = dix_data["DIX"]
    results["GEX"] = dix_data["GEX"]

    # 4. Indices (Optional for data depth, but not cards)
    indices = fetch_indices(target_dt)
    results.update(indices)

    # 5. Crypto & Macro
    results["Crypto F&G"] = fetch_crypto_fg()
    macro_vals = fetch_macro_data(target_dt)
    if all(v is not None for v in macro_vals):
        spread, cg_ratio, hyg_lqd, xly_xlp, kbe_spy, qqq_spy, rsp_spy, hyg_ief, dxy, tlt = macro_vals
        results["10Y-3M Spread"] = spread
        results["Copper/Gold Ratio"] = cg_ratio
        results["HYG/LQD Ratio"] = hyg_lqd
        results["XLY/XLP Ratio"] = xly_xlp
        results["KBE/SPY Ratio"] = kbe_spy
        results["QQQ/SPY Ratio"] = qqq_spy
        results["RSP/SPY Ratio"] = rsp_spy
        results["HYG/IEF Ratio"] = hyg_ief
        results["DXY"] = dxy
        results["TLT"] = tlt
    
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

    # Determine dates to process: Check last 3 business days
    from datetime import timezone
    ny_now = datetime.now(timezone.utc) - timedelta(hours=5)
    
    # If NY time is before 6 PM (18:00), don't treat today as a completed trading day yet
    if ny_now.hour < 18:
        ny_now -= timedelta(days=1)
    
    # We want to check the last 3 potential business days
    dates_to_check = []
    temp_dt = ny_now
    while len(dates_to_check) < 3:
        if temp_dt.weekday() < 5:
            dates_to_check.append(temp_dt)
        temp_dt -= timedelta(days=1)
    
    today_dt = dates_to_check[0]
    dates_to_process = []
    essential_keys = ["DIX", "NAAIM", "CNN", "VIX", "NYSE above 20MA", "GEX", "SPX", "Net New Highs", "McClellan Summation", "HY OAS"]

    # Check which of these dates need processing
    for work_dt in dates_to_check:
        work_date_str = work_dt.strftime("%Y/%-m/%-d")
        
        # Find local record
        record = next((r for r in history if r['Date'] == work_date_str), None)
        
        if record is None:
            print(f"Missing record for {work_date_str}, adding to fetch list.")
            dates_to_process.append(work_dt)
        else:
            # Check for missing essential data
            missing_essential = [k for k in essential_keys if record.get(k) is None]
            if missing_essential:
                print(f"Record for {work_date_str} has missing keys: {missing_essential}. Retrying.")
                dates_to_process.append(work_dt)

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
