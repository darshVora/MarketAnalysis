import polars as pl
import os
import time

def distill_prices():
    bhav_dir = r"d:\Project\MarketAnalysis\src\Data\bhav_dump\bhav\nse\*.parquet*"
    output_path = r"d:\Project\MarketAnalysis\src\Data\distilled_prices.parquet"
    
    print("Initiating sequential Polars extraction over 740+ Bhavcopy files...")
    start = time.time()
    
    import glob
    files = glob.glob(r"d:\Project\MarketAnalysis\src\Data\bhav_dump\bhav\nse\*.parquet*")
    
    dataframes = []
    
    for idx, f in enumerate(files):
        if idx % 100 == 0:
            print(f"Processed {idx}/{len(files)} files...")
            
        try:
            # First peek at columns to handle case sensitivity over historical evolutions
            schema = pl.read_parquet_schema(f)
            cols = list(schema.keys())
            
            # Find the actual names for our 4 target columns
            col_map = {}
            for c in cols:
                cu = c.upper()
                if cu in ['SYMBOL', 'TIMESTAMP', 'CLOSE', 'INSTRUMENT']:
                    col_map[cu] = c
            
            if not all(k in col_map for k in ['SYMBOL', 'TIMESTAMP', 'CLOSE', 'INSTRUMENT']):
                continue
                
            df = pl.read_parquet(f, columns=list(col_map.values()))
            
            # Standardize column names
            df = df.rename({col_map[k]: k for k in col_map})
            
            # Filter solely for Equity/Futures instruments (dropping options and bonds)
            df = df.filter(pl.col("INSTRUMENT").is_in(["EQ", "FUTSTK", "FUTIDX"]))
            
            dataframes.append(df)
        except Exception as e:
            print(f"Failed to read {f}: {e}")
            
    if dataframes:
        final_df = pl.concat(dataframes, how="vertical_relaxed")
        final_df = final_df.group_by(["SYMBOL", "TIMESTAMP"]).agg(pl.col("CLOSE").mean())
        
        print(f"Extraction successful! Distilled {len(final_df)} price rows.")
        print(f"Saving to {output_path}...")
        final_df.write_parquet(output_path)
        
        end = time.time()
        print(f"Complete! Distillation took {end - start:.2f} seconds.")
    else:
        print("No valid dataframes were generated.")

if __name__ == "__main__":
    distill_prices()
