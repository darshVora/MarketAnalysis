import polars as pl
import os
import glob
import time
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def compile_dataset():
    price_path = r"d:\Project\MarketAnalysis\src\Data\distilled_prices.parquet"
    res_dir = r"d:\Project\MarketAnalysis\src\Data\desiquant_aux\results\nse\*.parquet"
    output_path = r"d:\Project\MarketAnalysis\src\Data\earnings_model_data.parquet"
    
    print("Loading distilled price database...")
    prices_df = pl.read_parquet(price_path)
    
    # Standardize dates
    if prices_df['TIMESTAMP'].dtype == pl.String:
        prices_df = prices_df.with_columns(
            pl.coalesce([
                pl.col('TIMESTAMP').str.strptime(pl.Date, "%d-%b-%Y", strict=False),
                pl.col('TIMESTAMP').str.strptime(pl.Date, "%Y-%m-%d", strict=False)
            ]).alias('date')
        )
    else:
        prices_df = prices_df.with_columns(pl.col('TIMESTAMP').cast(pl.Date).alias('date'))
        
    prices_df = prices_df.drop_nulls('date').sort(['SYMBOL', 'date'])
    
    print("Finding corporate results files...")
    res_files = glob.glob(res_dir)
    
    dataset_rows = []
    
    print(f"Extracting features from {len(res_files)} stocks...")
    start = time.time()
    
    for count, f in enumerate(res_files):
        if count > 0 and count % 200 == 0:
            print(f"Parsed {count}/{len(res_files)} corporate earnings histories...")
            
        try:
            symbol = os.path.basename(f).replace('.parquet', '')
            res_df = pl.read_parquet(f)
            
            if 'filingDate' not in res_df.columns or 'resultsData2.re_net_profit' not in res_df.columns:
                continue
            
            # Extract filing date and metrics
            events = res_df.select([
                pl.col('filingDate'),
                pl.col('resultsData2.re_net_profit').alias('net_profit'),
                pl.col('resultsData2.re_net_sale').alias('revenue')
            ]).drop_nulls('filingDate')
            
            # Try parsing filingDate to Date. It might be '26-Oct-2023 12:07'
            events = events.with_columns(
                pl.col('filingDate').str.split(' ').list.get(0).str.strptime(pl.Date, "%d-%b-%Y", strict=False).alias('event_date')
            )
            # drop failures
            events = events.drop_nulls('event_date')
            events = events.with_columns(
                pl.col('net_profit').str.replace_all(',', '').cast(pl.Float64, strict=False),
                pl.col('revenue').str.replace_all(',', '').cast(pl.Float64, strict=False)
            )
            
            events = events.sort('event_date')
            
            # calculate YoY Growth (shift 4 quarters since data is quarterly)
            events = events.with_columns([
                ((pl.col('net_profit') - pl.col('net_profit').shift(4)) / pl.col('net_profit').shift(4).abs()).alias('profit_yoy_growth'),
                ((pl.col('revenue') - pl.col('revenue').shift(4)) / pl.col('revenue').shift(4).abs()).alias('rev_yoy_growth')
            ])
            
            # Filter prices for this symbol to quickly fetch nearest returns
            s_prices = prices_df.filter(pl.col('SYMBOL') == symbol)
            if s_prices.height < 50:
                continue
                
            price_dates = s_prices['date'].to_list()
            price_closes = s_prices['CLOSE'].to_list()
            # Fast index search needs integer ordinal arrays
            date_array = np.array([d.toordinal() for d in price_dates])
            
            for row in events.iter_rows(named=True):
                evt_date = row['event_date']
                if evt_date is None or row['profit_yoy_growth'] is None:
                    continue
                
                # To find T-20, T-1, T+1, T+20, we use idx in the sorted price array
                # Find the closest trading day strictly prior to the event
                e_ord = evt_date.toordinal()
                idx = np.searchsorted(date_array, e_ord)
                
                # Check absolute boundaries so we don't index out of bounds
                if idx < 20 or idx >= len(date_array) - 21:
                    continue 
                    
                t_minus_1 = price_closes[idx-1]
                t_minus_20 = price_closes[idx-20]
                t_plus_1 = price_closes[idx]
                t_plus_20 = price_closes[idx+20]
                
                # Avoid divide by zero
                if t_minus_20 == 0 or t_plus_1 == 0:
                    continue
                    
                pre_runup = (t_minus_1 - t_minus_20) / t_minus_20 * 100
                forward_drift = (t_plus_20 - t_plus_1) / t_plus_1 * 100
                
                # Exclude extreme infinity outliers caused by stock splits without adjustment
                if abs(forward_drift) > 200 or abs(pre_runup) > 200:
                    continue
                
                dataset_rows.append({
                    'symbol': symbol,
                    'event_date': evt_date,
                    'net_profit': float(row['net_profit']),
                    'profit_yoy_growth': float(row['profit_yoy_growth']),
                    'rev_yoy_growth': float(row['rev_yoy_growth'] if row['rev_yoy_growth'] else 0.0),
                    'pre_runup_20d_%': float(pre_runup),
                    'forward_drift_20d_%': float(forward_drift)
                })
                
        except Exception as e:
            continue
            
    if dataset_rows:
        final_df = pl.DataFrame(dataset_rows)
        # Drop inf values from naive division
        final_df = final_df.filter(~pl.col('profit_yoy_growth').is_nan() & ~pl.col('profit_yoy_growth').is_infinite())
        
        print(f"\nSUCCESS! Constructed Master Earnings Dataset with {len(final_df)} corporate earnings events matched to exact post-earnings market behavior!")
        final_df.write_parquet(output_path)
        print(f"Saved to {output_path}")
        print("\nDataset Snapshot:")
        print(final_df.head())
    else:
        print("Failed to map any overlap between earnings ranges and price dates.")

if __name__ == "__main__":
    compile_dataset()
