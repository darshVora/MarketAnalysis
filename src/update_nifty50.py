import pandas as pd
from jugaad_data.nse import index_df
from datetime import date, timedelta
import os
import time

def update_nifty50_data():
    csv_path = r"d:\Project\MarketAnalysis\src\Data\NIFTY 50_day.csv"
    
    print(f"Loading existing data from {csv_path}...")
    df_existing = pd.read_csv(csv_path)
    df_existing['date'] = pd.to_datetime(df_existing['date'])
    
    min_date = df_existing['date'].min()
    print(f"Earliest date in current dataset: {min_date.date()}")
    
    start_date = date(1995, 1, 1)
    end_date = min_date.date() - timedelta(days=1)
    
    print(f"Fetching historical NIFTY 50 index data from {start_date} to {end_date} in chunks...")
    
    df_new_list = []
    current_start = start_date
    while current_start <= end_date:
        current_end = min(current_start + timedelta(days=365), end_date)
        print(f"Fetching {current_start} to {current_end}...")
        try:
            # index_df returns a pandas dataframe
            chunk = index_df(symbol="NIFTY 50", from_date=current_start, to_date=current_end)
            if not chunk.empty:
                df_new_list.append(chunk)
            time.sleep(1) # Prevent rate limiting
        except Exception as e:
            print(f"Error fetching {current_start} to {current_end}: {e}")
        current_start = current_end + timedelta(days=1)
        
    df_new = pd.concat(df_new_list) if df_new_list else pd.DataFrame()
    
    if df_new.empty:
        print("No new data fetched. Could be rate limited or already fully backfilled.")
        return
        
    print(f"Fetched {len(df_new)} rows of new historical data.")
    
    # jugaad_data returns columns: Index Name, Index Date, Open Index Value, High Index Value, Low Index Value, Closing Index Value, Points Change, Change(%), Volume, Turnover (Rs. Cr.), P/E, P/B, Div Yield
    rename_map = {
        'Index Date': 'date',
        'Open Index Value': 'open',
        'High Index Value': 'high',
        'Low Index Value': 'low',
        'Closing Index Value': 'close',
        'Volume': 'volume'
    }
    df_new.rename(columns=rename_map, inplace=True)
    
    cols_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume']
    for col in cols_to_keep:
        if col not in df_new.columns:
            df_new[col] = 0
            
    df_new = df_new[cols_to_keep]
    df_new['date'] = pd.to_datetime(df_new['date'])
    
    print("Merging datasets...")
    df_combined = pd.concat([df_new, df_existing], ignore_index=True)
    
    df_combined.sort_values(by='date', inplace=True)
    df_combined.drop_duplicates(subset=['date'], keep='last', inplace=True)
    
    print(f"Total rows after merge: {len(df_combined)} (was {len(df_existing)})")
    print(f"New date range: {df_combined['date'].min().date()} to {df_combined['date'].max().date()}")
    
    df_combined['date'] = df_combined['date'].dt.strftime('%Y-%m-%d 00:00:00')
    
    print(f"Saving merged data back to {csv_path}...")
    df_combined.to_csv(csv_path, index=False)
    print("Done!")

if __name__ == "__main__":
    update_nifty50_data()
