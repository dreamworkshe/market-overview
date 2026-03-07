import json
import os
import pandas as pd
from datetime import datetime
from calculate_ma import calculate_all_ma

DATA_FILE = "data/history.json"
DIX_URL = "https://squeezemetrics.com/monitor/static/DIX.csv"

def backfill():
    # 1. Load existing history
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                history = json.load(f)
        except:
            history = []
    
    # 2. Download DIX/GEX data
    print(f"Downloading historical DIX/GEX data...")
    try:
        df = pd.read_csv(DIX_URL)
    except Exception as e:
        print(f"Error downloading CSV: {e}")
        return

    # 3. Get last 30 business days
    df_last_30 = df.tail(30).copy()
    
    # Map of date_str (Y/M/D) -> record index in existing history
    history_map = {r['Date']: i for i, r in enumerate(history)}
    
    updates_count = 0
    new_count = 0
    
    for _, row in df_last_30.iterrows():
        # Convert YYYY-MM-DD to YYYY/M/D explicitly
        dt = datetime.strptime(row['date'], '%Y-%m-%d')
        date_str = f"{dt.year}/{dt.month}/{dt.day}"
        
        dix_val = round(float(row['dix']) * 100, 2)
        gex_val = round(float(row['gex']) / 1e9, 2)
        
        if date_str in history_map:
            # Update existing row
            idx = history_map[date_str]
            history[idx]['DIX'] = dix_val
            history[idx]['GEX'] = gex_val
            updates_count += 1
        else:
            # Create new row
            new_record = {
                "Date": date_str,
                "DIX": dix_val,
                "GEX": gex_val
            }
            history.append(new_record)
            new_count += 1
            
    # 4. Sort history by date carefully
    def parse_date(d_str):
        parts = d_str.split('/')
        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))

    history.sort(key=lambda x: parse_date(x['Date']))

    # 5. Write back to file
    with open(DATA_FILE, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"Backfill complete: Updated {updates_count} records, added {new_count} new records.")
    
    # Recalculate MA
    calculate_all_ma()

if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
    backfill()
