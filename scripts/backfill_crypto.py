import json
import os
import requests
from datetime import datetime
from calculate_ma import calculate_all_ma

DATA_FILE = "data/history.json"
CRYPTO_URL = "https://api.alternative.me/fng/?limit=60" # Fetch 60 days to be safe

def backfill_crypto():
    if not os.path.exists(DATA_FILE):
        print("History file not found.")
        return

    try:
        with open(DATA_FILE, 'r') as f:
            history = json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
        return

    print("Fetching Crypto Fear & Greed history...")
    try:
        response = requests.get(CRYPTO_URL, timeout=10)
        data = response.json()
        crypto_data = data.get('data', [])
    except Exception as e:
        print(f"Error fetching API: {e}")
        return

    # Create a map of Date -> Value
    crypto_map = {}
    for item in crypto_data:
        ts = int(item['timestamp'])
        dt = datetime.fromtimestamp(ts)
        date_str = dt.strftime("%Y/%-m/%-d")
        crypto_map[date_str] = int(item['value'])

    updates = 0
    for record in history:
        d = record['Date']
        if d in crypto_map:
            if record.get('Crypto F&G') != crypto_map[d]:
                record['Crypto F&G'] = crypto_map[d]
                updates += 1

    if updates > 0:
        # Sort history by date
        def parse_date(d_str):
            parts = d_str.split('/')
            return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
        
        history.sort(key=lambda x: parse_date(x['Date']))

        with open(DATA_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"Backfill complete: Updated {updates} records with Crypto F&G data.")
        
        # Trigger MA Recalculation
        calculate_all_ma()
    else:
        print("No updates needed for Crypto F&G.")

if __name__ == "__main__":
    backfill_crypto()
