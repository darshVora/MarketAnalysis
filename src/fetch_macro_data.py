import yfinance as yf
import pandas as pd
import os

def fetch_macro_data():
    tickers = {
        'S&P500': '^GSPC',
        'DXY': 'DX-Y.NYB',
        'India_10Y_Yield': '^IN10YT',
        'USD_INR': 'INR=X',
        'Gold': 'GC=F',
        'Crude_Oil': 'BZ=F'
    }
    
    print("Fetching macroeconomic data from Yahoo Finance...")
    macro_dfs = []
    
    for name, symbol in tickers.items():
        print(f"Fetching {name} ({symbol})...")
        ticker = yf.Ticker(symbol)
        try:
            df = ticker.history(period="max")
            if not df.empty:
                # Keep only the Close price for macro indicators
                df = df[['Close']].rename(columns={'Close': name})
                df.index = pd.to_datetime(df.index).tz_localize(None).normalize()
                macro_dfs.append(df)
            else:
                print(f"Warning: No data found for {name}")
        except Exception as e:
            print(f"Error fetching {name}: {e}")
            
    if macro_dfs:
        print("Combining macroeconomic datasets...")
        # Join all macro dataframes on the Date index using an outer join
        combined_df = macro_dfs[0]
        for df in macro_dfs[1:]:
            combined_df = combined_df.join(df, how='outer')
            
        # Drop rows where everything is NaN
        combined_df.dropna(how='all', inplace=True)
        
        # Forward fill to handle mismatches in holiday schedules between India and US
        combined_df.ffill(inplace=True)
        
        # Reset index to make strictly a 'date' column
        combined_df.reset_index(inplace=True)
        # Handle index naming properly
        if 'Date' in combined_df.columns:
            combined_df.rename(columns={'Date': 'date'}, inplace=True)
        elif 'index' in combined_df.columns:
            combined_df.rename(columns={'index': 'date'}, inplace=True)
            
        out_path = r"d:\Project\MarketAnalysis\src\Data\macro_data.csv"
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        combined_df.to_csv(out_path, index=False)
        
        print(f"Successfully saved combined macro data to {out_path}")
        print(f"Date range: {combined_df['date'].min().date()} to {combined_df['date'].max().date()}")
        print(f"Rows: {len(combined_df)}")
    else:
        print("Failed to fetch any macro data.")

if __name__ == "__main__":
    fetch_macro_data()
