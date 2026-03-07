import json
import os
import pandas as pd
from datetime import datetime

HISTORY_FILE = "data/history.json"
MA_FILE = "data/history_ma.json"

def calculate_all_ma():
    if not os.path.exists(HISTORY_FILE):
        print(f"Error: {HISTORY_FILE} not found.")
        return

    try:
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
    except Exception as e:
        print(f"Error loading history: {e}")
        return

    if not history:
        return

    # Create DataFrame
    df = pd.DataFrame(history)
    
    # Identify numeric columns (excluding Date)
    numeric_cols = [col for col in df.columns if col != 'Date']
    
    # Ensure DataFrame is sorted by date
    def parse_date(d_str):
        parts = d_str.split('/')
        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
    
    df['parsed_date'] = df['Date'].apply(parse_date)
    df = df.sort_values('parsed_date').reset_index(drop=True)
    
    ma_results = []
    
    for i in range(len(df)):
        record = {"Date": df.loc[i, 'Date']}
        
        for col in numeric_cols:
            # Skip if current value is NaN
            if pd.isna(df.loc[i, col]):
                continue
                
            # Calculate 5, 10, 20 MA
            for window in [5, 10, 20]:
                if i >= window - 1:
                    # Get the window of values, dropping NaNs
                    window_values = df.loc[i-window+1:i, col].dropna()
                    if len(window_values) >= window / 2: # At least half data points present
                        record[f"{col}_{window}MA"] = round(float(window_values.mean()), 3)
        
        ma_results.append(record)

    # Save to file
    with open(MA_FILE, 'w') as f:
        json.dump(ma_results, f, indent=2)
    
    print(f"MA calculation complete. Saved to {MA_FILE}")

if __name__ == "__main__":
    calculate_all_ma()
