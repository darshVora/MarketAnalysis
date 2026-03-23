import os
import polars as pl

def explore_data():
    base_dir = r"d:\Project\MarketAnalysis\src\Data"
    
    # 1. Find a Result file
    result_files = []
    for root, dirs, files in os.walk(base_dir):
        if 'result' in root.lower() or 'results' in root.lower():
            for f in files:
                if f.endswith('.parquet'):
                    result_files.append(os.path.join(root, f))
    
    # 2. Find a Bhav file
    bhav_files = []
    for root, dirs, files in os.walk(base_dir):
        if 'bhav' in root.lower() and 'nse' in root.lower():
            for f in files:
                if f.endswith('.parquet') or f.endswith('.parquet.gz'):
                    bhav_files.append(os.path.join(root, f))
                    
    with open('eda_output.txt', 'w') as out:
        if result_files:
            out.write("--- FOUND RESULTS FILE ---\n")
            out.write(f"Total result files found: {len(result_files)}\n")
            out.write(f"Sample Path: {result_files[0]}\n")
            try:
                df = pl.read_parquet(result_files[0])
                out.write(f"Schema:\n{df.schema}\n\n")
                out.write(f"Data:\n{df.head().to_pandas().to_string()}\n\n")
            except Exception as e:
                out.write(f"Error reading result: {e}\n\n")
        else:
            out.write("NO RESULTS FILES FOUND\n\n")
            
        if bhav_files:
            out.write("--- FOUND BHAV FILE ---\n")
            out.write(f"Total bhav files found: {len(bhav_files)}\n")
            out.write(f"Sample Path: {bhav_files[0]}\n")
            try:
                df = pl.read_parquet(bhav_files[0])
                out.write(f"Schema:\n{df.schema}\n\n")
                out.write(f"Data:\n{df.head().to_pandas().to_string()}\n\n")
            except Exception as e:
                out.write(f"Error reading bhav: {e}\n\n")

if __name__ == "__main__":
    explore_data()
