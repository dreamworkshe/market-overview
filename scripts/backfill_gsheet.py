import json
import os
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

DATA_FILE = "data/history.json"
GSHEET_ID = "18NLQo5n6Ni_NrMWuhIr9dUZFc57AKbxGVzK6M7V-FBg"

# Mappings: JSON Key -> Column Header in GSheet
COLUMN_MAPPING = {
    "CNN": "CNN",
    "VIX": "VIX",
    "Total P/C Ratio": "Total P/C Ratio",
    "Equity P/C Ratio": "Equity P/C Ratio",
    "NAAIM": "NAAIM",
    "AAII B-B": "AAII B-B",
    "NYSE above 20MA": "NYSE above 20MA",
    "NASDAQ above 20MA": "NASDAQ above 20MA",
    "NYSE above 50MA": "NYSE above 50MA",
    "NASDAQ above 50MA": "NASDAQ above 50MA"
}

def parse_date(d_str):
    try:
        parts = d_str.strip().split('/')
        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    except:
        return None

def backfill_from_gsheet():
    # 1. Load existing history
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # 2. Connect to Google Sheets
    print("Connecting to Google Sheets...")
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds_path = "credentials.json"
    if not os.path.exists(creds_path):
        print("Error: credentials.json not found.")
        return

    try:
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sh = client.open_by_key(GSHEET_ID)
        worksheet = sh.worksheet("Log")
        all_data = worksheet.get_all_values()
        
        header = [h.strip() for h in all_data[0]]
        rows = all_data[1:]
        
        # Column Index Map
        col_map = {name: i for i, name in enumerate(header)}
    except Exception as e:
        print(f"Connection Error: {e}")
        return

    # 3. Process the last 30 entries (or more if you prefer)
    # We take the last 40 to ensure we have enough business days
    target_rows = rows[-40:]
    
    history_dict = {r['Date']: r for r in history}
    
    updated_count = 0
    added_count = 0
    
    for row in target_rows:
        raw_date = row[0].strip()
        if not raw_date: continue
        
        # Format date as YYYY/M/D (no leading zeros)
        dt = parse_date(raw_date)
        if not dt: continue
        date_str = f"{dt.year}/{dt.month}/{dt.day}"
        
        # Get/Create record
        if date_str in history_dict:
            record = history_dict[date_str]
            updated_count += 1
        else:
            record = {"Date": date_str}
            history.append(record)
            history_dict[date_str] = record
            added_count += 1
            
        # Map values
        for json_key, gsheet_col in COLUMN_MAPPING.items():
            if gsheet_col in col_map:
                val = row[col_map[gsheet_col]].strip()
                if val:
                    try:
                        # Clean values (remove %, commas)
                        clean_val = val.replace('%', '').replace(',', '')
                        if '.' in clean_val:
                            record[json_key] = round(float(clean_val), 2)
                        else:
                            record[json_key] = int(clean_val)
                    except:
                        pass # Keep existing or skip if invalid

    # 4. Sort history by date
    history.sort(key=lambda x: parse_date(x['Date']))

    # 5. Save back to file
    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"GSheet Backfill Complete: Added {added_count} new dates, updated {updated_count} existing dates.")

if __name__ == "__main__":
    backfill_from_gsheet()
