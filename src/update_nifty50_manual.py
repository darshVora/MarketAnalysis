import pandas as pd
import os

def merge_manual_data():
    existing_csv = r"d:\Project\MarketAnalysis\src\Data\NIFTY 50_day.csv"
    manual_csv = r"d:\Project\MarketAnalysis\src\Data\nifty50_2000_2025\data.csv"
    
    print(f"Loading existing data: {existing_csv}")
    df_existing = pd.read_csv(existing_csv)
    df_existing['date'] = pd.to_datetime(df_existing['date']).dt.normalize()
    
    print(f"Loading manual data: {manual_csv}")
    df_manual = pd.read_csv(manual_csv)
    
    # Rename matching columns
    rename_map = {
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    }
    df_manual.rename(columns=rename_map, inplace=True)
    
    if 'volume' not in df_manual.columns:
        df_manual['volume'] = 0
        
    df_manual = df_manual[['date', 'open', 'high', 'low', 'close', 'volume']]
    df_manual['date'] = pd.to_datetime(df_manual['date']).dt.normalize()
    
    print("Merging...")
    # Append the manual data so that existing data takes precedence if keeping 'last'
    df_combined = pd.concat([df_manual, df_existing], ignore_index=True)
    df_combined.sort_values(by='date', inplace=True)
    df_combined.drop_duplicates(subset=['date'], keep='last', inplace=True)
    
    print(f"Final dataset has {len(df_combined)} rows (from {len(df_existing)} before).")
    print(f"New date range: {df_combined['date'].min().date()} to {df_combined['date'].max().date()}")
    
    # Format date as YYYY-MM-DD 00:00:00 to match original style
    df_combined['date'] = df_combined['date'].dt.strftime('%Y-%m-%d 00:00:00')
    
    df_combined.to_csv(existing_csv, index=False)
    print("Data successfully merged and saved!")

if __name__ == "__main__":
    merge_manual_data()
