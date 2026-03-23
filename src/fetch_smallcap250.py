import s3fs
import pandas as pd
import os

_DATA_DIR = os.path.join(os.path.dirname(__file__), "Data")

def fetch_smallcap250():
    uri = "s3://desiquant/data/indices/nse/NIFTY SMALLCAP 250.csv"
    
    s3_params = {
        "endpoint_url": "https://cbabd13f6c54798a9ec05df5b8070a6e.r2.cloudflarestorage.com",
        "key": "5c8ea9c516abfc78987bc98c70d2868a",
        "secret": "0cf64f9f0b64f6008cf5efe1529c6772daa7d7d0822f5db42a7c6a1e41b3cadf",
        "client_kwargs": {
            "region_name": "auto"
        },
    }
    
    print(f"Fetching data from {uri}...")
    try:
        df = pd.read_csv(uri, storage_options=s3_params)
        print(f"Successfully fetched {len(df)} rows.")
        
        # Display the first few rows to understand columns
        print("Data columns:", df.columns.tolist())
        print(df.head())
        
        output_file = os.path.join(_DATA_DIR, "NIFTY_SMALLCAP_250_day.csv")
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file}")
        
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    fetch_smallcap250()
